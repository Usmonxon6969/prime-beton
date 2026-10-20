"""Thin Anthropic Messages API client (plain HTTPS, no SDK) with a swap point for tests.

The key comes only from the ANTHROPIC_API_KEY environment variable (see app.core.config); it is never logged,
stored or sent to the browser.
"""
import json
import logging
import time

import httpx

from app.core.config import settings

log = logging.getLogger("daybook.ai")


class AIError(Exception):
    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


class AnthropicClient:
    def create(self, **body) -> dict:
        body.setdefault("model", settings.ai_model)
        body.setdefault("max_tokens", 1500)
        try:
            r = httpx.post(settings.ai_base_url.rstrip("/") + "/v1/messages", json=body, timeout=settings.ai_timeout,
                           headers={"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01",
                                    "content-type": "application/json"})
        except httpx.HTTPError as e:
            log.warning("AI request failed: %s", type(e).__name__)
            raise AIError("ai_unreachable", "The AI service cannot be reached") from e
        if r.status_code == 401:
            raise AIError("ai_bad_key", "The AI key was rejected", 502)
        if r.status_code in (429, 503):
            raise AIError("ai_busy", "The AI service is busy, try again shortly", 503)
        if r.status_code >= 400:
            log.warning("AI error %s: %s", r.status_code, r.text[:300])
            raise AIError("ai_error", "The AI service returned an error", 502)
        data = r.json()
        u = data.get("usage") or {}
        log.info("AI call model=%s in=%s out=%s", data.get("model"), u.get("input_tokens"), u.get("output_tokens"))
        return data


class GeminiClient:
    """Google Gemini behind the same `.create(**anthropic_style_body) -> anthropic_style_dict` interface, so the assistant,
    briefing and draft code do not care which model answers. Tool calls keep Gemini's thoughtSignature (needed by
    thinking models) inside the tool_use block under `_sig`."""

    @staticmethod
    def _parts(content, names):
        if isinstance(content, str):
            return [{"text": content}]
        parts = []
        for b in content:
            t = b.get("type")
            if t == "text":
                parts.append({"text": b["text"]})
            elif t == "image":
                src = b["source"]
                parts.append({"inlineData": {"mimeType": src["media_type"], "data": src["data"]}})
            elif t == "tool_use":
                p = {"functionCall": {"name": b["name"], "args": b.get("input") or {}}}
                if b.get("_sig"):
                    p["thoughtSignature"] = b["_sig"]
                names[b["id"]] = b["name"]
                parts.append(p)
            elif t == "tool_result":
                try:
                    val = json.loads(b["content"])
                except (ValueError, TypeError):
                    val = b["content"]
                parts.append({"functionResponse": {"name": names.get(b["tool_use_id"], "tool"), "response": {"result": val}}})
        return parts

    @staticmethod
    def _schema(sch):
        out = {k: v for k, v in sch.items() if k in ("type", "description", "enum", "required", "properties", "items")}
        if "properties" in out:
            out["properties"] = {k: GeminiClient._schema(v) for k, v in out["properties"].items()}
        if "items" in out:
            out["items"] = GeminiClient._schema(out["items"])
        if not out.get("required"):
            out.pop("required", None)
        return out

    def create(self, **body) -> dict:
        names: dict = {}
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": self._parts(m["content"], names)} for m in body["messages"]]
        req: dict = {"contents": contents, "generationConfig": {"maxOutputTokens": body.get("max_tokens", 1500)}}
        if body.get("system"):
            req["systemInstruction"] = {"parts": [{"text": body["system"]}]}
        if body.get("tools"):
            decl = []
            for t in body["tools"]:
                d = {"name": t["name"], "description": t.get("description", "")}
                if t["input_schema"].get("properties"):
                    d["parameters"] = self._schema(t["input_schema"])
                decl.append(d)
            req["tools"] = [{"functionDeclarations": decl}]
        tc = body.get("tool_choice")
        if tc and tc.get("type") == "tool":
            req["toolConfig"] = {"functionCallingConfig": {"mode": "ANY", "allowedFunctionNames": [tc["name"]]}}
        model = settings.gemini_model
        url = f"{settings.gemini_base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
        hdr = {"x-goog-api-key": settings.gemini_api_key, "content-type": "application/json"}
        for attempt in range(3):                       # Gemini answers 503/429 under load: retry a couple of times
            try:
                r = httpx.post(url, json=req, timeout=settings.ai_timeout, headers=hdr)
            except httpx.HTTPError as e:
                log.warning("AI request failed: %s", type(e).__name__)
                raise AIError("ai_unreachable", "The AI service cannot be reached") from e
            if r.status_code not in (429, 500, 503) or attempt == 2:
                break
            time.sleep(1.5 * (attempt + 1))
        if r.status_code in (401, 403) or (r.status_code == 400 and "API_KEY" in r.text):
            raise AIError("ai_bad_key", "The AI key was rejected", 502)
        if r.status_code == 404:
            log.warning("AI model not available: %s (set GEMINI_MODEL in .env)", model)
            raise AIError("ai_bad_model", f"The AI model '{model}' is not available; change GEMINI_MODEL", 502)
        if r.status_code in (429, 503):
            raise AIError("ai_busy", "The AI service is busy, try again shortly", 503)
        if r.status_code >= 400:
            log.warning("AI error %s: %s", r.status_code, r.text[:300])
            raise AIError("ai_error", "The AI service returned an error", 502)
        data = r.json()
        cand = (data.get("candidates") or [{}])[0]
        content, n = [], 0
        for p in (cand.get("content") or {}).get("parts", []):
            if "text" in p and not p.get("thought"):
                content.append({"type": "text", "text": p["text"]})
            elif "functionCall" in p:
                n += 1
                b = {"type": "tool_use", "id": f"gm_{n}", "name": p["functionCall"]["name"], "input": p["functionCall"].get("args") or {}}
                if p.get("thoughtSignature"):
                    b["_sig"] = p["thoughtSignature"]
                content.append(b)
        u = data.get("usageMetadata") or {}
        log.info("AI call model=%s in=%s out=%s", model, u.get("promptTokenCount"), u.get("candidatesTokenCount"))
        return {"content": content, "stop_reason": "tool_use" if n else "end_turn", "model": model}


_override = None


def set_llm(obj) -> None:
    """Tests install a fake with .create(**body) -> dict. Pass None to restore."""
    global _override
    _override = obj


def provider() -> str | None:
    want = settings.ai_provider.lower()
    if want == "gemini":
        return "gemini" if settings.gemini_api_key else None
    if want == "anthropic":
        return "anthropic" if settings.anthropic_api_key else None
    return "anthropic" if settings.anthropic_api_key else "gemini" if settings.gemini_api_key else None


def model_name() -> str | None:
    return {"anthropic": settings.ai_model, "gemini": settings.gemini_model}.get(provider() or "")


def get_llm():
    if _override is not None:
        return _override
    prov = provider()
    return AnthropicClient() if prov == "anthropic" else GeminiClient() if prov == "gemini" else None


def text_of(resp: dict) -> str:
    return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
