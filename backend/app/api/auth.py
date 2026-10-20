import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core import passwords, throttle, totp
from app.core.audit import record
from app.core.config import settings
from app.core.deps import bearer, current_user, need
from app.core.roles import HOME, ROLES, SECTIONS
from app.core.security import create_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User, UserSession
from app.schemas.auth import (LoginIn, MeOut, PasswordIn, SessionOut, TokenOut, TotpDisableIn, TotpEnableIn, TotpSetupOut,
                              UserIn, UserOut, UserPatch)

router = APIRouter(prefix="/auth", tags=["auth"])


def _me(u: User) -> MeOut:
    lv = {s: ROLES.get(u.role, {}).get(s, 0) for s in SECTIONS}
    must = {r.strip() for r in settings.require_2fa_roles.split(",") if r.strip()}
    return MeOut(id=u.id, username=u.username, full_name=u.full_name, role=u.role, is_active=u.is_active,
                 home=HOME.get(u.role, "dash"), levels=lv, totp_enabled=bool(u.totp_enabled),
                 must_setup_2fa=u.role in must and not u.totp_enabled, features=u.features, premium=u.premium, owner=bool(u.is_owner))


def _err(status: int, code: str, message: str, **params):
    return HTTPException(status, {"code": code, "message": message, "params": params})


def _revoke_others(db: Session, uid: int, keep: str | None) -> int:
    n = 0
    for x in db.query(UserSession).filter(UserSession.user_id == uid, UserSession.revoked.is_(False)):
        if x.id != keep:
            x.revoked = True
            n += 1
    return n


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    name = body.username.strip().lower()
    key = name + "|" + (request.client.host if request.client else "")
    wait = throttle.blocked(key)
    if wait:
        raise _err(429, "too_many_attempts", "Too many attempts, wait and try again", seconds=wait)
    u = db.query(User).filter(User.username == name).first()
    if not u or not u.is_active or not verify_password(body.password, u.password_hash):
        throttle.failed(key)
        raise _err(401, "bad_login", "Wrong username or password")
    if u.totp_enabled:
        if not body.otp:
            raise _err(401, "otp_required", "Enter the 6-digit code from your authenticator app")      # no failure counted: the password was right
        secret = totp.unseal(u.totp_secret or "")
        step = totp.verify(secret, body.otp) if secret else None
        if step is None or step <= (u.totp_last_step or 0):
            throttle.failed(key)
            raise _err(401, "bad_otp", "The code is wrong or already used")
        u.totp_last_step = step
    throttle.ok(key)
    sid = uuid.uuid4().hex
    db.add(UserSession(id=sid, user_id=u.id, ip=(request.client.host if request.client else "")[:64],
                       agent=(request.headers.get("user-agent") or "")[:200]))
    record(db, u, "login", "users", u.id, u.username)
    db.commit()
    return TokenOut(access_token=create_token(u.id, sid), user=_me(u))


@router.post("/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_db), u: User = Depends(current_user)):
    sess = db.get(UserSession, db.info.get("sid", ""))
    if sess:
        sess.revoked = True
        db.commit()


@router.get("/sessions", response_model=list[SessionOut])
def my_sessions(db: Session = Depends(get_db), u: User = Depends(current_user)):
    cur = db.info.get("sid")
    rows = db.query(UserSession).filter(UserSession.user_id == u.id, UserSession.revoked.is_(False)).order_by(UserSession.last_seen.desc()).all()
    return [SessionOut(id=x.id, created_at=x.created_at.isoformat(), last_seen=x.last_seen.isoformat(), ip=x.ip, agent=x.agent,
                       current=x.id == cur) for x in rows]


@router.delete("/sessions/{sid}", status_code=204)
def revoke_session(sid: str, db: Session = Depends(get_db), u: User = Depends(current_user)):
    x = db.get(UserSession, sid)
    if not x or x.user_id != u.id:
        raise _err(404, "not_found", "Session not found")
    x.revoked = True
    db.commit()


@router.post("/sessions/revoke-others")
def revoke_other_sessions(db: Session = Depends(get_db), u: User = Depends(current_user)):
    n = _revoke_others(db, u.id, db.info.get("sid"))
    db.commit()
    return {"revoked": n}


@router.post("/2fa/setup", response_model=TotpSetupOut)
def totp_setup(db: Session = Depends(get_db), u: User = Depends(current_user)):
    if u.totp_enabled:
        raise _err(409, "2fa_on", "Two-factor sign-in is already on")
    secret = totp.new_secret()
    u.totp_secret = totp.seal(secret)
    db.commit()
    link = totp.uri(secret, u.username)
    return TotpSetupOut(secret=secret, uri=link, qr_svg=totp.qr_svg(link))


@router.post("/2fa/enable", status_code=204)
def totp_enable(body: TotpEnableIn, db: Session = Depends(get_db), u: User = Depends(current_user)):
    secret = totp.unseal(u.totp_secret or "") if u.totp_secret else None
    if u.totp_enabled or not secret:
        raise _err(409, "2fa_state", "Start the setup first")
    step = totp.verify(secret, body.code)
    if step is None:
        raise _err(422, "bad_otp", "The code is wrong or already used")
    u.totp_enabled, u.totp_last_step = True, step
    record(db, u, "update", "users", u.id, u.username, {"2fa": "on"})
    db.commit()


@router.post("/2fa/disable", status_code=204)
def totp_disable(body: TotpDisableIn, db: Session = Depends(get_db), u: User = Depends(current_user)):
    must = {r.strip() for r in settings.require_2fa_roles.split(",") if r.strip()}
    if u.role in must:
        raise _err(409, "2fa_mandatory", "Your role must keep two-factor sign-in on")
    if not verify_password(body.password, u.password_hash):
        raise _err(422, "bad_password", "The current password is wrong")
    secret = totp.unseal(u.totp_secret or "") if u.totp_secret else None
    step = totp.verify(secret, body.code) if secret else None
    if step is None:
        raise _err(422, "bad_otp", "The code is wrong or already used")
    u.totp_enabled, u.totp_secret, u.totp_last_step = False, None, 0
    record(db, u, "update", "users", u.id, u.username, {"2fa": "off"})
    db.commit()


@router.get("/me", response_model=MeOut)
def me(u: User = Depends(current_user)):
    return _me(u)


@router.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db), me: User = Depends(need("set", 1))):
    q = db.query(User)
    if not me.is_owner:
        q = q.filter(User.is_owner.is_(False))                  # the main administrator is invisible to everybody else
    return q.order_by(User.id).all()


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserIn, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    if body.role not in ROLES:
        raise HTTPException(422, {"code": "bad_role", "message": "Unknown role", "params": {}})
    name = body.username.strip().lower()
    passwords.check(body.password, name)
    if db.query(User).filter(User.username == name).first():
        raise HTTPException(409, {"code": "duplicate", "message": "This username is taken", "params": {}})
    u = User(username=name, password_hash=hash_password(body.password), full_name=body.full_name, role=body.role)
    db.add(u)
    db.commit()
    return u


def _admins_left(db: Session, skip: int) -> int:
    return db.query(User).filter(User.role == "admin", User.is_active, User.id != skip).count()


@router.patch("/users/{uid}", response_model=UserOut)
def edit_user(uid: int, body: UserPatch, db: Session = Depends(get_db), me: User = Depends(need("set", 2))):
    u = db.get(User, uid)
    if not u or (u.is_owner and not me.is_owner):                # to anybody else the main administrator does not exist
        raise HTTPException(404, {"code": "not_found", "message": "User not found", "params": {}})
    if u.is_owner and (body.is_active is False or (body.role is not None and body.role != "admin")):
        raise HTTPException(409, {"code": "last_admin", "message": "At least one active administrator must remain", "params": {}})
    if body.role is not None and body.role not in ROLES:
        raise HTTPException(422, {"code": "bad_role", "message": "Unknown role", "params": {}})
    demoting = (body.role is not None and body.role != "admin") or body.is_active is False
    if u.role == "admin" and u.is_active and demoting and _admins_left(db, u.id) == 0:
        raise HTTPException(409, {"code": "last_admin", "message": "At least one active administrator must remain", "params": {}})
    if u.id == me.id and body.is_active is False:
        raise HTTPException(409, {"code": "self_disable", "message": "You cannot deactivate yourself", "params": {}})
    if body.premium is not None:
        from app.core import premium
        if not me.is_owner:
            raise HTTPException(403, {"code": "owner_only", "message": "Only the main administrator switches premium features on", "params": {}})
        feat = body.premium.get("feature")
        if feat not in premium.FEATURES:
            raise HTTPException(422, {"code": "bad_feature", "message": "Unknown premium feature", "params": {}})
        if body.premium.get("on"):
            g = premium.switch_on(db, u, feat)
            record(db, me, "update", "users", u.id, u.username, {"premium": f"{feat} on until {g.expires_at:%Y-%m-%d}, {g.uses_limit} uses"})
        else:
            premium.switch_off(db, u, feat)
            record(db, me, "update", "users", u.id, u.username, {"premium": f"{feat} off"})
    if body.full_name is not None:
        u.full_name = body.full_name.strip() or u.full_name
    if body.role is not None:
        u.role = body.role
    if body.is_active is not None:
        u.is_active = body.is_active
    if body.reset_2fa:
        u.totp_enabled, u.totp_secret, u.totp_last_step = False, None, 0
        record(db, me, "update", "users", u.id, u.username, {"2fa": "reset"})
    if body.password:
        passwords.check(body.password, u.username)
        u.password_hash = hash_password(body.password)
        _revoke_others(db, u.id, None)                      # a reset password signs the person out everywhere
        record(db, me, "update", "users", u.id, u.username, {"password": "reset"})
    if body.is_active is False or body.role is not None:
        _revoke_others(db, u.id, None) if body.is_active is False else None
    db.commit()
    return u


@router.post("/password", status_code=204)
def change_password(body: PasswordIn, db: Session = Depends(get_db), u: User = Depends(current_user)):
    if not verify_password(body.old_password, u.password_hash):
        raise HTTPException(422, {"code": "bad_password", "message": "The current password is wrong", "params": {}})
    passwords.check(body.new_password, u.username)
    u.password_hash = hash_password(body.new_password)
    _revoke_others(db, u.id, db.info.get("sid"))             # other browsers are signed out; this one stays
    record(db, u, "update", "users", u.id, u.username, {"password": "changed"})
    db.commit()
