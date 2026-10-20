"""Units, warehouses, items (products and materials), specifications, customers, suppliers."""
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import current_user, need
from app.core.errors import bad, conflict, not_found
from app.db.session import get_db
from app.models import Customer, Item, Norm, Supplier, Unit, User, Warehouse
from app.schemas.catalog import (ItemIn, ItemOut, ItemUpdate, CustomerIn, CustomerOut, NormsPut, PartnerIn, PartnerOut, UnitIn, UnitOut,
                                 WarehouseIn, WarehouseOut)
from app.services import catalog as rules
from app.services import stock

router = APIRouter(tags=["reference"])


# ---------- units ----------
@router.get("/units", response_model=list[UnitOut])
def list_units(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.query(Unit).filter(Unit.is_active).order_by(Unit.id).all()


@router.post("/units", response_model=UnitOut, status_code=201)
def add_unit(body: UnitIn, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    u = rules.create_unit(db, body.name, body.name_ru, body.name_en)
    db.commit()
    return u


@router.put("/units/{uid}", response_model=UnitOut)
def edit_unit(uid: int, body: UnitIn, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    u = db.get(Unit, uid)
    if not u or not u.is_active:
        raise not_found("unit")
    rules.rename_unit(db, u, body.name, body.name_ru, body.name_en)
    db.commit()
    return u


@router.delete("/units/{uid}", status_code=204)
def remove_unit(uid: int, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    u = db.get(Unit, uid)
    if not u or not u.is_active:
        raise not_found("unit")
    rules.delete_unit(db, u)
    db.commit()


# ---------- warehouses ----------
@router.get("/warehouses", response_model=list[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.query(Warehouse).filter(Warehouse.is_active).order_by(Warehouse.sort_order, Warehouse.id).all()


@router.post("/warehouses", response_model=WarehouseOut, status_code=201)
def add_warehouse(body: WarehouseIn, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    w = rules.create_warehouse(db, body.name, body.is_workshop)
    db.commit()
    return w


@router.put("/warehouses/{wid}", response_model=WarehouseOut)
def edit_warehouse(wid: int, body: WarehouseIn, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    w = db.get(Warehouse, wid)
    if not w or not w.is_active:
        raise not_found("warehouse")
    rules.rename_warehouse(db, w, body.name)
    db.commit()
    return w


@router.delete("/warehouses/{wid}", status_code=204)
def remove_warehouse(wid: int, db: Session = Depends(get_db), _: User = Depends(need("set", 2))):
    w = db.get(Warehouse, wid)
    if not w or not w.is_active:
        raise not_found("warehouse")
    rules.delete_warehouse(db, w)
    db.commit()


# ---------- items ----------
def _items_out(db: Session, items: list[Item]) -> list[ItemOut]:
    st = stock.totals_by_item(db)
    out = []
    for it in items:
        s = st.get(it.id, {})
        out.append(ItemOut(id=it.id, kind=it.kind, name_uz=it.name_uz, name_ru=it.name_ru, name_en=it.name_en,
                           unit_id=it.unit_id, min_stock=float(it.min_stock), stock=s, total=sum(s.values())))
    return out


def _section(kind: str) -> str:
    return "items" if kind == "product" else "mats"


@router.get("/items", response_model=list[ItemOut])
def list_items(kind: str | None = Query(None, pattern="^(product|material)$"),
               db: Session = Depends(get_db), _: User = Depends(current_user)):
    q = db.query(Item).filter(Item.is_active)
    if kind:
        q = q.filter(Item.kind == kind)
    return _items_out(db, q.order_by(Item.id).all())


@router.post("/items", response_model=ItemOut, status_code=201)
def add_item(body: ItemIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    need(_section(body.kind), 2)(user)
    if not db.get(Unit, body.unit_id):
        raise bad("unknown_unit", "Unknown unit")
    for n in (body.name_uz, body.name_ru, body.name_en):
        if not n.strip():
            raise bad("name_required", "Enter the name in all languages")
    dup = db.query(Item).filter(Item.is_active, Item.kind == body.kind, (Item.name_uz == body.name_uz) | (Item.name_ru == body.name_ru) | (Item.name_en == body.name_en)).first()
    if dup:
        raise conflict("duplicate", "An item with this name exists", name=body.name_en)
    it = Item(kind=body.kind, name_uz=body.name_uz.strip(), name_ru=body.name_ru.strip(), name_en=body.name_en.strip(),
              unit_id=body.unit_id, min_stock=Decimal(str(body.min_stock)))
    db.add(it)
    db.commit()
    return _items_out(db, [it])[0]


@router.patch("/items/{iid}", response_model=ItemOut)
def edit_item(iid: int, body: ItemUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    it = db.get(Item, iid)
    if not it or not it.is_active:
        raise not_found("item")
    need(_section(it.kind), 2)(user)
    data = body.model_dump(exclude_none=True)
    if "unit_id" in data:
        if not db.get(Unit, data["unit_id"]):
            raise bad("unknown_unit", "Unknown unit")
        if data["unit_id"] != it.unit_id and rules.item_in_use(db, it.id):
            raise conflict("item_in_use", "Documents use this item, so its unit cannot change", name=it.name_en)
    for k, v in data.items():
        setattr(it, k, Decimal(str(v)) if k == "min_stock" else v)
    db.commit()
    return _items_out(db, [it])[0]


@router.delete("/items/{iid}", status_code=204)
def remove_item(iid: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    it = db.get(Item, iid)
    if not it or not it.is_active:
        raise not_found("item")
    need(_section(it.kind), 2)(user)
    rules.delete_item(db, it)
    db.commit()


# ---------- specifications (norms) ----------
@router.get("/specifications")
def all_specs(db: Session = Depends(get_db), _: User = Depends(need("specs", 1))):
    out: dict[int, dict[int, float]] = {}
    for n in db.query(Norm).all():
        out.setdefault(n.product_id, {})[n.material_id] = float(n.qty)
    return out


@router.put("/specifications/{product_id}")
def put_spec(product_id: int, body: NormsPut, db: Session = Depends(get_db), _: User = Depends(need("specs", 2))):
    p = db.get(Item, product_id)
    if not p or p.kind != "product" or not p.is_active:
        raise not_found("product")
    mats = {m.id for m in db.query(Item).filter(Item.kind == "material", Item.is_active)}
    for n in body.norms:
        if n.material_id not in mats:
            raise bad("unknown_material", "Unknown material", material_id=n.material_id)
    db.query(Norm).filter(Norm.product_id == product_id).delete()
    for n in body.norms:
        if n.qty > 0:
            db.add(Norm(product_id=product_id, material_id=n.material_id, qty=Decimal(str(n.qty))))
    db.commit()
    return {m.material_id: float(m.qty) for m in db.query(Norm).filter(Norm.product_id == product_id)}


# ---------- customers and suppliers ----------
def _terms(row, body) -> None:
    """Customers also carry a default payment term in days."""
    if hasattr(row, "pay_days") and hasattr(body, "pay_days"):
        row.pay_days = body.pay_days



def _partners(kind: str, model, section: str, pin=PartnerIn, pout=PartnerOut):
    @router.get(f"/{kind}s", response_model=list[pout], name=f"list_{kind}s")
    def lst(db: Session = Depends(get_db), _: User = Depends(current_user)):
        return db.query(model).filter(model.is_active).order_by(model.name).all()

    @router.post(f"/{kind}s", response_model=pout, status_code=201, name=f"add_{kind}")
    def add(body: pin, db: Session = Depends(get_db), _: User = Depends(need(section, 2))):
        if db.query(model).filter(model.is_active, model.name.ilike(body.name.strip())).first():
            raise conflict("duplicate", "This name already exists", name=body.name)
        row = model(name=body.name.strip(), phone=body.phone, contact=body.contact)
        existing = db.query(model).filter(model.name == row.name).first()   # re-activate a deleted one
        if existing:
            existing.is_active, existing.phone, existing.contact = True, body.phone, body.contact
            row = existing
        else:
            db.add(row)
        _terms(row, body)
        db.commit()
        return row

    @router.put(f"/{kind}s/{{pid}}", response_model=pout, name=f"edit_{kind}")
    def edit(pid: int, body: pin, db: Session = Depends(get_db), _: User = Depends(need(section, 2))):
        row = db.get(model, pid)
        if not row or not row.is_active:
            raise not_found(kind)
        if db.query(model).filter(model.is_active, model.id != pid, model.name.ilike(body.name.strip())).first():
            raise conflict("duplicate", "This name already exists", name=body.name)
        row.name, row.phone, row.contact = body.name.strip(), body.phone, body.contact
        _terms(row, body)
        db.commit()
        return row

    @router.delete(f"/{kind}s/{{pid}}", status_code=204, name=f"remove_{kind}")
    def remove(pid: int, db: Session = Depends(get_db), _: User = Depends(need(section, 2))):
        row = db.get(model, pid)
        if not row or not row.is_active:
            raise not_found(kind)
        if rules.partner_in_use(db, kind, pid):
            raise conflict(f"{kind}_in_use", "Documents use this record", name=row.name)
        row.is_active = False
        db.commit()


_partners("customer", Customer, "cus", CustomerIn, CustomerOut)
_partners("supplier", Supplier, "sup")
