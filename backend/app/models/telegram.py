from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, false as sa_false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelegramLink(Base):
    """A user's Telegram chat. Created only by the user proving who they are with a one-time code from the web app."""
    __tablename__ = "telegram_links"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    lang: Mapped[str] = mapped_column(String(2), default="uz")
    notify: Mapped[bool] = mapped_column(Boolean, default=True)
    topics: Mapped[str] = mapped_column(String(120), default="orders,ship,pay,prod,edits,dels,digest", server_default="orders,ship,pay,prod,edits,dels,digest")   # which event messages this chat gets
    digest_hour: Mapped[int] = mapped_column(Integer, default=18, server_default="18")      # local hour of the daily summary
    digest_day: Mapped[int] = mapped_column(Integer, default=0, server_default="0")        # yyyymmdd of the last summary sent
    quiet: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa_false())  # night: messages arrive without sound
    linked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TelegramCode(Base):
    """One-time link code (only its hash is stored)."""
    __tablename__ = "telegram_codes"

    code_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class TelegramSent(Base):
    """Alerts already pushed, so the same signal is not sent again every half hour."""
    __tablename__ = "telegram_sent"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_telegram_sent_user_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    key: Mapped[str] = mapped_column(String(100))
    sent_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class TelegramCursor(Base):
    """Where the bot stopped reading: the last document id announced per kind (and the day of the last daily summary)."""
    __tablename__ = "telegram_cursors"

    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    last_id: Mapped[int] = mapped_column(BigInteger, default=0)


class TelegramDraft(Base):
    """A production list read from a chat message, waiting for the sender to confirm it. Single use: it is deleted when confirmed or cancelled."""
    __tablename__ = "telegram_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="draft", server_default="draft")   # draft: sender has not confirmed yet; pending: waiting for the manager
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
