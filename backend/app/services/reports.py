"""Debts, statements (akt sverka) and dashboard numbers."""
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (Account, Customer, FinDoc, Invoice, InvoiceRow, Item, Order, ProductionDoc, ProductionRow,
                        Receipt, ReceiptRow, StockBalance, Supplier)
from app.services import finance, sales


def _sum_rows(db: Session, row, doc, fk, status="posted") -> dict[int, Decimal]:
    q = (select(getattr(doc, fk), func.sum(row.qty * row.price))
         .join(doc, getattr(row, "invoice_id" if doc is Invoice else "receipt_id") == doc.id)
         .where(doc.status == status).group_by(getattr(doc, fk)))
    return {k: Decimal(v or 0) for k, v in db.execute(q)}


def _paid(db: Session, col, article: str) -> dict[int, Decimal]:
    q = (select(col, func.sum(FinDoc.amount))
         .where(FinDoc.status == "posted", FinDoc.kind.in_(["in", "out"]), FinDoc.article == article, col.is_not(None))
         .group_by(col))
    return {k: Decimal(v or 0) for k, v in db.execute(q)}


def customer_debts(db: Session) -> list[dict]:
    shipped, paid = _sum_rows(db, InvoiceRow, Invoice, "customer_id"), _paid(db, FinDoc.customer_id, "cust")
    return [{"customer_id": c.id, "name": c.name, "shipped": float(shipped.get(c.id, 0)),
             "paid": float(paid.get(c.id, 0)), "debt": float(shipped.get(c.id, 0) - paid.get(c.id, 0))}
            for c in db.query(Customer).filter(Customer.is_active).order_by(Customer.name)]


def aging(db: Session, today: datetime | None = None) -> list[dict]:
    """What each customer owes, by how late it is. Payments are applied to the oldest delivery notes first;
    a delivery note is due on its pay-by date (or on the delivery day when no term was given).
    Money paid beyond all deliveries is an advance."""
    today = (today or datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)
    paid = _paid(db, FinDoc.customer_id, "cust")
    inv: dict[int, list] = {}
    for v in db.query(Invoice).filter(Invoice.status == "posted").order_by(Invoice.date, Invoice.id):
        inv.setdefault(v.customer_id, []).append(v)
    out = []
    for c in db.query(Customer).filter(Customer.is_active).order_by(Customer.name):
        left = paid.get(c.id, Decimal(0))
        row = {"customer_id": c.id, "name": c.name, "current": Decimal(0), "d30": Decimal(0), "d60": Decimal(0), "d90": Decimal(0),
               "oldest_days": 0, "next_due": None}
        for v in inv.get(c.id, []):
            amt = sum((r.qty * r.price for r in v.rows), Decimal(0))
            cover = min(left, amt)
            left -= cover
            rest = amt - cover
            if rest <= 0:
                continue
            due = (v.pay_due or v.date).replace(hour=0, minute=0, second=0, microsecond=0)
            late = (today - due).days
            key = "current" if late <= 0 else "d30" if late <= 30 else "d60" if late <= 60 else "d90"
            row[key] += rest
            if late > row["oldest_days"]:
                row["oldest_days"] = late
            if late <= 0 and (row["next_due"] is None or due < row["next_due"]):
                row["next_due"] = due
        row["advance"] = left
        row["overdue"] = row["d30"] + row["d60"] + row["d90"]
        row["debt"] = row["current"] + row["overdue"]
        for k in ("current", "d30", "d60", "d90", "advance", "overdue", "debt"):
            row[k] = float(row[k])
        row["next_due"] = row["next_due"].date().isoformat() if row["next_due"] else None
        if row["debt"] or row["advance"]:
            out.append(row)
    return out


def supplier_debts(db: Session) -> list[dict]:
    bought, paid = _sum_rows(db, ReceiptRow, Receipt, "supplier_id"), _paid(db, FinDoc.supplier_id, "sup")
    return [{"supplier_id": s.id, "name": s.name, "bought": float(bought.get(s.id, 0)),
             "paid": float(paid.get(s.id, 0)), "debt": float(bought.get(s.id, 0) - paid.get(s.id, 0))}
            for s in db.query(Supplier).filter(Supplier.is_active).order_by(Supplier.name)]


def statement(db: Session, *, customer_id: int | None, supplier_id: int | None, start: datetime | None, end: datetime | None,
              lang: str = "en") -> dict:
    """Reconciliation act. Customer: debt grows with shipments and falls with payments. Supplier: the same for purchases.
    Every shipment / receipt carries its lines (`items`: name, unit, qty, price, amount) so the printed act shows what was bought."""
    ev: list[tuple[datetime, str, str, Decimal, Decimal, list]] = []   # date, number, kind, debit, credit, doc rows
    if customer_id:
        for v in db.query(Invoice).filter(Invoice.customer_id == customer_id, Invoice.status == "posted"):
            ev.append((v.date, v.number, "invoice", sum((r.qty * r.price for r in v.rows), Decimal(0)), Decimal(0), list(v.rows)))
        for f in db.query(FinDoc).filter(FinDoc.customer_id == customer_id, FinDoc.status == "posted", FinDoc.kind == "in"):
            ev.append((f.date, f.number, "payment", Decimal(0), f.amount, []))
    else:
        for v in db.query(Receipt).filter(Receipt.supplier_id == supplier_id, Receipt.status == "posted"):
            ev.append((v.date, v.number, "receipt", sum((r.qty * r.price for r in v.rows), Decimal(0)), Decimal(0), list(v.rows)))
        for f in db.query(FinDoc).filter(FinDoc.supplier_id == supplier_id, FinDoc.status == "posted", FinDoc.kind == "out"):
            ev.append((f.date, f.number, "payment", Decimal(0), f.amount, []))
    ev.sort(key=lambda e: (e[0], e[1]))
    opening = sum((e[3] - e[4] for e in ev if start and e[0] < start), Decimal(0))
    ids = {r.item_id for e in ev for r in e[5]}
    its = {i.id: i for i in db.query(Item).filter(Item.id.in_(ids))} if ids else {}
    col = "name_" + (lang if lang in ("uz", "ru", "en") else "en")
    rows, bal = [], opening
    for d, no, kind, debit, credit, lines in ev:
        if (start and d < start) or (end and d > end):
            continue
        bal += debit - credit
        items = [{"name": getattr(its[r.item_id], col) or its[r.item_id].name_en, "unit": its[r.item_id].unit.name,
                  "qty": float(r.qty), "price": float(r.price), "amount": float(r.qty * r.price)} for r in lines]
        rows.append({"date": d, "number": no, "kind": kind, "debit": float(debit), "credit": float(credit), "balance": float(bal), "items": items})
    return {"opening": float(opening), "rows": rows, "closing": float(bal),
            "debit": float(sum(r["debit"] for r in rows)), "credit": float(sum(r["credit"] for r in rows))}


def low_stock(db: Session) -> list[dict]:
    tot = dict(db.execute(select(StockBalance.item_id, func.sum(StockBalance.qty)).group_by(StockBalance.item_id)).all())
    out = []
    for it in db.query(Item).filter(Item.is_active, Item.min_stock > 0):
        have = Decimal(tot.get(it.id) or 0)
        if have < it.min_stock:
            out.append({"item_id": it.id, "have": float(have), "min": float(it.min_stock), "unit": it.unit.name})
    return out


def dashboard(db: Session, levels: dict[str, int], days: int = 14) -> dict:
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=days - 1)
    out: dict = {"as_of": now.isoformat()}
    if levels.get("inv"):
        since = today - timedelta(days=29)
        inv30 = db.query(Invoice).filter(Invoice.status == "posted", Invoice.date >= since).all()
        out["sales_30d"] = float(sum(sum((r.qty * r.price for r in v.rows), Decimal(0)) for v in inv30))
        out["invoices_30d"] = len(inv30)
        daily = {}
        for v in db.query(Invoice).filter(Invoice.status == "posted", Invoice.date >= start):
            k = v.date.date().isoformat()
            daily.setdefault(k, {"shipped": 0.0, "paid": 0.0, "docs": 0})
            daily[k]["shipped"] += float(sum((r.qty * r.price for r in v.rows), Decimal(0)))
            daily[k]["docs"] += 1
        if levels.get("cus"):
            for f in db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind == "in", FinDoc.article == "cust", FinDoc.date >= start):
                k = f.date.date().isoformat()
                daily.setdefault(k, {"shipped": 0.0, "paid": 0.0, "docs": 0})
                daily[k]["paid"] += float(f.amount)
        out["daily"] = [{"date": (start + timedelta(days=i)).date().isoformat(),
                         **daily.get((start + timedelta(days=i)).date().isoformat(), {"shipped": 0.0, "paid": 0.0, "docs": 0})}
                        for i in range(days)]
    if levels.get("cus"):
        out["receivables"] = sum(max(0, d["debt"]) for d in customer_debts(db))
        ag = aging(db, now)
        out["overdue"] = sum(a["overdue"] for a in ag)
        out["overdue_customers"] = sum(1 for a in ag if a["overdue"] > 0)
    if levels.get("sup"):
        out["payables"] = sum(max(0, d["debt"]) for d in supplier_debts(db))
    if levels.get("bank") or levels.get("cash"):
        bal = finance.balances(db)
        accs = []
        for a in db.query(Account).filter(Account.is_active).order_by(Account.id):
            if levels.get(a.kind):
                accs.append({"id": a.id, "kind": a.kind, "name": {"uz": a.name_uz, "ru": a.name_ru, "en": a.name_en}, "balance": float(bal[a.id])})
        out["accounts"] = accs
        out["bank_total"] = sum(a["balance"] for a in accs if a["kind"] == "bank")
        out["cash_total"] = sum(a["balance"] for a in accs if a["kind"] == "cash")
    if levels.get("ord"):
        live = db.query(Order).filter(Order.status != "deleted").all()
        sh = sales.shipped_bulk(db, [o.id for o in live])
        out["open_orders"] = sum(1 for o in live if sales.order_state(db, o, sh[o.id]) != "shipped")
    if levels.get("wh"):
        out["low_stock"] = low_stock(db)
    if levels.get("prod"):
        q = (select(func.date(ProductionDoc.date), func.sum(ProductionRow.qty))
             .join(ProductionRow, ProductionRow.doc_id == ProductionDoc.id)
             .where(ProductionDoc.status == "posted", ProductionDoc.date >= start).group_by(func.date(ProductionDoc.date)))
        made = {str(k): float(v) for k, v in db.execute(q)}
        out["production_daily"] = [{"date": (start + timedelta(days=i)).date().isoformat(),
                                   "qty": made.get((start + timedelta(days=i)).date().isoformat(), 0.0)} for i in range(days)]
    return out
