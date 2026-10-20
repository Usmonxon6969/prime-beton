import asyncio
import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.deps import current_user
from app.core.events import hub, poke_token
from app.db.session import get_db
from app.models import User, UserSession

router = APIRouter(tags=["live"])
BEAT = 20          # seconds between keep-alive lines (nginx closes a silent connection after 120 s)
RECHECK = 3        # every third beat the sign-in is checked again


def _still_valid(maker, user_id: int, sid) -> bool:
    with maker() as s:
        u = s.get(User, user_id)
        ses = s.get(UserSession, sid) if sid else None
        return bool(u and u.is_active and ses and not ses.revoked and ses.user_id == user_id)


@router.get("/events")
async def events(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """One long-lived response per open page: `event: changed` whenever business data was committed."""
    uid, sid, maker = user.id, db.info.get("sid"), sessionmaker(bind=db.get_bind())
    db.close()                                    # no database connection is held while the stream is open
    sub = hub.join(uid)
    if sub is None:
        raise HTTPException(429, {"code": "too_many", "message": "Too many open pages", "params": {}})

    async def stream():
        beats = 0
        try:
            yield "retry: 5000\n: connected\n\n"
            while not await request.is_disconnected():
                try:
                    await asyncio.wait_for(sub.flag.wait(), BEAT)
                except asyncio.TimeoutError:
                    beats += 1
                    if beats % RECHECK == 0 and not await asyncio.to_thread(_still_valid, maker, uid, sid):
                        yield "event: bye\ndata: {}\n\n"
                        return
                    yield f": beat {datetime.utcnow().isoformat(timespec='seconds')}\n\n"
                    continue
                sub.flag.clear()
                yield "event: changed\ndata: {}\n\n"
        finally:
            hub.leave(sub)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no", "Connection": "keep-alive"})


@router.post("/live/poke", status_code=204)
def poke(x_poke: str = Header(default="")):
    """The Telegram bot runs as a separate process: after it records something it calls this so open pages reload at once.
    Carries no data; the key is derived from SECRET_KEY and is only known to the containers."""
    if not hmac.compare_digest(x_poke, poke_token(settings.secret_key)):
        raise HTTPException(403, {"code": "forbidden", "message": "Forbidden", "params": {}})
    hub.publish()
