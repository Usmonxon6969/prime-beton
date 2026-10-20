"""Import customers, suppliers or items from a CSV/Excel-exported file (for example a 1C nomenclature export).

    python -m app.tools.import_csv customers  kontragenty.csv
    python -m app.tools.import_csv suppliers  postavshiki.csv
    python -m app.tools.import_csv items      nomenklatura.csv

The first row is the header. Column names may be in English or Russian (1C):
  customers / suppliers:  name | Наименование,  phone | Телефон,  contact | Контактное лицо
  items:                  name | Наименование,  kind | Вид (product / material, Продукция / Материал),
                          unit | Единица | Ед. изм.,  min | Мин. остаток
The delimiter (; , or tab) and the encoding (UTF-8 or Windows-1251) are detected. Names that already exist are
skipped, so the file can be imported again safely. Stock is not imported: it comes from posted documents.
"""
import csv
import io
import sys
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.core.phone import normalize_phone
from app.models import Customer, Item, Supplier, Unit

ALIASES = {
    "name": ("name", "наименование", "название", "nomi"),
    "phone": ("phone", "телефон", "telefon"),
    "contact": ("contact", "контактное лицо", "контакт", "mas'ul shaxs"),
    "kind": ("kind", "вид", "тип", "turi"),
    "unit": ("unit", "единица", "ед. изм.", "ед.изм.", "birlik"),
    "min": ("min", "мин. остаток", "минимальный остаток", "minimal qoldiq"),
}
KINDS = {"product": "product", "продукция": "product", "товар": "product", "готовая продукция": "product",
         "material": "material", "материал": "material", "сырье": "material", "сырьё": "material"}


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_rows(text: str) -> list[dict[str, str]]:
    sample = text[:2000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return []
    head = [h.strip().lower() for h in rows[0]]
    col: dict[str, int] = {}
    for key, names in ALIASES.items():
        for i, h in enumerate(head):
            if h in names:
                col[key] = i
                break
    if "name" not in col:
        raise ValueError("The file needs a 'name' / 'Наименование' column")
    return [{k: (r[i].strip() if i < len(r) else "") for k, i in col.items()} for r in rows[1:]]


def _unit(db: Session, name: str, cache: dict[str, Unit]) -> Unit:
    key = name.strip().lower()
    if key in cache:
        return cache[key]
    u = Unit(name=name.strip(), name_ru=name.strip(), name_en=name.strip())
    db.add(u)
    db.flush()
    cache[key] = u
    return u


def import_rows(db: Session, what: str, rows: list[dict[str, str]]) -> dict[str, int]:
    added = skipped = 0
    if what in ("customers", "suppliers"):
        model = Customer if what == "customers" else Supplier
        have = {m.name.casefold(): m for m in db.query(model)}     # compared in Python: SQL lower() skips Cyrillic on some databases
        for r in rows:
            name = r["name"]
            if not name:
                continue
            old = have.get(name.casefold())
            if old and old.is_active:
                skipped += 1
                continue
            if old:                                   # was deleted earlier: bring it back
                old.is_active, old.phone, old.contact = True, normalize_phone(r.get("phone", "")), r.get("contact", "")
            else:
                have[name.casefold()] = new = model(name=name, phone=normalize_phone(r.get("phone", "")), contact=r.get("contact", ""))
                db.add(new)
            db.flush()
            added += 1
    elif what == "items":
        units: dict[str, Unit] = {}
        for u in db.query(Unit).filter(Unit.is_active):
            for n in (u.name, u.name_ru, u.name_en):
                if n:
                    units[n.lower()] = u
        seen = {(i.kind, i.name_uz.casefold()) for i in db.query(Item).filter(Item.is_active)}
        for r in rows:
            name = r["name"]
            if not name:
                continue
            kind = KINDS.get(r.get("kind", "").lower(), "product")
            if (kind, name.casefold()) in seen:                    # also catches a repeated line inside the same file
                skipped += 1
                continue
            seen.add((kind, name.casefold()))
            unit = _unit(db, r.get("unit") or ("kg" if kind == "material" else "dona"), units)
            try:
                mn = Decimal((r.get("min") or "0").replace(" ", "").replace(",", "."))
            except InvalidOperation:
                mn = Decimal(0)
            db.add(Item(kind=kind, name_uz=name, name_ru=name, name_en=name, unit_id=unit.id, min_stock=max(mn, 0)))
            db.flush()
            added += 1
    else:
        raise ValueError("what must be customers, suppliers or items")
    db.commit()
    return {"added": added, "skipped": skipped}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("customers", "suppliers", "items"):
        print(__doc__)
        return 2
    from app.db.session import SessionLocal
    with open(argv[2], "rb") as f:
        rows = read_rows(decode(f.read()))
    with SessionLocal() as db:
        db.info["user"] = {"id": None, "username": "import"}      # shows up in the change journal
        res = import_rows(db, argv[1], rows)
    print(f"{argv[1]}: {res['added']} added, {res['skipped']} already existed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
