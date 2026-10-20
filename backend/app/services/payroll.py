"""Piece-rate pay: a production document earns (good units x product rate); the crew shares it equally.
Bonuses and deductions are added by hand; salary payments from the bank/cash are linked to the worker."""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import FinDoc, PayAdjust, ProductionDoc, Worker

Z = Decimal(0)


def statement(db: Session, start: datetime | None = None, end: datetime | None = None) -> dict:
    """Per worker: earned / adjustments / paid in the period, and what is owed to date (all time up to the end of the period)."""
    def inside(d):
        return (not start or d >= start) and (not end or d <= end)

    def upto(d):
        return not end or d <= end

    earned_p, earned_all, unassigned = defaultdict(lambda: Z), defaultdict(lambda: Z), Z
    for d in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if not upto(d.date):
            continue
        if not d.crew:
            if inside(d.date):
                unassigned += d.labour
            continue
        share = d.labour / len(d.crew)
        for c in d.crew:
            earned_all[c.worker_id] += share
            if inside(d.date):
                earned_p[c.worker_id] += share
    adj_p, adj_all = defaultdict(lambda: Z), defaultdict(lambda: Z)
    for a in db.query(PayAdjust).filter(PayAdjust.status == "posted"):
        if upto(a.date):
            adj_all[a.worker_id] += a.amount
            if inside(a.date):
                adj_p[a.worker_id] += a.amount
    paid_p, paid_all = defaultdict(lambda: Z), defaultdict(lambda: Z)
    for f in db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind == "out", FinDoc.article == "sal", FinDoc.worker_id.is_not(None)):
        if upto(f.date):
            paid_all[f.worker_id] += f.amount
            if inside(f.date):
                paid_p[f.worker_id] += f.amount
    rows = []
    for w in db.query(Worker).order_by(Worker.name):
        owed = earned_all[w.id] + adj_all[w.id] - paid_all[w.id]
        if not w.is_active and not (earned_p[w.id] or adj_p[w.id] or paid_p[w.id] or owed):
            continue
        rows.append({"worker_id": w.id, "name": w.name, "position": w.position, "active": w.is_active,
                     "earned": float(earned_p[w.id]), "adjust": float(adj_p[w.id]), "paid": float(paid_p[w.id]), "owed": float(owed)})
    return {"rows": rows, "unassigned": float(unassigned),
            "totals": {k: round(sum(r[k] for r in rows), 2) for k in ("earned", "adjust", "paid", "owed")}}


def worker_statement(db: Session, worker_id: int, start: datetime | None = None, end: datetime | None = None) -> dict | None:
    """Reconciliation act for one worker: opening balance, every accrual / bonus / deduction / payment in the period in date order
    with a running balance, closing balance. 'owed' is what the plant owes the worker (negative = paid in advance)."""
    w = db.get(Worker, worker_id)
    if w is None:
        return None
    events = []                                           # (date, order, kind, number, accrual, paid, note, details)
    for d in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if d.crew and any(c.worker_id == worker_id for c in d.crew):
            events.append((d.date, 0, "earn", d.number, d.labour / len(d.crew), Z, d.comment or "",
                           {"items": [{"item_id": r.item_id, "qty": float(r.qty)} for r in d.rows], "crew": len(d.crew)}))
    for a in db.query(PayAdjust).filter(PayAdjust.status == "posted", PayAdjust.worker_id == worker_id):
        events.append((a.date, 1, "adj", f"#{a.id}", a.amount, Z, a.note or "", None))
    for f in db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind == "out", FinDoc.article == "sal", FinDoc.worker_id == worker_id):
        events.append((f.date, 2, "pay", f.number, Z, f.amount, f.comment or "", None))
    events.sort(key=lambda e: (e[0], e[1], e[3]))
    opening = Z
    rows, accrued, paid, bal = [], Z, Z, Z
    for date, _, kind, no, acc, pd, note, det in events:
        if start and date < start:
            opening += acc - pd
            continue
        if end and date > end:
            continue
        if not rows:
            bal = opening
        bal += acc - pd
        accrued += acc
        paid += pd
        rows.append({"date": date.isoformat(), "kind": kind, "no": no, "accrued": float(acc), "paid": float(pd), "balance": float(bal), "note": note, **(det or {})})
    return {"worker": {"id": w.id, "name": w.name, "position": w.position, "phone": w.phone, "active": w.is_active},
            "opening": float(opening), "accrued": float(accrued), "paid": float(paid), "closing": float(opening + accrued - paid), "rows": rows}
