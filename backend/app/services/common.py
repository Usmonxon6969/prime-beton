from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.errors import bad, conflict, not_found
from app.models import Customer, Item, Supplier, Warehouse


def D(x) -> Decimal:
    return Decimal(str(x))


def item_names(it: Item) -> dict:
    return {"uz": it.name_uz, "ru": it.name_ru, "en": it.name_en}


def merge_rows(rows: Iterable) -> dict[int, Decimal]:
    """Total quantity per item (the same item may appear on several rows)."""
    out: dict[int, Decimal] = {}
    for r in rows:
        out[r.item_id] = out.get(r.item_id, Decimal(0)) + D(r.qty)
    return out


def get_items(db: Session, ids: Iterable[int], kind: str | None = None) -> dict[int, Item]:
    ids = set(ids)
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_(ids)).all()} if ids else {}
    for i in ids:
        it = items.get(i)
        if it is None or not it.is_active:
            raise bad("unknown_item", "Unknown or deleted item", item_id=i)
        if kind and it.kind != kind:
            raise bad("wrong_item_kind", f"Item must be a {kind}", item_id=i, kind=kind)
    return items


def need_rows(rows) -> None:
    if not rows:
        raise bad("no_rows", "Add at least one row")


def get_customer(db: Session, cid: int) -> Customer:
    c = db.get(Customer, cid)
    if c is None or not c.is_active:
        raise not_found("customer")
    return c


def get_supplier(db: Session, sid: int) -> Supplier:
    s = db.get(Supplier, sid)
    if s is None or not s.is_active:
        raise not_found("supplier")
    return s


def get_warehouse(db: Session, wid: int) -> Warehouse:
    w = db.get(Warehouse, wid)
    if w is None or not w.is_active:
        raise not_found("warehouse")
    return w


def total(rows) -> float:
    return float(sum(D(r.qty) * D(r.price) for r in rows if D(r.qty) > 0 and D(r.price) > 0))


def ensure_not_deleted(doc) -> None:
    if doc.status == "deleted":
        raise conflict("doc_deleted", "The document is deleted; restore it first")
