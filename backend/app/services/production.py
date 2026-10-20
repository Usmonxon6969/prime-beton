"""Production documents: products are added to a workshop, materials are consumed by norms."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import bad
from app.models import Norm, ProductionConsumption, ProductionCrew, ProductionDoc, ProductionRow, Worker
from app.services import stock
from app.services.common import D, ensure_not_deleted, get_items, get_warehouse, merge_rows, need_rows
from app.services.numbering import next_number


def material_need(db: Session, made: dict[int, Decimal]) -> dict[int, Decimal]:
    need: dict[int, Decimal] = {}
    if not made:
        return need
    for n in db.query(Norm).filter(Norm.product_id.in_(made.keys())).all():
        if n.qty > 0:
            need[n.material_id] = need.get(n.material_id, Decimal(0)) + n.qty * made[n.product_id]
    return need


def _gross(rows) -> dict[int, Decimal]:
    """Units that used materials: the good ones plus the spoiled ones."""
    out: dict[int, Decimal] = {}
    for r in rows:
        out[r.item_id] = out.get(r.item_id, Decimal(0)) + D(r.qty) + D(r.scrap or 0)
    return out


def _apply(db: Session, d: ProductionDoc) -> None:
    made = {k: v for k, v in merge_rows(d.rows).items() if v > 0}
    need = material_need(db, _gross(d.rows))
    stock.require(db, d.warehouse_id, need)
    for mid, q in need.items():
        stock.move(db, item_id=mid, wh_id=d.warehouse_id, delta=-q, doc_type="production", doc_id=d.id, number=d.number)
    for pid, q in made.items():
        stock.move(db, item_id=pid, wh_id=d.warehouse_id, delta=q, doc_type="production", doc_id=d.id, number=d.number)
    d.consumption = [ProductionConsumption(material_id=m, qty=q) for m, q in need.items()]


def _validate(db: Session, data) -> None:
    need_rows(data.rows)
    get_warehouse(db, data.warehouse_id)
    get_items(db, [r.item_id for r in data.rows], "product")
    ids = set(getattr(data, "worker_ids", []) or [])
    if ids:
        found = {w.id for w in db.query(Worker).filter(Worker.id.in_(ids), Worker.is_active)}
        if found != ids:
            raise bad("unknown_worker", "Unknown or removed worker")


def _rows(data):
    return [ProductionRow(item_id=r.item_id, qty=D(r.qty), scrap=D(r.scrap)) for r in data.rows]


def labour_for(db: Session, rows) -> Decimal:
    """Piece-rate pay of a batch at today's rates (frozen on the document, so later rate changes do not rewrite pay)."""
    from app.models import ProductRate
    rate = {r.item_id: r.rate for r in db.query(ProductRate)}
    return sum((D(r.qty) * rate.get(r.item_id, Decimal(0)) for r in rows), Decimal(0))


def _crew(data):
    return [ProductionCrew(worker_id=i) for i in dict.fromkeys(getattr(data, "worker_ids", []) or [])]


def create_production(db: Session, data) -> ProductionDoc:
    _validate(db, data)
    d = ProductionDoc(number=next_number(db, "PRD"), date=data.date, warehouse_id=data.warehouse_id,
                      comment=data.comment, status="posted",
                      rows=_rows(data), crew=_crew(data))
    d.labour = labour_for(db, d.rows)
    db.add(d)
    db.flush()
    _apply(db, d)
    return d


def update_production(db: Session, d: ProductionDoc, data) -> ProductionDoc:
    ensure_not_deleted(d)
    _validate(db, data)
    with stock.deferred(db):
        stock.revert(db, "production", d.id, d.number)
        d.date, d.warehouse_id, d.comment = data.date, data.warehouse_id, data.comment
        d.rows = _rows(data)
        d.crew = _crew(data)
        d.labour = labour_for(db, d.rows)
        db.flush()
        _apply(db, d)
    return d


def delete_production(db: Session, d: ProductionDoc) -> None:
    ensure_not_deleted(d)
    stock.revert(db, "production", d.id, d.number)   # fails if the products were already shipped
    d.status = "deleted"


def restore_production(db: Session, d: ProductionDoc) -> None:
    if d.status != "deleted":
        return
    _apply(db, d)
    d.status = "posted"
