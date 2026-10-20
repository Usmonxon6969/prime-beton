from app.tools.import_csv import decode, import_rows, read_rows


def test_import_customers_from_1c_export_is_idempotent(ctx, db_session):
    text = "Наименование;Телефон;Контактное лицо\nOrient Stroy;+998 90 1;Aziz\nBektemir MChJ;;\nOrient Stroy;;\n"
    with db_session() as db:
        assert import_rows(db, "customers", read_rows(text)) == {"added": 2, "skipped": 1}
        assert import_rows(db, "customers", read_rows(text)) == {"added": 0, "skipped": 3}
    names = [c["name"] for c in ctx.get("/customers").json()]
    assert names == ["Bektemir MChJ", "Orient Stroy"]


def test_import_items_creates_units_and_reads_cp1251(ctx, db_session):
    raw = "Наименование;Вид;Единица;Мин. остаток\nЩебень 5-20;Материал;кг;1 000,5\nПлита ПК-1;Продукция;шт;10\n".encode("cp1251")
    with db_session() as db:
        res = import_rows(db, "items", read_rows(decode(raw)))
    assert res == {"added": 2, "skipped": 0}
    items = {i["name_ru"]: i for i in ctx.get("/items").json()}
    assert items["Щебень 5-20"]["kind"] == "material" and items["Щебень 5-20"]["min_stock"] == 1000.5
    assert items["Плита ПК-1"]["kind"] == "product"
    assert "кг" in [u["name_ru"] for u in ctx.get("/units").json()]     # matched the existing kg, no duplicate
    assert len([u for u in ctx.get("/units").json() if u["name_ru"] == "кг"]) == 1
