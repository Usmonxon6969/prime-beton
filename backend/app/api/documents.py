"""Orders, delivery notes, purchase receipts and production documents."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import need
from app.core.errors import not_found
from app.db.session import get_db
from app.models import Invoice, Order, ProductionDoc, Receipt, User
from app.schemas.documents import (InvoiceIn, InvoiceOut, OrderIn, OrderOut, ProductionIn, ProductionOut, ReceiptIn,
                                   ReceiptOut)
from app.services import finance, production as prod
from app.services import purchasing, sales
from app.services.common import total

router = APIRouter(tags=["documents"])


def _get(db: Session, model, did: int, what: str):
    d = db.get(model, did)
    if d is None:
        raise not_found(what)
    return d


def _range(q, col, start: datetime | None, end: datetime | None, status: str | None, model):
    if start:
        q = q.filter(col >= start)
    if end:
        q = q.filter(col <= end)
    if status:
        q = q.filter(model.status == status)
    return q.order_by(col.desc(), model.id.desc())


# ---------- orders ----------
def _order_out(db: Session, o: Order, shipped: dict | None = None, advance=None) -> OrderOut:
    out = OrderOut.model_validate(o)
    out.total, out.state = total(o.rows), sales.order_state(db, o, shipped)
    out.advance = float(advance if advance is not None else finance.advances(db, [o.id]).get(o.id, 0))
    return out


@router.get("/orders", response_model=list[OrderOut])
def list_orders(customer_id: int | None = None, status: str | None = None, start: datetime | None = None,
                end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(need("ord", 1))):
    q = db.query(Order)
    if customer_id:
        q = q.filter(Order.customer_id == customer_id)
    orders = _range(q, Order.date, start, end, status, Order).all()
    sh = sales.shipped_bulk(db, [o.id for o in orders])
    adv = finance.advances(db, [o.id for o in orders])
    return [_order_out(db, o, sh[o.id], adv.get(o.id, 0)) for o in orders]


@router.get("/orders/{oid}", response_model=OrderOut)
def get_order(oid: int, db: Session = Depends(get_db), _: User = Depends(need("ord", 1))):
    return _order_out(db, _get(db, Order, oid, "order"))


@router.get("/orders/{oid}/remaining")
def order_remaining(oid: int, except_invoice: int | None = None, db: Session = Depends(get_db),
                    _: User = Depends(need("inv", 1))):
    o = _get(db, Order, oid, "order")
    return {k: float(v) for k, v in sales.remaining(db, o, except_invoice).items()}


@router.post("/orders", response_model=OrderOut, status_code=201)
def add_order(body: OrderIn, db: Session = Depends(get_db), _: User = Depends(need("ord", 2))):
    o = sales.create_order(db, body)
    db.commit()
    return _order_out(db, o)


@router.put("/orders/{oid}", response_model=OrderOut)
def edit_order(oid: int, body: OrderIn, db: Session = Depends(get_db), _: User = Depends(need("ord", 2))):
    o = sales.update_order(db, _get(db, Order, oid, "order"), body)
    db.commit()
    return _order_out(db, o)


@router.delete("/orders/{oid}", response_model=OrderOut)
def remove_order(oid: int, db: Session = Depends(get_db), _: User = Depends(need("ord", 2))):
    o = _get(db, Order, oid, "order")
    sales.delete_order(db, o)
    db.commit()
    return _order_out(db, o)


@router.post("/orders/{oid}/restore", response_model=OrderOut)
def restore_order(oid: int, db: Session = Depends(get_db), _: User = Depends(need("ord", 2))):
    o = _get(db, Order, oid, "order")
    sales.restore_order(db, o)
    db.commit()
    return _order_out(db, o)


# ---------- invoices ----------
def _inv_out(inv: Invoice) -> InvoiceOut:
    out = InvoiceOut.model_validate(inv)
    out.total = total(inv.rows)
    return out


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(customer_id: int | None = None, status: str | None = None, start: datetime | None = None,
                  end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(need("inv", 1))):
    q = db.query(Invoice)
    if customer_id:
        q = q.filter(Invoice.customer_id == customer_id)
    return [_inv_out(i) for i in _range(q, Invoice.date, start, end, status, Invoice)]


@router.get("/invoices/{iid}", response_model=InvoiceOut)
def get_invoice(iid: int, db: Session = Depends(get_db), _: User = Depends(need("inv", 1))):
    return _inv_out(_get(db, Invoice, iid, "invoice"))


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def add_invoice(body: InvoiceIn, db: Session = Depends(get_db), _: User = Depends(need("inv", 2))):
    inv = sales.create_invoice(db, body)
    db.commit()
    return _inv_out(inv)


@router.put("/invoices/{iid}", response_model=InvoiceOut)
def edit_invoice(iid: int, body: InvoiceIn, db: Session = Depends(get_db), _: User = Depends(need("inv", 2))):
    inv = sales.update_invoice(db, _get(db, Invoice, iid, "invoice"), body)
    db.commit()
    return _inv_out(inv)


@router.delete("/invoices/{iid}", response_model=InvoiceOut)
def remove_invoice(iid: int, db: Session = Depends(get_db), _: User = Depends(need("inv", 2))):
    inv = _get(db, Invoice, iid, "invoice")
    sales.delete_invoice(db, inv)
    db.commit()
    return _inv_out(inv)


@router.post("/invoices/{iid}/restore", response_model=InvoiceOut)
def restore_invoice(iid: int, db: Session = Depends(get_db), _: User = Depends(need("inv", 2))):
    inv = _get(db, Invoice, iid, "invoice")
    sales.restore_invoice(db, inv)
    db.commit()
    return _inv_out(inv)


# ---------- receipts ----------
def _rc_out(r: Receipt) -> ReceiptOut:
    out = ReceiptOut.model_validate(r)
    out.total = total(r.rows)
    return out


@router.get("/receipts", response_model=list[ReceiptOut])
def list_receipts(supplier_id: int | None = None, status: str | None = None, start: datetime | None = None,
                  end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(need("rec", 1))):
    q = db.query(Receipt)
    if supplier_id:
        q = q.filter(Receipt.supplier_id == supplier_id)
    return [_rc_out(r) for r in _range(q, Receipt.date, start, end, status, Receipt)]


@router.get("/receipts/{rid}", response_model=ReceiptOut)
def get_receipt(rid: int, db: Session = Depends(get_db), _: User = Depends(need("rec", 1))):
    return _rc_out(_get(db, Receipt, rid, "receipt"))


@router.post("/receipts", response_model=ReceiptOut, status_code=201)
def add_receipt(body: ReceiptIn, db: Session = Depends(get_db), _: User = Depends(need("rec", 2))):
    r = purchasing.create_receipt(db, body)
    db.commit()
    return _rc_out(r)


@router.put("/receipts/{rid}", response_model=ReceiptOut)
def edit_receipt(rid: int, body: ReceiptIn, db: Session = Depends(get_db), _: User = Depends(need("rec", 2))):
    r = purchasing.update_receipt(db, _get(db, Receipt, rid, "receipt"), body)
    db.commit()
    return _rc_out(r)


@router.delete("/receipts/{rid}", response_model=ReceiptOut)
def remove_receipt(rid: int, db: Session = Depends(get_db), _: User = Depends(need("rec", 2))):
    r = _get(db, Receipt, rid, "receipt")
    purchasing.delete_receipt(db, r)
    db.commit()
    return _rc_out(r)


@router.post("/receipts/{rid}/restore", response_model=ReceiptOut)
def restore_receipt(rid: int, db: Session = Depends(get_db), _: User = Depends(need("rec", 2))):
    r = _get(db, Receipt, rid, "receipt")
    purchasing.restore_receipt(db, r)
    db.commit()
    return _rc_out(r)


# ---------- production ----------
@router.get("/production", response_model=list[ProductionOut])
def list_production(warehouse_id: int | None = None, status: str | None = None, start: datetime | None = None,
                    end: datetime | None = None, db: Session = Depends(get_db), _: User = Depends(need("prod", 1))):
    q = db.query(ProductionDoc)
    if warehouse_id:
        q = q.filter(ProductionDoc.warehouse_id == warehouse_id)
    return _range(q, ProductionDoc.date, start, end, status, ProductionDoc).all()


@router.get("/production/{did}", response_model=ProductionOut)
def get_production(did: int, db: Session = Depends(get_db), _: User = Depends(need("prod", 1))):
    return _get(db, ProductionDoc, did, "production document")


@router.post("/production", response_model=ProductionOut, status_code=201)
def add_production(body: ProductionIn, db: Session = Depends(get_db), _: User = Depends(need("prod", 2))):
    d = prod.create_production(db, body)
    db.commit()
    return d


@router.put("/production/{did}", response_model=ProductionOut)
def edit_production(did: int, body: ProductionIn, db: Session = Depends(get_db), _: User = Depends(need("prod", 2))):
    d = prod.update_production(db, _get(db, ProductionDoc, did, "production document"), body)
    db.commit()
    return d


@router.delete("/production/{did}", response_model=ProductionOut)
def remove_production(did: int, db: Session = Depends(get_db), _: User = Depends(need("prod", 2))):
    d = _get(db, ProductionDoc, did, "production document")
    prod.delete_production(db, d)
    db.commit()
    return d


@router.post("/production/{did}/restore", response_model=ProductionOut)
def restore_production(did: int, db: Session = Depends(get_db), _: User = Depends(need("prod", 2))):
    d = _get(db, ProductionDoc, did, "production document")
    prod.restore_production(db, d)
    db.commit()
    return d
