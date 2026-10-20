"""Workers, piece rates, bonuses/deductions and the pay statement."""
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import need, need_any
from app.core.errors import bad, conflict, not_found
from app.db.session import get_db
from app.models import FinDoc, Item, PayAdjust, ProductionCrew, ProductRate, User, Worker
from app.schemas.payroll import AdjIn, AdjOut, RateOut, RatesPut, WorkerIn, WorkerOut
from app.services import payroll

router = APIRouter(tags=["payroll"])


def _worker(db: Session, wid: int) -> Worker:
    w = db.get(Worker, wid)
    if w is None:
        raise not_found("worker")
    return w


def _unique(db: Session, name: str, wid: int | None = None) -> None:
    q = db.query(Worker).filter(Worker.name == name.strip())
    if wid:
        q = q.filter(Worker.id != wid)
    if q.first():
        raise conflict("duplicate", "A worker with this name already exists")


@router.get("/workers", response_model=list[WorkerOut])
def list_workers(db: Session = Depends(get_db), _: User = Depends(need("pay", 1))):
    return db.query(Worker).order_by(Worker.is_active.desc(), Worker.name).all()


@router.get("/crew-workers", response_model=list[WorkerOut])
def crew_workers(db: Session = Depends(get_db), _: User = Depends(need_any("prod", "pay"))):
    """Active workers, for choosing a crew or a salary payee (no pay data)."""
    return db.query(Worker).filter(Worker.is_active).order_by(Worker.name).all()


@router.post("/workers", response_model=WorkerOut, status_code=201)
def add_worker(body: WorkerIn, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    _unique(db, body.name)
    w = Worker(name=body.name.strip(), position=body.position, phone=body.phone, is_active=body.is_active)
    db.add(w)
    db.commit()
    return w


@router.put("/workers/{wid}", response_model=WorkerOut)
def edit_worker(wid: int, body: WorkerIn, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    w = _worker(db, wid)
    _unique(db, body.name, wid)
    w.name, w.position, w.phone, w.is_active = body.name.strip(), body.position, body.phone, body.is_active
    db.commit()
    return w


@router.delete("/workers/{wid}", status_code=204)
def remove_worker(wid: int, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    """A worker with history is archived, never erased."""
    w = _worker(db, wid)
    used = (db.query(ProductionCrew).filter_by(worker_id=wid).first() or db.query(PayAdjust).filter_by(worker_id=wid).first()
            or db.query(FinDoc).filter_by(worker_id=wid).first())
    if used:
        w.is_active = False
    else:
        db.delete(w)
    db.commit()


@router.get("/rates", response_model=list[RateOut])
def list_rates(db: Session = Depends(get_db), _: User = Depends(need("pay", 1))):
    return db.query(ProductRate).all()


@router.put("/rates", response_model=list[RateOut])
def put_rates(body: RatesPut, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    ids = [r.item_id for r in body.rates]
    found = {i.id for i in db.query(Item).filter(Item.id.in_(ids), Item.kind == "product")}
    if set(ids) - found:
        raise bad("invalid_item", "Rates can be set for products only")
    cur = {r.item_id: r for r in db.query(ProductRate)}
    for r in body.rates:
        if r.item_id in cur:
            cur[r.item_id].rate = Decimal(str(r.rate))
        else:
            db.add(ProductRate(item_id=r.item_id, rate=Decimal(str(r.rate))))
    db.commit()
    return db.query(ProductRate).all()


@router.get("/pay-adjusts", response_model=list[AdjOut])
def list_adjusts(worker_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(need("pay", 1))):
    q = db.query(PayAdjust)
    if worker_id:
        q = q.filter(PayAdjust.worker_id == worker_id)
    return q.order_by(PayAdjust.date.desc(), PayAdjust.id.desc()).all()


@router.post("/pay-adjusts", response_model=AdjOut, status_code=201)
def add_adjust(body: AdjIn, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    _worker(db, body.worker_id)
    if not body.amount:
        raise bad("amount_required", "Enter an amount")
    a = PayAdjust(worker_id=body.worker_id, date=body.date, amount=Decimal(str(body.amount)), note=body.note, status="posted")
    db.add(a)
    db.commit()
    return a


@router.delete("/pay-adjusts/{aid}", response_model=AdjOut)
def remove_adjust(aid: int, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    a = db.get(PayAdjust, aid)
    if a is None:
        raise not_found("entry")
    a.status = "deleted"
    db.commit()
    return a


@router.post("/pay-adjusts/{aid}/restore", response_model=AdjOut)
def restore_adjust(aid: int, db: Session = Depends(get_db), _: User = Depends(need("pay", 2))):
    a = db.get(PayAdjust, aid)
    if a is None:
        raise not_found("entry")
    a.status = "posted"
    db.commit()
    return a


@router.get("/payroll")
def statement(start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(need("pay", 1))):
    return payroll.statement(db, start, end)


@router.get("/payroll/worker/{wid}")
def worker_act(wid: int, start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(need("pay", 1))):
    """Reconciliation act (akt sverka) of one worker for a period; no dates = all time."""
    res = payroll.worker_statement(db, wid, start, end)
    if res is None:
        raise not_found("worker")
    return res
