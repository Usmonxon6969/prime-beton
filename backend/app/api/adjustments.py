"""Stock counts and write-offs."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import need
from app.core.errors import not_found
from app.db.session import get_db
from app.models import StockAdjust, User
from app.schemas.documents import AdjustIn, AdjustOut
from app.services import adjust

router = APIRouter(tags=["adjustments"])


def _get(db: Session, aid: int) -> StockAdjust:
    a = db.get(StockAdjust, aid)
    if a is None:
        raise not_found("stock document")
    return a


@router.get("/adjustments", response_model=list[AdjustOut])
def list_adjustments(kind: str | None = None, warehouse_id: int | None = None, status: str | None = None,
                     start: datetime | None = None, end: datetime | None = None,
                     db: Session = Depends(get_db), _: User = Depends(need("adj", 1))):
    q = db.query(StockAdjust)
    if kind:
        q = q.filter(StockAdjust.kind == kind)
    if warehouse_id:
        q = q.filter(StockAdjust.warehouse_id == warehouse_id)
    if status:
        q = q.filter(StockAdjust.status == status)
    if start:
        q = q.filter(StockAdjust.date >= start)
    if end:
        q = q.filter(StockAdjust.date <= end)
    return q.order_by(StockAdjust.date.desc(), StockAdjust.id.desc()).all()


@router.get("/adjustments/{aid}", response_model=AdjustOut)
def get_adjustment(aid: int, db: Session = Depends(get_db), _: User = Depends(need("adj", 1))):
    return _get(db, aid)


@router.post("/adjustments", response_model=AdjustOut, status_code=201)
def add_adjustment(body: AdjustIn, db: Session = Depends(get_db), _: User = Depends(need("adj", 2))):
    a = adjust.create(db, body)
    db.commit()
    return a


@router.put("/adjustments/{aid}", response_model=AdjustOut)
def edit_adjustment(aid: int, body: AdjustIn, db: Session = Depends(get_db), _: User = Depends(need("adj", 2))):
    a = adjust.update(db, _get(db, aid), body)
    db.commit()
    return a


@router.delete("/adjustments/{aid}", response_model=AdjustOut)
def remove_adjustment(aid: int, db: Session = Depends(get_db), _: User = Depends(need("adj", 2))):
    a = _get(db, aid)
    adjust.delete(db, a)
    db.commit()
    return a


@router.post("/adjustments/{aid}/restore", response_model=AdjustOut)
def restore_adjustment(aid: int, db: Session = Depends(get_db), _: User = Depends(need("adj", 2))):
    a = _get(db, aid)
    adjust.restore(db, a)
    db.commit()
    return a
