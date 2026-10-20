"""Linking a user's Telegram chat (the bot itself runs as a separate process: python -m app.telegram_bot)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import current_user
from app.core.errors import conflict
from app.db.session import get_db
from app.models import TelegramLink, User
from app.services import telegram

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _state(db: Session, u: User) -> dict:
    lk = db.get(TelegramLink, u.id)
    return {"enabled": bool(settings.telegram_bot_token), "username": settings.telegram_bot_username,
            "linked": lk is not None, "notify": bool(lk and lk.notify), "lang": lk.lang if lk else None}


@router.get("")
def status(db: Session = Depends(get_db), u: User = Depends(current_user)):
    return _state(db, u)


@router.post("/code")
def make_code(db: Session = Depends(get_db), u: User = Depends(current_user)):
    if not settings.telegram_bot_token:
        raise conflict("telegram_off", "The Telegram bot is not set up on the server")
    code = telegram.new_code(db, u)
    db.commit()
    return {"code": code, "expires_in": int(telegram.CODE_TTL.total_seconds()), "username": settings.telegram_bot_username}


@router.delete("")
def disconnect(db: Session = Depends(get_db), u: User = Depends(current_user)):
    telegram.unlink(db, u.id)
    db.commit()
    return _state(db, u)
