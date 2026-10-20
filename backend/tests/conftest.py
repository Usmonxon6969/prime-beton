import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["FRONTEND_DIR"] = "/nonexistent"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.seed import seed

NOW = "2026-10-12T10:00:00"


def legacy(s):
    """The product and the store the test-suite was written around (no longer part of the seed)."""
    from decimal import Decimal
    from app.models import Item, Norm, Unit, Warehouse
    mats = {i.name_en: i for i in s.query(Item).filter(Item.kind == "material")}
    p = Item(kind="product", name_uz="ФБС 24.4.6-Т", name_ru="ФБС 24.4.6-Т", name_en="ФБС 24.4.6-Т", min_stock=Decimal(100),
             unit_id=s.query(Unit).filter(Unit.name == "dona").one().id)
    s.add(p)
    s.flush()
    for n, q in (("Cement", 260), ("Crushed stone", 760), ("Sand", 440)):
        s.add(Norm(product_id=p.id, material_id=mats[n].id, qty=Decimal(q)))
    for i, n in enumerate(["Завод 1", "Завод 2", "Завод 3", "Завод 4"]):
        s.add(Warehouse(name=n, is_workshop=True, sort_order=i))
    s.add(Warehouse(name="Метал склад", is_workshop=False, sort_order=99))
    s.commit()


@pytest.fixture()
def db_session():
    url = os.environ.get("TEST_DATABASE_URL")   # run the suite against PostgreSQL: TEST_DATABASE_URL=postgresql+psycopg://...
    if url:
        engine = create_engine(url)
        Base.metadata.drop_all(engine)
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        seed(s, demo_users=True, catalogue=True)
        legacy(s)
    yield Session
    engine.dispose()


@pytest.fixture()
def client(db_session):
    from app.core import throttle
    throttle.reset()
    def override():
        s = db_session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def login(client, user="admin", password="admin123"):
    r = client.post("/api/auth/login", json={"username": user, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


@pytest.fixture()
def admin(client):
    return login(client)


class Ctx:
    """Handy lookups used across tests."""

    def __init__(self, client, h):
        self.c, self.h = client, h
        self.items = {i["name_en"]: i for i in client.get("/api/items", headers=h).json()}
        self.wh = {w["name"]: w for w in client.get("/api/warehouses", headers=h).json()}
        self.accounts = client.get("/api/accounts", headers=h).json()

    def post(self, url, body):
        return self.c.post("/api" + url, json=body, headers=self.h)

    def get(self, url):
        return self.c.get("/api" + url, headers=self.h)

    def customer(self, name="Orient Stroy"):
        return self.post("/customers", {"name": name}).json()["id"]

    def supplier(self, name="Klinets Supply"):
        return self.post("/suppliers", {"name": name}).json()["id"]

    def stock(self, item_name, wh_name):
        it = self.get("/items").json()
        for i in it:
            if i["name_en"] == item_name:
                return i["stock"].get(str(self.wh[wh_name]["id"]), 0)


@pytest.fixture()
def ctx(client, admin):
    return Ctx(client, admin)


def scenario(ctx):
    """A small, known business: materials bought, 5 blocks made, 3 shipped, partly paid, one tax payment."""
    sup, cus = ctx.supplier("Cement Trade"), ctx.customer("Orient Stroy")
    sur = ctx.wh["Завод 1"]["id"]
    I = ctx.items
    ctx.post("/receipts", {"date": "2026-09-01T09:00:00", "supplier_id": sup, "warehouse_id": sur, "rows": [
        {"item_id": I["Cement"]["id"], "qty": 5000, "price": 1000}, {"item_id": I["Crushed stone"]["id"], "qty": 10000, "price": 100},
        {"item_id": I["Sand"]["id"], "qty": 8000, "price": 50}, {"item_id": I["Rebar"]["id"], "qty": 1000, "price": 9000}]})
    fbs = I["ФБС 24.4.6-Т"]["id"]
    ctx.post("/production", {"date": "2026-09-05T09:00:00", "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 5}]})
    ctx.post("/invoices", {"date": "2026-09-10T09:00:00", "customer_id": cus, "warehouse_id": sur, "rows": [{"item_id": fbs, "qty": 3, "price": 500000}]})
    bank = [a for a in ctx.accounts if a["kind"] == "bank"][0]
    ctx.post("/finance", {"date": "2026-09-12T09:00:00", "kind": "in", "account_id": bank["id"], "article": "cust", "customer_id": cus, "amount": 600000})
    ctx.post("/finance", {"date": "2026-09-13T09:00:00", "kind": "out", "account_id": bank["id"], "article": "tax", "party": "Soliq", "amount": 100000})
    return {"sup": sup, "cus": cus, "fbs": fbs, "sur": sur}
