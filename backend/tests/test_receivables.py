from datetime import datetime

from app.services import reports
from tests.conftest import scenario


def cust(ctx, name, days=0):
    r = ctx.post("/customers", {"name": name, "pay_days": days})
    assert r.status_code == 201, r.text
    return r.json()


def setup_stock(ctx):
    sc = scenario(ctx)
    r = ctx.post("/production", {"date": "2026-09-06T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": sc["fbs"], "qty": 8}]})
    assert r.status_code == 201, r.text      # 2 left from the scenario + 8 = 10 blocks to sell
    return sc


def invoice(ctx, cid, sur, fbs, qty, price, date, **kw):
    r = ctx.post("/invoices", {"date": date, "customer_id": cid, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": qty, "price": price}], **kw})
    assert r.status_code == 201, r.text
    return r.json()


def test_customer_term_sets_the_pay_by_date(ctx):
    sc = setup_stock(ctx)
    c = cust(ctx, "Term Co", 14)
    assert c["pay_days"] == 14
    v = invoice(ctx, c["id"], sc["sur"], sc["fbs"], 1, 100, "2026-10-01T10:00:00")
    assert v["pay_due"].startswith("2026-10-15")
    v2 = invoice(ctx, c["id"], sc["sur"], sc["fbs"], 1, 100, "2026-10-01T10:00:00", pay_due="2026-10-05T00:00:00")
    assert v2["pay_due"].startswith("2026-10-05")                       # explicit date wins
    n = cust(ctx, "Cash Co", 0)
    assert invoice(ctx, n["id"], sc["sur"], sc["fbs"], 1, 100, "2026-10-01T10:00:00")["pay_due"] is None
    e = ctx.c.put(f"/api/customers/{c['id']}", json={"name": "Term Co", "pay_days": 30}, headers=ctx.h)
    assert e.status_code == 200 and e.json()["pay_days"] == 30
    assert ctx.post("/customers", {"name": "Bad", "pay_days": 4000}).status_code == 422


def test_aging_buckets_and_fifo_payments(db_session, ctx):
    sc = setup_stock(ctx)
    c = cust(ctx, "Aging Co", 10)
    fbs, sur = sc["fbs"], sc["sur"]
    invoice(ctx, c["id"], sur, fbs, 1, 1000, "2026-08-01T10:00:00")     # due 08-11  -> 62 days late on 10-12
    invoice(ctx, c["id"], sur, fbs, 1, 2000, "2026-09-01T10:00:00")     # due 09-11  -> 31 days late
    invoice(ctx, c["id"], sur, fbs, 1, 4000, "2026-09-25T10:00:00")     # due 10-05  -> 7 days late
    invoice(ctx, c["id"], sur, fbs, 1, 8000, "2026-10-10T10:00:00")     # due 10-20  -> not due
    bank = [a for a in ctx.accounts if a["kind"] == "bank"][0]
    ctx.post("/finance", {"date": "2026-10-02T09:00:00", "kind": "in", "account_id": bank["id"], "article": "cust", "customer_id": c["id"], "amount": 1500})
    with db_session() as db:
        row = next(a for a in reports.aging(db, datetime(2026, 10, 12)) if a["customer_id"] == c["id"])
    # 1500 pays the oldest note (1000) and half of the second (500): 1500 of the second is left
    assert row["d90"] == 0 and row["d60"] == 1500 and row["d30"] == 4000 and row["current"] == 8000
    assert row["overdue"] == 5500 and row["debt"] == 13500 and row["advance"] == 0
    assert row["oldest_days"] == 31 and row["next_due"] == "2026-10-20"
    ctx.post("/finance", {"date": "2026-10-03T09:00:00", "kind": "in", "account_id": bank["id"], "article": "cust", "customer_id": c["id"], "amount": 20000})
    with db_session() as db:
        row = next(a for a in reports.aging(db, datetime(2026, 10, 12)) if a["customer_id"] == c["id"])
    assert row["debt"] == 0 and row["advance"] == 6500 and row["overdue"] == 0          # paid ahead


def test_aging_report_and_dashboard(ctx):
    sc = setup_stock(ctx)
    r = ctx.get("/reports/center/aging")
    assert r.status_code == 200, r.text
    t = r.json()
    assert [c["key"] for c in t["columns"]][:2] == ["customer", "current"] and t["totals"]["overdue"] > 0
    assert t["labels"]["d30"]
    d = ctx.get("/reports/dashboard").json()
    assert d["overdue"] > 0 and d["overdue_customers"] == 1
    assert ctx.c.get("/api/reports/center/aging", headers={"Authorization": "Bearer x"}).status_code == 401


def test_advance_against_an_order(ctx):
    sc = setup_stock(ctx)
    c, other = cust(ctx, "Adv Co"), cust(ctx, "Other Co")
    o = ctx.post("/orders", {"date": "2026-10-01T09:00:00", "customer_id": c["id"], "rows": [{"item_id": sc["fbs"], "qty": 2, "price": 500000}]}).json()
    bank = [a for a in ctx.accounts if a["kind"] == "bank"][0]
    pay = {"date": "2026-10-02T09:00:00", "kind": "in", "account_id": bank["id"], "article": "cust", "customer_id": c["id"], "amount": 300000, "order_id": o["id"]}
    r = ctx.post("/finance", pay)
    assert r.status_code == 201 and r.json()["order_id"] == o["id"]
    assert ctx.get(f"/orders/{o['id']}").json()["advance"] == 300000
    assert next(x for x in ctx.get("/orders").json() if x["id"] == o["id"])["advance"] == 300000
    assert ctx.post("/finance", {**pay, "customer_id": other["id"]}).status_code == 422          # not this customer's order
    assert ctx.post("/finance", {**pay, "kind": "out", "article": "sup", "supplier_id": ctx.supplier()}).status_code == 422
    # the advance is part of what the customer paid
    debts = {d["name"]: d for d in ctx.get("/reports/customer-debts").json()}
    assert debts["Adv Co"]["paid"] == 300000
