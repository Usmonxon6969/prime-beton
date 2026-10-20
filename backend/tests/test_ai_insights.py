from datetime import datetime

from app.ai import insights
from app.core.roles import ROLES, SECTIONS
from tests.conftest import scenario


def lv(role):
    return {s: ROLES[role].get(s, 0) for s in SECTIONS}


def test_insights_from_scenario(db_session, ctx):
    scenario(ctx)
    with db_session() as db:
        out = insights.collect(db, lv("admin"), "en", datetime(2026, 9, 20))
        kinds = {i["kind"] for i in out}
        assert "stockout" in kinds or "below_min" in kinds
        assert "debt_old" in kinds                          # 900 000 is 10 days past its due date (no term = due on delivery)
        early = insights.collect(db, lv("admin"), "en", datetime(2026, 9, 14))
        assert "debt_old" not in {i["kind"] for i in early}  # only 4 days late: not worth a signal yet
        late = insights.collect(db, lv("admin"), "ru", datetime(2026, 11, 20))
        d = [i for i in late if i["kind"] == "debt_old"]
        assert d and d[0]["data"]["debt"] == 900000 and "Orient Stroy" in d[0]["text"] and "просрочено" in d[0]["text"]
        assert any(i["kind"] == "slow" for i in late)       # blocks unsold for 60+ days
        cash = [i for i in late if i["id"] == "cash_forecast"]
        assert cash


def test_insights_respect_roles(db_session, ctx):
    scenario(ctx)
    with db_session() as db:
        out = insights.collect(db, lv("sales"), "en", datetime(2026, 11, 20))
        assert all(i["section"] in ("wh", "inv", "cus") for i in out)       # no money-account insights
        assert not any(i["kind"] in ("cash_out", "cash_ok", "payables") for i in out)
        prod = insights.collect(db, lv("prod"), "en", datetime(2026, 11, 20))
        assert not any(i["section"] in ("cus", "inv", "bank") for i in prod)


def test_duplicate_documents_are_flagged(db_session, ctx):
    sc = scenario(ctx)
    bank = [a for a in ctx.accounts if a["kind"] == "bank"][0]
    pay = {"date": "2026-09-14T10:00:00", "kind": "out", "account_id": bank["id"], "article": "fee", "party": "Bank", "amount": 55000}
    assert ctx.post("/finance", pay).status_code == 201
    assert ctx.post("/finance", {**pay, "date": "2026-09-14T15:00:00"}).status_code == 201       # same payment, same day
    inv = {"date": "2026-09-15T09:00:00", "customer_id": sc["cus"], "warehouse_id": sc["sur"], "rows": [{"item_id": sc["fbs"], "qty": 1, "price": 500000}]}
    assert ctx.post("/invoices", inv).status_code == 201
    assert ctx.post("/invoices", {**inv, "date": "2026-09-15T11:00:00"}).status_code == 201
    with db_session() as db:
        out = [i for i in insights.collect(db, lv("admin"), "en", datetime(2026, 9, 20)) if i["kind"] == "duplicate"]
        assert len(out) == 2 and {i["section"] for i in out} == {"inv", "bank"}
        assert "identical" in out[0]["text"]
        assert not [i for i in insights.collect(db, lv("sales"), "en", datetime(2026, 9, 20)) if i["kind"] == "duplicate" and i["section"] == "bank"]
        assert not [i for i in insights.collect(db, lv("admin"), "en", datetime(2026, 12, 1)) if i["kind"] == "duplicate"]   # old documents are not nagged about


def test_forecast_report(ctx):
    sc = scenario(ctx)
    now = datetime.now().replace(microsecond=0).isoformat()
    assert ctx.post("/production", {"date": now, "warehouse_id": sc["sur"], "rows": [{"item_id": sc["fbs"], "qty": 2}]}).status_code == 201
    assert ctx.post("/invoices", {"date": now, "customer_id": sc["cus"], "warehouse_id": sc["sur"], "rows": [{"item_id": sc["fbs"], "qty": 1, "price": 500000}]}).status_code == 201
    t = ctx.get("/reports/center/forecast?lang=en").json()
    assert t["rows"] and [r["days_left"] for r in t["rows"]] == sorted(r["days_left"] for r in t["rows"])
    assert {"item", "in_stock", "daily", "days_left"} <= {c["key"] for c in t["columns"]}
