import time
from collections import defaultdict, deque
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai import assistant, draft, insights
from app.ai.client import AIError, get_llm, model_name, provider
from app.ai.tools import Ctx
from app.core.config import settings
from app.core.deps import current_user
from app.core.roles import ROLES, SECTIONS
from app.db.session import get_db
from app.models import User

router = APIRouter(prefix="/ai", tags=["ai"])
_hits: dict[int, deque] = defaultdict(deque)


def _levels(u: User) -> dict:
    return {s: ROLES.get(u.role, {}).get(s, 0) for s in SECTIONS}


def _limit(u: User) -> None:
    q, now = _hits[u.id], time.time()
    while q and now - q[0] > 600:
        q.popleft()
    if len(q) >= settings.ai_rate_per_10min:
        raise HTTPException(429, {"code": "too_many_attempts", "message": "Too many AI requests, wait a few minutes", "params": {"seconds": 60}})
    q.append(now)


def _fail(e: AIError):
    raise HTTPException(e.status, {"code": e.code, "message": e.message, "params": {}})


class ChatIn(BaseModel):
    messages: list[dict] = Field(min_length=1, max_length=40)
    mode: str = Field("assistant", pattern="^(assistant|finance|analyst)$")
    lang: str = Field("en", pattern="^(uz|ru|en)$")


class DraftIn(BaseModel):
    text: str = ""
    image: dict | None = None
    lang: str = Field("en", pattern="^(uz|ru|en)$")


@router.get("/status")
def status(_: User = Depends(current_user)):
    on = get_llm() is not None
    return {"enabled": on, "model": model_name() if on else None, "provider": provider() if on else None}


@router.get("/insights")
def get_insights(lang: str = Query("en", pattern="^(uz|ru|en)$"), db: Session = Depends(get_db), u: User = Depends(current_user)):
    return insights.collect(db, _levels(u), lang)


@router.get("/brief")
def get_brief(mode: str = Query("daily", pattern="^(daily|finance)$"), lang: str = Query("en", pattern="^(uz|ru|en)$"),
              db: Session = Depends(get_db), u: User = Depends(current_user)):
    _limit(u)
    try:
        return assistant.brief(Ctx(db, _levels(u), lang), u.role, mode)
    except AIError as e:
        _fail(e)


@router.post("/chat")
def chat(body: ChatIn, db: Session = Depends(get_db), u: User = Depends(current_user)):
    _limit(u)
    try:
        return assistant.chat(Ctx(db, _levels(u), body.lang), u.role, body.messages, body.mode)
    except AIError as e:
        _fail(e)


@router.post("/draft")
def make_draft(body: DraftIn, db: Session = Depends(get_db), u: User = Depends(current_user)):
    _limit(u)
    try:
        return draft.propose(Ctx(db, _levels(u), body.lang), body.text, body.image)
    except AIError as e:
        _fail(e)


class CommitIn(BaseModel):
    kind: str
    date: str | None = None
    party_id: int | None = None
    new_party: str | None = None
    warehouse_id: int | None = None
    comment: str = ""
    rows: list[dict] = Field(min_length=1, max_length=200)
    lang: str = Field("en", pattern="^(uz|ru|en)$")


@router.post("/draft/commit", status_code=201)
def commit_draft(body: CommitIn, db: Session = Depends(get_db), u: User = Depends(current_user)):
    """Create the reviewed document. Not an AI call (no model involved), so no rate limit; role checks as on the normal screens."""
    try:
        return draft.commit(Ctx(db, _levels(u), body.lang), body.model_dump())
    except AIError as e:
        _fail(e)
