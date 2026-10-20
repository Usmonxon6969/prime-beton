from tests.conftest import login


def test_audit_records_create_edit_delete(ctx):
    cid = ctx.customer("Audit Co")
    r = ctx.c.put(f"/api/customers/{cid}", json={"name": "Audit Co 2", "phone": "1"}, headers=ctx.h)
    assert r.status_code == 200
    ctx.c.delete(f"/api/customers/{cid}", headers=ctx.h)
    rows = ctx.get("/audit?entity=customers").json()["rows"]
    acts = [x["action"] for x in rows]
    assert "create" in acts and "update" in acts and "delete" in acts
    assert all(x["user"] == "admin" for x in rows)
    upd = next(x for x in rows if x["action"] == "update")
    assert upd["changes"]["name"] == ["Audit Co", "Audit Co 2"]


def test_audit_document_rows_and_restore(ctx):
    sup = ctx.supplier()
    it = ctx.items["Cement"]
    body = {"date": "2026-10-01T10:00:00", "supplier_id": sup, "warehouse_id": ctx.wh["Метал склад"]["id"],
            "rows": [{"item_id": it["id"], "qty": 10, "price": 5}]}
    r = ctx.post("/receipts", body)
    assert r.status_code == 201, r.text
    rid = r.json()["id"]
    body["rows"][0]["qty"] = 20
    assert ctx.c.put(f"/api/receipts/{rid}", json=body, headers=ctx.h).status_code == 200
    rows = ctx.get(f"/audit?entity=receipts&entity_id={rid}").json()["rows"]
    assert any(x["action"] == "create" for x in rows)
    assert any(x["action"] == "update" and x["changes"] == {"rows": True} for x in rows)
    ctx.c.delete(f"/api/receipts/{rid}", headers=ctx.h)
    ctx.c.post(f"/api/receipts/{rid}/restore", headers=ctx.h)
    acts = [x["action"] for x in ctx.get(f"/audit?entity=receipts&entity_id={rid}").json()["rows"]]
    assert "delete" in acts and "restore" in acts
    # stock tables are never logged
    assert ctx.get("/audit?entity=stock_moves").json()["total"] == 0


def test_audit_needs_settings_access(client):
    h = login(client, "buxgalter", "buh123")
    assert client.get("/api/audit", headers=h).status_code == 403


def test_audit_is_for_the_owner_only(client, admin):
    client.post("/api/auth/users", json={"username": "adm2", "password": "longenough1", "full_name": "Second", "role": "admin"}, headers=admin)
    h = login(client, "adm2", "longenough1")
    r = client.get("/api/audit", headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "owner_only"
    assert client.get("/api/audit", headers=admin).status_code == 200


def test_login_lockout(client):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"username": "sotuv", "password": "bad"}).status_code == 401
    r = client.post("/api/auth/login", json={"username": "sotuv", "password": "sotuv123"})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "too_many_attempts"


def test_user_admin_and_password(client, admin):
    r = client.post("/api/auth/users", json={"username": "newbie", "password": "longenough1", "full_name": "N", "role": "wh"}, headers=admin)
    uid = r.json()["id"]
    r = client.patch(f"/api/auth/users/{uid}", json={"role": "sales", "password": "anotherpass1"}, headers=admin)
    assert r.status_code == 200 and r.json()["role"] == "sales"
    h = login(client, "newbie", "anotherpass1")
    assert client.post("/api/auth/password", json={"old_password": "x", "new_password": "abcdefghij1"}, headers=h).status_code == 422
    assert client.post("/api/auth/password", json={"old_password": "anotherpass1", "new_password": "abcdefghij1"}, headers=h).status_code == 204
    login(client, "newbie", "abcdefghij1")
    client.patch(f"/api/auth/users/{uid}", json={"is_active": False}, headers=admin)
    assert client.post("/api/auth/login", json={"username": "newbie", "password": "abcdefghij1"}).status_code == 401


def test_last_admin_protected(client, admin):
    me = client.get("/api/auth/me", headers=admin).json()
    r = client.patch(f"/api/auth/users/{me['id']}", json={"role": "director"}, headers=admin)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "last_admin"


def test_main_administrator_is_invisible_and_untouchable_for_other_admins(client, admin):
    owner_id = client.get("/api/auth/me", headers=admin).json()["id"]
    client.post("/api/auth/users", json={"username": "second", "password": "Strong-pass-123", "full_name": "Second", "role": "admin"}, headers=admin)
    other = login(client, "second", "Strong-pass-123")
    seen = [u["username"] for u in client.get("/api/auth/users", headers=other).json()]
    assert "second" in seen and "admin" not in seen                                                          # not in the list
    assert "admin" in [u["username"] for u in client.get("/api/auth/users", headers=admin).json()]            # the owner sees everybody
    for body in ({"password": "Another-pass-123"}, {"is_active": False}, {"role": "wh"}, {"full_name": "X"}):
        assert client.patch(f"/api/auth/users/{owner_id}", json=body, headers=other).status_code == 404       # as if it did not exist
    assert login(client)                                                                                      # the password still works
    assert client.patch(f"/api/auth/users/{owner_id}", json={"role": "wh"}, headers=admin).status_code == 409  # not even the owner can lock himself out
    assert client.patch(f"/api/auth/users/{owner_id}", json={"full_name": "Boss"}, headers=admin).status_code == 200


def test_reset_owner_recovers_the_main_administrator(client, admin, db_session):
    from app.core.security import hash_password
    from app.models import User
    from app.tools import reset_owner as ro
    client.post("/api/auth/users", json={"username": "second", "password": "Strong-pass-123", "full_name": "S", "role": "admin"}, headers=admin)
    with db_session() as db:
        o = db.query(User).filter(User.is_owner).one()
        o.is_active, o.role, o.totp_enabled = False, "wh", True
        db.commit()
        for weak in ("short1", "alllettersnodigit", "admin123456"):
            try:
                ro.recover(db, weak)
                assert False, weak
            except SystemExit:
                pass
        pw = ro.generate()
        ro.recover(db, pw, reset_2fa=True)
        o = db.query(User).filter(User.is_owner).one()
        assert o.is_active and o.role == "admin" and not o.totp_enabled
        try:
            ro.recover(db, pw, username="second")                      # another account is refused unless it is named the owner
            assert False
        except SystemExit:
            pass
        ro.recover(db, pw, username="second", make_owner=True)
        assert db.query(User).filter(User.is_owner).one().username == "second"
    assert login(client, "second", pw)
