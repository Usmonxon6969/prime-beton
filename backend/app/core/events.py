"""Live updates (Server-Sent Events).

Whenever a request commits a change to business data, every open page is told "something changed" and reloads its lists
through the normal, permission-checked API. The message carries no data, so nobody can see more than their role allows.

The hub lives in the memory of one process, which is how the API runs (a single uvicorn worker). If the API is ever run
with several workers, move `publish` onto a shared channel (for example PostgreSQL LISTEN/NOTIFY).
"""
import asyncio
import hashlib
import threading

from sqlalchemy import event
from sqlalchemy.orm import Session

QUIET = {"audit_log", "user_sessions", "telegram_codes", "telegram_sent", "telegram_drafts", "telegram_cursors", "counters"}   # changes here are not news
MAX_TOTAL = 200
MAX_PER_USER = 10


class Sub:
    def __init__(self, user_id: int, loop: asyncio.AbstractEventLoop):
        self.user_id, self.loop, self.flag = user_id, loop, asyncio.Event()

    def poke(self) -> None:
        try:
            self.loop.call_soon_threadsafe(self.flag.set)
        except RuntimeError:           # the loop is already closed
            pass


class Hub:
    def __init__(self) -> None:
        self._subs: set[Sub] = set()
        self._lock = threading.Lock()

    def join(self, user_id: int) -> Sub | None:
        with self._lock:
            if len(self._subs) >= MAX_TOTAL or sum(1 for s in self._subs if s.user_id == user_id) >= MAX_PER_USER:
                return None
            sub = Sub(user_id, asyncio.get_running_loop())
            self._subs.add(sub)
            return sub

    def leave(self, sub: Sub) -> None:
        with self._lock:
            self._subs.discard(sub)

    def publish(self) -> None:
        with self._lock:
            subs = list(self._subs)
        for s in subs:
            s.poke()

    def count(self) -> int:
        with self._lock:
            return len(self._subs)


hub = Hub()


def _after_flush(session: Session, ctx) -> None:
    for o in (*session.new, *session.dirty, *session.deleted):
        t = getattr(getattr(o, "__table__", None), "name", None)
        if t and t not in QUIET:
            session.info["_live"] = True
            return


def _after_commit(session: Session) -> None:
    if session.info.pop("_live", False):
        hub.publish()


def _after_rollback(session: Session, previous_transaction) -> None:
    session.info.pop("_live", None)


def install() -> None:
    event.listen(Session, "after_flush", _after_flush)
    event.listen(Session, "after_commit", _after_commit)
    event.listen(Session, "after_soft_rollback", _after_rollback)


def poke_token(secret: str) -> str:
    """The key the bot process shows to /live/poke (derived from SECRET_KEY, so nothing new has to be configured)."""
    return hashlib.sha256((secret + "|live-poke").encode()).hexdigest()
