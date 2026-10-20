from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import current_user, need, need_any
from app.core.errors import not_found
from app.core.roles import level
from app.db.session import get_db
from app.models import Account, FinDoc, User
from app.schemas.finance import AccountIn, AccountOut, AccountUpdate, FinIn, FinOut
from app.services import catalog as rules
from app.services import finance as fin
from app.services.common import D

router = APIRouter(tags=["finance"])


def _acc_out(db: Session, accs: list[Account]) -> list[AccountOut]:
    bal = fin.balances(db)
    return [AccountOut(id=a.id, kind=a.kind, name_uz=a.name_uz, name_ru=a.name_ru, name_en=a.name_en, number=a.number,
                       opening_balance=float(a.opening_balance), balance=float(bal[a.id])) for a in accs]


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(kind: str | None = Query(None, pattern="^(bank|cash)$"), db: Session = Depends(get_db),
                  user: User = Depends(need_any("bank", "cash", "set", "dash"))):
    q = db.query(Account).filter(Account.is_active)
    if kind:
        q = q.filter(Account.kind == kind)
    accs = [a for a in q.order_by(Account.id) if level(user.role, a.kind) or level(user.role, "set")]
    return _acc_out(db, accs)


@router.post("/accounts", response_model=AccountOut, status_code=201)
def add_account(body: AccountIn, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    a = Account(kind=body.kind, name_uz=body.name_uz, name_ru=body.name_ru, name_en=body.name_en, number=body.number,
                opening_balance=D(body.opening_balance))
    db.add(a)
    fin.ensure_cash_ok(db)
    db.commit()
    return _acc_out(db, [a])[0]


@router.patch("/accounts/{aid}", response_model=AccountOut)
def edit_account(aid: int, body: AccountUpdate, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    a = db.get(Account, aid)
    if not a or not a.is_active:
        raise not_found("account")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(a, k, D(v) if k == "opening_balance" else v)
    fin.ensure_cash_ok(db)   # an opening balance edit must not push a cash desk below zero
    db.commit()
    return _acc_out(db, [a])[0]


@router.delete("/accounts/{aid}", status_code=204)
def remove_account(aid: int, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    a = db.get(Account, aid)
    if not a or not a.is_active:
        raise not_found("account")
    rules.delete_account(db, a)
    db.commit()


def _section_of(db: Session, f: FinDoc) -> str:
    a = db.get(Account, f.account_id)
    return a.kind


def _guard(user: User, section: str, lvl: int) -> None:
    need(section, lvl)(user)


@router.get("/finance", response_model=list[FinOut])
def list_fin(kind: str = Query(..., pattern="^(bank|cash)$"), start: datetime | None = None, end: datetime | None = None,
             status: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    _guard(user, kind, 1)
    ids = [a.id for a in db.query(Account).filter(Account.kind == kind)]
    q = db.query(FinDoc).filter(FinDoc.account_id.in_(ids) | FinDoc.to_account_id.in_(ids))
    if start:
        q = q.filter(FinDoc.date >= start)
    if end:
        q = q.filter(FinDoc.date <= end)
    if status:
        q = q.filter(FinDoc.status == status)
    return q.order_by(FinDoc.date.desc(), FinDoc.id.desc()).all()


def _doc(db: Session, fid: int) -> FinDoc:
    f = db.get(FinDoc, fid)
    if not f:
        raise not_found("money document")
    return f


@router.post("/finance", response_model=FinOut, status_code=201)
def add_fin(body: FinIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    acc = db.get(Account, body.account_id)
    if not acc:
        raise not_found("account")
    _guard(user, acc.kind, 2)
    f = fin.create_fin(db, body)
    db.commit()
    return f


@router.put("/finance/{fid}", response_model=FinOut)
def edit_fin(fid: int, body: FinIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    f = _doc(db, fid)
    _guard(user, _section_of(db, f), 2)
    acc = db.get(Account, body.account_id)
    if acc:
        _guard(user, acc.kind, 2)
    fin.update_fin(db, f, body)
    db.commit()
    return f


@router.delete("/finance/{fid}", response_model=FinOut)
def remove_fin(fid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    f = _doc(db, fid)
    _guard(user, _section_of(db, f), 2)
    fin.delete_fin(db, f)
    db.commit()
    return f


@router.post("/finance/{fid}/restore", response_model=FinOut)
def restore_fin(fid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    f = _doc(db, fid)
    _guard(user, _section_of(db, f), 2)
    fin.restore_fin(db, f)
    db.commit()
    return f
