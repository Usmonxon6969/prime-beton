"""Split the rebar in the 2ПК slab specifications by the slab length: every slab gets the rebar of its own diameter.

    docker compose exec api python -m app.tools.split_rebar          # only shows what would change
    docker compose exec api python -m app.tools.split_rebar --yes    # does it (one transaction)

Default rule (length = the first number of the name, «71,5*12» is 71.5):
    up to 49     -> rebar 12   (length 49,5 counts as 50)
    50 .. 65     -> rebar 14
    over 65      -> rebar 16   (66 and longer, 65,5 included)
The quantity (kg per slab) stays exactly as it is in the specification; only the material changes. The three rebar materials must
already exist (a name with «арматура» / «armatura» / «rebar» and the diameter 12, 14 or 16). Products that are not 2ПК slabs (poles, blocks)
are not touched. Old production documents keep what they consumed. Make a backup first: `docker compose exec backup sh /ops/backup.sh once`."""
import argparse
import re
from collections import Counter
from decimal import Decimal

import app.models  # noqa: F401
from app.db.session import SessionLocal
from app.models import Item, Norm

SLAB = re.compile(r"2\s*[пp][кk]\s*(\d+)(?:[.,](\d+))?\s*[*xх×]", re.I)


def length_of(item: Item):
    for n in (item.name_ru, item.name_uz, item.name_en):
        m = SLAB.search(n or "")
        if m:
            return Decimal(m.group(1) + ("." + m.group(2) if m.group(2) else ""))
    return None


def rebar_materials(db, diameters=(12, 14, 16)) -> dict[int, Item]:
    mats = [m for m in db.query(Item).filter(Item.kind == "material")
            if any(re.search(r"арматур|armatur|rebar", (n or "").lower()) for n in (m.name_ru, m.name_uz, m.name_en))]
    out = {}
    for d in diameters:
        hit = [m for m in mats if any(re.search(rf"(?<!\d){d}(?!\d)", n or "") for n in (m.name_ru, m.name_uz, m.name_en))]
        if len(hit) != 1:
            raise SystemExit(f"rebar {d}: found {len(hit)} materials ({', '.join(m.name_ru for m in hit) or 'none'}), need exactly 1")
        out[d] = hit[0]
    return out


def target_for(length: Decimal, small_to: int, mid_to: int) -> int:
    if length < small_to + 1:
        return 12
    return 14 if length <= mid_to else 16


def plan(db, small_to: int = 49, mid_to: int = 65):
    """-> (rows [(product, length, target_diameter, [norms on any rebar], total_qty)], untouched [products with rebar but not a 2ПК slab])"""
    mats = rebar_materials(db)
    ids = {m.id for m in mats.values()}
    rows, untouched = [], []
    for it in db.query(Item).filter(Item.kind == "product"):
        norms = [n for n in db.query(Norm).filter(Norm.product_id == it.id) if n.material_id in ids]
        if not norms:
            continue
        ln = length_of(it)
        if ln is None:
            untouched.append(it)
            continue
        rows.append((it, ln, target_for(ln, small_to, mid_to), norms, sum((n.qty for n in norms), Decimal(0))))
    return mats, rows, untouched


def apply(db, small_to: int = 49, mid_to: int = 65) -> dict:
    mats, rows, _ = plan(db, small_to, mid_to)
    changed = 0
    for it, _, d, norms, total in rows:
        target = mats[d]
        keep = next((n for n in norms if n.material_id == target.id), None)
        if keep is not None and len(norms) == 1:
            continue                                                  # already right
        keep = keep or norms[0]
        for n in norms:
            if n is not keep:
                db.delete(n)
        keep.material_id, keep.qty = target.id, total
        changed += 1
    db.commit()
    return {"slabs checked": len(rows), "changed": changed}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--small-to", type=int, default=49, help="slabs up to this length get the smallest rebar (default 49)")
    ap.add_argument("--mid-to", type=int, default=65, help="slabs up to this length get the middle rebar (default 65)")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    with SessionLocal() as s:
        mats, rows, untouched = plan(s, a.small_to, a.mid_to)
        print("Rebar materials:", ", ".join(f"{d} = «{m.name_ru}»" for d, m in mats.items()))
        now = Counter()
        for it, ln, d, norms, _ in rows:
            now[(d, tuple(sorted({n.material_id for n in norms})) == (mats[d].id,))] += 1
        for d in (12, 14, 16):
            sel = [r for r in rows if r[2] == d]
            if sel:
                lens = sorted(r[1] for r in sel)
                print(f"  rebar {d}: {len(sel)} slabs, length {lens[0]} .. {lens[-1]}; already right: {now[(d, True)]}, to change: {now[(d, False)]}")
        print(f"2ПК slabs found: {len(rows)}")
        if untouched:
            print("Not 2ПК slabs, left as they are:", ", ".join(i.name_ru for i in untouched))
        if a.yes:
            print(apply(s, a.small_to, a.mid_to))
        else:
            print("DRY RUN - nothing changed. To do it: add --yes (after a backup).")
