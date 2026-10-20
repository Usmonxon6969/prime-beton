from io import BytesIO

from tests.conftest import login, scenario


def test_meeting_deck_numbers_and_summary(ctx):
    scenario(ctx)
    d = ctx.get("/reports/meeting?month=2026-09&lang=en").json()
    ids = [s["id"] for s in d["slides"]]
    assert ids == ["overview", "production", "plants", "products", "scrap", "sales", "purchases", "debts", "stock", "materials", "people", "summary"]
    assert d["label"] == "September 2026" and d["prev_label"] == "August 2026"
    prod = next(s for s in d["slides"] if s["id"] == "production")
    assert prod["kpis"][0]["value"] == 5
    assert [(k["label"], k["value"], k["prev"]) for k in prod["kpis"][1:]] == [("Block", 5, 0)]        # one card per kind of product, with last month beside it
    assert next(s for s in d["slides"] if s["id"] == "products")["tables"][0]["rows"][0]["good"] == 5
    ov = next(s for s in d["slides"] if s["id"] == "overview")
    assert [x["label"] for x in ov["spots"]][:3] == ["Top plant", "Best day"]            # sales put nobody in the spotlight
    assert ov["spots"][0]["name"] == "Завод 1" and ov["spots"][0]["value"] == 5
    assert next(s for s in d["slides"] if s["id"] == "plants")["tables"][0]["rows"][0]["share"] == 100
    sales = next(s for s in d["slides"] if s["id"] == "sales")
    assert sales["kpis"][0]["value"] == 1_500_000
    assert not sales.get("spots") or all("customer" not in x["label"].lower() for x in sales["spots"])      # sales are figures only
    assert [t["title"] for t in sales["tables"]] == ["By product"] and "top3" not in str(sales["kpis"])
    assert d["slides"][-1]["bullets"]
    assert not any("cash" in str(s).lower() or "bank" in s["id"] for s in d["slides"])      # no money-movement slide
    uz = ctx.get("/reports/meeting?month=2026-09&lang=uz").json()
    assert uz["label"] == "Sentyabr 2026" and uz["slides"][0]["title"] == "Umumiy ko‘rinish"
    empty = ctx.get("/reports/meeting?month=2020-01&lang=en").json()
    assert empty["slides"][-1]["id"] == "summary"
    assert ctx.get("/reports/meeting?month=2026-13").status_code in (400, 422)


def test_meeting_pptx_download(ctx):
    scenario(ctx)
    r = ctx.get("/reports/meeting/export.pptx?month=2026-09&lang=ru")
    assert r.status_code == 200 and r.content[:2] == b"PK"
    from pptx import Presentation
    prs = Presentation(BytesIO(r.content))
    assert len(prs.slides) >= 12                                                             # cover + the slides (long ones take two pages)
    assert ctx.get("/reports/meeting/export.pptx?month=bad").status_code == 422


def _grant(ctx, username, on=True):
    uid = next(u["id"] for u in ctx.get("/auth/users").json() if u["username"] == username)
    r = ctx.c.patch(f"/api/auth/users/{uid}", json={"premium": {"feature": "meeting", "on": on}}, headers=ctx.h)
    assert r.status_code == 200, r.text
    return r.json()


def test_meeting_shows_each_role_only_its_own_slides(client, ctx):
    scenario(ctx)
    _grant(ctx, "omborchi")
    _grant(ctx, "buxgalter")
    wh = client.get("/api/reports/meeting?month=2026-09", headers=login(client, "omborchi", "sklad123")).json()
    ids = [x["id"] for x in wh["slides"]]
    assert "production" in ids and "stock" in ids and "sales" in ids      # warehouse keeper ships goods
    assert "people" not in ids
    debts = next(x for x in wh["slides"] if x["id"] == "debts")            # sees supplier debts only, never the customers'
    assert [k["label"] for k in debts["kpis"]] == ["We owe suppliers"] and [t["title"] for t in debts["tables"]] == ["What we owe suppliers"]
    acc = client.get("/api/reports/meeting?month=2026-09", headers=login(client, "buxgalter", "buh123")).json()
    ids = [x["id"] for x in acc["slides"]]
    assert "production" not in ids and "stock" not in ids and "debts" in ids and "people" in ids


def test_running_month_is_compared_with_the_same_days_of_the_month_before(db_session, ctx):
    from datetime import datetime
    from app.services import meeting
    scenario(ctx)
    lv = {s: 2 for s in ("prod", "inv", "cus", "sup", "wh", "pay")}
    with db_session() as db:
        d = meeting.build(db, "2026-09", "en", lv, today=datetime(2026, 9, 10, 12))
        assert "1–10 September" in d["note"] and "1–10 August" in d["note"]
        full = meeting.build(db, "2026-09", "en", lv, today=datetime(2026, 10, 19))
        assert full["note"] == ""
        assert next(s for s in full["slides"] if s["id"] == "production")["kpis"][0]["value"] == 5


def test_meeting_ai_is_off_without_a_key_and_only_adds_remarks_when_on(ctx, monkeypatch):
    import json
    from app.ai import client, meeting_ai
    from tests.test_ai import Fake, say
    scenario(ctx)
    meeting_ai._cache.clear()
    monkeypatch.setattr("app.core.config.settings.anthropic_api_key", "")
    monkeypatch.setattr("app.core.config.settings.gemini_api_key", "")
    assert ctx.get("/reports/meeting/ai?month=2026-09&lang=en").json()["ai"] is False
    reply = {"slides": {"production": "Output was 5 units.", "nonsense": "dropped"}, "points": ["Point one"], "questions": ["Why is scrap high?", "What to buy?"]}
    fake = Fake(say("```json\n" + json.dumps(reply) + "\n```"))
    client.set_llm(fake)
    try:
        r = ctx.get("/reports/meeting/ai?month=2026-09&lang=uz").json()
        assert r["ai"] is True and r["slides"] == {"production": "Output was 5 units."} and len(r["questions"]) == 2
        sent = fake.calls[0]
        assert "Uzbek" in sent["system"] and "ONLY the numbers" in sent["system"]
        assert "525" not in sent["messages"][0]["content"] and "Cement" not in sent["system"]
        again = ctx.get("/reports/meeting/ai?month=2026-09&lang=uz").json()           # cached: the script has no second answer
        assert again == r
        p = ctx.get("/reports/meeting/export.pptx?month=2026-09&lang=uz&ai=1")
        assert p.status_code == 200
        from io import BytesIO
        from pptx import Presentation
        assert len(Presentation(BytesIO(p.content)).slides) >= 14                    # cover + the slides (long ones take two pages) + questions
    finally:
        client.set_llm(None)
        meeting_ai._cache.clear()
    client.set_llm(Fake(say("not json at all")))
    try:
        bad = ctx.get("/reports/meeting/ai?month=2026-08&lang=en").json()
        assert bad["ai"] is False and bad["error"] == "ai_bad_answer"
    finally:
        client.set_llm(None)


def test_meeting_is_premium_until_the_main_administrator_switches_it_on(client, ctx):
    scenario(ctx)
    other = login(client, "buxgalter", "buh123")
    for url in ("/reports/meeting?month=2026-09", "/reports/meeting/ai?month=2026-09", "/reports/meeting/export.pptx?month=2026-09"):
        r = client.get("/api" + url, headers=other)
        assert r.status_code == 403 and r.json()["detail"]["code"] == "premium_required", url
    assert client.get("/api/auth/me", headers=other).json()["features"] == []
    assert ctx.get("/reports/meeting?month=2026-09").status_code == 200                   # the main administrator always has it, with no limit
    assert client.get("/api/auth/me", headers=ctx.h).json()["features"] == ["meeting"]
    g = _grant(ctx, "buxgalter")["premium"][0]
    assert g["feature"] == "meeting" and g["active"] and g["uses_limit"] == 2 and g["uses_left"] == 2
    assert client.get("/api/reports/meeting?month=2026-09", headers=other).status_code == 200
    assert client.get("/api/auth/me", headers=other).json()["features"] == ["meeting"]
    _grant(ctx, "buxgalter", on=False)                                                     # and it can be taken away again
    assert client.get("/api/reports/meeting?month=2026-09", headers=other).status_code == 403


def test_premium_lasts_a_month_and_two_meetings(client, ctx, db_session):
    from datetime import datetime, timedelta
    from app.models import PremiumGrant
    scenario(ctx)
    g = _grant(ctx, "buxgalter")["premium"][0]
    assert 29 <= (datetime.fromisoformat(g["expires_at"]) - datetime.utcnow()).days <= 30       # one month
    other = login(client, "buxgalter", "buh123")
    get = lambda m, path="": client.get(f"/api/reports/meeting{path}?month={m}", headers=other)
    assert get("2026-09").status_code == 200 and get("2026-09").status_code == 200            # the same month again costs nothing
    assert get("2026-09", "/ai").status_code == 200 and get("2026-09", "/export.pptx").status_code == 200
    me = client.get("/api/auth/me", headers=other).json()["premium"][0]
    assert me["uses_left"] == 1 and me["used"] == ["2026-09"]
    assert get("2026-08").status_code == 200                                                    # the second meeting
    r = get("2026-07")                                                                          # a third one is over the limit
    assert r.status_code == 403 and r.json()["detail"]["code"] == "premium_limit"
    assert get("2026-08").status_code == 200 and get("2026-09").status_code == 200              # the ones already held still open
    assert _grant(ctx, "buxgalter")["premium"][0]["uses_left"] == 2                             # switching on again starts a new month with full uses
    assert get("2026-07").status_code == 200
    with db_session() as db:                                                                    # after a month it stops
        row = db.query(PremiumGrant).one()
        row.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    r = get("2026-07")
    assert r.status_code == 403 and r.json()["detail"]["code"] == "premium_required"
    me = client.get("/api/auth/me", headers=other).json()
    assert me["features"] == [] and me["premium"][0]["active"] is False


def test_only_the_main_administrator_can_switch_premium_on(client, ctx):
    uid = next(u["id"] for u in ctx.get("/auth/users").json() if u["username"] == "buxgalter")
    r = ctx.c.post("/api/auth/users", json={"username": "second", "password": "Str0ng-Pass-77", "full_name": "Second", "role": "admin"}, headers=ctx.h)
    assert r.status_code == 201, r.text
    second = login(client, "second", "Str0ng-Pass-77")                                      # a second administrator is not the main one
    r = client.patch(f"/api/auth/users/{uid}", json={"premium": {"feature": "meeting", "on": True}}, headers=second)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "owner_only"
    assert client.get("/api/reports/meeting?month=2026-09", headers=second).status_code == 403    # an administrator is not exempt either
    assert client.get("/api/auth/me", headers=second).json()["owner"] is False
    assert client.get("/api/auth/me", headers=ctx.h).json()["owner"] is True
    r = client.patch(f"/api/auth/users/{uid}", json={"full_name": "Buxgalter"}, headers=second)   # normal edits still work for them
    assert r.status_code == 200
    r = ctx.c.patch(f"/api/auth/users/{uid}", json={"premium": {"feature": "nope", "on": True}}, headers=ctx.h)
    assert r.status_code == 422


def test_production_kpis_split_by_kind_of_product(ctx):
    scenario(ctx)
    I = ctx.items
    sur = ctx.wh["Завод 1"]["id"]
    for name, qty in (("2ПК 40*12", 7), ("Опора СВ 110-3,5", 2)):
        if name in I:
            ctx.post("/production", {"date": "2026-09-20T09:00:00", "warehouse_id": sur, "rows": [{"item_id": I[name]["id"], "qty": qty}]})
    from app.services import meeting
    from app.models import Item
    assert meeting._ptype(Item(name_ru="2ПК 66,5*10", name_uz="", name_en="")) == "slab"
    assert meeting._ptype(Item(name_ru="Опора СВ 110-3,5", name_uz="", name_en="")) == "pole"
    assert meeting._ptype(Item(name_ru="Лоток Л-5", name_uz="", name_en="")) == "tray"
    assert meeting._ptype(Item(name_ru="ФБС 24.4.6-Т", name_uz="", name_en="")) == "block"
    assert meeting._ptype(Item(name_ru="Что-то", name_uz="", name_en="")) == "other"
    d = ctx.get("/reports/meeting?month=2026-09&lang=uz").json()
    prod = next(x for x in d["slides"] if x["id"] == "production")
    assert prod["kpis"][0]["label"] == "Ishlab chiqarildi" and all(k["prev"] is not None for k in prod["kpis"])


def test_best_worker_is_counted_from_the_crew_of_each_document(ctx):
    scenario(ctx)
    a = ctx.post("/workers", {"name": "Ali", "position": "Quyuvchi"}).json()["id"]
    b = ctx.post("/workers", {"name": "Vali", "position": "Quyuvchi"}).json()["id"]
    fbs, sur = ctx.items["ФБС 24.4.6-Т"]["id"], ctx.wh["Завод 1"]["id"]
    assert ctx.post("/production", {"date": "2026-09-21T09:00:00", "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 1}], "worker_ids": [a]}).status_code == 201
    assert ctx.post("/production", {"date": "2026-09-22T09:00:00", "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 2}], "worker_ids": [a, b]}).status_code == 201
    d = ctx.get("/reports/meeting?month=2026-09&lang=en").json()
    ppl = next(x for x in d["slides"] if x["id"] == "people")
    rows = ppl["tables"][0]["rows"]
    assert [(r["worker"], r["pieces"], r["days_c"]) for r in rows] == [("Ali", 2, 2), ("Vali", 1, 1)]       # a shared document counts for each, split equally
    best = next(x for x in ppl["spots"] if x["label"] == "Best worker")
    assert best["name"] == "Ali" and best["value"] == 2


def test_numbers_are_whole_with_spaces_and_slab_target():
    from app.services import meeting as m
    from app.services.meeting_pptx import _num
    assert m._q(1234.56) == 1235 and m._q(12.0) == 12 and m._q(3.04) == 3 and m._q(3.46) == 3.5
    assert m._nf(1234567.2) == "1 234 567" and m._nf(0.4) == "0,4" and m._nf(5.0) == "5"
    assert _num(1234567) == "1 234 567" and _num(12.0) == "12" and _num(4.0) == "4" and _num(2.5) == "2,5"
    assert _num(5.0, "pct") == "+5%" and _num(-12.4, "pct") == "-12%" and _num(1234.5, "money") == "1 235"
    k = m._kpi("slab_avg", "en", 52, 38, "pcs", m.SLAB_TARGET)
    assert k["target"]["ok"] is True and "good" in k["target"]["text"] and k["value"] == 52
    assert m._kpi("slab_avg", "uz", 31, 38, "dona", m.SLAB_TARGET)["target"]["ok"] is False
    assert "52" in m._tr("f_slab_ok", "en", a=52.0, n=40)


def test_ai_sees_no_customers_in_sales():
    from app.ai.meeting_ai import _compact
    deck = {"label": "x", "prev_label": "y", "slides": [
        {"id": "sales", "title": "Sales", "kpis": [{"label": "Shipped", "value": 5, "unit": "UZS"}], "spots": [{"label": "Top customer", "name": "ACME", "value": 1}],
         "tables": [{"columns": [{"key": "customer", "label": "Customer"}], "rows": [{"customer": "ACME"}]}]},
        {"id": "summary", "title": "S", "bullets": ["fact"]}]}
    out = _compact(deck)
    assert "ACME" not in str(out) and out["slides"][0]["id"] == "sales"
