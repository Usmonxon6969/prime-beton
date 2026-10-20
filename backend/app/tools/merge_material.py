"""Merge a duplicate material into another one: its specification lines move to the target and the duplicate is deleted.

    docker compose exec api python -m app.tools.merge_material "Проволока" "Проволока ВР-1 / 4мм"          # only shows
    docker compose exec api python -m app.tools.merge_material "Проволока" "Проволока ВР-1 / 4мм" --yes    # does it

The target keeps its own name, unit and minimum stock. If the duplicate is used anywhere else (stock, receipts, production ...) nothing is
changed and the places are listed. Make a backup first: `docker compose exec backup sh /ops/backup.sh once`."""
import argparse
import sys

from sqlalchemy import func, select

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import Item, Norm


def one(db, name: str) -> Item:
    rows = db.query(Item).filter(Item.kind == "material", (Item.name_ru == name) | (Item.name_uz == name) | (Item.name_en == name)).all()
    if len(rows) != 1:
        raise SystemExit(f"material «{name}»: found {len(rows)}, need exactly 1")
    return rows[0]


def uses(db, item_id: int) -> dict[str, int]:
    """Rows in other tables that point at the item (specification lines excluded: they are moved)."""
    out = {}
    for table in Base.metadata.sorted_tables:
        for col in table.columns:
            if any(fk.column.table.name == "items" for fk in col.foreign_keys) and table.name != "norms":
                n = db.execute(select(func.count()).select_from(table).where(col == item_id)).scalar_one()
                if n:
                    out[f"{table.name}.{col.name}"] = n
    return out


def merge(db, src: Item, dst: Item) -> dict[str, int]:
    if src.id == dst.id:
        raise SystemExit("source and target are the same material")
    busy = uses(db, src.id)
    if busy:
        raise SystemExit(f"«{src.name_ru}» is used elsewhere, nothing changed: {busy}")
    have = {n.product_id for n in db.query(Norm).filter(Norm.material_id == dst.id)}
    moved = dropped = 0
    for n in db.query(Norm).filter(Norm.material_id == src.id).all():
        if n.product_id in have:
            db.delete(n)
            dropped += 1
        else:
            n.material_id = dst.id
            moved += 1
    db.flush()
    db.delete(src)
    db.commit()
    return {"moved": moved, "dropped (target already had it)": dropped}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("target")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    with SessionLocal() as s:
        src, dst = one(s, a.source), one(s, a.target)
        n = s.query(Norm).filter(Norm.material_id == src.id).count()
        print(f"«{src.name_ru}» ({n} specification lines) -> «{dst.name_ru}»; «{src.name_ru}» is deleted afterwards")
        print("used elsewhere:", uses(s, src.id) or "nowhere")
        if a.yes:
            print(merge(s, src, dst))
        else:
            print("DRY RUN - nothing changed. To do it: add --yes (after a backup).")
