"""Paid (premium) features. Everybody sees them, but a user can use one only after the main administrator switched it on:
it then works for DAYS days and for a limited number of uses (for the monthly meeting: two meetings = two different months)."""
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.db.session import get_db
from app.models import PremiumGrant, User

FEATURES = ("meeting",)            # monthly meeting: slides, AI remarks, PowerPoint
DAYS = 30                          # how long a switched-on feature works
USES = {"meeting": 2}              # how many uses it has in that time


def _now() -> datetime:
    return datetime.utcnow()


def _grant(user: User, feature: str) -> PremiumGrant | None:
    return next((g for g in user.grants if g.feature == feature), None)


def _used(g: PremiumGrant) -> list[str]:
    return [x for x in (g.used or "").split(",") if x]


def active_features(user: User) -> list[str]:
    if user.is_owner:
        return list(FEATURES)
    now = _now()
    return [f for f in FEATURES if (g := _grant(user, f)) and g.expires_at > now]


def info(user: User) -> list[dict]:
    out = []
    for g in user.grants:
        used = _used(g)
        out.append({"feature": g.feature, "active": g.expires_at > _now(), "expires_at": g.expires_at.isoformat(),
                    "uses_limit": g.uses_limit, "uses_left": max(0, g.uses_limit - len(used)), "used": used})
    return out


def switch_on(db: Session, user: User, feature: str) -> PremiumGrant:
    """Start (or restart) the period: DAYS days from now, a full set of uses."""
    g = _grant(user, feature)
    now = _now()
    if g is None:
        g = PremiumGrant(user_id=user.id, feature=feature)
        user.grants.append(g)
    g.granted_at, g.expires_at, g.uses_limit, g.used = now, now + timedelta(days=DAYS), USES.get(feature, 0), ""
    db.flush()
    return g


def switch_off(db: Session, user: User, feature: str) -> None:
    g = _grant(user, feature)
    if g is not None:
        user.grants.remove(g)
        db.flush()


def premium(feature: str):
    """Dependency factory: the signed-in user must have `feature` switched on (and not expired)."""
    def dep(user: User = Depends(current_user)) -> User:
        if feature not in user.features:
            raise HTTPException(403, {"code": "premium_required", "message": "This is a premium feature: ask the administrator to switch it on", "params": {"feature": feature}})
        return user
    return dep


def spend(db: Session, user: User, feature: str, key: str) -> None:
    """Use `feature` for `key` (a month). Going back to something already used is free; a new one costs one use. The main administrator has no limit."""
    if user.is_owner:
        return
    g = _grant(user, feature)
    if g is None or g.expires_at <= _now():
        raise HTTPException(403, {"code": "premium_required", "message": "This is a premium feature: ask the administrator to switch it on", "params": {"feature": feature}})
    used = _used(g)
    if key in used:
        return
    if len(used) >= g.uses_limit:
        raise HTTPException(403, {"code": "premium_limit", "message": "The limit of this premium feature is used up: ask the administrator", "params": {"feature": feature, "limit": g.uses_limit}})
    g.used = ",".join(used + [key])
    db.commit()
