import json

import pytest

from app.ai import assistant, client
from app.core.config import settings
from tests.conftest import login, scenario


class Fake:
    """Scripted stand-in for the Claude API: each call pops the next response and records the request."""

    def __init__(self, *responses):
        self.script, self.calls = list(responses), []

    def create(self, **body):
        self.calls.append(body)
        return self.script.pop(0)


def say(text):
    return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"}


def use(name, args, id_="tu_1"):
    return {"content": [{"type": "tool_use", "id": id_, "name": name, "input": args}], "stop_reason": "tool_use"}


@pytest.fixture(autouse=True)
def reset_llm():
    assistant._cache.clear()
    yield
    client.set_llm(None)


def test_disabled_without_key(ctx, monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert ctx.get("/ai/status").json() == {"enabled": False, "model": None, "provider": None}
    r = ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "hi"}], "lang": "uz"})
    assert r.status_code == 503 and r.json()["detail"]["code"] == "ai_disabled"
    assert ctx.get("/ai/insights?lang=uz").status_code == 200
    b = ctx.get("/ai/brief?mode=daily&lang=uz").json()
    assert b["ai"] is False
    assert ctx.post("/ai/draft", {"text": "x"}).status_code == 503


def test_chat_runs_tool_loop(ctx):
    scenario(ctx)
    fake = Fake(use("get_stock", {"query": "cement"}), say("Sementdan 3 700 kg qoldi."))
    client.set_llm(fake)
    r = ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "Sement qancha qoldi?"}], "lang": "uz"})
    assert r.status_code == 200, r.text
    assert r.json() == {"reply": "Sementdan 3 700 kg qoldi.", "tools": ["get_stock"]}
    first, second = fake.calls
    assert "Uzbek" in first["system"] and "administrator" in first["system"]
    assert {t["name"] for t in first["tools"]} >= {"get_stock", "run_report", "get_account_balances"}
    result = json.loads(second["messages"][-1]["content"][0]["content"])
    cement = result["items"][0]
    assert cement["item"] == "Cement" or cement["item"] == "Sement"
    assert cement["total"] == 3700


def test_chat_is_scoped_to_role(client, ctx):
    scenario(ctx)
    h = login(client, "sotuv", "sotuv123")                 # sales: no money accounts, no suppliers
    fake = Fake(use("get_account_balances", {}), use("supplier_statement", {"supplier": "Cement"}, "tu_2"),
                use("run_report", {"name": "cashflow"}, "tu_3"), say("ok"))
    from app.ai.client import set_llm
    set_llm(fake)
    r = client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "money?"}], "lang": "en"}, headers=h)
    assert r.status_code == 200
    names = {t["name"] for t in fake.calls[0]["tools"]}
    assert "get_account_balances" not in names and "supplier_statement" not in names
    for call in fake.calls[1:]:
        res = json.loads(call["messages"][-1]["content"][0]["content"])
        assert res.get("error") == "forbidden"


def test_chat_validation(ctx):
    from app.ai.client import set_llm
    set_llm(Fake(say("x")))
    assert ctx.post("/ai/chat", {"messages": [{"role": "assistant", "content": "hi"}], "lang": "en"}).status_code == 422
    assert ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "  "}], "lang": "en"}).status_code == 422
    assert ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "a"}], "lang": "de"}).status_code == 422


def test_brief_uses_model_and_caches(ctx):
    scenario(ctx)
    from app.ai.client import set_llm
    fake = Fake(say("• Pul yetarli."))
    set_llm(fake)
    a = ctx.get("/ai/brief?mode=finance&lang=uz").json()
    assert a["text"] == "• Pul yetarli." and a["ai"] is True
    sent = fake.calls[0]["messages"][0]["content"]
    assert "profit_30d" in sent and "dashboard" in sent
    b = ctx.get("/ai/brief?mode=finance&lang=uz").json()      # same data -> served from cache, no second model call
    assert b.get("cached") is True and len(fake.calls) == 1


def test_draft_matches_catalogue(ctx):
    scenario(ctx)
    from app.ai.client import set_llm
    prop = {"kind": "receipt", "party": "cement trade", "warehouse": "завод 1", "date": "2026-10-05",
            "rows": [{"item": "Sement", "qty": 500, "price": 1100}, {"item": "Armatura", "qty": 20}, {"item": "Unknown gizmo", "qty": 1}]}
    fake = Fake(use("propose_document", prop))
    set_llm(fake)
    r = ctx.post("/ai/draft", {"text": "Cement Trade dan 500 kg sement 1100 dan, 20 armatura", "lang": "en"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["kind"] == "receipt" and d["party"]["name"] == "Cement Trade" and d["warehouse"]["name"] == "Завод 1"
    assert d["rows"][0]["name"] == "Cement" and d["rows"][0]["price"] == 1100
    assert d["rows"][1]["name"] == "Rebar" and d["rows"][2]["item_id"] is None
    assert {w["code"] for w in d["warnings"]} == {"item_unmatched"}
    assert fake.calls[0]["tool_choice"] == {"type": "tool", "name": "propose_document"}
    assert ctx.get("/receipts").json()[0]["number"]        # the draft itself saved nothing new
    assert len(ctx.get("/receipts").json()) == 1


def test_draft_permissions_and_image(client, ctx):
    from app.ai.client import set_llm
    h = login(client, "sotuv", "sotuv123")
    set_llm(Fake(use("propose_document", {"kind": "receipt", "rows": []})))
    r = client.post("/api/ai/draft", json={"text": "x"}, headers=h)
    assert r.status_code == 403
    set_llm(Fake(use("propose_document", {"kind": "invoice", "party": "none", "rows": []})))
    assert client.post("/api/ai/draft", json={"text": "x"}, headers=h).status_code == 200
    set_llm(Fake())
    assert ctx.post("/ai/draft", {"image": {"media_type": "image/tiff", "data": "AAAA"}}).status_code == 422
    assert ctx.post("/ai/draft", {"image": {"media_type": "image/png", "data": "!!notbase64"}}).status_code == 422


def test_image_is_sent_to_model(ctx):
    from app.ai.client import set_llm
    fake = Fake(use("propose_document", {"kind": "payment_in", "amount": 1000, "article": "oin"}))
    set_llm(fake)
    r = ctx.post("/ai/draft", {"image": {"media_type": "image/png", "data": "iVBORw0KGgo="}})
    assert r.status_code == 200 and r.json()["amount"] == 1000
    assert fake.calls[0]["messages"][0]["content"][0]["type"] == "image"


def test_ai_rate_limit(ctx, monkeypatch):
    from app.ai.client import set_llm
    monkeypatch.setattr(settings, "ai_rate_per_10min", 2)
    from app.api import ai as ai_api
    ai_api._hits.clear()
    set_llm(Fake(say("a"), say("b"), say("c")))
    m = {"messages": [{"role": "user", "content": "hi"}], "lang": "en"}
    assert ctx.post("/ai/chat", m).status_code == 200
    assert ctx.post("/ai/chat", m).status_code == 200
    assert ctx.post("/ai/chat", m).status_code == 429



def test_stock_tool_survives_transliterated_warehouse_name(ctx):
    scenario(ctx)
    from app.ai.client import set_llm
    fake = Fake(use("get_stock", {"query": "rebar", "warehouse": "Zavod 1"}), say("ok"))
    set_llm(fake)
    ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "Zavod 1 da armatura?"}], "lang": "uz"})
    res = json.loads(fake.calls[1]["messages"][-1]["content"][0]["content"])
    assert "note" in res and "Завод 1" in res["warehouses"]          # no match -> all warehouses, model picks
    assert res["items"][0]["by_warehouse"]["Завод 1"] == 1000
