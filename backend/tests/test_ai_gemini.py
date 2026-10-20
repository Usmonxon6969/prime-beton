import json

import httpx
import pytest

from app.ai import client
from app.core.config import settings
from tests.conftest import scenario


class FakeGemini:
    """Replaces httpx.post: answers like the Gemini generateContent API and records the requests."""

    def __init__(self, *replies):
        self.replies, self.reqs = list(replies), []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.reqs.append((url, json, headers))
        return httpx.Response(200, json=self.replies.pop(0))


def parts(*p):
    return {"candidates": [{"content": {"role": "model", "parts": list(p)}}], "usageMetadata": {}}


@pytest.fixture(autouse=True)
def gemini_only(monkeypatch):
    client.set_llm(None)
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "g-test")


def test_provider_selection(monkeypatch):
    assert client.provider() == "gemini" and isinstance(client.get_llm(), client.GeminiClient)
    monkeypatch.setattr(settings, "anthropic_api_key", "a-test")
    assert client.provider() == "anthropic"                       # auto prefers Anthropic when both are set
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    assert client.provider() == "gemini"
    monkeypatch.setattr(settings, "gemini_api_key", "")
    assert client.get_llm() is None


def test_chat_tool_loop_through_gemini(ctx, monkeypatch):
    scenario(ctx)
    fake = FakeGemini(parts({"functionCall": {"name": "get_stock", "args": {"query": "rebar", "warehouse": "Zavod 2"}}, "thoughtSignature": "SIG1"}),
                      parts({"text": "Armatura: 1 000 kg."}))
    monkeypatch.setattr(httpx, "post", fake)
    assert ctx.get("/ai/status").json() == {"enabled": True, "model": "gemini-3.8-flash", "provider": "gemini"}
    r = ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "Zavod 2 da armatura?"}], "lang": "uz"})
    assert r.status_code == 200 and r.json() == {"reply": "Armatura: 1 000 kg.", "tools": ["get_stock"]}
    url, first, headers = fake.reqs[0]
    assert url.endswith("/v1beta/models/gemini-3.8-flash:generateContent") and headers["x-goog-api-key"] == "g-test"
    decl = {d["name"]: d for d in first["tools"][0]["functionDeclarations"]}
    assert "get_stock" in decl and "parameters" in decl["get_stock"] and "parameters" not in decl["get_insights"]   # empty schemas omitted
    assert first["systemInstruction"]["parts"][0]["text"]
    second = fake.reqs[1][1]["contents"]
    assert second[1]["role"] == "model" and second[1]["parts"][0]["thoughtSignature"] == "SIG1"      # signature echoed back
    resp = second[2]["parts"][0]["functionResponse"]
    assert resp["name"] == "get_stock" and "note" in resp["response"]["result"]                     # tool result delivered as JSON


def test_draft_with_forced_function_and_image(ctx, monkeypatch):
    scenario(ctx)
    fake = FakeGemini(parts({"functionCall": {"name": "propose_document", "args": {"kind": "receipt", "party": "cement trade", "rows": [{"item": "Sement", "qty": 5}]}}}))
    monkeypatch.setattr(httpx, "post", fake)
    r = ctx.post("/ai/draft", {"text": "x", "image": {"media_type": "image/png", "data": "iVBORw0KGgo="}, "lang": "en"})
    assert r.status_code == 200 and r.json()["party"]["name"] == "Cement Trade" and r.json()["rows"][0]["name"] == "Cement"
    req = fake.reqs[0][1]
    assert req["toolConfig"]["functionCallingConfig"] == {"mode": "ANY", "allowedFunctionNames": ["propose_document"]}
    assert req["contents"][0]["parts"][0]["inlineData"]["mimeType"] == "image/png"


@pytest.mark.parametrize("status,code", [(503, "ai_busy"), (404, "ai_bad_model"), (400, "ai_bad_key"), (403, "ai_bad_key"), (429, "ai_busy"), (500, "ai_error")])
def test_gemini_errors(ctx, monkeypatch, status, code):
    monkeypatch.setattr(client.time, "sleep", lambda s: None)
    body = {"error": {"status": "INVALID_ARGUMENT", "message": "API_KEY_INVALID"}}
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(status, json=body if status == 400 else {}))
    r = ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "hi"}], "lang": "en"})
    assert r.json()["detail"]["code"] == code


def test_gemini_retries_on_overload(ctx, monkeypatch):
    scenario(ctx)
    monkeypatch.setattr(client.time, "sleep", lambda s: None)
    seq = [httpx.Response(503, json={}), httpx.Response(200, json=parts({"text": "ok"}))]
    monkeypatch.setattr(httpx, "post", lambda *a, **k: seq.pop(0))
    r = ctx.post("/ai/chat", {"messages": [{"role": "user", "content": "hi"}], "lang": "en"})
    assert r.status_code == 200 and r.json()["reply"] == "ok"
