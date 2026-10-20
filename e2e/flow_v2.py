"""v2 screens: AI assistant, draft -> form, reports + Excel, journal, users, dashboard AI box, PDF. Needs a server with a (fake) Claude."""
import json, urllib.request, sys
from playwright.sync_api import sync_playwright
errs = []; fails = []
SHOT = sys.argv[1] if len(sys.argv) > 1 else '/tmp'
def check(name, cond, info=''):
    print(('OK  ' if cond else 'FAIL'), name, info if not cond else '')
    if not cond: fails.append(name)
def call(method, path, body=None, tok=None):
    r = urllib.request.Request('http://localhost:8000/api' + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={'content-type': 'application/json', **({'Authorization': 'Bearer ' + tok} if tok else {})})
    return json.load(urllib.request.urlopen(r))
tok = call('POST', '/auth/login', {'username': 'admin', 'password': 'admin123'})['access_token']
sup = call('POST', '/suppliers', {'name': 'Cement Trade'}, tok)['id']; cus = call('POST', '/customers', {'name': 'Orient Stroy'}, tok)['id']
items = {i['name_en']: i for i in call('GET', '/items', None, tok)}; whs = {w['name']: w for w in call('GET', '/warehouses', None, tok)}
sur = whs['Завод 1']['id']
if 'ФБС 24.4.6-Т' not in items:      # the seed no longer ships this product: create it with its norms
    uid = [u for u in call('GET', '/units', None, tok) if u['name'] == 'dona'][0]['id']
    n = 'ФБС 24.4.6-Т'; pid = call('POST', '/items', {'kind': 'product', 'name_uz': n, 'name_ru': n, 'name_en': n, 'unit_id': uid, 'min_stock': 100}, tok)['id']
    call('PUT', '/specifications/%d' % pid, {'norms': [{'material_id': items[m]['id'], 'qty': q} for m, q in (('Cement', 260), ('Crushed stone', 760), ('Sand', 440))]}, tok)
    items = {i['name_en']: i for i in call('GET', '/items', None, tok)}
call('POST', '/receipts', {'date': '2026-09-01T09:00:00', 'supplier_id': sup, 'warehouse_id': sur, 'rows': [{'item_id': items[n]['id'], 'qty': q, 'price': p} for n, q, p in [('Cement', 5000, 1000), ('Crushed stone', 10000, 100), ('Sand', 8000, 50), ('Rebar', 1000, 9000)]]}, tok)
fbs = items['ФБС 24.4.6-Т']['id']
call('POST', '/production', {'date': '2026-09-05T09:00:00', 'warehouse_id': sur, 'rows': [{'item_id': fbs, 'qty': 5}]}, tok)
call('POST', '/invoices', {'date': '2026-09-10T09:00:00', 'customer_id': cus, 'warehouse_id': sur, 'rows': [{'item_id': fbs, 'qty': 3, 'price': 500000}]}, tok)
bank = [a for a in call('GET', '/accounts', None, tok) if a['kind'] == 'bank'][0]
call('POST', '/finance', {'date': '2026-09-12T09:00:00', 'kind': 'in', 'account_id': bank['id'], 'article': 'cust', 'customer_id': cus, 'amount': 600000}, tok)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox'])
    ctxb = b.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
    pg = ctxb.new_page()
    pg.on('pageerror', lambda e: errs.append('PAGEERR ' + str(e)))
    pg.on('console', lambda m: errs.append('CONSOLE ' + m.text) if m.type == 'error' and 'TUNNEL' not in m.text and 'Failed to load resource' not in m.text else None)
    pg.route('**/*fonts.*', lambda r: r.abort())
    pg.goto('http://localhost:8000/'); pg.evaluate("localStorage.setItem('daybook-lang','uz')"); pg.reload(); pg.wait_for_timeout(400)
    def go(h, w=700): pg.evaluate(f"location.hash='{h}'"); pg.wait_for_timeout(w)
    def txt(sel): return pg.inner_text(sel)
    go('login'); pg.fill('#u', 'admin'); pg.fill('#pw', 'admin123'); pg.click('#loginForm button[type=submit]'); pg.wait_for_timeout(1800)
    check('dashboard open', pg.evaluate('location.hash') == '#dashboard')
    pg.wait_for_timeout(800)
    check('dashboard AI box rendered', pg.is_visible('#aibox') and 'AI' in txt('#aibox'), txt('#aibox')[:200] if pg.query_selector('#aibox') else 'no box')
    pg.screenshot(path=SHOT + '/v2_dash.png')
    nav = txt('#side')
    check('sidebar has new items', all(w in nav for w in ['AI yordamchi', 'Hisobotlar', 'O‘zgarishlar jurnali', 'Foydalanuvchilar']), nav[:400])

    # --- assistant
    go('assistant', 1200)
    check('assistant page', pg.is_visible('#ai-form'))
    check('AI connected chip', 'ulangan' in txt('#ai-state'), txt('#ai-state'))
    pg.fill('#ai-in', 'Sement qancha qoldi?'); pg.click('#ai-send'); pg.wait_for_timeout(1500)
    log = txt('#ai-log')
    check('assistant answered with markdown list', '3 700' in log and pg.query_selector('#ai-log li') is not None, log[:300])
    check('tool chip shown', 'ombor qoldig‘i' in log, log[-200:])
    check('brief card filled', 'sement' in txt('#ai-brief').lower(), txt('#ai-brief')[:200])
    check('signals listed', pg.query_selector('#ai-sig .sev') is not None, txt('#ai-sig')[:200])
    pg.screenshot(path=SHOT + '/v2_ai.png', full_page=True)
    pg.click('#ai-modes button[data-m=finance]'); pg.wait_for_timeout(600)
    check('finance mode has own empty chat', '3 700' not in txt('#ai-log'))

    # --- draft -> form
    pg.fill('#dr-text', 'Cement Trade dan 100 kg sement 1200 dan'); pg.click('#dr-make'); pg.wait_for_timeout(1200)
    prev = txt('#ai-draft')
    check('draft preview matched', 'Cement' in prev and 'mystery' in prev, prev[:300])
    check('unmatched warning shown', 'topilmadi' in prev.lower(), prev[-250:])
    pg.screenshot(path=SHOT + '/v2_draft.png', full_page=True)
    pg.click('#dr-open'); pg.wait_for_timeout(900)
    check('receipt form opened', pg.evaluate('location.hash') == '#receipt-new')
    check('supplier prefilled', pg.input_value('#rcsup') == 'Cement Trade', pg.input_value('#rcsup'))
    check('row prefilled', pg.input_value('#rcm0') != '' and pg.input_value('#rcq0') in ('100', '100,000', '100.000') or '100' in pg.input_value('#rcq0'), pg.input_value('#rcm0') + '|' + pg.input_value('#rcq0'))
    check('nothing saved by the draft', len(call('GET', '/receipts', None, tok)) == 1)

    # --- reports
    go('reports', 1200)
    check('reports page + default tab', pg.is_visible('#rp-tabs') and pg.query_selector('#rp-out table') is not None, txt('#rp-out')[:200])
    pg.fill('#rp-from', '2026-09-01'); pg.fill('#rp-to', '2026-09-30'); pg.dispatch_event('#rp-to', 'change'); pg.wait_for_timeout(1500)
    t1 = txt('#rp-out')
    check('turnover shows cement closing', 'Sement' in t1 and '3,700' in t1, t1)
    with pg.expect_download() as dl:
        pg.click('#rp-xlsx')
    d = dl.value; d.save_as(SHOT + '/turnover.xlsx')
    check('excel downloaded', d.suggested_filename == 'turnover.xlsx' and open(SHOT + '/turnover.xlsx', 'rb').read(2) == b'PK')
    pg.click('#rp-tabs button[data-r=sales]'); pg.wait_for_timeout(900)
    check('sales tab', '1' in txt('#rp-out') and 'Orient' in txt('#rp-out'), txt('#rp-out')[:200])
    pg.click('#rp-tabs button[data-r=debts_customer]'); pg.wait_for_timeout(900)
    check('debts tab shows 900 000', '900' in txt('#rp-out'), txt('#rp-out')[:200])
    pg.screenshot(path=SHOT + '/v2_reports.png', full_page=True)

    # --- PDF
    go('invoices', 800); 
    inv_no = call('GET', '/invoices', None, tok)[0]['number']
    pg.evaluate(f"IS.view='{inv_no}';location.hash='invoice-view'"); pg.wait_for_timeout(800)
    check('invoice PDF button present', pg.is_visible('#ivvpdf'))
    pg.click('#ivvpdf'); pg.wait_for_timeout(1500)
    check('PDF opens in the in-page viewer (no pop-up)', pg.is_visible('#pdfv iframe') and pg.get_attribute('#pdfv iframe', 'src').startswith('blob:'))
    with pg.expect_download() as dl:
        pg.click('#pdfv [data-a=dl]')
    check('viewer can download the PDF', dl.value.suggested_filename.endswith('.pdf'), dl.value.suggested_filename)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
    check('viewer closes with Esc', not pg.query_selector('#pdfv'))

    # --- journal
    go('journal', 1200)
    j = txt('#au-out')
    check('journal lists my actions', 'admin' in j and 'yaratdi' in j, j[:300])
    pg.select_option('#au-e', 'receipts'); pg.wait_for_timeout(900)
    check('journal filter by entity', 'Kirim' in txt('#au-out') and 'Mijoz' not in txt('#au-out'), txt('#au-out')[:300])
    pg.screenshot(path=SHOT + '/v2_journal.png', full_page=True)

    # --- users
    go('users', 1200)
    check('users table editable', pg.query_selector('#xv-users [data-save]') is not None)
    pg.fill('#nu-name', 'Test User'); pg.fill('#nu-login', 'tester'); pg.fill('#nu-pw', 'longpassword1'); pg.select_option('#nu-role', 'wh'); pg.click('#nu-add'); pg.wait_for_timeout(1000)
    check('user created', 'tester' in txt('#xv-users'), txt('#xv-users')[:200])
    pg.click('#pwbtn'); pg.fill('#pw-o', 'wrong'); pg.fill('#pw-n', 'short'); pg.click('.xbox button[type=submit]'); pg.wait_for_timeout(700)
    check('password dialog shows error', len(txt('#pw-m')) > 0, txt('#pw-m'))
    pg.click('#pw-x')
    pg.screenshot(path=SHOT + '/v2_users.png', full_page=True)

    # --- statement PDF button
    go('customers', 600); pg.evaluate("openAkt(0)"); pg.wait_for_timeout(800)
    check('statement PDF button', pg.is_visible('#akpdf'), pg.evaluate("location.hash+' hidden='+document.querySelector('#cu-akt').hidden+' me='+(typeof ME)+' toast='+[].map.call(document.querySelectorAll('#toasts .toast'),e=>e.textContent).join('|')"))
    # --- language switch repaints the page
    go('reports', 800); pg.click('[data-lang=ru]'); pg.wait_for_timeout(900)
    check('ru repaint', 'Отчёты' in txt('#xv-reports') or 'Оборот' in txt('#xv-reports'), txt('#xv-reports')[:120])

    # --- role scoping in the UI: warehouse keeper
    pg.click('#signout'); pg.wait_for_timeout(500)
    go('login'); pg.fill('#u', 'omborchi'); pg.fill('#pw', 'sklad123'); pg.click('#loginForm button[type=submit]'); pg.wait_for_timeout(1800)
    nav = txt('#side')
    check('warehouse keeper: reports yes, journal/users no', ('Отчёты' in nav or 'Hisobotlar' in nav) and 'жур' not in nav.lower() and 'Пользов' not in nav and 'Foydalanuvchilar' not in nav, nav[:300])
    go('journal', 600)
    check('journal blocked for keeper', pg.evaluate('location.hash') != '#journal')
    go('reports', 1000)
    tabs = txt('#rp-tabs')
    check('keeper sees only the reports his role allows', pg.evaluate("[].map.call(document.querySelectorAll('#rp-tabs button'),b=>b.dataset.r).join()") == 'turnover,sales,purchases,plan,plan_materials,debts_supplier', tabs)
    b.close()
print('PAGE ERRORS:', errs if errs else 'none')
print('FAILED:', fails if fails else 'none')
sys.exit(1 if fails or errs else 0)
