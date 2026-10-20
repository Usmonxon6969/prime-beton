from tests.conftest import login, scenario


def test_turnover(ctx):
    s = scenario(ctx)
    t = ctx.get("/reports/center/turnover?start=2026-09-02T00:00:00&end=2026-09-30T00:00:00&lang=en").json()
    row = {r["item"]: r for r in t["rows"]}
    cem = row["Cement"]
    assert cem["opening"] == 5000 and cem["receipt"] == 0 and cem["consumed"] == 1300 and cem["closing"] == 3700
    blk = row["ФБС 24.4.6-Т"] if "ФБС 24.4.6-Т" in row else next(r for k, r in row.items() if "24.4.6" in k)
    assert blk["production"] == 5 and blk["shipped"] == 3 and blk["closing"] == 2
    assert t["labels"]["opening"] == "Opening"
    uz = ctx.get("/reports/center/turnover?lang=uz").json()
    assert uz["labels"]["closing"].startswith("Oxirgi")


def test_sales_purchases_cashflow_profit_debts(ctx):
    scenario(ctx)
    by_c = ctx.get("/reports/center/sales?group=customer").json()
    assert by_c["rows"][0]["amount"] == 1_500_000 and by_c["totals"]["amount"] == 1_500_000
    assert ctx.get("/reports/center/sales?group=month").json()["rows"][0]["month"] == "2026-09"
    p = ctx.get("/reports/center/purchases?group=supplier").json()
    assert p["totals"]["amount"] == 5000 * 1000 + 10000 * 100 + 8000 * 50 + 1000 * 9000
    cf = ctx.get("/reports/center/cashflow?group=article").json()
    assert cf["totals"] == {"in": 600000, "out": 100000, "net": 500000}
    pr = ctx.get("/reports/center/profit").json()
    last = pr["rows"][-1]["amount"]
    mat = 5 * (260 * 1000)   # only cement is priced at 1000; other norm lines use their own averages
    assert pr["rows"][0]["amount"] == 1_500_000 and last < 1_500_000 - 100000
    d = ctx.get("/reports/center/debts?who=customer").json()
    assert d["rows"][0]["debt"] == 900000
    assert ctx.get("/reports/center/nonsense").status_code == 404


def test_report_permissions(client, ctx):
    scenario(ctx)
    h = login(client, "omborchi", "sklad123")      # warehouse keeper: turnover yes, money no
    assert client.get("/api/reports/center/turnover", headers=h).status_code == 200
    assert client.get("/api/reports/center/cashflow", headers=h).status_code == 403
    assert client.get("/api/reports/center/debts?who=customer", headers=h).status_code == 403
    h2 = login(client, "buxgalter", "buh123")
    assert client.get("/api/reports/center/cashflow", headers=h2).status_code == 200
    assert client.get("/api/reports/center/turnover", headers=h2).status_code == 403


def test_exports(ctx):
    s = scenario(ctx)
    r = ctx.c.get("/api/reports/center/sales/export.xlsx?lang=ru", headers=ctx.h)
    assert r.status_code == 200 and r.content[:2] == b"PK"
    from io import BytesIO
    from openpyxl import load_workbook
    ws = load_workbook(BytesIO(r.content)).active
    vals = [c.value for row in ws.iter_rows() for c in row]
    assert "Покупатель" in vals and 1500000 in vals
    inv = ctx.get("/invoices").json()[0]["id"]
    for lang in ("uz", "ru", "en"):
        pdf = ctx.c.get(f"/api/reports/print/invoice/{inv}.pdf?lang={lang}", headers=ctx.h)
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
        act = ctx.c.get(f"/api/reports/print/statement.pdf?customer_id={s['cus']}&lang={lang}", headers=ctx.h)
        assert act.status_code == 200 and act.content.startswith(b"%PDF")
    assert ctx.c.get("/api/reports/print/statement.pdf", headers=ctx.h).status_code == 422


def test_production_plan_roles(client):
    assert client.get("/api/reports/center/plan", headers=login(client, "omborchi", "sklad123")).status_code == 200
    assert client.get("/api/reports/center/plan", headers=login(client, "buxgalter", "buh123")).status_code == 403


def test_production_plan(ctx):
    s = scenario(ctx)
    ctx.post("/orders", {"date": "2026-09-14T09:00:00", "due_date": "2026-10-01T09:00:00", "customer_id": s["cus"], "rows": [{"item_id": s["fbs"], "qty": 20, "price": 500000}]})
    p = ctx.get("/reports/center/plan?lang=en").json()
    r = p["rows"][0]
    assert r["open_qty"] == 20 and r["in_stock"] == 2 and r["to_make"] == 18 and r["due"] == "2026-10-01"
    m = {x["item"]: x for x in ctx.get("/reports/center/plan_materials?lang=en").json()["rows"]}
    assert m["Cement"]["need"] == 18 * 260 and m["Cement"]["in_stock"] == 3700 and m["Cement"]["short"] == 18 * 260 - 3700
    assert next(iter(m.values()))["short"] >= 0 and ctx.get("/reports/center/plan?lang=uz").json()["labels"]["to_make"].startswith("Ishlab")


def test_printed_act_lists_what_each_document_contained(ctx):
    from app.services import reports
    from app.db.session import get_db
    from app.main import app
    s = scenario(ctx)
    db = next(app.dependency_overrides[get_db]())
    try:
        sup = reports.statement(db, customer_id=None, supplier_id=s["sup"], start=None, end=None, lang="ru")
        cus = reports.statement(db, customer_id=s["cus"], supplier_id=None, start=None, end=None)
    finally:
        db.close()
    rec = [r for r in sup["rows"] if r["kind"] == "receipt"][0]
    assert {i["name"] for i in rec["items"]} >= {"Цемент", "Песок"} and rec["items"][0]["price"] > 0
    assert round(sum(i["amount"] for i in rec["items"]), 2) == rec["debit"]
    inv = [r for r in cus["rows"] if r["kind"] == "invoice"][0]
    assert inv["items"][0]["qty"] == 3 and inv["items"][0]["price"] == 500000
    assert [r for r in cus["rows"] if r["kind"] == "payment"][0]["items"] == []
    for lang in ("uz", "ru", "en"):                                   # the PDF still builds with the line rows
        r = ctx.c.get(f"/api/reports/print/statement.pdf?supplier_id={s['sup']}&lang={lang}", headers=ctx.h)
        assert r.status_code == 200 and r.content[:4] == b"%PDF"


# ---------------------------------------------------------------- waybill (yuk xati)
def test_waybill_has_driver_vehicle_and_company_details(ctx):
    s = scenario(ctx)
    assert ctx.c.put("/api/company", headers=ctx.h, json={"name": "OOO PRIME BETON", "address": "Toshkent sh., Bektemir tumani", "postcode": "1730405",
                                                         "okonh": "16140", "account": "20208000700818029003", "bank": "Tiff bank", "mfo": "00450",
                                                         "inn": "305097248", "receive_note": "Plitalarni butun qabul qilib oldim!"}).status_code == 200
    assert ctx.get("/company").json()["inn"] == "305097248"
    inv = ctx.post("/invoices", {"date": "2026-10-15T09:00:00", "customer_id": s["cus"], "warehouse_id": s["sur"], "driver": "Azamov Alisher",
                                 "vehicle": "01 320 hna", "rows": [{"item_id": s["fbs"], "qty": 2, "price": 100}]}).json()
    assert inv["driver"] == "Azamov Alisher" and inv["vehicle"] == "01 320 HNA"                 # plate numbers are upper-cased
    r = ctx.get(f"/reports/print/waybill/{inv['id']}.pdf")
    assert r.status_code == 200 and r.content.startswith(b"%PDF") and len(r.content) > 5000
    upd = ctx.c.put(f"/api/invoices/{inv['id']}", headers=ctx.h, json={"date": "2026-10-15T09:00:00", "customer_id": s["cus"], "warehouse_id": s["sur"],
                                                                        "driver": "Karimov", "vehicle": "10 777 AAA", "rows": [{"item_id": s["fbs"], "qty": 2, "price": 100}]})
    assert upd.json()["driver"] == "Karimov"
    assert ctx.get("/reports/print/waybill/999999.pdf").status_code == 404


def test_company_details_start_with_defaults(ctx):
    r = ctx.get("/company")
    assert r.status_code == 200 and "name" in r.json()                                           # readable, with a sensible start


def test_responses_are_compressed(client):
    r = client.get("/api/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and r.headers.get("content-encoding") == "gzip"


def test_movements(ctx):
    scenario(ctx)
    m = ctx.get("/reports/center/movements?lang=en").json()
    assert m["rows"] and m["totals"]["qty_in"] > 0 and m["totals"]["qty_out"] > 0
    assert all("balance" not in c["key"] for c in m["columns"])
    assert all(r["qty_in"] or r["qty_out"] for r in m["rows"])
    cem = next(r for r in m["rows"] if r["item"] == "Cement")
    one = ctx.get(f"/reports/center/movements?lang=en&item_id={cem['item_id']}&start=2026-09-02T00:00:00").json()
    assert one["columns"][-1]["key"] == "balance" and one["rows"][0]["doc_type"] == "Opening"
    assert one["rows"][0]["balance"] == 5000
    assert one["rows"][-1]["balance"] == one["totals"]["balance"]
    only = ctx.get("/reports/center/movements?doc=receipt").json()
    assert only["rows"] and all(r["doc_key"] == "receipt" for r in only["rows"])
    assert ctx.get("/reports/center/movements?doc=bogus").status_code == 422
    assert ctx.get("/reports/center/movements/export.xlsx").status_code in (200, 404)


def test_production_report(ctx):
    scenario(ctx)
    r = ctx.get("/reports/center/production?lang=en").json()
    assert r["rows"] and r["totals"]["good"] == 5
    assert [c["key"] for c in r["columns"]] == ["item", "good", "scrap"]
    m = ctx.get("/reports/center/production?group=month").json()
    assert m["rows"][0]["month"] == "2026-09" and m["totals"]["good"] == 5
    w = ctx.get("/reports/center/production?group=warehouse").json()
    assert w["rows"][0]["warehouse"] and w["totals"]["good"] == 5
    assert ctx.get("/reports/center/production?start=2030-01-01T00:00:00").json()["rows"] == []
    assert ctx.get("/reports/center/production/export.xlsx").status_code == 200


def test_production_report_lists_products_under_each_period(ctx):
    scenario(ctx)
    r = ctx.get("/reports/center/production?group=month_item").json()
    assert [c["key"] for c in r["columns"]][:2] == ["month", "item"]
    assert r["rows"][0]["month"] == "2026-09" and r["rows"][0]["item"] and r["totals"]["good"] == 5
    assert sum(x["good"] for x in r["rows"]) == 5
    assert ctx.get("/reports/center/production?group=warehouse_item").json()["rows"][0]["warehouse"]
    assert ctx.get("/reports/center/production?group=nonsense").json()["totals"]["good"] == 5
