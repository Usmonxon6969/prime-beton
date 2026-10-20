from app.models import (Account, AuditLog, Customer, FinDoc, Invoice, Item, Order, ProductionDoc, Receipt, StockBalance, StockMove, TelegramCursor,
                        TelegramLink, User, Warehouse, Worker)
from app.tools import clear_movements as cm
from tests.conftest import scenario


def test_clear_movements_keeps_master_data_and_restarts_numbering(db_session, ctx):
    sc = scenario(ctx)
    ctx.post("/orders", {"date": "2026-10-15T09:00:00", "customer_id": sc["cus"], "rows": [{"item_id": sc["fbs"], "qty": 2, "price": 100}]})
    with db_session() as db:
        db.add(TelegramCursor(kind="prod", last_id=99))
        db.commit()
        before = {"items": db.query(Item).count(), "wh": db.query(Warehouse).count(), "acc": db.query(Account).count(),
                  "cus": db.query(Customer).count(), "users": db.query(User).count()}
        counts = cm.plan(db)                                                   # a dry run changes nothing
        assert counts["invoices"] == 1 and counts["fin_docs"] == 2 and counts["production_docs"] == 1 and counts["orders"] == 1 and counts["receipts"] == 1
        assert db.query(Invoice).count() == 1 and db.query(StockMove).count() > 0
        done = cm.clear(db)
        assert done["invoices"] == 1 and done["fin_docs"] == 2
        for model in (Order, Invoice, Receipt, ProductionDoc, FinDoc, StockMove, StockBalance, TelegramCursor):
            assert db.query(model).count() == 0, model
        assert db.query(AuditLog).filter(AuditLog.entity.in_(["orders", "invoices", "production_docs", "fin_docs"])).count() == 0
        assert {"items": db.query(Item).count(), "wh": db.query(Warehouse).count(), "acc": db.query(Account).count(),
                "cus": db.query(Customer).count(), "users": db.query(User).count()} == before        # master data stays
    # numbering starts again and stock is empty, so a new document works from scratch
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 0
    r = ctx.post("/orders", {"date": "2026-10-16T09:00:00", "customer_id": sc["cus"], "rows": [{"item_id": sc["fbs"], "qty": 1, "price": 100}]})
    assert r.json()["number"].endswith("000001")
    assert ctx.get("/customers").json()


def test_clear_movements_keeps_workers_and_telegram_links(db_session, ctx):
    scenario(ctx)
    ctx.post("/workers", {"name": "Ali Valiyev"})
    uid = ctx.post("/auth/users", {"username": "tgu", "password": "Strong-pass-123", "full_name": "Tg User", "role": "prod"}).json()["id"]
    with db_session() as db:
        db.add(TelegramLink(user_id=uid, chat_id=77, lang="uz"))
        db.commit()
        cm.clear(db)
        assert db.query(Worker).count() == 1 and db.query(TelegramLink).count() == 1


def test_clear_with_people_deletes_customers_suppliers_workers_but_keeps_lists(db_session, ctx):
    from app.models import Supplier, Unit
    sc = scenario(ctx)
    ctx.post("/workers", {"name": "Ali Valiyev"})
    ctx.post("/orders", {"date": "2026-10-15T09:00:00", "customer_id": sc["cus"], "rows": [{"item_id": sc["fbs"], "qty": 2, "price": 100}]})
    with db_session() as db:
        keep = {m.__name__: db.query(m).count() for m in (Item, Warehouse, Account, User, Unit)}
        assert cm.plan(db, True)["workers"] == 1 and "workers" not in cm.plan(db)
        cm.clear(db, True)
        assert db.query(Customer).count() == 0 and db.query(Supplier).count() == 0 and db.query(Worker).count() == 0
        assert {m.__name__: db.query(m).count() for m in (Item, Warehouse, Account, User, Unit)} == keep


def test_import_specs_replaces_norms_for_2pk_only(db_session, ctx):
    import os
    from app.models import Norm
    from app.tools import import_specs as isp
    path = os.path.join(os.path.dirname(__file__), "..", "app", "tools", "data", "specs-2pk.xlsx")
    scenario(ctx)
    with db_session() as db:
        heads, mat_for, new_mats, found, missing = isp.plan(db, path)
        assert "щебень" in heads and "проволока" in heads and len(found) + len(missing) == 106 + 104    # 2ПК rows only, no ФБС / Опора
        before = db.query(Norm).count()
        res = isp.apply(db, path)
        assert res["products"] == len(found) and db.query(Norm).count() != 0
        n = db.query(Item).filter(Item.name_ru == "2ПК 66*12").first()
        if n:
            q = {db.get(Item, x.material_id).name_ru.lower(): float(x.qty) for x in db.query(Norm).filter(Norm.product_id == n.id)}
            assert q["цемент"] == 460 and q["проволока"] == 6.08


def test_half_sizes_are_the_mean_of_their_neighbours():
    from decimal import Decimal
    from app.tools import import_specs as isp
    rows = [("2ПК 71*12", {"цемент": Decimal(500), "проволока": Decimal("8.12")}), ("2ПК 72*12", {"цемент": Decimal(460), "проволока": Decimal("6.08")}),
            ("2ПК 71*10", {"цемент": Decimal(450)})]
    h = isp.halves(rows)
    assert h == [("2ПК 71,5*12", {"цемент": Decimal("480.000"), "проволока": Decimal("7.100")})]


def test_merge_material_moves_norms_and_import_finds_the_long_name(db_session, ctx):
    from decimal import Decimal
    from app.models import Norm, Unit
    from app.tools import import_specs as isp, merge_material as mm
    scenario(ctx)
    with db_session() as db:
        kg = db.query(Unit).filter(Unit.name == "kg").one()
        long = Item(kind="material", name_uz="Sim 4mm", name_ru="Проволока ВР-1 / 4мм", name_en="Wire 4mm", unit_id=kg.id, min_stock=Decimal(1000))
        dup = Item(kind="material", name_uz="Sim", name_ru="Проволока", name_en="Wire", unit_id=kg.id, min_stock=Decimal(0))
        db.add_all([long, dup])
        db.flush()
        assert isp.find_material([long], "проволока").id == long.id
        p = db.query(Item).filter(Item.kind == "product").first()
        db.add(Norm(product_id=p.id, material_id=dup.id, qty=Decimal("6.08")))
        db.commit()
        res = mm.merge(db, dup, long)
        assert res["moved"] == 1 and db.query(Item).filter(Item.name_ru == "Проволока").count() == 0
        assert float(db.query(Norm).filter(Norm.material_id == long.id, Norm.product_id == p.id).one().qty) == 6.08
