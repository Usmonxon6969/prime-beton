"""Cost of a product: materials by the norms at the average purchase price, plus the scrap that normally goes with it,
plus piece-rate labour. Used by the cost report, the profit report and the value of losses."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Norm, ProductionDoc, ProductionRow, ProductRate, Receipt, ReceiptRow

Z = Decimal(0)


def avg_prices(db: Session, upto=None) -> dict[int, Decimal]:
    """Average purchase price per item: total paid / total received (all posted receipts up to the date)."""
    q = (select(ReceiptRow.item_id, func.sum(ReceiptRow.qty * ReceiptRow.price), func.sum(ReceiptRow.qty))
         .join(Receipt, ReceiptRow.receipt_id == Receipt.id).where(Receipt.status == "posted").group_by(ReceiptRow.item_id))
    if upto:
        q = q.where(Receipt.date <= upto)
    return {i: Decimal(v) / Decimal(qty) for i, v, qty in db.execute(q) if qty}


def scrap_rates(db: Session, upto=None) -> dict[int, Decimal]:
    """Spoiled units per good unit, by product, over all posted production."""
    q = (select(ProductionRow.item_id, func.sum(ProductionRow.scrap), func.sum(ProductionRow.qty))
         .join(ProductionDoc, ProductionRow.doc_id == ProductionDoc.id).where(ProductionDoc.status == "posted").group_by(ProductionRow.item_id))
    if upto:
        q = q.where(ProductionDoc.date <= upto)
    return {i: Decimal(s or 0) / Decimal(g) for i, s, g in db.execute(q) if g}


def labour_rates(db: Session) -> dict[int, Decimal]:
    return {r.item_id: r.rate for r in db.query(ProductRate)}


def unit_costs(db: Session, upto=None) -> dict[int, dict[str, Decimal]]:
    """Per finished unit: materials, extra materials lost to normal scrap, labour and the total."""
    avg, rates, lab = avg_prices(db, upto), scrap_rates(db, upto), labour_rates(db)
    mat: dict[int, Decimal] = {}
    for n in db.query(Norm).all():
        mat[n.product_id] = mat.get(n.product_id, Z) + n.qty * avg.get(n.material_id, Z)
    out = {}
    for pid in set(mat) | set(lab):
        m, sc, lb = mat.get(pid, Z), mat.get(pid, Z) * rates.get(pid, Z), lab.get(pid, Z)
        out[pid] = {"materials": m, "scrap": sc, "labour": lb, "total": m + sc + lb}
    return out


def item_costs(db: Session, upto=None) -> dict[int, Decimal]:
    """One cost per item: materials (and bought goods) at the average purchase price, products at their unit cost."""
    costs = dict(avg_prices(db, upto))
    for pid, c in unit_costs(db, upto).items():
        if c["total"] > 0:
            costs[pid] = c["total"]
    return costs
