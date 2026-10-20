"""Wipe all business data and the old demo catalogue entries, keeping only users, units and money accounts.

    python -m app.tools.reset_data --yes
    docker compose exec api python -m app.tools.reset_data --yes

Removes: every document (orders, delivery notes, receipts, production, money), stock and stock history, customers, suppliers,
the change journal and number counters. Account opening balances are set to 0. Also deletes every product, material and norm,
and every warehouse and plant (the user creates their own).
"""
import argparse

from sqlalchemy import delete, update

from app.db.base import Base
from app.db.session import SessionLocal
import app.models  # noqa: F401
from app.models import Account, Item, Norm, Warehouse

KEEP = {"users", "user_sessions", "units", "items", "norms", "warehouses", "accounts", "product_rates"}
DROP_ITEMS = None        # None = the whole catalogue (every product, material and norm)


def reset(db, drop_items=DROP_ITEMS, drop_stores=True) -> dict:
    done = {}
    for table in reversed(Base.metadata.sorted_tables):
        if table.name in KEEP:
            continue
        done[table.name] = db.execute(delete(table)).rowcount
    db.execute(update(Account).values(opening_balance=0))
    q = db.query(Item.id)
    if drop_items is not None:
        q = q.filter(Item.name_uz.in_(drop_items) | Item.name_ru.in_(drop_items) | Item.name_en.in_(drop_items))
    ids = [i for (i,) in q]
    if ids:
        db.execute(delete(Norm).where((Norm.product_id.in_(ids)) | (Norm.material_id.in_(ids))))
        done["items"] = db.execute(delete(Item).where(Item.id.in_(ids))).rowcount
    if drop_stores:
        done["warehouses"] = db.execute(delete(Warehouse).where(Warehouse.id.is_not(None))).rowcount
    db.commit()
    return done


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yes", action="store_true", help="really delete the data")
    ap.add_argument("--keep-stores", action="store_true", help="keep the warehouses and plants")
    ap.add_argument("--keep-catalogue", action="store_true", help="keep products, materials and norms")
    a = ap.parse_args()
    if not a.yes:
        raise SystemExit("Nothing deleted. Add --yes to wipe all documents, stock, partners and the journal.")
    with SessionLocal() as s:
        for k, v in reset(s, drop_items=() if a.keep_catalogue else None, drop_stores=not a.keep_stores).items():
            print(f"{k}: {v}")
    print("reset done")
