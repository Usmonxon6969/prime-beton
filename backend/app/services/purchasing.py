"""Purchase receipts: materials or products arrive into a warehouse."""
from sqlalchemy.orm import Session

from app.models import Receipt, ReceiptRow
from app.services import stock
from app.services.common import (D, ensure_not_deleted, get_items, get_supplier, get_warehouse, merge_rows,
                                 need_rows)
from app.services.numbering import next_number


def _apply(db: Session, r: Receipt) -> None:
    for item_id, qty in merge_rows(r.rows).items():
        stock.move(db, item_id=item_id, wh_id=r.warehouse_id, delta=qty, doc_type="receipt", doc_id=r.id, number=r.number)


def _validate(db: Session, data) -> None:
    need_rows(data.rows)
    get_supplier(db, data.supplier_id)
    get_warehouse(db, data.warehouse_id)
    get_items(db, [x.item_id for x in data.rows])


def create_receipt(db: Session, data) -> Receipt:
    _validate(db, data)
    r = Receipt(number=next_number(db, "PN"), date=data.date, supplier_id=data.supplier_id,
                warehouse_id=data.warehouse_id, comment=data.comment, status="posted",
                rows=[ReceiptRow(item_id=x.item_id, qty=D(x.qty), price=D(x.price)) for x in data.rows])
    db.add(r)
    db.flush()
    _apply(db, r)
    return r


def update_receipt(db: Session, r: Receipt, data) -> Receipt:
    ensure_not_deleted(r)
    _validate(db, data)
    with stock.deferred(db):   # fails if the goods were already used up
        stock.revert(db, "receipt", r.id, r.number)
        r.date, r.supplier_id, r.warehouse_id, r.comment = data.date, data.supplier_id, data.warehouse_id, data.comment
        r.rows = [ReceiptRow(item_id=x.item_id, qty=D(x.qty), price=D(x.price)) for x in data.rows]
        db.flush()
        _apply(db, r)
    return r


def delete_receipt(db: Session, r: Receipt) -> None:
    ensure_not_deleted(r)
    stock.revert(db, "receipt", r.id, r.number)
    r.status = "deleted"


def restore_receipt(db: Session, r: Receipt) -> None:
    if r.status != "deleted":
        return
    _apply(db, r)
    r.status = "posted"
