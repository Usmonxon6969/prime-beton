"""Reference data rules: what may be renamed, changed or deleted."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import bad, conflict
from app.models import (Account, Customer, FinDoc, Invoice, InvoiceRow, Item, Norm, Order, OrderRow, ProductionDoc,
                        ProductionRow, Receipt, ReceiptRow, StockBalance, Supplier, Unit, Warehouse)
from app.services import finance


def _taken(db: Session, model, col, value, exclude_id=None):
    q = select(model.id).where(func.lower(col) == value.strip().lower())
    if exclude_id:
        q = q.where(model.id != exclude_id)
    return db.scalar(q.limit(1)) is not None


# ---- units ----
def unit_in_use(db: Session, uid: int) -> bool:
    return db.scalar(select(Item.id).where(Item.unit_id == uid).limit(1)) is not None


def create_unit(db: Session, name: str, name_ru: str = "", name_en: str = "") -> Unit:
    if _taken(db, Unit, Unit.name, name):
        raise conflict("duplicate", "This unit already exists", name=name)
    u = Unit(name=name.strip(), name_ru=name_ru.strip() or name.strip(), name_en=name_en.strip() or name.strip())
    db.add(u)
    db.flush()
    return u


def rename_unit(db: Session, u: Unit, name: str, name_ru: str = "", name_en: str = "") -> Unit:
    if _taken(db, Unit, Unit.name, name, u.id):
        raise conflict("duplicate", "This unit already exists", name=name)
    u.name = name.strip()
    u.name_ru = name_ru.strip() or u.name
    u.name_en = name_en.strip() or u.name
    return u


def delete_unit(db: Session, u: Unit) -> None:
    if db.scalar(select(func.count(Unit.id)).where(Unit.is_active)) <= 1:
        raise conflict("last_unit", "At least one unit of measure must remain")
    if unit_in_use(db, u.id):
        raise conflict("unit_in_use", "The unit is used by products or materials", name=u.name)
    u.is_active = False


# ---- warehouses ----
def warehouse_stock(db: Session, wid: int) -> Decimal:
    return Decimal(db.scalar(select(func.coalesce(func.sum(StockBalance.qty), 0)).where(StockBalance.warehouse_id == wid)) or 0)


def warehouse_in_use(db: Session, wid: int) -> bool:
    for m in (Invoice, Receipt, ProductionDoc):
        if db.scalar(select(m.id).where(m.warehouse_id == wid).limit(1)):
            return True
    return False


def create_warehouse(db: Session, name: str, is_workshop: bool = False) -> Warehouse:
    if _taken(db, Warehouse, Warehouse.name, name):
        raise conflict("duplicate", "A warehouse with this name exists", name=name)
    nxt = (db.scalar(select(func.max(Warehouse.sort_order))) or 0) + 1
    w = Warehouse(name=name.strip(), is_workshop=is_workshop, sort_order=nxt)
    db.add(w)
    db.flush()
    return w


def rename_warehouse(db: Session, w: Warehouse, name: str) -> Warehouse:
    if _taken(db, Warehouse, Warehouse.name, name, w.id):
        raise conflict("duplicate", "A warehouse with this name exists", name=name)
    w.name = name.strip()
    return w


def delete_warehouse(db: Session, w: Warehouse) -> None:
    if warehouse_stock(db, w.id) != 0:
        raise conflict("warehouse_has_stock", "The warehouse still holds stock", name=w.name)
    if warehouse_in_use(db, w.id):
        raise conflict("warehouse_in_use", "Documents use this warehouse", name=w.name)
    w.is_active = False


# ---- accounts ----
def account_in_use(db: Session, aid: int) -> bool:
    return db.scalar(select(FinDoc.id).where((FinDoc.account_id == aid) | (FinDoc.to_account_id == aid)).limit(1)) is not None


def delete_account(db: Session, a: Account) -> None:
    if account_in_use(db, a.id):
        raise conflict("account_in_use", "Money documents use this account")
    if a.opening_balance != 0:
        raise conflict("account_has_balance", "Zero the opening balance before deleting the account")
    a.is_active = False


# ---- items ----
def item_in_use(db: Session, item_id: int) -> bool:
    for m in (OrderRow, InvoiceRow, ReceiptRow, ProductionRow):
        if db.scalar(select(m.id).where(m.item_id == item_id).limit(1)):
            return True
    if db.scalar(select(Norm.id).where((Norm.material_id == item_id) | (Norm.product_id == item_id)).limit(1)):
        # norms alone do not block products, only a material used in specifications
        pass
    return False


def delete_item(db: Session, it: Item) -> None:
    if item_in_use(db, it.id):
        raise conflict("item_in_use", "Documents use this item", name=it.name_en)
    if db.scalar(select(func.coalesce(func.sum(StockBalance.qty), 0)).where(StockBalance.item_id == it.id)) != 0:
        raise conflict("item_has_stock", "The item still has stock", name=it.name_en)
    if it.kind == "material" and db.scalar(select(Norm.id).where(Norm.material_id == it.id, Norm.qty > 0).limit(1)):
        raise conflict("material_in_specs", "A specification uses this material", name=it.name_en)
    db.query(Norm).filter((Norm.product_id == it.id) | (Norm.material_id == it.id)).delete()
    it.is_active = False


def partner_in_use(db: Session, kind: str, pid: int) -> bool:
    if kind == "customer":
        return any(db.scalar(select(m.id).where(m.customer_id == pid).limit(1)) for m in (Order, Invoice, FinDoc))
    return any(db.scalar(select(m.id).where(m.supplier_id == pid).limit(1)) for m in (Receipt, FinDoc))
