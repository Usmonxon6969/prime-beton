"""AI document entry: tolerant matching (Latin/Cyrillic/typos), units, and posting a reviewed draft."""
import pytest

from app.ai import client, matching
from tests.conftest import login, scenario
from tests.test_ai import Fake, use


@pytest.fixture(autouse=True)
def reset():
    yield
    client.set_llm(None)


@pytest.mark.parametrize("a,b", [
    ("sement", "Цемент"), ("Cement", "Цемент"), ("Cемeнт", "Цемент"),            # Latin look-alike letters inside a Cyrillic word
    ("sementt", "Sement"), ("armatora", "Арматура"), ("kilinets", "Клинец"),     # typos
    ("sementdan", "Sement"), ("2PK 66x12", "2ПК 66*12"), ("2пк 71,5*10", "2ПК 71,5*10"),
    ("zavod 4", "Завод 4"), ("zavod 2", "Завод 2"), ("Zavod 1", "Завод 1"), ("ориент строй", "Orient Stroy"),
])
def test_same_name_in_either_script(a, b):
    assert matching.score(a, b) >= 0.85


@pytest.mark.parametrize("a,b", [("2PK 62x12", "2ПК 66*12"), ("Завод 4", "Zavod 3"), ("sement", "Qum"), ("armatura", "Klinets")])
def test_different_things_do_not_match(a, b):
    assert matching.score(a, b) < 0.6


def make(ctx, kind, **kw):
    return {"kind": kind, **kw}


def draft(ctx, prop, lang="uz"):
    client.set_llm(Fake(use("propose_document", prop)))
    r = ctx.post("/ai/draft", {"text": "x", "lang": lang})
    assert r.status_code == 200, r.text
    return r.json()


def test_draft_with_cyrillic_latin_and_typos(ctx):
    scenario(ctx)
    d = draft(ctx, {"kind": "receipt", "party": "цемент трейд", "warehouse": "zavod 1",
                    "rows": [{"item": "семент", "qty": 5}, {"item": "Klinec", "qty": 2}, {"item": "armatora", "qty": 1}, {"item": "pesok", "qty": 3}]})
    assert d["party"]["name"] == "Cement Trade" and d["warehouse"]["name"] == "Завод 1"
    assert [r["name"] for r in d["rows"]] == ["Sement", "Klinets", "Armatura", "Qum"]          # uz catalogue names, each written differently
    assert d["warnings"] == [] and d["can_post"]


def test_ambiguous_row_is_left_to_the_user(ctx):
    scenario(ctx)
    d = draft(ctx, {"kind": "production", "warehouse": "Завод 1", "rows": [{"item": "2пк 66", "qty": 5}]})
    r = d["rows"][0]
    assert r["item_id"] is None and len(r["candidates"]) >= 2 and r["candidates"][0]["name"].startswith("2ПК 66")


def test_tonnes_are_converted_and_wrong_kind_is_flagged(ctx):
    scenario(ctx)
    d = draft(ctx, {"kind": "receipt", "party": "Cement Trade", "warehouse": "Завод 1",
                    "rows": [{"item": "Sement", "qty": 2.5, "unit": "tonna", "price": 1_000_000}, {"item": "ФБС 24.4.6-Т", "qty": 4}]})
    a, b = d["rows"]
    assert a["qty"] == 2500 and a["price"] == 1000 and a["unit"] == "kg" and "tonna" in a["note"]
    assert b["item_id"] is None
    assert {w["code"] for w in d["warnings"]} == {"unit_converted", "item_wrong_kind"}


def test_production_draft_only_offers_plants(ctx):
    scenario(ctx)
    d = draft(ctx, {"kind": "production", "warehouse": "metal sklad", "rows": [{"item": "ФБС 24.4.6-Т", "qty": 3}]})
    assert d["warehouse"] is None and {w["code"] for w in d["warnings"]} == {"warehouse_unmatched"}
    d = draft(ctx, {"kind": "production", "warehouse": "завод 2", "rows": [{"item": "fbs 24.4.6-t", "qty": 3}]})
    assert d["warehouse"]["name"] == "Завод 2" and d["rows"][0]["qty"] == 3


def body(d, **kw):
    out = {"kind": d["kind"], "date": "2026-10-12T10:00:00", "party_id": d["party"]["id"] if d.get("party") else None,
           "warehouse_id": d["warehouse"]["id"] if d.get("warehouse") else None, "comment": d["comment"],
           "rows": [{"item_id": r["item_id"], "qty": r["qty"], "price": r["price"] or 0} for r in d["rows"]], "lang": "uz"}
    out.update(kw)
    return out


def test_commit_receipt_invoice_and_production(ctx):
    scenario(ctx)
    I = ctx.items
    d = draft(ctx, {"kind": "receipt", "party": "cement trade", "warehouse": "zavod 1", "rows": [{"item": "sement", "qty": 1000, "price": 1200}]})
    r = ctx.post("/ai/draft/commit", body(d))
    assert r.status_code == 201, r.text
    assert r.json()["number"].startswith("PN-") and r.json()["total"] == 1_200_000
    assert ctx.stock("Cement", "Завод 1") == 3700 + 1000
    d = draft(ctx, {"kind": "production", "warehouse": "завод 1", "rows": [{"item": "ФБС 24.4.6-Т", "qty": 2}]})
    r = ctx.post("/ai/draft/commit", body(d))
    assert r.status_code == 201 and r.json()["number"].startswith("PRD-") and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 4
    assert ctx.stock("Cement", "Завод 1") == 3700 + 1000 - 520
    d = draft(ctx, {"kind": "invoice", "party": "orient stroy", "warehouse": "завод 1", "rows": [{"item": "фбс 24.4.6 т", "qty": 4, "price": 500000}]})
    r = ctx.post("/ai/draft/commit", body(d))
    assert r.status_code == 201 and r.json()["number"].startswith("RN-") and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 0
    assert any(x["number"] == r.json()["number"] for x in ctx.get("/invoices").json())
    # the journal shows who posted it
    j = ctx.get("/audit?entity=invoices").json()
    assert (j["rows"] if isinstance(j, dict) else j)[0]["user"] == "admin"


def test_commit_checks_stock_and_completeness(ctx):
    s = scenario(ctx)
    d = draft(ctx, {"kind": "invoice", "party": "orient stroy", "warehouse": "завод 1", "rows": [{"item": "фбс", "qty": 50}]})
    r = ctx.post("/ai/draft/commit", body(d, rows=[{"item_id": s["fbs"], "qty": 50, "price": 1}]))
    assert r.status_code == 409 and r.json()["detail"]["code"] == "insufficient_stock"          # same rule as the normal screen
    r = ctx.post("/ai/draft/commit", body(d, rows=[{"item_id": None, "qty": 1}]))
    assert r.json()["detail"]["code"] == "draft_incomplete"
    r = ctx.post("/ai/draft/commit", body(d, warehouse_id=None, rows=[{"item_id": s["fbs"], "qty": 1, "price": 1}]))
    assert r.status_code == 422 and r.json()["detail"]["code"] == "draft_incomplete"
    assert len(ctx.get("/invoices").json()) == 1                                                  # nothing half-saved


def test_commit_can_add_the_partner(ctx):
    scenario(ctx)
    d = draft(ctx, {"kind": "receipt", "party": "Yangi Ta'minotchi", "warehouse": "завод 1", "rows": [{"item": "sement", "qty": 10, "price": 1000}]})
    assert d["party"]["id"] is None and d["warnings"][0]["code"] == "party_unmatched"
    r = ctx.post("/ai/draft/commit", body(d, new_party="Yangi Ta'minotchi"))
    assert r.status_code == 201
    assert "Yangi Ta'minotchi" in [x["name"] for x in ctx.get("/suppliers").json()]


def test_commit_respects_roles(client, ctx):
    scenario(ctx)
    d = draft(ctx, {"kind": "receipt", "party": "cement trade", "warehouse": "завод 1", "rows": [{"item": "sement", "qty": 1, "price": 1}]})
    h = login(client, "sotuv", "sotuv123")                                    # sales cannot post receipts
    assert client.post("/api/ai/draft/commit", json=body(d), headers=h).status_code == 403
    h = login(client, "ishlab", "prod123")                                    # production head can post production only
    prod = draft(ctx, {"kind": "production", "warehouse": "завод 1", "rows": [{"item": "фбс", "qty": 1}]})
    assert client.post("/api/ai/draft/commit", json=body(prod), headers=h).status_code in (201, 409)
    assert client.post("/api/ai/draft/commit", json=body(d), headers=h).status_code == 403
