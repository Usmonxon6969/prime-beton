"""Orders and delivery notes (invoices)."""
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import bad, conflict, not_found
from app.models import Invoice, InvoiceRow, Order, OrderRow
from app.services import stock
from app.services.common import (D, ensure_not_deleted, get_customer, get_items, get_warehouse, merge_rows,
                                 need_rows)
from app.services.numbering import next_number


# ---------- orders ----------
def shipped_map(db: Session, order_id: int, except_invoice: int | None = None) -> dict[int, Decimal]:
    out: dict[int, Decimal] = {}
    q = select(Invoice).where(Invoice.order_id == order_id, Invoice.status == "posted")
    for inv in db.scalars(q):
        if inv.id == except_invoice:
            continue
        for r in inv.rows:
            out[r.item_id] = out.get(r.item_id, Decimal(0)) + r.qty
    return out


def shipped_bulk(db: Session, order_ids: list[int]) -> dict[int, dict[int, Decimal]]:
    """Shipped quantities of many orders in a few queries (lists must not ask the database once per order)."""
    out: dict[int, dict[int, Decimal]] = {i: {} for i in order_ids}
    for k in range(0, len(order_ids), 500):
        chunk = order_ids[k:k + 500]
        q = (select(Invoice.order_id, InvoiceRow.item_id, func.sum(InvoiceRow.qty))
             .join(InvoiceRow, InvoiceRow.invoice_id == Invoice.id)
             .where(Invoice.order_id.in_(chunk), Invoice.status == "posted")
             .group_by(Invoice.order_id, InvoiceRow.item_id))
        for oid, item, qty in db.execute(q):
            out[oid][item] = Decimal(qty)
    return out


def order_state(db: Session, o: Order, shipped: dict[int, Decimal] | None = None) -> str:
    if o.status == "deleted":
        return "deleted"
    need = merge_rows(o.rows)
    sh = shipped if shipped is not None else shipped_map(db, o.id)
    done = sum(min(sh.get(k, Decimal(0)), v) for k, v in need.items())
    want = sum(need.values())
    return "shipped" if done >= want else ("partial" if done > 0 else "new")


def remaining(db: Session, o: Order, except_invoice: int | None = None) -> dict[int, Decimal]:
    need, sh = merge_rows(o.rows), shipped_map(db, o.id, except_invoice)
    return {k: v - sh.get(k, Decimal(0)) for k, v in need.items() if v - sh.get(k, Decimal(0)) > 0}


def _set_order_rows(db: Session, o: Order, rows) -> None:
    need_rows(rows)
    get_items(db, [r.item_id for r in rows], "product")
    o.rows = [OrderRow(item_id=r.item_id, qty=D(r.qty), price=D(r.price)) for r in rows]


def create_order(db: Session, data) -> Order:
    get_customer(db, data.customer_id)
    o = Order(number=next_number(db, "ZK"), date=data.date, due_date=data.due_date,
              customer_id=data.customer_id, comment=data.comment, status="open")
    _set_order_rows(db, o, data.rows)
    db.add(o)
    db.flush()
    return o


def update_order(db: Session, o: Order, data) -> Order:
    ensure_not_deleted(o)
    get_customer(db, data.customer_id)
    sh = shipped_map(db, o.id)
    if sh and data.customer_id != o.customer_id:
        raise conflict("order_has_invoices", "The order already has delivery notes; the customer cannot change")
    new = merge_rows(data.rows)
    for item_id, qty in sh.items():
        if new.get(item_id, Decimal(0)) < qty:
            raise conflict("order_below_shipped", "An order row cannot be smaller than what is already shipped",
                           item_id=item_id, shipped=float(qty))
    o.date, o.due_date, o.customer_id, o.comment = data.date, data.due_date, data.customer_id, data.comment
    _set_order_rows(db, o, data.rows)
    db.flush()
    return o


def delete_order(db: Session, o: Order) -> None:
    if db.scalar(select(Invoice.id).where(Invoice.order_id == o.id, Invoice.status == "posted").limit(1)):
        raise conflict("order_has_invoices", "The order has delivery notes; delete them first")
    o.status = "deleted"


def restore_order(db: Session, o: Order) -> None:
    o.status = "open"


# ---------- invoices ----------
def _check_against_order(db: Session, data, inv_id: int | None):
    if data.order_id is None:
        return
    o = db.get(Order, data.order_id)
    if o is None or o.status == "deleted":
        raise not_found("order")
    if o.customer_id != data.customer_id:
        raise bad("order_customer_mismatch", "The order belongs to another customer")
    rem = remaining(db, o, inv_id)
    for item_id, qty in merge_rows(data.rows).items():
        if qty > rem.get(item_id, Decimal(0)):
            raise conflict("over_order", "Quantity exceeds what is left to ship on the order",
                           item_id=item_id, left=float(rem.get(item_id, 0)))


def _apply(db: Session, inv: Invoice) -> None:
    needs = merge_rows(inv.rows)
    stock.require(db, inv.warehouse_id, needs)
    for item_id, qty in needs.items():
        stock.move(db, item_id=item_id, wh_id=inv.warehouse_id, delta=-qty, doc_type="invoice", doc_id=inv.id, number=inv.number)


def _pay_due(data, cust):
    """The date the customer must pay by: given explicitly, else the date plus the customer's usual term, else none."""
    if getattr(data, "pay_due", None):
        return data.pay_due
    days = getattr(cust, "pay_days", 0) or 0
    return data.date + timedelta(days=days) if days else None


def create_invoice(db: Session, data) -> Invoice:
    need_rows(data.rows)
    cust = get_customer(db, data.customer_id)
    get_warehouse(db, data.warehouse_id)
    get_items(db, [r.item_id for r in data.rows], "product")
    _check_against_order(db, data, None)
    inv = Invoice(pay_due=_pay_due(data, cust), number=next_number(db, "RN"), date=data.date, customer_id=data.customer_id, order_id=data.order_id,
                  warehouse_id=data.warehouse_id, comment=data.comment, status="posted",
                  driver=data.driver.strip(), vehicle=data.vehicle.strip().upper(),
                  rows=[InvoiceRow(item_id=r.item_id, qty=D(r.qty), price=D(r.price)) for r in data.rows])
    db.add(inv)
    db.flush()
    _apply(db, inv)
    return inv


def update_invoice(db: Session, inv: Invoice, data) -> Invoice:
    ensure_not_deleted(inv)
    need_rows(data.rows)
    cust = get_customer(db, data.customer_id)
    get_warehouse(db, data.warehouse_id)
    get_items(db, [r.item_id for r in data.rows], "product")
    _check_against_order(db, data, inv.id)
    with stock.deferred(db):
        stock.revert(db, "invoice", inv.id, inv.number)
        inv.pay_due = _pay_due(data, cust)
        inv.date, inv.customer_id, inv.order_id = data.date, data.customer_id, data.order_id
        inv.warehouse_id, inv.comment = data.warehouse_id, data.comment
        inv.driver, inv.vehicle = data.driver.strip(), data.vehicle.strip().upper()
        inv.rows = [InvoiceRow(item_id=r.item_id, qty=D(r.qty), price=D(r.price)) for r in data.rows]
        db.flush()
        _apply(db, inv)
    return inv


def delete_invoice(db: Session, inv: Invoice) -> None:
    ensure_not_deleted(inv)
    stock.revert(db, "invoice", inv.id, inv.number)
    inv.status = "deleted"


def restore_invoice(db: Session, inv: Invoice) -> None:
    if inv.status != "deleted":
        return
    _apply(db, inv)
    inv.status = "posted"
