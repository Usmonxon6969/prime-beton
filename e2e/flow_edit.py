from playwright.sync_api import sync_playwright
errs=[]; fails=[]
def check(name,cond,info=''):
    print(('OK  ' if cond else 'FAIL'),name,info if not cond else '')
    if not cond: fails.append(name)
with sync_playwright() as p:
    b=p.chromium.launch(args=['--no-sandbox'])
    pg=b.new_page(viewport={'width':1280,'height':900})
    pg.on('pageerror',lambda e:errs.append('PAGEERR '+str(e)))
    pg.route('**/*fonts.*',lambda r:r.abort())
    pg.goto('http://localhost:8000/'); pg.evaluate("localStorage.setItem('daybook-lang','en')"); pg.reload(); pg.wait_for_timeout(300)
    def go(h,w=500): pg.evaluate(f"location.hash='{h}'"); pg.wait_for_timeout(w)
    def txt(sel): return pg.inner_text(sel)
    def kebab(tbl,i=0,act='edit'):
        pg.locator(f'{tbl} tbody tr .kebab').nth(i).click(); pg.click(f'#pmenu [data-act={act}]'); pg.wait_for_timeout(300)
    go('login'); pg.fill('#u','admin'); pg.fill('#pw','admin123'); pg.click('#loginForm button[type=submit]'); pg.wait_for_timeout(1500)
    # edit production doc: 10 -> 8 slabs
    go('production'); kebab('#plog',0,'edit'); pg.wait_for_timeout(300)
    pg.fill('#pq0','8'); pg.click('#pfill'); pg.click('#ppost'); pg.wait_for_timeout(1000)
    check('production edited to 8', pg.evaluate('plog[0].rows[0].q')==8, txt('#pdone')+txt('#pmsg'))
    go('warehouse'); pg.select_option('#wsite','0'); pg.wait_for_timeout(300)
    t=txt('#wtbl'); check('stock after edit: 2 slabs (8 made, 6 shipped)', '2ПК 66*12' in t, t[:200])
    # delete production doc -> would leave negative slabs (6 shipped of 8)
    go('production'); pg.locator('#plog tbody tr .kebab').first.click(); pg.click('#pmenu [data-act=del]'); pg.click('#pmenu [data-act=confirmdel]'); pg.wait_for_timeout(800)
    check('deleting production that feeds a shipment is blocked', 'Not enough' in txt('#pdone'), txt('#pdone'))
    # invoice delete + restore
    go('invoices'); kebab('#ivtbl',0,'del'); pg.click('#pmenu [data-act=confirmdel]'); pg.wait_for_timeout(800)
    check('invoice deleted', 'deleted' in pg.inner_html('#ivtbl').lower(), txt('#ivmsg'))
    pg.locator('#ivtbl tbody tr .kebab').first.click(); pg.click('#pmenu [data-act=restore]'); pg.wait_for_timeout(800)
    check('invoice restored', 'restored' in txt('#ivmsg').lower(), txt('#ivmsg'))
    # order delete blocked (has shipment)
    go('orders'); pg.locator('#odtbl tbody tr .kebab').first.click(); pg.click('#pmenu [data-act=del]'); pg.click('#pmenu [data-act=confirmdel]'); pg.wait_for_timeout(800)
    check('order with shipments cannot be deleted', len(txt('#odmsg'))>0 and 'deleted' not in txt('#odmsg').lower().replace('delivery notes','') , txt('#odmsg'))
    # customer in use cannot be deleted
    go('customers'); pg.locator('#cutbl tbody tr .kebab').first.click(); pg.click('#pmenu [data-act=del]'); pg.click('#pmenu [data-act=confirmdel]'); pg.wait_for_timeout(800)
    check('customer in use blocked', 'cannot be deleted' in txt('#cumsg'), txt('#cumsg'))
    # edit order: lower qty below shipped
    go('orders'); kebab('#odtbl',0,'edit'); pg.fill('#odq0','2'); pg.click('#odsave'); pg.wait_for_timeout(800)
    check('order below shipped rejected', 'already shipped' in txt('#oderr'), txt('#oderr'))
    # statement (akt)
    go('customers'); kebab('#cutbl',0,'akt'); pg.wait_for_timeout(500)
    check('akt shows invoice', 'RN-' in pg.inner_text('#cu-akt'), pg.inner_text('#cu-akt')[:300])
    # product delete blocked (in docs)
    go('products'); pg.fill('#itq','66*12'); pg.wait_for_timeout(300)
    kebab('#itbl',0,'del'); pg.click('#pmenu [data-act=confirmdel]'); pg.wait_for_timeout(800)
    check('product in use cannot be deleted', len(txt('#gnmsg'))>0, txt('#gnmsg'))
    # rename material
    go('materials'); kebab('#mttbl',0,'edit'); pg.fill('#mtname','Sement M500'); pg.click('#mtsave'); pg.wait_for_timeout(800)
    check('material renamed', 'Sement M500' in txt('#mttbl'), txt('#mttbl')[:200])
    # mobile layout screenshot
    pg.set_viewport_size({'width':400,'height':800}); go('warehouse'); pg.screenshot(path='m-wh.png'); go('dashboard',700); pg.screenshot(path='m-dash.png',full_page=True)
    print('\n'.join(errs) or 'no page errors')
    b.close()
print('FAILS:',fails)
raise SystemExit(1 if fails else 0)
