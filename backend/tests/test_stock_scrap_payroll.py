from tests.conftest import scenario


def stock_of(ctx, item_id, wh):
    return next(i for i in ctx.get("/items").json() if i["id"] == item_id)["stock"].get(str(wh), 0)


def adj(ctx, wh, rows, kind="count", **kw):
    return ctx.post("/adjustments", {"date": "2026-09-20T10:00:00", "kind": kind, "warehouse_id": wh, "rows": rows, **kw})


# ---------- stock counts and write-offs ----------
def test_count_sets_stock_to_the_counted_quantity(ctx):
    sc = scenario(ctx)
    cement = ctx.items["Cement"]["id"]
    before = stock_of(ctx, cement, sc["sur"])
    r = adj(ctx, sc["sur"], [{"item_id": cement, "qty": before - 10}])
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["number"].startswith("STK") and d["rows"][0]["delta"] == -10 and d["rows"][0]["system_qty"] == before
    assert stock_of(ctx, cement, sc["sur"]) == before - 10
    assert ctx.c.put(f"/api/adjustments/{d['id']}", json={"date": "2026-09-20T10:00:00", "kind": "count", "warehouse_id": sc["sur"],
                     "rows": [{"item_id": cement, "qty": before + 5}]}, headers=ctx.h).status_code == 200
    assert stock_of(ctx, cement, sc["sur"]) == before + 5                       # re-measured against stock before this document
    assert ctx.c.delete(f"/api/adjustments/{d['id']}", headers=ctx.h).status_code == 200
    assert stock_of(ctx, cement, sc["sur"]) == before
    assert ctx.post(f"/adjustments/{d['id']}/restore", {}).status_code == 200
    assert stock_of(ctx, cement, sc["sur"]) == before + 5


def test_writeoff_needs_reason_and_stock(ctx):
    sc = scenario(ctx)
    cement = ctx.items["Cement"]["id"]
    assert adj(ctx, sc["sur"], [{"item_id": cement, "qty": 5}], "writeoff").status_code == 422          # no reason
    before = stock_of(ctx, cement, sc["sur"])
    r = adj(ctx, sc["sur"], [{"item_id": cement, "qty": 50}], "writeoff", reason="damage")
    assert r.status_code == 201 and r.json()["number"].startswith("WO")
    assert stock_of(ctx, cement, sc["sur"]) == before - 50
    assert adj(ctx, sc["sur"], [{"item_id": cement, "qty": 10 ** 9}], "writeoff", reason="loss").status_code == 409   # more than in stock


def test_adjustments_in_turnover_and_losses_and_profit(ctx):
    sc = scenario(ctx)
    cement = ctx.items["Cement"]["id"]
    adj(ctx, sc["sur"], [{"item_id": cement, "qty": 100}], "writeoff", reason="expired")
    t = ctx.get("/reports/center/turnover?lang=en").json()
    row = next(r for r in t["rows"] if r["item"] == "Cement")
    assert row["adjust"] == -100
    assert row["closing"] == row["opening"] + row["receipt"] + row["production"] + row["adjust"] - row["consumed"] - row["shipped"]
    l = ctx.get("/reports/center/losses").json()
    assert l["totals"]["amount"] == 100 * 1000 and l["rows"][0]["reason"] == "Expired"
    p = ctx.get("/reports/center/profit").json()
    assert any(r["line"] == "Write-offs and shortages" and r["amount"] == -100000 for r in p["rows"])


# ---------- scrap ----------
def test_scrap_uses_materials_but_not_stock(ctx):
    sc = scenario(ctx)
    fbs = sc["fbs"]
    cement = ctx.items["Cement"]["id"]
    c0, f0 = stock_of(ctx, cement, sc["sur"]), stock_of(ctx, fbs, sc["sur"])
    r = ctx.post("/production", {"date": "2026-09-15T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": fbs, "qty": 3, "scrap": 1}]})
    assert r.status_code == 201, r.text
    assert stock_of(ctx, fbs, sc["sur"]) == f0 + 3                              # only good units are stock
    used1 = c0 - stock_of(ctx, cement, sc["sur"])
    r2 = ctx.post("/production", {"date": "2026-09-16T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": fbs, "qty": 4}]})
    assert r2.status_code == 201
    used2 = c0 - used1 - stock_of(ctx, cement, sc["sur"])
    assert used1 > 0 and used1 == used2                                          # 4 gross units (3 good + 1 spoiled) use what 4 good units use
    assert ctx.post("/production", {"date": "2026-09-17T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": fbs, "qty": 0, "scrap": 0}]}).status_code == 422
    s = ctx.get("/reports/center/scrap").json()
    row = next(r for r in s["rows"] if r["good"] == 12)
    assert row["scrap"] == 1 and round(row["scrap_pct"], 2) == round(100 / 13, 2)


# ---------- cost and profit by product ----------
def test_cost_sheet_and_profit_by_product(ctx):
    sc = scenario(ctx)
    fbs = sc["fbs"]
    ctx.c.put("/api/rates", json={"rates": [{"item_id": fbs, "rate": 20000}]}, headers=ctx.h)
    c = ctx.get("/reports/center/cost").json()
    row = next(r for r in c["rows"] if r["labour"] == 20000)
    assert row["materials"] > 0 and abs(row["cost"] - (row["materials"] + row["scrap_cost"] + row["labour"])) < 0.01
    assert row["price"] == 500000 and abs(row["margin"] - (500000 - row["cost"])) < 0.01
    pp = ctx.get("/reports/center/profit_products").json()
    r = pp["rows"][0]
    assert r["qty"] == 3 and r["revenue"] == 1500000 and abs(r["profit"] - (r["revenue"] - r["cost"])) < 0.01


# ---------- payroll ----------
def worker(ctx, name):
    r = ctx.post("/workers", {"name": name, "position": "Molder"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_workers_crud_and_unique(ctx):
    a = worker(ctx, "Aziz")
    assert ctx.post("/workers", {"name": "Aziz"}).status_code == 409
    assert ctx.c.put(f"/api/workers/{a}", json={"name": "Aziz K", "position": "Foreman", "is_active": True}, headers=ctx.h).json()["name"] == "Aziz K"
    assert ctx.c.delete(f"/api/workers/{a}", headers=ctx.h).status_code == 204
    assert ctx.get("/workers").json() == []


def test_piece_rate_pay_shared_by_crew_with_adjustments_and_payments(ctx):
    sc = scenario(ctx)
    fbs = sc["fbs"]
    a, b = worker(ctx, "Aziz"), worker(ctx, "Bobur")
    assert ctx.c.put("/api/rates", json={"rates": [{"item_id": ctx.items["Cement"]["id"], "rate": 1}]}, headers=ctx.h).status_code == 422   # products only
    ctx.c.put("/api/rates", json={"rates": [{"item_id": fbs, "rate": 10000}]}, headers=ctx.h)
    r = ctx.post("/production", {"date": "2026-09-15T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": fbs, "qty": 4, "scrap": 2}], "worker_ids": [a, b]})
    assert r.status_code == 201, r.text
    assert r.json()["worker_ids"] == [a, b] and r.json()["labour"] == 40000          # scrap earns nothing
    ctx.c.put("/api/rates", json={"rates": [{"item_id": fbs, "rate": 99999}]}, headers=ctx.h)           # later rate change does not rewrite pay
    ctx.post("/production", {"date": "2026-09-16T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": fbs, "qty": 1}]})      # no crew
    assert ctx.post("/pay-adjusts", {"worker_id": a, "date": "2026-09-17T09:00:00", "amount": 5000, "note": "bonus"}).status_code == 201
    bank = [x for x in ctx.accounts if x["kind"] == "bank"][0]
    pay = {"date": "2026-09-18T09:00:00", "kind": "out", "account_id": bank["id"], "article": "sal", "party": "Aziz", "amount": 12000}
    assert ctx.post("/finance", {**pay, "worker_id": a}).status_code == 201
    assert ctx.post("/finance", {**pay, "article": "tax", "worker_id": a}).status_code == 422       # worker only on salary
    st = ctx.get("/payroll").json()
    rows = {x["name"]: x for x in st["rows"]}
    assert rows["Aziz"]["earned"] == 20000 and rows["Aziz"]["adjust"] == 5000 and rows["Aziz"]["paid"] == 12000 and rows["Aziz"]["owed"] == 13000
    assert rows["Bobur"]["owed"] == 20000 and st["unassigned"] == 99999
    rep = ctx.get("/reports/center/payroll").json()
    assert rep["totals"]["owed"] == 33000
    # an unknown worker in a crew is refused
    assert ctx.post("/production", {"date": "2026-09-19T09:00:00", "warehouse_id": sc["sur"], "rows": [{"item_id": fbs, "qty": 1}], "worker_ids": [9999]}).status_code == 422


def test_pay_sections_follow_roles(ctx):
    from app.core.roles import level
    assert level("director", "pay") == 1 and level("acc", "pay") == 2 and level("wh", "pay") == 0


def test_worker_act_opening_period_and_closing(db_session, ctx):
    """The akt sverka of a worker: what was owed before the period, what happened in it, what is owed at the end."""
    from datetime import datetime
    from decimal import Decimal
    from app.models import FinDoc, PayAdjust, ProductionCrew, ProductionDoc, Worker
    from app.services import payroll as py
    with db_session() as db:
        w = Worker(name="Aziz", position="Press")
        w2 = Worker(name="Bobur", position="Press")
        db.add_all([w, w2])
        db.flush()
        for no, day, labour, crew in (("P1", 5, 1000, [w, w2]), ("P2", 20, 600, [w])):
            d = ProductionDoc(number=no, date=datetime(2026, 9, day), warehouse_id=1, status="posted", labour=Decimal(labour))
            d.crew = [ProductionCrew(worker_id=c.id) for c in crew]
            db.add(d)
        db.add(PayAdjust(worker_id=w.id, date=datetime(2026, 9, 25), amount=Decimal(-100), note="late", status="posted"))
        db.add(FinDoc(number="RKO-1", date=datetime(2026, 9, 28), kind="out", article="sal", account_id=1, worker_id=w.id, amount=Decimal(400), status="posted"))
        db.commit()
        wid = w.id
        full = py.worker_statement(db, wid)
        assert [r["kind"] for r in full["rows"]] == ["earn", "earn", "adj", "pay"]                 # date order
        assert (full["opening"], full["accrued"], full["paid"], full["closing"]) == (0, 1000, 400, 600)   # 500 + 600 - 100 accrued, 400 paid
        assert [r["balance"] for r in full["rows"]] == [500, 1100, 1000, 600]                     # running balance
        late = py.worker_statement(db, wid, start=datetime(2026, 9, 15), end=datetime(2026, 9, 30, 23, 59, 59))
        assert late["opening"] == 500 and late["accrued"] == 500 and late["paid"] == 400 and late["closing"] == 600
        assert py.worker_statement(db, wid, start=datetime(2026, 10, 1))["closing"] == 600 and not py.worker_statement(db, wid, start=datetime(2026, 10, 1))["rows"]
        assert py.worker_statement(db, 9999) is None
        # the closing balance equals what the pay statement says is owed
        assert py.statement(db)["rows"][0]["owed"] == 600
    r = ctx.get(f"/payroll/worker/{wid}")
    assert r.status_code == 200 and r.json()["closing"] == 600
    assert ctx.get("/payroll/worker/9999").status_code == 404
