#!/usr/bin/env python3
"""Load test: fills a TEST copy of the system with thousands of documents through the real API, then times the screens.

   python ops/loadtest.py --url http://127.0.0.1:8000 --user admin --password '...' --docs 4000

NEVER point it at your real data - it creates thousands of fake customers, orders, invoices and payments.
Needs: pip install httpx.  The server needs the product catalogue (SEED_CATALOGUE=true on first start).
"""
import argparse, random, statistics, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import httpx

ap = argparse.ArgumentParser()
ap.add_argument("--url", default="http://127.0.0.1:8000")
ap.add_argument("--user", default="admin")
ap.add_argument("--password", required=True)
ap.add_argument("--docs", type=int, default=4000, help="orders; the same number of invoices, and payments, are created too")
ap.add_argument("--measure-only", action="store_true", help="do not create data, only time the screens on what is already there")
ap.add_argument("--threads", type=int, default=6)
ap.add_argument("--budget", type=float, default=1.5, help="seconds a screen may take before it is reported as slow")
a = ap.parse_args()

c = httpx.Client(base_url=a.url + "/api", timeout=120)
r = c.post("/auth/login", json={"username": a.user, "password": a.password})
r.raise_for_status()
H = {"Authorization": "Bearer " + r.json()["access_token"]}
c.headers.update(H)
rnd = random.Random(7)


def get(p, **kw):
    r = c.get(p, **kw); r.raise_for_status(); return r.json()


def post(p, body):
    r = c.post(p, json=body)
    if r.status_code >= 300:
        raise RuntimeError(f"{p} {r.status_code} {r.text[:200]}")
    return r.json()


items = get("/items")
products = [i for i in items if i["kind"] == "product"]
materials = [i for i in items if i["kind"] == "material"]
whs = get("/warehouses")
if not whs:
    whs = [post("/warehouses", {"name": "Load plant", "is_workshop": True})]
shop = whs[0]   # one warehouse is enough for the test
accounts = get("/accounts")
cash = next(x for x in accounts if x["kind"] == "cash")
assert products and materials, "no catalogue: start the server once with SEED_CATALOGUE=true"
print(f"catalogue: {len(products)} products, {len(materials)} materials")

if a.measure_only:
    custs = [x["id"] for x in get("/customers")][:5]
else:
    t0 = time.time()
    ncust = max(50, a.docs // 20)
    with ThreadPoolExecutor(a.threads) as ex:
        custs = list(ex.map(lambda i: post("/customers", {"name": f"Load customer {i}", "phone": "+998"})["id"], range(ncust)))
        sups = list(ex.map(lambda i: post("/suppliers", {"name": f"Load supplier {i}"})["id"], range(max(10, ncust // 5))))
    day0 = datetime(2026, 1, 1)
    def when(i): return (day0 + timedelta(minutes=i * 60 * 24 * 280 // max(a.docs, 1) // 60)).isoformat()

    # stock first: a few huge receipts and production runs so that sales never run out
    for m in materials:
        post("/receipts", {"date": day0.isoformat(), "supplier_id": sups[0], "warehouse_id": shop["id"],
                           "rows": [{"item_id": m["id"], "qty": 50_000_000_000, "price": 1000}]})
    for p in products:
        try:
            post("/production", {"date": day0.isoformat(), "warehouse_id": shop["id"], "rows": [{"item_id": p["id"], "qty": a.docs * 90 // len(products) + 100}]})
        except RuntimeError as e:
            print("production skipped:", str(e)[:120])


    def order(i):
        rows = [{"item_id": rnd.choice(products)["id"], "qty": rnd.randint(1, 20), "price": rnd.randint(50, 900) * 1000} for _ in range(rnd.randint(1, 5))]
        o = post("/orders", {"date": when(i), "customer_id": rnd.choice(custs), "rows": rows})
        if i % 3:                                    # two thirds are shipped (some partly), the rest stay open
            part = rows if i % 3 == 1 else rows[:1]
            post("/invoices", {"date": when(i), "customer_id": o["customer_id"], "warehouse_id": shop["id"], "order_id": o["id"], "rows": part})
        if i % 2:
            post("/finance", {"date": when(i), "kind": "in", "account_id": cash["id"], "article": "cust", "customer_id": o["customer_id"],
                              "amount": rnd.randint(1, 50) * 1_000_000})
        if i % 7 == 0:
            post("/receipts", {"date": when(i), "supplier_id": rnd.choice(sups), "warehouse_id": shop["id"],
                               "rows": [{"item_id": rnd.choice(materials)["id"], "qty": rnd.randint(10, 500), "price": 1000}]})

    t = time.time()
    with ThreadPoolExecutor(a.threads) as ex:
        list(ex.map(order, range(a.docs)))
    print(f"created {a.docs} orders (+invoices, payments, receipts) in {time.time()-t:.0f}s  ({a.docs/(time.time()-t):.1f} orders/s)")


rows = []
def timed(name, path, **kw):
    ts = []
    for _ in range(3):
        s = time.time(); r = c.get(path, **kw); ts.append(time.time() - s)
        if r.status_code >= 300:
            rows.append((name, None, r.status_code, 0)); return
    rows.append((name, statistics.median(ts), r.status_code, len(r.content)))

timed("Orders (all)", "/orders")
timed("Orders (one customer)", f"/orders?customer_id={custs[0]}")
timed("Invoices (all)", "/invoices")
timed("Receipts (all)", "/receipts")
timed("Production (all)", "/production")
timed("Bank / cash (all)", "/finance?kind=cash")
timed("Dashboard", "/reports/dashboard?days=14")
timed("Dashboard 60 days", "/reports/dashboard?days=60")
timed("Customer debts", "/reports/customer-debts")
timed("Supplier debts", "/reports/supplier-debts")
timed("Customer statement", f"/reports/customers/{custs[0]}/statement")
for n in ("turnover", "sales", "purchases", "cashflow", "profit", "debts", "plan", "plan_materials"):
    timed(f"Report centre: {n}", f"/reports/center/{n}")
timed("Items", "/items")
timed("AI signals", "/ai/insights")
timed("Journal", "/audit")
ids = get("/invoices")
timed("PDF invoice", f"/reports/print/invoice/{ids[0]['id']}.pdf")
timed("PDF statement", f"/reports/print/statement.pdf?customer_id={custs[0]}")

print(f"\n{'screen':28}{'seconds':>9}{'KB':>8}  status")
bad = 0
for n, s, st, ln in rows:
    slow = s is None or s > a.budget
    bad += slow
    print(f"{n:28}{('-' if s is None else f'{s:.2f}'):>9}{ln/1024:>8.0f}  {'HTTP '+str(st) if st>=300 else ('SLOW' if slow else 'ok')}")
print(f"\n{bad} of {len(rows)} screens over {a.budget}s or failing")
sys.exit(1 if bad else 0)
