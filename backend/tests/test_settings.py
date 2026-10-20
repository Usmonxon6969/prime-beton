from tests.conftest import NOW


def test_units_rules(ctx):
    assert ctx.post("/units", {"name": "pallet"}).status_code == 201
    assert ctx.post("/units", {"name": "PALLET"}).status_code == 409           # duplicate (case-insensitive)
    dona = [u for u in ctx.get("/units").json() if u["name"] == "dona"][0]
    assert ctx.c.delete(f"/api/units/{dona['id']}", headers=ctx.h).status_code == 409   # products use it
    pallet = [u for u in ctx.get("/units").json() if u["name"] == "pallet"][0]
    assert ctx.c.delete(f"/api/units/{pallet['id']}", headers=ctx.h).status_code == 204


def test_warehouse_rules(ctx):
    w = ctx.post("/warehouses", {"name": "Yangi ombor"})
    assert w.status_code == 201 and not w.json()["is_workshop"]
    z = ctx.post("/warehouses", {"name": "Yangi zavod", "is_workshop": True}).json()      # a plant can be created and, while empty, deleted
    assert z["is_workshop"] and ctx.c.delete(f"/api/warehouses/{z['id']}", headers=ctx.h).status_code == 204
    sup = ctx.supplier()
    ctx.post("/receipts", {"date": NOW, "supplier_id": sup, "warehouse_id": w.json()["id"], "rows": [{"item_id": ctx.items["Cement"]["id"], "qty": 5, "price": 1}]})
    assert ctx.c.delete(f"/api/warehouses/{w.json()['id']}", headers=ctx.h).json()["detail"]["code"] == "warehouse_has_stock"
    empty = ctx.post("/warehouses", {"name": "Bo'sh"}).json()
    assert ctx.c.delete(f"/api/warehouses/{empty['id']}", headers=ctx.h).status_code == 204
    assert "Bo'sh" not in [x["name"] for x in ctx.get("/warehouses").json()]


def test_account_rules(ctx):
    a = ctx.post("/accounts", {"kind": "cash", "name_uz": "K3", "name_ru": "К3", "name_en": "Cash 3", "opening_balance": 1000}).json()
    assert a["balance"] == 1000
    bad = ctx.c.patch(f"/api/accounts/{a['id']}", json={"opening_balance": -5}, headers=ctx.h)
    assert bad.status_code == 409 and bad.json()["detail"]["code"] == "cash_negative"
    assert ctx.c.delete(f"/api/accounts/{a['id']}", headers=ctx.h).status_code == 409    # balance not zero
    ctx.c.patch(f"/api/accounts/{a['id']}", json={"opening_balance": 0}, headers=ctx.h)
    assert ctx.c.delete(f"/api/accounts/{a['id']}", headers=ctx.h).status_code == 204


def test_items_and_specs(ctx):
    unit = ctx.get("/units").json()[0]["id"]
    p = ctx.post("/items", {"kind": "product", "name_uz": "Plita X", "name_ru": "Плита X", "name_en": "Slab X", "unit_id": unit, "min_stock": 5})
    assert p.status_code == 201
    cement = ctx.items["Cement"]["id"]
    s = ctx.c.put(f"/api/specifications/{p.json()['id']}", json={"norms": [{"material_id": cement, "qty": 12.5}]}, headers=ctx.h)
    assert s.json() == {str(cement): 12.5}
    assert ctx.post("/items", {"kind": "product", "name_uz": "Plita X", "name_ru": "z", "name_en": "z", "unit_id": unit}).status_code == 409
    assert ctx.c.delete(f"/api/items/{p.json()['id']}", headers=ctx.h).status_code == 204
    # a material used in specifications cannot be removed
    assert ctx.c.delete(f"/api/items/{cement}", headers=ctx.h).status_code == 409


def test_partner_in_use_cannot_be_deleted(ctx):
    cus = ctx.customer()
    ctx.post("/orders", {"date": NOW, "customer_id": cus, "rows": [{"item_id": ctx.items["ФБС 24.4.6-Т"]["id"], "qty": 1, "price": 1}]})
    assert ctx.c.delete(f"/api/customers/{cus}", headers=ctx.h).status_code == 409
    other = ctx.customer("Free one")
    assert ctx.c.delete(f"/api/customers/{other}", headers=ctx.h).status_code == 204


def test_seed_is_repeatable_with_demo_users_and_admin_password(db_session, monkeypatch):
    """Docker runs the seed on every start; with demo users and ADMIN_PASSWORD both set it must not collide."""
    from app.core.config import settings
    from app.models import User
    from app.seed import seed
    monkeypatch.setattr(settings, "admin_password", "secret123")
    with db_session() as db:
        db.query(User).delete()
        db.commit()
        seed(db, demo_users=True)
        seed(db, demo_users=True)
        assert db.query(User).filter(User.username == "admin").count() == 1
        assert db.query(User).count() == 6


def test_reset_data_tool(ctx, db_session):
    from tests.conftest import scenario
    from app.models import Customer, FinDoc, Invoice, Item, StockBalance, Warehouse
    from app.tools.reset_data import reset
    scenario(ctx)
    with db_session() as s:
        out = reset(s)
        assert s.query(Invoice).count() == 0 and s.query(FinDoc).count() == 0 and s.query(Customer).count() == 0
        assert s.query(StockBalance).count() == 0
        assert s.query(Item).count() == 0 and s.query(Warehouse).count() == 0            # catalogue, stores and plants are gone
        assert out["warehouses"] == 5
    # the user builds their own: a plant, a material, a first receipt
    plant = ctx.post("/warehouses", {"name": "Mening zavodim", "is_workshop": True}).json()
    assert plant["is_workshop"] is True
    unit = [u for u in ctx.get("/units").json() if u["name"] == "kg"][0]["id"]
    mat = ctx.post("/items", {"kind": "material", "name_uz": "Sement", "name_ru": "Цемент", "name_en": "Cement", "unit_id": unit}).json()["id"]
    assert ctx.post("/receipts", {"date": "2026-10-12T10:00:00", "supplier_id": ctx.supplier("New"), "warehouse_id": plant["id"],
                                  "rows": [{"item_id": mat, "qty": 1, "price": 1}]}).json()["number"] == "PN-000001"


def test_security_headers(ctx):
    r = ctx.c.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "SAMEORIGIN"
    assert ctx.c.get("/api/units", headers=ctx.h).headers["cache-control"] == "no-store"


def test_frontend_not_stale(client):
    r = client.get("/")
    assert r.headers.get("cache-control") == "no-cache"
