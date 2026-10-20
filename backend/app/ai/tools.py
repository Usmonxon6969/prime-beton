"""Read-only tools the model may call. Every tool checks the signed-in user's section levels, so the assistant can
never reveal more than the user could open on screen. Tools return compact JSON-able data."""
import json
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai import insights
from app.models import Account, Customer, FinDoc, Invoice, Item, Order, ProductionDoc, Receipt, StockBalance, Supplier, Warehouse
from app.services import analytics, finance, reports


def _date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s)[:19])
    except ValueError:
        return None


class Ctx:
    def __init__(self, db: Session, levels: dict, lang: str, now: datetime | None = None):
        self.db, self.levels, self.lang, self.now = db, levels, lang, now or datetime.now()

    def ok(self, *sections):
        return all(self.levels.get(s, 0) >= 1 for s in sections)

    def any(self, *sections):
        return any(self.levels.get(s, 0) >= 1 for s in sections)

    def name(self, it: Item):
        return getattr(it, "name_" + (self.lang if self.lang in ("uz", "ru", "en") else "en"))


def _like(q, *cols):
    return or_(*[c.ilike(f"%{q}%") for c in cols])


def get_stock(c: Ctx, query: str = "", warehouse: str = "", kind: str = ""):
    q = c.db.query(Item).filter(Item.is_active)
    if kind in ("product", "material"):
        q = q.filter(Item.kind == kind)
    if query:
        q = q.filter(_like(query, Item.name_uz, Item.name_ru, Item.name_en))
    whs = {w.id: w for w in c.db.query(Warehouse)}
    note = None
    if warehouse:
        hit = {i: w for i, w in whs.items() if warehouse.lower() in w.name.lower()}
        if hit:
            whs = hit
        else:   # the user may write the name in another script (Zavod vs Завод): show every warehouse and let the model pick
            note = "No warehouse matches that text; all warehouses are shown. Pick the right one by name."
    bal: dict = {}
    for b in c.db.query(StockBalance).filter(StockBalance.qty != 0):
        if b.warehouse_id in whs:
            bal.setdefault(b.item_id, {})[whs[b.warehouse_id].name] = float(b.qty)
    out = []
    for it in q.order_by(Item.kind, Item.name_en).limit(400):
        per = bal.get(it.id, {})
        if query or per:
            out.append({"item": c.name(it), "kind": it.kind, "unit": it.unit.name, "total": round(sum(per.values()), 3),
                        "minimum": float(it.min_stock), "by_warehouse": per})
    res = {"items": out[:60], "count": len(out), "warehouses": [w.name for w in whs.values()]}
    if note:
        res["note"] = note
    return res


def get_dashboard(c: Ctx, days: int = 14):
    return reports.dashboard(c.db, c.levels, max(7, min(int(days or 14), 60)))


def get_insights(c: Ctx):
    return [{"severity": i["severity"], "text": i["text"], "kind": i["kind"]} for i in insights.collect(c.db, c.levels, c.lang, c.now)]


def run_report(c: Ctx, name: str, start: str = "", end: str = "", group: str = "", who: str = "customer", kind: str = "", warehouse: str = ""):
    if not analytics.allowed(c.levels, name, who):
        return {"error": "forbidden", "message": "This report is not available for the user's role."}
    wid = None
    if warehouse:
        w = c.db.query(Warehouse).filter(Warehouse.name.ilike(f"%{warehouse}%")).first()
        wid = w.id if w else None
    t = analytics.run(c.db, name, start=_date(start), end=_date(end), group=group or None, warehouse_id=wid, kind=kind or None,
                      who=who, lang=c.lang, levels=c.levels)
    t["rows"] = t["rows"][:80]
    return {"report": name, "columns": [x["key"] for x in t["columns"]], "rows": t["rows"], "totals": t["totals"]}


def get_account_balances(c: Ctx):
    if not c.any("bank", "cash"):
        return {"error": "forbidden"}
    bal = finance.balances(c.db)
    return [{"name": getattr(a, "name_" + (c.lang if c.lang in ("uz", "ru", "en") else "en")), "kind": a.kind, "balance": float(bal[a.id])}
            for a in c.db.query(Account).filter(Account.is_active) if c.levels.get(a.kind)]


def customer_statement(c: Ctx, customer: str, start: str = "", end: str = ""):
    if not c.ok("cus"):
        return {"error": "forbidden"}
    cu = c.db.query(Customer).filter(Customer.name.ilike(f"%{customer}%")).first()
    if not cu:
        return {"error": "not_found", "message": "No customer with that name"}
    st = reports.statement(c.db, customer_id=cu.id, supplier_id=None, start=_date(start), end=_date(end))
    st["rows"] = [{**r, "date": r["date"].date().isoformat()} for r in st["rows"]][-40:]
    return {"customer": cu.name, **st}


def supplier_statement(c: Ctx, supplier: str, start: str = "", end: str = ""):
    if not c.ok("sup"):
        return {"error": "forbidden"}
    s = c.db.query(Supplier).filter(Supplier.name.ilike(f"%{supplier}%")).first()
    if not s:
        return {"error": "not_found", "message": "No supplier with that name"}
    st = reports.statement(c.db, customer_id=None, supplier_id=s.id, start=_date(start), end=_date(end))
    st["rows"] = [{**r, "date": r["date"].date().isoformat()} for r in st["rows"]][-40:]
    return {"supplier": s.name, **st}


def list_documents(c: Ctx, kind: str, limit: int = 10, party: str = "", since: str = ""):
    limit = max(1, min(int(limit or 10), 30))
    sec = {"invoice": "inv", "receipt": "rec", "order": "ord", "production": "prod", "payment": None}.get(kind, "-")
    if sec == "-" or (sec and not c.ok(sec)) or (sec is None and not c.any("bank", "cash")):
        return {"error": "forbidden"}
    since_d = _date(since)
    out = []
    if kind == "payment":
        accs = {a.id: a for a in c.db.query(Account)}
        q = c.db.query(FinDoc).filter(FinDoc.status == "posted").order_by(FinDoc.date.desc())
        for f in q.limit(200):
            a = accs.get(f.account_id)
            if a is None or not c.levels.get(a.kind) or (since_d and f.date < since_d):
                continue
            if party and party.lower() not in (f.party or "").lower():
                cu = c.db.get(Customer, f.customer_id) if f.customer_id else None
                su = c.db.get(Supplier, f.supplier_id) if f.supplier_id else None
                if not any(x and party.lower() in x.name.lower() for x in (cu, su)):
                    continue
            out.append({"number": f.number, "date": f.date.isoformat(), "kind": f.kind, "article": f.article, "amount": float(f.amount), "party": f.party})
            if len(out) >= limit:
                break
        return out
    model = {"invoice": Invoice, "receipt": Receipt, "order": Order, "production": ProductionDoc}[kind]
    partner = {"invoice": (Customer, "customer_id"), "order": (Customer, "customer_id"), "receipt": (Supplier, "supplier_id")}.get(kind)
    names = {p.id: p.name for p in c.db.query(partner[0])} if partner else {}
    for d in c.db.query(model).filter(model.status != "deleted").order_by(model.date.desc()).limit(300):
        if since_d and d.date < since_d:
            continue
        who = names.get(getattr(d, partner[1])) if partner else ""
        if party and party.lower() not in (who or "").lower():
            continue
        row = {"number": d.number, "date": d.date.isoformat(), "party": who}
        if hasattr(d.rows[0] if d.rows else None, "price"):
            row["total"] = float(sum((r.qty * r.price for r in d.rows), Decimal(0)))
        row["lines"] = len(d.rows)
        out.append(row)
        if len(out) >= limit:
            break
    return out


DATE = {"type": "string", "description": "ISO date or datetime, e.g. 2026-09-01"}
TOOLS = [
    ("get_stock", "Current stock of products and materials per warehouse. Use for 'how much X is left'.", {
        "query": {"type": "string", "description": "part of the item name in any language"}, "warehouse": {"type": "string"},
        "kind": {"type": "string", "enum": ["product", "material"]}}, [], get_stock, ("wh",)),
    ("get_dashboard", "Headline numbers: sales for 30 days, receivables, payables, bank and cash totals, open orders, low stock, daily series.", {
        "days": {"type": "integer"}}, [], get_dashboard, ()),
    ("get_insights", "Automatic signals: stock-out forecast, slow movers, overdue debts, sales trend, cash forecast, anomalies.", {}, [], get_insights, ()),
    ("run_report", "Business report. name: turnover (stock movement by item), sales, purchases, cashflow, profit (estimated), debts, plan (what to produce for open orders), plan_materials (raw material need vs stock, shortages). "
     "group: sales=customer|item|day|month, purchases=supplier|item|day|month, cashflow=article|day|account. who=customer|supplier for debts.", {
        "name": {"type": "string", "enum": ["turnover", "sales", "purchases", "cashflow", "profit", "debts", "plan", "plan_materials"]}, "start": DATE, "end": DATE,
        "group": {"type": "string"}, "who": {"type": "string", "enum": ["customer", "supplier"]}, "kind": {"type": "string", "enum": ["product", "material"]},
        "warehouse": {"type": "string"}}, ["name"], run_report, ()),
    ("get_account_balances", "Balances of bank accounts and cash desks.", {}, [], get_account_balances, ("bank|cash",)),
    ("customer_statement", "Reconciliation of a customer: shipments, payments, running debt.", {
        "customer": {"type": "string"}, "start": DATE, "end": DATE}, ["customer"], customer_statement, ("cus",)),
    ("supplier_statement", "Reconciliation of a supplier: purchases, payments, running debt.", {
        "supplier": {"type": "string"}, "start": DATE, "end": DATE}, ["supplier"], supplier_statement, ("sup",)),
    ("list_documents", "Recent documents. kind: invoice (delivery notes), receipt (purchases), order, production, payment.", {
        "kind": {"type": "string", "enum": ["invoice", "receipt", "order", "production", "payment"]}, "limit": {"type": "integer"},
        "party": {"type": "string"}, "since": DATE}, ["kind"], list_documents, ()),
]
BY_NAME = {t[0]: t for t in TOOLS}


def _can(levels: dict, secs) -> bool:
    return all(any(levels.get(x, 0) >= 1 for x in s.split("|")) for s in secs)


def available(levels: dict) -> list[dict]:
    """Tool definitions for the model: only those whose section the user can open."""
    out = []
    for name, desc, props, req, _fn, secs in TOOLS:
        if _can(levels, secs):
            out.append({"name": name, "description": desc, "input_schema": {"type": "object", "properties": props, "required": req}})
    return out


def execute(name: str, args: dict, c: Ctx) -> str:
    t = BY_NAME.get(name)
    if t is None or not _can(c.levels, t[5]):
        return json.dumps({"error": "forbidden", "message": "Tool not available for this user"})
    try:
        res = t[4](c, **(args or {}))
    except TypeError:
        return json.dumps({"error": "bad_arguments"})
    except Exception as e:     # a failing tool must not break the chat
        return json.dumps({"error": "tool_failed", "message": type(e).__name__})
    s = json.dumps(res, default=str, ensure_ascii=False)
    return s if len(s) < 24000 else s[:24000] + "…(truncated)"
