from tests.conftest import NOW, login


def acc(ctx, kind, i=0):
    return [a for a in ctx.accounts if a["kind"] == kind][i]


def fin(ctx, kind, account, amount, **kw):
    body = {"date": NOW, "kind": kind, "account_id": account["id"], "article": kw.pop("article"), "amount": amount}
    body.update(kw)
    return ctx.post("/finance", body)


def test_money_numbers_and_balances(ctx):
    bank, cash = acc(ctx, "bank"), acc(ctx, "cash")
    cus = ctx.customer()
    a = fin(ctx, "in", bank, 5_000_000, article="cust", customer_id=cus)
    assert a.status_code == 201 and a.json()["number"] == "BP-000001"
    assert fin(ctx, "out", bank, 1_000_000, article="tax", party="Soliq").json()["number"] == "BS-000001"
    assert fin(ctx, "in", cash, 300_000, article="oin").json()["number"] == "PKO-000001"
    t = fin(ctx, "tr", bank, 2_000_000, article="tr", to_account_id=cash["id"])
    assert t.status_code == 201, t.text
    bal = {x["id"]: x["balance"] for x in ctx.get("/accounts").json()}
    assert bal[bank["id"]] == 2_000_000 and bal[cash["id"]] == 2_300_000


def test_cash_cannot_go_negative(ctx):
    cash = acc(ctx, "cash")
    r = fin(ctx, "out", cash, 1000, article="sal", party="Workers")
    assert r.status_code == 409 and r.json()["detail"]["code"] == "cash_negative"
    assert ctx.get("/finance?kind=cash").json() == []
    fin(ctx, "in", cash, 5000, article="oin")
    assert fin(ctx, "out", cash, 5000, article="sal", party="Workers").status_code == 201
    # deleting the income would leave the cash desk negative -> blocked
    inc = ctx.get("/finance?kind=cash").json()
    income = [d for d in inc if d["kind"] == "in"][0]
    assert ctx.c.delete(f"/api/finance/{income['id']}", headers=ctx.h).status_code == 409


def test_account_validation(ctx):
    bank = acc(ctx, "bank")
    cus = ctx.customer()
    assert fin(ctx, "in", bank, 10, article="tax").status_code == 422          # tax is an expense
    assert fin(ctx, "in", bank, 10, article="cust").status_code == 422         # needs a customer
    assert fin(ctx, "tr", bank, 10, article="tr", to_account_id=bank["id"]).status_code == 422
    assert fin(ctx, "in", bank, 10, article="cust", customer_id=cus).status_code == 201


def test_customer_debt_and_statement(ctx):
    sup = ctx.supplier()
    fbs = ctx.items["ФБС 24.4.6-Т"]["id"]
    ctx.post("/receipts", {"date": NOW, "supplier_id": sup, "warehouse_id": ctx.wh["Завод 1"]["id"], "rows": [{"item_id": fbs, "qty": 10, "price": 400000}]})
    cus = ctx.customer()
    ctx.post("/invoices", {"date": "2026-10-10T09:00:00", "customer_id": cus, "warehouse_id": ctx.wh["Завод 1"]["id"], "rows": [{"item_id": fbs, "qty": 4, "price": 420000}]})
    fin(ctx, "in", acc(ctx, "bank"), 600_000, article="cust", customer_id=cus, date="2026-10-11T09:00:00")
    d = [x for x in ctx.get("/reports/customer-debts").json() if x["customer_id"] == cus][0]
    assert d["shipped"] == 1_680_000 and d["paid"] == 600_000 and d["debt"] == 1_080_000
    st = ctx.get(f"/reports/customers/{cus}/statement").json()
    assert [r["kind"] for r in st["rows"]] == ["invoice", "payment"] and st["closing"] == 1_080_000
    later = ctx.get(f"/reports/customers/{cus}/statement?start=2026-10-11T00:00:00").json()
    assert later["opening"] == 1_680_000 and later["closing"] == 1_080_000 and len(later["rows"]) == 1


def test_supplier_debt(ctx):
    sup = ctx.supplier()
    ctx.post("/receipts", {"date": NOW, "supplier_id": sup, "warehouse_id": ctx.wh["Завод 1"]["id"], "rows": [{"item_id": ctx.items["Cement"]["id"], "qty": 1000, "price": 1000}]})
    fin(ctx, "in", acc(ctx, "bank"), 5_000_000, article="oin")
    fin(ctx, "out", acc(ctx, "bank"), 400_000, article="sup", supplier_id=sup)
    d = [x for x in ctx.get("/reports/supplier-debts").json() if x["supplier_id"] == sup][0]
    assert d["bought"] == 1_000_000 and d["debt"] == 600_000


def test_dashboard_is_filtered_by_role(client, ctx):
    d = ctx.get("/reports/dashboard").json()
    assert {"bank_total", "cash_total", "accounts", "daily", "low_stock", "production_daily"} <= d.keys()
    h = login(client, "ishlab", "prod123")
    p = client.get("/api/reports/dashboard", headers=h).json()
    assert "bank_total" not in p and "sales_30d" not in p and "production_daily" in p


# ---------------------------------------------------------------- a bank account cannot be pushed below zero
def _bank(ctx):
    return [a for a in ctx.accounts if a["kind"] == "bank"][0]


def _pay_out(ctx, bank, amount, **kw):
    return ctx.post("/finance", {"date": "2026-10-14T22:18:00", "kind": "out", "account_id": bank["id"], "article": "oout", "party": "Kriptex Metal", "amount": amount, **kw})


def test_bank_payment_needs_money_on_the_account(ctx):
    bank = _bank(ctx)
    r = _pay_out(ctx, bank, 1000)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "bank_negative"        # empty account: refused
    assert ctx.post("/finance", {"date": "2026-10-14T09:00:00", "kind": "in", "account_id": bank["id"], "article": "oin", "party": "Investor", "amount": 5000}).status_code == 201
    assert _pay_out(ctx, bank, 3000).status_code == 201
    r = _pay_out(ctx, bank, 3000)                                                          # only 2000 left
    assert r.status_code == 409 and r.json()["detail"]["params"]["available"] == 2000
    assert _pay_out(ctx, bank, 2000).status_code == 201                                    # exactly the rest is fine


def test_bank_transfer_and_edits_cannot_overdraw(ctx):
    bank = _bank(ctx)
    cash = [a for a in ctx.accounts if a["kind"] == "cash"][0]
    inc = ctx.post("/finance", {"date": "2026-10-14T09:00:00", "kind": "in", "account_id": bank["id"], "article": "oin", "party": "Investor", "amount": 1000}).json()
    tr = {"date": "2026-10-14T10:00:00", "kind": "tr", "account_id": bank["id"], "to_account_id": cash["id"], "article": "tr", "amount": 5000}
    assert ctx.post("/finance", tr).status_code == 409                                     # transfer out of an empty account
    ok = _pay_out(ctx, bank, 600).json()
    r = ctx.c.put(f"/api/finance/{ok['id']}", headers=ctx.h, json={"date": "2026-10-14T22:18:00", "kind": "out", "account_id": bank["id"], "article": "oout", "party": "Kriptex Metal", "amount": 1500})
    assert r.status_code == 409                                                            # raising an old payment above the balance
    # deleting the incoming money would leave the 600 payment uncovered
    assert ctx.c.delete(f"/api/finance/{inc['id']}", headers=ctx.h).status_code == 409


def test_already_negative_bank_does_not_block_other_documents(ctx, monkeypatch):
    from app.core.config import settings
    bank = _bank(ctx)
    monkeypatch.setattr(settings, "bank_allow_negative", True)
    assert _pay_out(ctx, bank, 700).status_code == 201                                     # overdraft allowed by the switch: balance is -700
    monkeypatch.setattr(settings, "bank_allow_negative", False)
    assert ctx.post("/finance", {"date": "2026-10-14T09:00:00", "kind": "in", "account_id": bank["id"], "article": "oin", "party": "Investor", "amount": 100}).status_code == 201   # incoming money is never blocked
    assert _pay_out(ctx, bank, 50).status_code == 409                                      # but paying out of a negative account is
