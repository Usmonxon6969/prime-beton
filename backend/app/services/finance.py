"""Bank and cash: balances, money documents, the no-negative-cash rule."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import bad, conflict, not_found
from app.models import Account, FinDoc
from app.services.common import D, ensure_not_deleted, get_customer, get_supplier
from app.services.numbering import next_number

ARTICLES = {"in": {"cust", "oin"}, "out": {"sup", "sal", "tax", "fee", "oout"}, "tr": {"tr"}}


def balances(db: Session) -> dict[int, Decimal]:
    """Opening balance plus posted money in, minus out, minus transfers out, plus transfers in."""
    bal = {a.id: a.opening_balance for a in db.query(Account).all()}

    def add(col, sign, *conds):
        q = select(col, func.sum(FinDoc.amount)).where(FinDoc.status == "posted", *conds).group_by(col)
        for aid, s in db.execute(q):
            if aid in bal and s:
                bal[aid] += sign * Decimal(s)

    add(FinDoc.account_id, 1, FinDoc.kind == "in")
    add(FinDoc.account_id, -1, FinDoc.kind == "out")
    add(FinDoc.account_id, -1, FinDoc.kind == "tr")
    add(FinDoc.to_account_id, 1, FinDoc.kind == "tr")
    return bal


def advances(db: Session, order_ids: list[int]) -> dict[int, Decimal]:
    """Money received against orders (advances), by order."""
    out: dict[int, Decimal] = {}
    for k in range(0, len(order_ids), 500):
        q = (select(FinDoc.order_id, func.sum(FinDoc.amount))
             .where(FinDoc.order_id.in_(order_ids[k:k + 500]), FinDoc.status == "posted", FinDoc.kind == "in").group_by(FinDoc.order_id))
        out.update({oid: Decimal(v or 0) for oid, v in db.execute(q)})
    return out


def ensure_cash_ok(db: Session, before: dict | None = None) -> None:
    """A cash desk never goes below zero. A bank account may not be pushed (further) below zero by the document being saved:
    `before` is the balances before the change, so an account that is already negative does not block unrelated documents or
    incoming money. BANK_ALLOW_NEGATIVE=true in .env switches the bank rule off (overdraft)."""
    db.flush()
    bal = balances(db)
    for a in db.query(Account).filter(Account.kind == "cash").all():
        if bal[a.id] < 0:
            raise conflict("cash_negative", f"The cash desk {a.name_en} cannot go below zero",
                           account={"uz": a.name_uz, "ru": a.name_ru, "en": a.name_en}, balance=float(bal[a.id]))
    if before is None or settings.bank_allow_negative:
        return
    for a in db.query(Account).filter(Account.kind == "bank").all():
        if bal[a.id] < 0 and bal[a.id] < before.get(a.id, Decimal(0)):
            raise conflict("bank_negative", f"Not enough money on the bank account {a.name_en}",
                           account={"uz": a.name_uz, "ru": a.name_ru, "en": a.name_en}, available=float(max(before.get(a.id, Decimal(0)), 0)))


def _before(db: Session) -> dict:
    db.flush()
    return balances(db)


def _account(db: Session, aid: int | None, required=True) -> Account | None:
    if aid is None:
        if required:
            raise bad("account_required", "Choose an account")
        return None
    a = db.get(Account, aid)
    if a is None or not a.is_active:
        raise not_found("account")
    return a


def prefix_for(kind: str, acc: Account) -> str:
    if acc.kind == "bank":
        return "BP" if kind == "in" else "BS"
    return "PKO" if kind == "in" else "RKO"


def _validate(db: Session, data):
    acc = _account(db, data.account_id)
    if data.article not in ARTICLES[data.kind]:
        raise bad("bad_article", "This article does not fit the document kind", article=data.article, kind=data.kind)
    if data.kind == "tr":
        to = _account(db, data.to_account_id)
        if to.id == acc.id:
            raise bad("same_account", "Choose two different accounts")
    elif data.to_account_id is not None:
        raise bad("to_account_only_for_transfer", "Only a transfer has a destination account")
    if data.article == "cust":
        get_customer(db, data.customer_id) if data.customer_id else _need("customer")
    if getattr(data, "worker_id", None):
        from app.models import Worker
        w = db.get(Worker, data.worker_id)
        if data.article != "sal" or w is None or not w.is_active:
            raise bad("worker_mismatch", "Choose an active worker for a salary payment")
    if getattr(data, "order_id", None):
        from app.models import Order
        o = db.get(Order, data.order_id)
        if data.article != "cust" or o is None or o.status == "deleted" or o.customer_id != data.customer_id:
            raise bad("order_mismatch", "The order does not belong to this customer")
    if data.article == "sup":
        get_supplier(db, data.supplier_id) if data.supplier_id else _need("supplier")
    return acc


def _need(what: str):
    raise bad(f"{what}_required", f"Choose a {what}")


def _fill(f: FinDoc, data) -> None:
    f.date, f.kind, f.account_id, f.to_account_id = data.date, data.kind, data.account_id, data.to_account_id
    f.article = data.article
    f.customer_id = data.customer_id if data.article == "cust" else None
    f.supplier_id = data.supplier_id if data.article == "sup" else None
    f.order_id = getattr(data, "order_id", None) if data.article == "cust" else None
    f.worker_id = getattr(data, "worker_id", None) if data.article == "sal" else None
    f.party, f.amount, f.comment = data.party, D(data.amount), data.comment


def create_fin(db: Session, data) -> FinDoc:
    acc = _validate(db, data)
    before = _before(db)
    f = FinDoc(number=next_number(db, prefix_for(data.kind, acc)), status="posted")
    _fill(f, data)
    db.add(f)
    ensure_cash_ok(db, before)
    return f


def update_fin(db: Session, f: FinDoc, data) -> FinDoc:
    ensure_not_deleted(f)
    _validate(db, data)
    before = _before(db)
    _fill(f, data)
    ensure_cash_ok(db, before)
    return f


def delete_fin(db: Session, f: FinDoc) -> None:
    ensure_not_deleted(f)
    before = _before(db)
    f.status = "deleted"
    ensure_cash_ok(db, before)


def restore_fin(db: Session, f: FinDoc) -> None:
    before = _before(db)
    f.status = "posted"
    ensure_cash_ok(db, before)
