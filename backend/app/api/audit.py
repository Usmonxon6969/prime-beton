from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import current_user
from app.db.session import get_db
from app.models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["audit"])


def owner_only(user: User = Depends(current_user)) -> User:
    """The change journal belongs to the main administrator alone."""
    if not user.is_owner:
        raise HTTPException(403, {"code": "owner_only", "message": "Only the main administrator sees the change journal", "params": {}})
    return user


@router.get("")
def journal(entity: str | None = None, entity_id: int | None = None, username: str | None = None,
            action: str | None = None, start: datetime | None = None, end: datetime | None = None,
            limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0),
            db: Session = Depends(get_db), _: User = Depends(owner_only)):
    q = db.query(AuditLog)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if username:
        q = q.filter(AuditLog.username == username)
    if action:
        q = q.filter(AuditLog.action == action)
    if start:
        q = q.filter(AuditLog.at >= start)
    if end:
        q = q.filter(AuditLog.at <= end)
    total = q.count()
    rows = q.order_by(AuditLog.at.desc(), AuditLog.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "rows": [{"id": r.id, "at": r.at.isoformat() if r.at else None, "user": r.username,
                                      "action": r.action, "entity": r.entity, "entity_id": r.entity_id,
                                      "label": r.label, "changes": r.changes} for r in rows]}
