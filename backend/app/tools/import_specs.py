"""Load specifications (material norms per product) from an Excel file. Only the 2ПК slabs are taken (rows starting with «2ПК»). The «,5» sizes (71,5*12 ...) are not in the file: they get the average of their two neighbours.

    docker compose exec api python -m app.tools.import_specs app/tools/data/specs-2pk.xlsx          # only shows what would change
    docker compose exec api python -m app.tools.import_specs app/tools/data/specs-2pk.xlsx --yes    # applies it (one transaction)

Layout: the first row has the material names (цемент, клинец, щебень, арматура, проволока), the first column the product names,
the cells the quantity per one product in kg. A material that does not exist yet is created (unit kg). A product's
specification in the file REPLACES its old one (materials not in the file are removed from that product). Products that
are not in the file stay as they are; names that find no product are listed and skipped (with --create they are created as pieces).
Make a backup first: `docker compose exec backup sh /ops/backup.sh once`."""
import argparse
import re
import sys
from decimal import Decimal

import openpyxl

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models import Item, Norm, Unit
from app.services.telegram_prod import _score, keys

NEW_MATERIALS = {  # (uz, ru, en) for a material the system does not have yet
    "цемент": ("Sement", "Цемент", "Cement"), "клинец": ("Klinets", "Клинец", "Crushed stone fines"),
    "щебень": ("Shcheben", "Щебень", "Crushed stone"), "арматура": ("Armatura", "Арматура", "Rebar"),
    "проволока": ("Sim", "Проволока", "Wire"),
}
FIX = {"щебен": "щебень", "провалока": "проволока", "щебёнка": "щебень"}      # typos in the header


def _norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().replace("..", ".")).lower()


def read(path: str):
    ws = openpyxl.load_workbook(path, data_only=True).active
    head = [(_norm_name(c.value), c.column - 1) for c in ws[1] if c.value and c.column > 1]
    heads = [(FIX.get(h, h), i) for h, i in head]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        name = _norm_name(r[0])
        if not name.startswith("2пк"):
            continue
        rows.append((str(r[0]).strip(), {h: Decimal(str(r[i])) for h, i in heads if isinstance(r[i], (int, float)) and r[i] > 0}))
    return [h for h, _ in heads], rows + halves(rows)


def halves(rows):
    """The «,5» sizes are not in the file: each is the average of its two neighbours of the same width (71,5*12 = mean of 71*12 and 72*12)."""
    by = {}
    for name, norms in rows:
        m = re.match(r"2пк\s*(\d+)\*(\d+)$", _norm_name(name))
        if m:
            by[(int(m.group(1)), int(m.group(2)))] = norms
    out = []
    for (length, width), lo in sorted(by.items()):
        hi = by.get((length + 1, width))
        if hi:
            avg = {h: (lo.get(h, Decimal(0)) + hi.get(h, Decimal(0))) / 2 for h in set(lo) | set(hi)}
            out.append((f"2ПК {length},5*{width}", {h: q.quantize(Decimal("0.001")) for h, q in avg.items() if q > 0}))
    return out


def find_material(mats: list[Item], name: str):
    """The material the header means: the same name, or a name that starts with that word («Проволока ВР-1 / 4мм» for «проволока»)."""
    first = lambda n: re.split(r"[\s/(,]+", _norm_name(n))[0]
    for m in mats:
        names = [n for n in (m.name_ru, m.name_uz, m.name_en) if n]
        if any(_score(name, n) >= 0.84 or first(n) == name for n in names):
            return m
    return None


def plan(db, path: str):
    heads, rows = read(path)
    mats = db.query(Item).filter(Item.kind == "material").all()
    mat_for, new_mats = {}, []
    for h in heads:
        m = find_material(mats, h)
        if m:
            mat_for[h] = m
        else:
            new_mats.append(h)
    products = {}
    for it in db.query(Item).filter(Item.kind == "product"):
        for n in (it.name_ru, it.name_uz, it.name_en):
            for k in keys(n or ""):
                products.setdefault(k, it)
    found, missing = [], []
    for name, norms in rows:
        it = next((products[k] for k in keys(name) if k in products), None)
        (found if it else missing).append((it, name, norms))
    return heads, mat_for, new_mats, found, missing


def apply(db, path: str, create: bool = False) -> dict:
    heads, mat_for, new_mats, found, missing = plan(db, path)
    kg = db.query(Unit).filter(Unit.name == "kg").one()
    for h in new_mats:
        uz, ru, en = NEW_MATERIALS.get(h, (h.capitalize(),) * 3)
        m = Item(kind="material", name_uz=uz, name_ru=ru, name_en=en, unit_id=kg.id, min_stock=Decimal(0))
        db.add(m)
        db.flush()
        mat_for[h] = m
    if create:                                                      # products that do not exist yet: made as pieces, with the file's spelling
        dona = db.query(Unit).filter(Unit.name == "dona").one()
        for _, name, norms in missing:
            it = Item(kind="product", name_uz=name, name_ru=name, name_en=name, unit_id=dona.id, min_stock=Decimal(0))
            db.add(it)
            db.flush()
            found.append((it, name, norms))
        missing = []
    for it, _, norms in found:
        db.query(Norm).filter(Norm.product_id == it.id).delete()
        for h, q in norms.items():
            db.add(Norm(product_id=it.id, material_id=mat_for[h].id, qty=q))
    db.commit()
    return {"products": len(found), "materials created": len(new_mats), "not found": len(missing)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--create", action="store_true", help="also create the products that are not in the system yet")
    ap.add_argument("--yes", action="store_true", help="really write (without it nothing changes)")
    a = ap.parse_args()
    with SessionLocal() as s:
        heads, mat_for, new_mats, found, missing = plan(s, a.file)
        print("Materials in the file:", ", ".join(heads))
        for h in heads:
            print(f"  {h}: " + (f"existing «{mat_for[h].name_ru}»" if h in mat_for else "NOT in the system - will be created (kg)"))
        print(f"Products found: {len(found)}, with norms to write; products NOT found: {len(missing)}")
        for _, name, _ in missing:
            print("  not found:", name)
        if found:
            it, name, norms = found[0]
            print(f"Example: {it.name_ru}: " + ", ".join(f"{h} {q}" for h, q in norms.items()))
        if a.yes:
            print(apply(s, a.file, a.create))
        else:
            print("DRY RUN - nothing changed. To write: add --yes (after a backup).")
