import sys, json
from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(name,cond,info=''):
    print(('OK  ' if cond else 'FAIL'),name,info if not cond else '')
    if not cond: fails.append(name)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e)))
    pg.on('console',lambda m:errs.append('CONSOLE '+m.text) if m.type=='error' and 'TUNNEL' not in m.text else None)
    pg.route('**/*fonts.*',lambda r:r.abort())
    pg.goto('http://localhost:8000/'); pg.evaluate("localStorage.setItem('daybook-lang','en')"); pg.reload(); pg.wait_for_timeout(400)
    def go(h,w=500): pg.evaluate(f"location.hash='{h}'"); pg.wait_for_timeout(w)
    def toast(): return pg.evaluate("[].map.call(document.querySelectorAll('#toasts .toast'),e=>e.textContent).join(' | ')")
    def txt(sel): return pg.inner_text(sel)
    # login
    go('login'); pg.fill('#u','admin'); pg.fill('#pw','wrong'); pg.click('#loginForm button[type=submit]'); pg.wait_for_timeout(700)
    check('wrong password shows error', 'password' in txt('#ep').lower() or len(txt('#ep'))>0, txt('#ep'))
    pg.fill('#pw','admin123'); pg.click('#loginForm button[type=submit]'); pg.wait_for_timeout(1500)
    check('logged in -> dashboard', pg.evaluate('location.hash')=='#dashboard')
    # supplier + customer
    go('suppliers'); pg.click('#sunew'); pg.fill('#sun','Sement Savdo'); pg.fill('#suph','+998 90 111'); pg.click('#susave'); pg.wait_for_timeout(700)
    check('supplier saved', 'Sement Savdo' in txt('#sutbl'), txt('#sutbl')[:200])
    pg.click('#sunew'); pg.fill('#sun','Sement Savdo'); pg.click('#susave'); pg.wait_for_timeout(500)
    check('duplicate supplier rejected', pg.is_visible('#suform'))
    pg.click('#sucancel')
    go('customers'); pg.click('#cunew'); pg.fill('#cun','Orient Stroy'); pg.fill('#cuph','+998 90 222'); pg.click('#cusave'); pg.wait_for_timeout(700)
    check('customer saved', 'Orient Stroy' in txt('#cutbl'))
    # receipt of materials
    go('receipt-new'); pg.wait_for_timeout(300)
    pg.fill('#rcsup','Sement Savdo')
    mats=[('Sement',100000,'1150'),('Klinets',200000,'190'),('Qum',150000,'150'),('Armatura',5000,'9500')]
    for i,(n,q,pr) in enumerate(mats):
        if i>0: pg.click('#rcadd')
        pg.fill(f'#rcm{i}',n); pg.fill(f'#rcq{i}',str(q)); pg.fill(f'#rcr{i}',pr)
    pg.click('#rcsave'); pg.wait_for_timeout(1000)
    check('receipt posted', pg.evaluate('location.hash')=='#receipts' and 'Sement' in txt('#rctbl'), toast()+txt('#rctbl')[:200])
    go('warehouse'); 
    check('stock shows cement 100,000', '100,000' in txt('#wtbl'), txt('#wtbl')[:300])
    # production
    go('production-new'); pg.wait_for_timeout(300)
    pg.fill('#pr0','2ПК 66*12'); pg.fill('#pq0','10'); pg.click('#pfill'); pg.click('#ppost'); pg.wait_for_timeout(1000)
    check('production posted', pg.evaluate('location.hash')=='#production' and 'PRD-' in txt('#plog'), toast()+txt('#pdone'))
    go('warehouse'); pg.select_option('#wsite','0'); pg.wait_for_timeout(300)
    t=txt('#wtbl'); check('site stock has 10 slabs and 96,100 cement', '2ПК 66*12' in t and '96,100' in t, t[:300])
    # production fails: not enough materials
    go('production-new'); pg.wait_for_timeout(300); pg.select_option('#psite','1')
    pg.fill('#pr0','2ПК 66*12'); pg.fill('#pq0','5'); pg.click('#pfill'); pg.click('#ppost'); pg.wait_for_timeout(800)
    check('insufficient materials rejected', 'Not enough' in txt('#pmsg'), txt('#pmsg'))
    # order
    go('order-new'); pg.wait_for_timeout(300)
    pg.fill('#odcus','Orient Stroy'); pg.fill('#odp0','2ПК 66*12'); pg.fill('#odq0','6'); pg.fill('#odr0','3000000'); pg.click('#odsave'); pg.wait_for_timeout(1000)
    check('order saved', pg.evaluate('location.hash')=='#orders' and 'ZK-' in txt('#odtbl'), toast()+txt('#oderr'))
    # invoice for more than on order
    go('invoice-new'); pg.wait_for_timeout(300)
    pg.fill('#ivcus','Orient Stroy'); pg.wait_for_timeout(200)
    pg.select_option('#ivord', index=1); pg.wait_for_timeout(300)
    pg.select_option('#ivsite','0')
    pg.fill('#ivq0','7'); pg.click('#ivsave'); pg.wait_for_timeout(800)
    check('over-order shipment rejected', 'left to ship' in txt('#iverr'), txt('#iverr'))
    pg.fill('#ivq0','6'); pg.click('#ivsave'); pg.wait_for_timeout(1000)
    check('invoice posted', pg.evaluate('location.hash')=='#invoices' and 'RN-' in txt('#ivtbl'), toast()+txt('#iverr'))
    go('warehouse'); pg.select_option('#wsite','0'); pg.wait_for_timeout(300)
    check('stock reduced to 4', '<b>4</b>' in pg.inner_html('#wtbl') or '>4<' in pg.inner_html('#wtbl'), txt('#wtbl')[:200])
    go('customers'); check('customer debt 18 000 000', '18' in txt('#cutbl') and '000' in txt('#cutbl'), txt('#cutbl'))
    # payment
    go('bank'); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#fnew button[data-k=in]').click()"); pg.wait_for_timeout(500)
    pg.select_option('#fart','cust'); pg.fill('#fcus','Orient Stroy'); pg.fill('#famt','5000000'); pg.click('#fsave'); pg.wait_for_timeout(1000)
    check('payment saved', pg.evaluate('location.hash')=='#bank' and 'BP-' in txt('#ftbl'), toast()+txt('#ferr'))
    check('bank balance 5 000 000', '5' in txt('#fcards') and '000' in txt('#fcards'), txt('#fcards'))
    go('customers'); check('debt now 13 000 000', '13' in txt('#cutbl'), txt('#cutbl'))
    # cash desk cannot go negative
    go('cash'); pg.wait_for_timeout(300)
    pg.evaluate("document.querySelector('#fnew button[data-k=out]').click()"); pg.wait_for_timeout(500)
    pg.select_option('#fart','sal'); pg.fill('#fparty','Workers'); pg.fill('#famt','100000'); pg.click('#fsave'); pg.wait_for_timeout(800)
    check('cash negative rejected', 'below zero' in txt('#ferr') or 'cannot go' in txt('#ferr'), txt('#ferr'))
    # delete receipt used by production -> blocked
    go('receipts'); pg.locator('#rctbl tbody tr .kebab').first.click(); pg.click('#pmenu [data-act=del]'); pg.click('#pmenu [data-act=confirmdel]'); pg.wait_for_timeout(800)
    check('deleting consumed receipt blocked', 'Not enough' in txt('#rcmsg') or 'Not enough' in toast(), txt('#rcmsg'))
    # settings: add warehouse + unit + account
    go('settings'); pg.click('#stnew'); pg.fill('#stname','Sklad 2'); pg.click('#stsave'); pg.wait_for_timeout(800)
    check('warehouse added', 'Sklad 2' in txt('#sttbl'))
    pg.click('#sttabs button[data-tab=unit]'); pg.click('#stnew'); pg.fill('#stn_uz','paddon'); pg.fill('#stn_ru','поддон'); pg.fill('#stn_en','pallet'); pg.click('#stsave'); pg.wait_for_timeout(800)
    check('unit added', 'pallet' in txt('#sttbl'), txt('#sttbl'))
    pg.click('#sttabs button[data-tab=cash]'); pg.click('#stnew'); pg.fill('#stname','Test kassa'); pg.click('#stsave'); pg.wait_for_timeout(800)
    check('cash desk added', 'Test kassa' in txt('#sttbl'))
    # reload keeps session and data
    pg.reload(); pg.wait_for_timeout(1500)
    check('reload keeps session', pg.evaluate('location.hash')!='#login' and pg.evaluate('!!ME'))
    go('orders'); check('order persisted', 'ZK-' in txt('#odtbl'))
    # new product with spec copy
    go('products'); pg.click('#gnnew'); pg.fill('#gnname','2ПК 99*12'); pg.fill('#gncopy','2ПК 66*12'); pg.click('#gnsave'); pg.wait_for_timeout(1000)
    check('product created', '2ПК 99*12' in txt('#itbl'), toast()+txt('#gnmsg'))
    go('specifications'); pg.fill('#spq','99'); pg.wait_for_timeout(300)
    pg.click('#splist .spitem'); pg.wait_for_timeout(300)
    check('spec copied from 66*12', '390' in pg.inner_html('#spedit'), pg.inner_text('#spedit')[:200])
    print('\n'.join(errs) or 'no console errors')
    pg.screenshot(path='final.png')
    b.close()
print('FAILS:',fails)
raise SystemExit(1 if fails else 0)
