"""Stock counts (inventory) and write-offs: documents that change stock without a purchase, production or sale."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import bad
from app.models import StockAdjust, StockAdjustRow
from app.services import stock
from app.services.common import D, ensure_not_deleted, get_items, get_warehouse, need_rows
from app.services.numbering import next_number

TYPE = "adjust"


def _validate(db: Session, data) -> None:
    need_rows(data.rows)
    get_warehouse(db, data.warehouse_id)
    get_items(db, [r.item_id for r in data.rows])
    ids = [r.item_id for r in data.rows]
    if data.kind == "count" and len(set(ids)) != len(ids):
        raise bad("duplicate_item", "Each item can be counted only once")
    if data.kind == "writeoff":
        if not data.reason:
            raise bad("reason_required", "Choose the reason for the write-off")
        if any(r.qty <= 0 for r in data.rows):
            raise bad("qty_required", "Enter a quantity above zero")


def _rows(db: Session, data) -> list[StockAdjustRow]:
    out = []
    merged: dict[int, Decimal] = {}
    if data.kind == "writeoff":                                  # the same item on two rows is one write-off
        for r in data.rows:
            merged[r.item_id] = merged.get(r.item_id, Decimal(0)) + D(r.qty)
    for r in data.rows if data.kind == "count" else []:
        have = stock.balance(db, r.item_id, data.warehouse_id)
        out.append(StockAdjustRow(item_id=r.item_id, system_qty=have, qty=D(r.qty), delta=D(r.qty) - have))
    for item_id, q in merged.items():
        out.append(StockAdjustRow(item_id=item_id, system_qty=Decimal(0), qty=q, delta=-q))
    return out


def _apply(db: Session, a: StockAdjust) -> None:
    for r in a.rows:
        stock.move(db, item_id=r.item_id, wh_id=a.warehouse_id, delta=r.delta, doc_type=TYPE, doc_id=a.id, number=a.number)


def create(db: Session, data) -> StockAdjust:
    _validate(db, data)
    a = StockAdjust(number=next_number(db, "STK" if data.kind == "count" else "WO"), date=data.date, kind=data.kind,
                    warehouse_id=data.warehouse_id, reason=data.reason if data.kind == "writeoff" else "", comment=data.comment, status="posted")
    a.rows = _rows(db, data)
    db.add(a)
    db.flush()
    _apply(db, a)
    return a


def update(db: Session, a: StockAdjust, data) -> StockAdjust:
    ensure_not_deleted(a)
    if data.kind != a.kind:
        raise bad("kind_locked", "The type of the document cannot be changed")
    _validate(db, data)
    with stock.deferred(db):
        stock.revert(db, TYPE, a.id, a.number)
        a.date, a.warehouse_id, a.comment = data.date, data.warehouse_id, data.comment
        a.reason = data.reason if data.kind == "writeoff" else ""
        a.rows = _rows(db, data)          # a count is re-measured against the stock as it was before this document
        db.flush()
        _apply(db, a)
    return a


def delete(db: Session, a: StockAdjust) -> None:
    ensure_not_deleted(a)
    stock.revert(db, TYPE, a.id, a.number)
    a.status = "deleted"


def restore(db: Session, a: StockAdjust) -> None:
    if a.status != "deleted":
        return
    with stock.deferred(db):
        _apply(db, a)
    a.status = "posted"
