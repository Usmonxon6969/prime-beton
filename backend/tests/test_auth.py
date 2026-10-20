from tests.conftest import login


def test_login_and_me(client):
    h = login(client, "omborchi", "sklad123")
    me = client.get("/api/auth/me", headers=h).json()
    assert me["role"] == "wh" and me["home"] == "wh"
    assert me["levels"]["inv"] == 2 and me["levels"]["bank"] == 0


def test_wrong_password(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    assert r.status_code == 401 and r.json()["detail"]["code"] == "bad_login"


def test_requires_token(client):
    assert client.get("/api/items").status_code == 401


def test_roles_are_enforced_on_the_server(client):
    wh = login(client, "omborchi", "sklad123")
    assert client.get("/api/finance?kind=bank", headers=wh).status_code == 403   # no bank access
    assert client.post("/api/customers", json={"name": "X"}, headers=wh).status_code == 403   # view only for customers
    sales = login(client, "sotuv", "sotuv123")
    assert client.post("/api/customers", json={"name": "X"}, headers=sales).status_code == 201
    director = login(client, "direktor", "dir123")   # sees everything, edits nothing
    assert client.get("/api/orders", headers=director).status_code == 200
    assert client.post("/api/customers", json={"name": "Y"}, headers=director).status_code == 403


def test_only_admin_creates_users(client, admin):
    r = client.post("/api/auth/users", json={"username": "New", "password": "longenough1", "full_name": "N", "role": "sales"}, headers=admin)
    assert r.status_code == 201 and r.json()["username"] == "new"
    assert client.post("/api/auth/users", json={"username": "x", "password": "short", "full_name": "N", "role": "sales"}, headers=admin).status_code == 422
    h = login(client, "new", "longenough1")
    assert client.post("/api/auth/users", json={"username": "z", "password": "longenough1", "full_name": "N", "role": "sales"}, headers=h).status_code == 403
