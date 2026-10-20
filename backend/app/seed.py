"""Idempotent catalogue seed: units, plants (production sites), materials, products with norms, accounts and (optionally) demo logins.

Run:  python -m app.seed
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Account, Item, Norm, Unit, User, Warehouse

UNITS = [("dona", "шт", "pcs"), ("kg", "кг", "kg"), ("tonna", "т", "t"), ("m³", "м³", "m³"), ("m²", "м²", "m²"),
         ("m", "м", "m"), ("litr", "л", "l")]
# No stores are seeded: the plants below are the production sites; stores are created by the user in Settings.
MATERIALS = [  # (uz, ru, en, minimum stock)
    ("Sement", "Цемент", "Cement", 30000),
    ("Klinets", "Клинец", "Crushed stone", 150000),
    ("Qum", "Песок", "Sand", 100000),
    ("Armatura", "Арматура", "Rebar", 40000),
]
# 2ПК slabs: sizes 19..71.5 in 0.5 steps, widths 12 and 10 (norm per slab scales with the area).
SLAB_MIN = {"2ПК 66*12": 60, "2ПК 54*12": 60, "2ПК 62*12": 40}
OTHER_PRODUCTS = [("Опора СВ 110-3,5", 20, [520, 1500, 900, 95])]
ACCOUNTS = [
    ("bank", "1-bank hisobi (asosiy)", "Банковский счёт №1 (основной)", "Bank account 1 (main)"),
    ("bank", "2-bank hisobi", "Банковский счёт №2", "Bank account 2"),
    ("cash", "Bosh ofis kassasi", "Касса Главного офиса", "Head office cash desk"),
]
DEMO_USERS = [
    ("admin", "admin123", "admin", "Usmonxon Abbosov"),
    ("direktor", "dir123", "director", "Rustam Karimov"),
    ("ishlab", "prod123", "prod", "Sherzod Aliyev"),
    ("omborchi", "sklad123", "wh", "Bahodir Tursunov"),
    ("sotuv", "sotuv123", "sales", "Dilnoza Yusupova"),
    ("buxgalter", "buh123", "acc", "Malika Rahimova"),
]


def _slab_name(half_len: int, width: int) -> str:
    length = half_len / 2
    return "2ПК " + (str(int(length)) if length == int(length) else str(length).replace(".", ",")) + f"*{width}"


def seed(db: Session, demo_users: bool = False, catalogue: bool = False) -> None:
    """Units, money accounts and the first admin are always created. The sample catalogue (materials, 2ПК slabs; no plants or warehouses: the user creates their own) only with catalogue=True: a real installation starts empty."""
    if db.query(Unit).count() == 0:
        db.add_all(Unit(name=uz, name_ru=ru, name_en=en) for uz, ru, en in UNITS)
        db.flush()
    units = {u.name: u.id for u in db.query(Unit)}

    if catalogue and db.query(Item).count() == 0:
        mats = []
        for uz, ru, en, mn in MATERIALS:
            it = Item(kind="material", name_uz=uz, name_ru=ru, name_en=en, unit_id=units["kg"], min_stock=Decimal(mn))
            db.add(it)
            mats.append(it)
        db.flush()

        def product(name: str, mn: int, norms: list[int]) -> None:
            p = Item(kind="product", name_uz=name, name_ru=name, name_en=name, unit_id=units["dona"], min_stock=Decimal(mn))
            db.add(p)
            db.flush()
            for m, q in zip(mats, norms):
                if q:
                    db.add(Norm(product_id=p.id, material_id=m.id, qty=Decimal(q)))

        for half in range(143, 37, -1):
            for w in (12, 10):
                f = (half / 2) * w / 792
                product(_slab_name(half, w), SLAB_MIN.get(_slab_name(half, w), 0),
                        [round(390 * f), round(1150 * f), round(680 * f), round(44 * f)])
        for name, mn, norms in OTHER_PRODUCTS:
            product(name, mn, norms)

    if db.query(Account).count() == 0:
        for kind, uz, ru, en in ACCOUNTS:
            db.add(Account(kind=kind, name_uz=uz, name_ru=ru, name_en=en, opening_balance=0))

    if demo_users and db.query(User).count() == 0:
        for u, p, role, name in DEMO_USERS:
            db.add(User(username=u, password_hash=hash_password(p), role=role, full_name=name, is_owner=(u == "admin")))
    db.flush()
    admin = settings.admin_username.lower()
    if settings.admin_password and not db.query(User).filter(User.username == admin).first():
        db.add(User(username=admin, password_hash=hash_password(settings.admin_password),
                    role="admin", full_name="Administrator", is_owner=not db.query(User).filter(User.is_owner).first()))
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as s:
        import os
        seed(s, settings.seed_demo_users, catalogue=os.environ.get("SEED_CATALOGUE", "").lower() in ("1", "true", "yes"))
    print("seed done")
