"""Stock balances per warehouse, backed by an append-only movement ledger."""
from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import conflict
from app.models import Item, StockBalance, StockMove, Warehouse
from app.services.common import item_names


def balance(db: Session, item_id: int, wh_id: int) -> Decimal:
    b = db.get(StockBalance, (item_id, wh_id))
    return b.qty if b else Decimal(0)


def _short(db: Session, item_id: int, wh_id: int, have: Decimal):
    it, wh = db.get(Item, item_id), db.get(Warehouse, wh_id)
    return conflict(
        "insufficient_stock",
        f"Not enough {it.name_en} in {wh.name}: {have:f} {it.unit.name} available",
        item=item_names(it), warehouse=wh.name, available=float(have), unit=it.unit.name,
    )


def move(db: Session, *, item_id: int, wh_id: int, delta: Decimal, doc_type: str, doc_id: int, number: str) -> None:
    if delta == 0:
        return
    b = db.get(StockBalance, (item_id, wh_id))
    if b is None:
        b = StockBalance(item_id=item_id, warehouse_id=wh_id, qty=Decimal(0))
        db.add(b)
        db.flush()
    new = b.qty + delta
    touched = db.info.get("stock_touched")
    if touched is not None:
        touched.setdefault((item_id, wh_id), b.qty)   # remember what was there before the edit started
    elif new < 0:
        raise _short(db, item_id, wh_id, b.qty)
    b.qty = new
    db.add(StockMove(item_id=item_id, warehouse_id=wh_id, delta=delta, doc_type=doc_type, doc_id=doc_id, doc_number=number))
    db.flush()


@contextmanager
def deferred(db: Session):
    """Editing a document = undo its old effect, then apply the new one. Inside this block a balance may dip
    below zero while the old effect is undone; only the final balances are checked, when the block ends."""
    db.info["stock_touched"] = {}
    try:
        yield
        for (item_id, wh_id), before in db.info["stock_touched"].items():
            b = db.get(StockBalance, (item_id, wh_id))
            if b is not None and b.qty < 0:
                raise _short(db, item_id, wh_id, before)
    finally:
        db.info.pop("stock_touched", None)


def require(db: Session, wh_id: int, needs: dict[int, Decimal]) -> None:
    """Fail before changing anything if the warehouse cannot cover every item."""
    for item_id, qty in needs.items():
        have = balance(db, item_id, wh_id)
        if qty > have:
            raise _short(db, item_id, wh_id, have)


def revert(db: Session, doc_type: str, doc_id: int, number: str) -> None:
    """Undo whatever the document currently does to stock (net of its ledger entries)."""
    rows = db.execute(
        select(StockMove.item_id, StockMove.warehouse_id, func.sum(StockMove.delta))
        .where(StockMove.doc_type == doc_type, StockMove.doc_id == doc_id)
        .group_by(StockMove.item_id, StockMove.warehouse_id)
    ).all()
    for item_id, wh_id, net in rows:
        if net:
            move(db, item_id=item_id, wh_id=wh_id, delta=-Decimal(net), doc_type=doc_type, doc_id=doc_id, number=number)


def totals_by_item(db: Session) -> dict[int, dict[int, float]]:
    out: dict[int, dict[int, float]] = {}
    for b in db.query(StockBalance).all():
        out.setdefault(b.item_id, {})[b.warehouse_id] = float(b.qty)
    return out
