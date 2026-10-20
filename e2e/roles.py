from playwright.sync_api import sync_playwright
users=[('admin','admin123'),('direktor','dir123'),('ishlab','prod123'),('omborchi','sklad123'),('sotuv','sotuv123'),('buxgalter','buh123')]
pages=['dashboard','production','specifications','materials','products','warehouse','customers','orders','invoices','suppliers','receipts','bank','cash','settings','order-new','invoice-new','receipt-new','production-new','bank-new','cash-new']
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(args=['--no-sandbox'])
    for u,pw in users:
        for lang in ['uz','ru','en']:
            pg=b.new_page(viewport={'width':1280,'height':900})
            pg.on('pageerror',lambda e,u=u,lang=lang:errs.append(f'{u}/{lang} PAGEERR {e}'))
            pg.route('**/*fonts.*',lambda r:r.abort())
            pg.goto('http://localhost:8000/'); pg.evaluate(f"localStorage.setItem('daybook-lang','{lang}')"); pg.reload(); pg.wait_for_timeout(300)
            pg.evaluate("location.hash='login'"); pg.fill('#u',u); pg.fill('#pw',pw); pg.click('#loginForm button[type=submit]'); pg.wait_for_timeout(1200)
            ok=pg.evaluate('!!ME')
            if not ok: errs.append(f'{u}/{lang} login failed')
            for h in pages:
                pg.evaluate(f"location.hash='{h}'"); pg.wait_for_timeout(120)
            pg.close()
    b.close()
print('\n'.join(errs) or 'no errors')
raise SystemExit(1 if errs else 0)
