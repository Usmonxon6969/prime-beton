from app.models import Customer, Item
from app.tools import import_csv as ic

CSV = '"name";"kind";"unit";"min"\n"3ПК 71,5*12";"product";"dona";"0"\n"3ПК 71,5*10";"product";"dona";"0"\n"3пк 71,5*12";"product";"dona";"0"\n'


def test_items_import_is_repeatable_and_handles_cyrillic_and_commas(db_session):
    rows = ic.read_rows(ic.decode(("﻿" + CSV).encode("utf-8")))
    assert [r["name"] for r in rows][:2] == ["3ПК 71,5*12", "3ПК 71,5*10"]
    with db_session() as db:
        assert ic.import_rows(db, "items", rows) == {"added": 2, "skipped": 1}       # the lower-case repeat inside the file is skipped
    with db_session() as db:
        assert ic.import_rows(db, "items", rows) == {"added": 0, "skipped": 3}       # a second run adds nothing
        assert db.query(Item).filter(Item.name_uz.like("3ПК%")).count() == 2


def test_customers_import_skips_cyrillic_repeats(db_session):
    rows = [{"name": "Орион Строй"}, {"name": "орион строй"}]
    with db_session() as db:
        assert ic.import_rows(db, "customers", rows) == {"added": 1, "skipped": 1}
    with db_session() as db:
        assert ic.import_rows(db, "customers", rows) == {"added": 0, "skipped": 2}
        assert db.query(Customer).count() == 1
