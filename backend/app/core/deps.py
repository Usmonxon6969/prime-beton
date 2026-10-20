from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import level
from app.core.security import decode_token
from app.db.session import get_db
from app.models import User, UserSession

bearer = HTTPBearer(auto_error=False)


def _unauth():
    return HTTPException(401, {"code": "unauthorized", "message": "Sign in first", "params": {}})


def current_user(request: Request, cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    tok = decode_token(cred.credentials) if cred else None
    user = db.get(User, tok[0]) if tok else None
    if user is None or not user.is_active:
        raise _unauth()
    sess = db.get(UserSession, tok[1]) if tok[1] else None
    if sess is None or sess.revoked or sess.user_id != user.id:      # signed out, revoked by an administrator, or an old token
        raise _unauth()
    now = datetime.utcnow()
    if now - sess.last_seen > timedelta(minutes=1):                   # touch at most once a minute
        sess.last_seen = now
        db.commit()
    must = {r.strip() for r in settings.require_2fa_roles.split(",") if r.strip()}
    if user.role in must and not user.totp_enabled and not request.url.path.startswith("/api/auth/"):
        raise HTTPException(403, {"code": "2fa_required", "message": "Set up two-factor sign-in first", "params": {}})
    db.info["user"] = {"id": user.id, "username": user.username}      # read by the audit hook
    db.info["sid"] = sess.id
    return user


def need(section: str, lvl: int = 1):
    """Dependency factory: the signed-in user must hold at least `lvl` in `section`."""
    def dep(user: User = Depends(current_user)) -> User:
        if level(user.role, section) < lvl:
            raise HTTPException(403, {"code": "forbidden", "message": "Your role cannot do this", "params": {"section": section}})
        return user
    return dep


def need_any(*sections: str):
    def dep(user: User = Depends(current_user)) -> User:
        if not any(level(user.role, s) for s in sections):
            raise HTTPException(403, {"code": "forbidden", "message": "Your role cannot do this", "params": {}})
        return user
    return dep
