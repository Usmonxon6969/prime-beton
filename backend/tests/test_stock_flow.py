from tests.conftest import NOW


def rc(ctx, sup, wh, rows):
    return ctx.post("/receipts", {"date": NOW, "supplier_id": sup, "warehouse_id": ctx.wh[wh]["id"], "rows": rows})


def test_catalogue_seeded(ctx):
    assert len(ctx.wh) == 5 and ctx.wh["Завод 1"]["is_workshop"] and not ctx.wh["Метал склад"]["is_workshop"]
    assert "Cement" in ctx.items and "ФБС 24.4.6-Т" in ctx.items
    assert len([i for i in ctx.items.values() if i["kind"] == "product"]) == 106 * 2 + 2


def test_receipt_adds_materials_and_products(ctx):
    sup = ctx.supplier()
    r = rc(ctx, sup, "Завод 1", [{"item_id": ctx.items["Cement"]["id"], "qty": 1000, "price": 1150},
                               {"item_id": ctx.items["ФБС 24.4.6-Т"]["id"], "qty": 20, "price": 420000}])
    assert r.status_code == 201, r.text
    assert r.json()["number"] == "PN-000001" and r.json()["total"] == 1000 * 1150 + 20 * 420000
    assert ctx.stock("Cement", "Завод 1") == 1000 and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 20


def test_numbers_increase(ctx):
    sup = ctx.supplier()
    item = ctx.items["Cement"]["id"]
    nums = [rc(ctx, sup, "Завод 1", [{"item_id": item, "qty": 1, "price": 1}]).json()["number"] for _ in range(3)]
    assert nums == ["PN-000001", "PN-000002", "PN-000003"]


def test_delete_receipt_reverts_stock_and_blocks_when_used(ctx):
    sup = ctx.supplier()
    cement = ctx.items["Cement"]["id"]
    r = rc(ctx, sup, "Завод 1", [{"item_id": cement, "qty": 600, "price": 1000}]).json()
    assert ctx.c.delete(f"/api/receipts/{r['id']}", headers=ctx.h).json()["status"] == "deleted"
    assert ctx.stock("Cement", "Завод 1") == 0
    ctx.c.post(f"/api/receipts/{r['id']}/restore", headers=ctx.h)
    assert ctx.stock("Cement", "Завод 1") == 600
    # use 520 of the cement in production (2 x 260), then the receipt can no longer be deleted
    for n in ("Crushed stone", "Sand", "Rebar"):
        rc(ctx, sup, "Завод 1", [{"item_id": ctx.items[n]["id"], "qty": 10000, "price": 1}])
    fbs = ctx.items["ФБС 24.4.6-Т"]["id"]
    made = ctx.post("/production", {"date": NOW, "warehouse_id": ctx.wh["Завод 1"]["id"], "rows": [{"item_id": fbs, "qty": 2}]})
    assert made.status_code == 201, made.text
    assert ctx.stock("Cement", "Завод 1") == 80
    blocked = ctx.c.delete(f"/api/receipts/{r['id']}", headers=ctx.h)
    assert blocked.status_code == 409 and blocked.json()["detail"]["code"] == "insufficient_stock"
    assert ctx.stock("Cement", "Завод 1") == 80          # untouched by the failed delete


def test_production_consumes_by_norms(ctx):
    sup = ctx.supplier()
    mats = {n: ctx.items[n]["id"] for n in ("Cement", "Crushed stone", "Sand", "Rebar")}
    sur = ctx.wh["Завод 1"]["id"]
    rc(ctx, sup, "Завод 1", [{"item_id": i, "qty": 10000, "price": 1} for i in mats.values()])
    fbs = ctx.items["ФБС 24.4.6-Т"]["id"]
    d = ctx.post("/production", {"date": NOW, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 10}]})
    assert d.status_code == 201, d.text
    assert d.json()["number"] == "PRD-000001"
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 10
    assert ctx.stock("Cement", "Завод 1") == 10000 - 2600          # 260 per unit
    assert ctx.stock("Crushed stone", "Завод 1") == 10000 - 7600
    assert {c["material_id"]: c["qty"] for c in d.json()["consumption"]}[mats["Cement"]] == 2600
    # editing to 5 returns half of the materials
    e = ctx.c.put(f"/api/production/{d.json()['id']}", json={"date": NOW, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 5}]}, headers=ctx.h)
    assert e.status_code == 200
    assert ctx.stock("Cement", "Завод 1") == 10000 - 1300 and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 5
    # deleting returns all materials and removes the products
    ctx.c.delete(f"/api/production/{d.json()['id']}", headers=ctx.h)
    assert ctx.stock("Cement", "Завод 1") == 10000 and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 0


def test_production_blocked_without_materials(ctx):
    fbs = ctx.items["ФБС 24.4.6-Т"]["id"]
    r = ctx.post("/production", {"date": NOW, "warehouse_id": ctx.wh["Завод 1"]["id"], "rows": [{"item_id": fbs, "qty": 1}]})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "insufficient_stock"
    assert ctx.get("/production").json() == []        # nothing half-saved


def _stocked(ctx, qty=50):
    sup = ctx.supplier()
    fbs = ctx.items["ФБС 24.4.6-Т"]["id"]
    rc(ctx, sup, "Завод 1", [{"item_id": fbs, "qty": qty, "price": 400000}])
    return fbs


def test_invoice_ships_stock_and_checks_availability(ctx):
    fbs, cus = _stocked(ctx), None
    cus = ctx.customer()
    sur = ctx.wh["Завод 1"]["id"]
    too_much = ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 60, "price": 420000}]})
    assert too_much.status_code == 409 and too_much.json()["detail"]["params"]["available"] == 50
    ok = ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 20, "price": 420000}]})
    assert ok.status_code == 201 and ok.json()["number"] == "RN-000001" and ok.json()["total"] == 8_400_000
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 30
    # edit 20 -> 45
    e = ctx.c.put(f"/api/invoices/{ok.json()['id']}", headers=ctx.h, json={"date": NOW, "customer_id": cus, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 45, "price": 420000}]})
    assert e.status_code == 200 and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 5
    # edit beyond stock fails and leaves stock unchanged
    f = ctx.c.put(f"/api/invoices/{ok.json()['id']}", headers=ctx.h, json={"date": NOW, "customer_id": cus, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 99, "price": 1}]})
    assert f.status_code == 409 and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 5
    ctx.c.delete(f"/api/invoices/{ok.json()['id']}", headers=ctx.h)
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 50


def test_invoice_against_order_limits_quantity(ctx):
    fbs = _stocked(ctx)
    cus, sur = ctx.customer(), ctx.wh["Завод 1"]["id"]
    o = ctx.post("/orders", {"date": NOW, "customer_id": cus, "rows": [{"item_id": fbs, "qty": 30, "price": 420000}]}).json()
    assert o["number"] == "ZK-000001" and o["state"] == "new"
    a = ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": sur, "order_id": o["id"], "rows": [{"item_id": fbs, "qty": 20, "price": 420000}]})
    assert a.status_code == 201
    assert ctx.get(f"/orders/{o['id']}").json()["state"] == "partial"
    assert ctx.get(f"/orders/{o['id']}/remaining").json() == {str(fbs): 10.0}
    b = ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": sur, "order_id": o["id"], "rows": [{"item_id": fbs, "qty": 11, "price": 420000}]})
    assert b.status_code == 409 and b.json()["detail"]["code"] == "over_order"
    ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": sur, "order_id": o["id"], "rows": [{"item_id": fbs, "qty": 10, "price": 420000}]})
    assert ctx.get(f"/orders/{o['id']}").json()["state"] == "shipped"
    # an order with delivery notes cannot be deleted, nor shrunk below what shipped
    assert ctx.c.delete(f"/api/orders/{o['id']}", headers=ctx.h).status_code == 409
    low = ctx.c.put(f"/api/orders/{o['id']}", headers=ctx.h, json={"date": NOW, "customer_id": cus, "rows": [{"item_id": fbs, "qty": 5, "price": 1}]})
    assert low.status_code == 409 and low.json()["detail"]["code"] == "order_below_shipped"


def test_invoice_rejects_materials(ctx):
    cus = ctx.customer()
    r = ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": ctx.wh["Завод 1"]["id"], "rows": [{"item_id": ctx.items["Cement"]["id"], "qty": 1, "price": 1}]})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "wrong_item_kind"


def test_editing_a_document_checks_only_the_final_balance(ctx):
    """Produce 10, ship 6: the production may drop to 8 (2 left) but not to 5 (would leave -1)."""
    sup, cus = ctx.supplier(), ctx.customer()
    sur = ctx.wh["Завод 1"]["id"]
    rc(ctx, sup, "Завод 1", [{"item_id": ctx.items[n]["id"], "qty": 100000, "price": 1} for n in ("Cement", "Crushed stone", "Sand", "Rebar")])
    fbs = ctx.items["ФБС 24.4.6-Т"]["id"]
    prod = ctx.post("/production", {"date": NOW, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 10}]}).json()
    inv = ctx.post("/invoices", {"date": NOW, "customer_id": cus, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 6, "price": 100}]})
    assert inv.status_code == 201, inv.text
    edit = lambda q: ctx.c.put(f"/api/production/{prod['id']}", headers=ctx.h,
                               json={"date": NOW, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": q}]})
    assert edit(8).status_code == 200
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 2
    bad = edit(5)
    assert bad.status_code == 409 and bad.json()["detail"]["code"] == "insufficient_stock"
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == 2          # the failed edit changed nothing
    assert ctx.stock("Cement", "Завод 1") == 100000 - 8 * 260


def test_product_without_specification_can_be_produced(ctx):
    """A specification is optional: such a product is simply added to stock and no material is consumed."""
    unit = ctx.get("/units").json()[0]["id"]
    p = ctx.post("/items", {"kind": "product", "name_uz": "Plita X", "name_ru": "Плита X", "name_en": "Slab X", "unit_id": unit, "min_stock": 0}).json()
    sur = ctx.wh["Завод 1"]["id"]
    d = ctx.post("/production", {"date": NOW, "warehouse_id": sur, "rows": [{"item_id": p["id"], "qty": 4}]})
    assert d.status_code == 201, d.text
    assert d.json()["consumption"] == [] and ctx.stock("Slab X", "Завод 1") == 4
    plan = ctx.get("/reports/center/plan").json()
    assert plan["rows"] == []                                  # nothing ordered, nothing to plan
