"""Reports center: turnover (oborotka), sales, purchases, cash flow, profit, debts.

Every report returns the same table shape so one screen, one Excel exporter and the AI tools can all use it:
    {"key", "columns": [{"key", "type"}], "rows": [dict], "totals": dict}
Column types: text, num (quantity), money, date, int.
"""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import bad
from app.models import (Account, Customer, FinDoc, Invoice, InvoiceRow, Item, ProductionConsumption, ProductionDoc,
                        ProductionRow, Receipt, ReceiptRow, StockAdjust, StockBalance, StockMove, Supplier, Warehouse)
from app.services import costing, payroll as pay, reports as base

LABELS = {  # key -> uz, ru, en
    "item": ("Pozitsiya", "Позиция", "Item"), "unit": ("Birlik", "Ед.", "Unit"),
    "kind": ("Turi", "Тип", "Kind"),
    "opening": ("Boshlang‘ich qoldiq", "Нач. остаток", "Opening"),
    "receipt": ("Kirim", "Приход", "Received"), "production": ("Ishlab chiqarildi", "Выпуск", "Produced"),
    "consumed": ("Sarflandi", "Расход в производство", "Consumed"), "shipped": ("Jo‘natildi", "Отгружено", "Shipped"),
    "closing": ("Oxirgi qoldiq", "Кон. остаток", "Closing"),
    "customer": ("Mijoz", "Покупатель", "Customer"), "supplier": ("Yetkazib beruvchi", "Поставщик", "Supplier"),
    "date": ("Sana", "Дата", "Date"), "month": ("Oy", "Месяц", "Month"),
    "docs": ("Hujjatlar", "Документов", "Documents"), "qty": ("Miqdor", "Кол-во", "Quantity"),
    "amount": ("Summa", "Сумма", "Amount"), "paid": ("To‘langan", "Оплачено", "Paid"), "debt": ("Qarz", "Долг", "Debt"),
    "bought": ("Xarid", "Закуплено", "Purchased"), "sold": ("Sotuv", "Отгружено на сумму", "Shipped value"),
    "article": ("Modda", "Статья", "Article"), "account": ("Hisob", "Счёт", "Account"),
    "in": ("Kirim", "Поступило", "Money in"), "out": ("Chiqim", "Выплачено", "Money out"), "net": ("Farq", "Итог", "Net"),
    "line": ("Ko‘rsatkich", "Показатель", "Line"),
    "ordered": ("Buyurtma", "Заказано", "Ordered"), "open_qty": ("Yetkazilmagan", "К отгрузке", "To ship"),
    "in_stock": ("Omborda", "На складе", "In stock"), "to_make": ("Ishlab chiqarish kerak", "Нужно произвести", "To produce"),
    "need": ("Kerak", "Нужно", "Needed"), "short": ("Yetishmaydi", "Не хватает", "Short"),
    "due": ("Muddat", "Срок", "Due"), "orders": ("Buyurtmalar", "Заказы", "Orders"),
    "balance": ("Qoldiq", "Остаток", "Balance"),
    "qty_in": ("Kirim", "Приход", "In"), "qty_out": ("Chiqim", "Расход", "Out"), "doc_type": ("Hujjat turi", "Тип документа", "Document type"),
    "doc": ("Hujjat", "Документ", "Document"), "warehouse": ("Ombor", "Склад", "Warehouse"),
    "daily": ("Kunlik sarf", "Расход в день", "Use per day"), "days_left": ("Necha kunga yetadi", "Хватит дней", "Days of cover"), "min_stock": ("Minimum", "Минимум", "Minimum"),
    "current": ("Muddati kelmagan", "Не просрочено", "Not due yet"), "d30": ("1–30 kun kechikkan", "Просрочено 1–30 дн.", "1–30 days late"),
    "d60": ("31–60 kun", "31–60 дн.", "31–60 days"), "d90": ("60+ kun", "60+ дн.", "60+ days"),
    "adjust": ("Inventarizatsiya / hisobdan chiqarish", "Инвентаризация / списание", "Counts / write-offs"),
    "good": ("Yaroqli", "Годных", "Good"), "scrap": ("Brak", "Брак", "Scrap"), "scrap_pct": ("Brak %", "Брак %", "Scrap %"),
    "reason": ("Sabab", "Причина", "Reason"), "cost": ("Tannarx", "Себестоимость", "Unit cost"), "price": ("Narx", "Цена", "Price"),
    "materials": ("Materiallar", "Материалы", "Materials"), "scrap_cost": ("Brak ulushi", "Доля брака", "Scrap share"),
    "labour": ("Ish haqi (donabay)", "Сдельная оплата", "Piece pay"), "margin": ("Marja", "Маржа", "Margin"), "margin_pct": ("Marja %", "Маржа %", "Margin %"),
    "revenue": ("Tushum", "Выручка", "Revenue"), "profit": ("Foyda", "Прибыль", "Profit"),
    "worker": ("Ishchi", "Работник", "Worker"), "position": ("Lavozim", "Должность", "Position"), "earned": ("Hisoblandi", "Начислено", "Earned"),
    "bonus": ("Mukofot / ushlanma", "Премии / удержания", "Bonus / deduction"), "owed": ("To‘lanishi kerak", "К выплате", "Owed"),
    "overdue": ("Muddati o‘tgan", "Просрочено всего", "Overdue"), "advance": ("Avans", "Аванс", "Advance"),
}
ARTICLES = {"cust": ("Mijozdan to‘lov", "Оплата от покупателя", "Customer payment"),
            "oin": ("Boshqa kirim", "Прочий приход", "Other income"),
            "sup": ("Yetkazib beruvchiga", "Поставщику", "Supplier payment"),
            "sal": ("Ish haqi", "Зарплата", "Salary"), "tax": ("Soliq", "Налоги", "Taxes"),
            "fee": ("Bank xizmati", "Комиссии банка", "Bank fees"), "oout": ("Boshqa chiqim", "Прочий расход", "Other expense")}
KINDS = {"product": ("Mahsulot", "Продукция", "Product"), "material": ("Material", "Материал", "Material")}
LANGS = {"uz": 0, "ru": 1, "en": 2}


def label(key: str, lang: str) -> str:
    return LABELS.get(key, (key, key, key))[LANGS.get(lang, 2)]


def _t(pair, lang):
    return pair[LANGS.get(lang, 2)]


def _name(it: Item, lang: str) -> str:
    return getattr(it, "name_" + (lang if lang in LANGS else "en"))


def _table(key, cols, rows, totals=None):
    return {"key": key, "columns": [{"key": k, "type": t} for k, t in cols], "rows": rows, "totals": totals or {}}


def _f(x) -> float:
    return round(float(x or 0), 3)


def _in(d, start, end):
    return (not start or d >= start) and (not end or d <= end)


def _amt(rows) -> Decimal:
    return sum((r.qty * r.price for r in rows), Decimal(0))


# ---------- turnover (oborotka) ----------
def turnover(db: Session, start, end, warehouse_id=None, kind=None, lang="en"):
    items = {i.id: i for i in db.query(Item)}
    acc = defaultdict(lambda: defaultdict(Decimal))

    def put(item_id, col, date, qty):
        if date is None or (end and date > end):
            return
        a = acc[item_id]
        if start and date < start:
            a["opening"] += qty if col in ("receipt", "production", "adjust") else -qty
        else:
            a[col] += qty

    wh = lambda d: warehouse_id is None or d.warehouse_id == warehouse_id   # noqa: E731
    for r in db.query(Receipt).filter(Receipt.status == "posted"):
        if wh(r):
            for x in r.rows:
                put(x.item_id, "receipt", r.date, x.qty)
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if wh(p):
            for x in p.rows:
                put(x.item_id, "production", p.date, x.qty)
            for c in p.consumption:
                put(c.material_id, "consumed", p.date, c.qty)
    for v in db.query(Invoice).filter(Invoice.status == "posted"):
        if wh(v):
            for x in v.rows:
                put(x.item_id, "shipped", v.date, x.qty)
    for v in db.query(StockAdjust).filter(StockAdjust.status == "posted"):
        if wh(v):
            for x in v.rows:
                put(x.item_id, "adjust", v.date, x.delta)
    rows = []
    for iid, a in acc.items():
        it = items.get(iid)
        if it is None or (kind and it.kind != kind):
            continue
        closing = a["opening"] + a["receipt"] + a["production"] + a["adjust"] - a["consumed"] - a["shipped"]
        if not any(a.values()) and closing == 0:
            continue
        rows.append({"item_id": it.id, "item": _name(it, lang), "kind": _t(KINDS[it.kind], lang), "unit": it.unit.name,
                     "opening": _f(a["opening"]), "receipt": _f(a["receipt"]), "production": _f(a["production"]),
                     "adjust": _f(a["adjust"]), "consumed": _f(a["consumed"]), "shipped": _f(a["shipped"]), "closing": _f(closing)})
    rows.sort(key=lambda r: (r["kind"], r["item"]))
    cols = [("item", "text"), ("kind", "text"), ("unit", "text")] + [(k, "num") for k in
            ("opening", "receipt", "production", "adjust", "consumed", "shipped", "closing")]
    return _table("turnover", cols, rows)


# ---------- movement of goods (dvijeniya tovarov): every document line that changed stock ----------
DOC_TYPES = {"production": ("Ishlab chiqarish", "Производство", "Production"), "receipt": ("Kirim nakladnoyi", "Поступление", "Receipt"),
             "invoice": ("Chiqim nakladnoyi", "Расходная накладная", "Delivery note"),
             "adjust": ("Inventarizatsiya / hisobdan chiqarish", "Инвентаризация / списание", "Stock count / write-off")}
MOVES_CAP = 5000


def movements(db: Session, start, end, warehouse_id=None, kind=None, item_id=None, doc=None, lang="en"):
    """One row per document line: date, document, item, warehouse, quantity in / out. The ledger holds an undo and a redo for every edited
    document, so lines are netted per document, item and warehouse (a deleted document nets to nothing and disappears).
    With one item chosen the table starts from its opening balance and carries a running balance."""
    from sqlalchemy import func
    q = db.query(StockMove.doc_type, StockMove.doc_id, StockMove.doc_number, StockMove.item_id, StockMove.warehouse_id,
                 func.sum(StockMove.delta), func.min(StockMove.created_at)).group_by(
        StockMove.doc_type, StockMove.doc_id, StockMove.doc_number, StockMove.item_id, StockMove.warehouse_id)
    if warehouse_id:
        q = q.filter(StockMove.warehouse_id == warehouse_id)
    if item_id:
        q = q.filter(StockMove.item_id == item_id)
    if doc:
        q = q.filter(StockMove.doc_type == doc)
    nets = [r for r in q if r[5] != 0]
    models = {"production": ProductionDoc, "receipt": Receipt, "invoice": Invoice, "adjust": StockAdjust}
    dates = {}
    for typ, model in models.items():
        ids = {r[1] for r in nets if r[0] == typ}
        if ids:
            dates[typ] = {i: d for i, d in db.query(model.id, model.date).filter(model.id.in_(ids))}
    items = {i.id: i for i in db.query(Item)}
    whs = {w.id: w.name for w in db.query(Warehouse)}
    ent = []
    for typ, did, number, iid, wid, net, first in nets:
        it = items.get(iid)
        if it is None or (kind and it.kind != kind):
            continue
        ent.append((dates.get(typ, {}).get(did) or first, typ, did, number, it, wid, net))
    ent.sort(key=lambda e: (e[0], e[2]))
    opening = sum((e[6] for e in ent if start and e[0] < start), Decimal(0))
    shown = [e for e in ent if _in(e[0], start, end)]
    truncated = len(shown) > MOVES_CAP
    shown = shown[-MOVES_CAP:] if truncated else shown
    one = bool(item_id)
    bal = opening
    if truncated and one:
        bal = opening + sum((e[6] for e in ent if _in(e[0], start, end)), Decimal(0)) - sum((e[6] for e in shown), Decimal(0))
    rows = []
    if one:
        first = ent[0][4] if ent else items.get(item_id)
        rows.append({"date": "", "doc_type": label("opening", lang), "doc": "", "item": _name(first, lang) if first else "", "unit": first.unit.name if first else "",
                     "warehouse": "", "qty_in": None, "qty_out": None, "balance": _f(bal)})
    t_in = t_out = Decimal(0)
    for d, typ, did, number, it, wid, net in shown:
        bal += net
        t_in += net if net > 0 else 0
        t_out += -net if net < 0 else 0
        rows.append({"date": d.strftime("%d.%m.%Y %H:%M"), "doc_type": _t(DOC_TYPES.get(typ, (typ,) * 3), lang), "doc": number, "item": _name(it, lang),
                     "unit": it.unit.name, "warehouse": whs.get(wid, ""), "qty_in": _f(net) if net > 0 else None, "qty_out": _f(-net) if net < 0 else None,
                     "balance": _f(bal) if one else None, "item_id": it.id, "doc_key": typ, "doc_id": did})
    cols = [("date", "text"), ("doc_type", "text"), ("doc", "text"), ("item", "text"), ("unit", "text"), ("warehouse", "text"), ("qty_in", "num"), ("qty_out", "num")]
    if one:
        cols.append(("balance", "num"))
    totals = {"qty_in": _f(t_in), "qty_out": _f(t_out)}
    if one:
        totals["balance"] = _f(bal)
    out = _table("movements", cols, rows, totals)
    out["truncated"] = truncated
    return out


# ---------- sales / purchases ----------
def _period(group, d: datetime):
    return d.date().isoformat() if group == "day" else d.strftime("%Y-%m")


def _doc_report(db, key, docs, rows_of, party_attr, party_label, start, end, group, lang):
    parties = {p.id: p.name for p in db.query(Customer if party_label == "customer" else Supplier)}
    items = {i.id: i for i in db.query(Item)}
    agg = defaultdict(lambda: {"docs": set(), "qty": Decimal(0), "amount": Decimal(0)})
    for d in docs:
        if not _in(d.date, start, end):
            continue
        for r in rows_of(d):
            k = {"customer": parties.get(getattr(d, party_attr)), "supplier": parties.get(getattr(d, party_attr)),
                 "item": _name(items[r.item_id], lang) if r.item_id in items else "?",
                 "day": _period("day", d.date), "month": _period("month", d.date)}[group]
            a = agg[k]
            a["docs"].add(d.id)
            a["qty"] += r.qty
            a["amount"] += r.qty * r.price
    rows = [{group: k, "docs": len(a["docs"]), "qty": _f(a["qty"]), "amount": _f(a["amount"])} for k, a in agg.items()]
    rows.sort(key=lambda r: (r[group] if group in ("day", "month") else -r["amount"]))
    tot = {"docs": sum(r["docs"] for r in rows), "amount": _f(sum(r["amount"] for r in rows))}
    first = {"customer": "customer", "supplier": "supplier", "item": "item", "day": "date", "month": "month"}[group]
    for r in rows:
        r[first] = r.pop(group)
    cols = [(first, "date" if group == "day" else "text"), ("docs", "int")]
    cols += [("qty", "num"), ("amount", "money")]
    return _table(key, cols, rows, tot)


def sales(db, start, end, group="customer", lang="en"):
    if group not in ("customer", "item", "day", "month"):
        raise bad("invalid", "Unknown grouping")
    return _doc_report(db, "sales", db.query(Invoice).filter(Invoice.status == "posted"), lambda d: d.rows,
                       "customer_id", "customer", start, end, group, lang)


def purchases(db, start, end, group="supplier", lang="en"):
    if group not in ("supplier", "item", "day", "month"):
        raise bad("invalid", "Unknown grouping")
    return _doc_report(db, "purchases", db.query(Receipt).filter(Receipt.status == "posted"), lambda d: d.rows,
                       "supplier_id", "supplier", start, end, group, lang)


# ---------- cash flow ----------
def cashflow(db, start, end, group="article", lang="en", levels=None):
    if group not in ("article", "day", "account"):
        raise bad("invalid", "Unknown grouping")
    accs = {a.id: a for a in db.query(Account)}
    allowed = {k for k in ("bank", "cash") if levels is None or levels.get(k)}
    agg = defaultdict(lambda: {"in": Decimal(0), "out": Decimal(0)})
    for f in db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind.in_(["in", "out"])):
        a = accs.get(f.account_id)
        if a is None or a.kind not in allowed or not _in(f.date, start, end):
            continue
        k = {"article": _t(ARTICLES[f.article], lang) if f.article in ARTICLES else f.article,
             "day": f.date.date().isoformat(), "account": getattr(a, "name_" + (lang if lang in LANGS else "en"))}[group]
        agg[k][f.kind] += f.amount
    rows = [{"k": k, "in": _f(v["in"]), "out": _f(v["out"]), "net": _f(v["in"] - v["out"])} for k, v in sorted(agg.items())]
    first = {"article": "article", "day": "date", "account": "account"}[group]
    for r in rows:
        r[first] = r.pop("k")
    tot = {"in": _f(sum(r["in"] for r in rows)), "out": _f(sum(r["out"] for r in rows))}
    tot["net"] = _f(tot["in"] - tot["out"])
    return _table("cashflow", [(first, "date" if group == "day" else "text"), ("in", "money"), ("out", "money"), ("net", "money")], rows, tot)


# ---------- losses, scrap, cost ----------
REASONS = {"": ("Inventarizatsiya", "Инвентаризация", "Stock count"), "scrap": ("Brak", "Брак", "Scrap"),
           "damage": ("Shikastlanish", "Повреждение", "Damage"), "loss": ("Yo‘qotish", "Потеря", "Loss"),
           "expired": ("Muddati o‘tgan", "Истёк срок", "Expired"), "other": ("Boshqa", "Другое", "Other")}


def _loss_lines(db, start, end):
    """(item_id, reason, lost qty) for posted write-offs and count shortages; surpluses count as negative loss."""
    out = []
    for a in db.query(StockAdjust).filter(StockAdjust.status == "posted"):
        if _in(a.date, start, end):
            for r in a.rows:
                if r.delta:
                    out.append((r.item_id, a.reason if a.kind == "writeoff" else "", -r.delta))
    return out


def losses_value(db, start, end) -> Decimal:
    cost = costing.item_costs(db, end)
    return sum((q * cost.get(i, Decimal(0)) for i, _, q in _loss_lines(db, start, end)), Decimal(0))


def losses(db, start, end, lang="en"):
    items = {i.id: i for i in db.query(Item)}
    cost = costing.item_costs(db, end)
    acc = defaultdict(Decimal)
    for i, reason, q in _loss_lines(db, start, end):
        acc[(i, reason)] += q
    rows = []
    for (i, reason), q in acc.items():
        it = items.get(i)
        c = cost.get(i, Decimal(0))
        rows.append({"item": _name(it, lang), "reason": _t(REASONS.get(reason, REASONS["other"]), lang), "qty": _f(q), "cost": _f(c), "amount": _f(q * c)})
    rows.sort(key=lambda r: -r["amount"])
    return _table("losses", [("item", "text"), ("reason", "text"), ("qty", "num"), ("cost", "money"), ("amount", "money")], rows,
                  {"amount": _f(sum(r["amount"] for r in rows))})


def production(db, start, end, group="item", warehouse_id=None, lang="en"):
    """What the plant made: good and spoiled units per product, plant, day or month (or per plant / day / month AND product)."""
    items = {i.id: i for i in db.query(Item)}
    whs = {w.id: w.name for w in db.query(Warehouse)}
    outer, _, inner = group.partition("_")
    if outer not in ("item", "warehouse", "day", "month") or inner not in ("", "item") or (outer == "item" and inner):
        outer, inner = "item", ""
    agg = defaultdict(lambda: {"docs": set(), "good": Decimal(0), "scrap": Decimal(0)})
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if not _in(p.date, start, end) or (warehouse_id is not None and p.warehouse_id != warehouse_id):
            continue
        for x in p.rows:
            nm = _name(items[x.item_id], lang) if x.item_id in items else "?"
            k = ({"item": nm, "warehouse": whs.get(p.warehouse_id, "?"), "day": _period("day", p.date), "month": _period("month", p.date)}[outer],
                 nm if inner else "")
            a = agg[k]
            a["docs"].add(p.id)
            a["good"] += x.qty
            a["scrap"] += x.scrap
    first = {"item": "item", "warehouse": "warehouse", "day": "date", "month": "month"}[outer]
    rows = []
    for (k, nm), a in agg.items():
        r = {first: k}
        if inner:
            r["item"] = nm
        r.update({"good": _f(a["good"]), "scrap": _f(a["scrap"])})
        rows.append(r)
    rows.sort(key=lambda r: (r[first], -r["good"]) if outer in ("day", "month", "warehouse") else (-r["good"],))
    tg, tb = sum(r["good"] for r in rows), sum(r["scrap"] for r in rows)
    tot = {"good": _f(tg), "scrap": _f(tb)}
    cols = [(first, "date" if outer == "day" else "text")] + ([("item", "text")] if inner else [])
    return _table("production", cols + [("good", "num"), ("scrap", "num")], rows, tot)


def scrap(db, start, end, warehouse_id=None, lang="en"):
    items = {i.id: i for i in db.query(Item)}
    good, bad_ = defaultdict(Decimal), defaultdict(Decimal)
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if _in(p.date, start, end) and (warehouse_id is None or p.warehouse_id == warehouse_id):
            for x in p.rows:
                good[x.item_id] += x.qty
                bad_[x.item_id] += x.scrap
    cost = costing.unit_costs(db, end)
    rows = []
    for i in good:
        g, b = good[i], bad_[i]
        if not (g or b):
            continue
        unit = cost.get(i, {}).get("materials", Decimal(0)) + cost.get(i, {}).get("labour", Decimal(0))
        rows.append({"item": _name(items[i], lang), "good": _f(g), "scrap": _f(b), "scrap_pct": _f(b * 100 / (g + b)), "amount": _f(b * unit)})
    rows.sort(key=lambda r: -r["scrap_pct"])
    tg, tb = sum(r["good"] for r in rows), sum(r["scrap"] for r in rows)
    return _table("scrap", [("item", "text"), ("good", "num"), ("scrap", "num"), ("scrap_pct", "num"), ("amount", "money")], rows,
                  {"good": _f(tg), "scrap": _f(tb), "scrap_pct": _f(tb * 100 / (tg + tb)) if tg + tb else 0, "amount": _f(sum(r["amount"] for r in rows))})


def cost_sheet(db, end=None, lang="en"):
    items = {i.id: i for i in db.query(Item)}
    sold_q, sold_v = defaultdict(Decimal), defaultdict(Decimal)
    for v in db.query(Invoice).filter(Invoice.status == "posted"):
        for x in v.rows:
            sold_q[x.item_id] += x.qty
            sold_v[x.item_id] += x.qty * x.price
    active = set(costing.scrap_rates(db, end)) | set(sold_q) | set(costing.labour_rates(db))      # products made, sold or paid by the piece
    rows = []
    for pid, c in costing.unit_costs(db, end).items():
        it = items.get(pid)
        if it is None or it.kind != "product" or pid not in active:
            continue
        price = sold_v[pid] / sold_q[pid] if sold_q[pid] else Decimal(0)
        margin = price - c["total"]
        rows.append({"item": _name(it, lang), "materials": _f(c["materials"]), "scrap_cost": _f(c["scrap"]), "labour": _f(c["labour"]),
                     "cost": _f(c["total"]), "price": _f(price), "margin": _f(margin), "margin_pct": _f(margin * 100 / price) if price else 0})
    rows.sort(key=lambda r: r["item"])
    cols = [("item", "text")] + [(k, "money") for k in ("materials", "scrap_cost", "labour", "cost", "price", "margin")] + [("margin_pct", "num")]
    return _table("cost", cols, rows)


def profit_products(db, start, end, lang="en"):
    items = {i.id: i for i in db.query(Item)}
    cost = costing.unit_costs(db, end)
    q, v = defaultdict(Decimal), defaultdict(Decimal)
    for inv in db.query(Invoice).filter(Invoice.status == "posted"):
        if _in(inv.date, start, end):
            for x in inv.rows:
                q[x.item_id] += x.qty
                v[x.item_id] += x.qty * x.price
    rows = []
    for i in q:
        it = items.get(i)
        unit = cost.get(i, {}).get("total")
        if unit is None:                                   # bought goods: their purchase price
            unit = costing.avg_prices(db, end).get(i, Decimal(0))
        c = q[i] * unit
        rows.append({"item": _name(it, lang), "qty": _f(q[i]), "revenue": _f(v[i]), "cost": _f(c), "profit": _f(v[i] - c),
                     "margin_pct": _f((v[i] - c) * 100 / v[i]) if v[i] else 0})
    rows.sort(key=lambda r: -r["profit"])
    tr, tc = sum(r["revenue"] for r in rows), sum(r["cost"] for r in rows)
    return _table("profit_products", [("item", "text"), ("qty", "num"), ("revenue", "money"), ("cost", "money"), ("profit", "money"), ("margin_pct", "num")], rows,
                  {"revenue": _f(tr), "cost": _f(tc), "profit": _f(tr - tc), "margin_pct": _f((tr - tc) * 100 / tr) if tr else 0})


def payroll_report(db, start, end, lang="en"):
    st = pay.statement(db, start, end)
    rows = [{"worker": r["name"], "position": r["position"], "earned": r["earned"], "bonus": r["adjust"], "paid": r["paid"], "owed": r["owed"]} for r in st["rows"]]
    if st["unassigned"]:
        rows.append({"worker": {"uz": "Brigada ko‘rsatilmagan", "ru": "Бригада не указана", "en": "No crew assigned"}[lang if lang in LANGS else "en"],
                     "position": "", "earned": st["unassigned"], "bonus": 0, "paid": 0, "owed": 0})
    t = st["totals"]
    return _table("payroll", [("worker", "text"), ("position", "text"), ("earned", "money"), ("bonus", "money"), ("paid", "money"), ("owed", "money")], rows,
                  {"earned": t["earned"] + st["unassigned"], "bonus": t["adjust"], "paid": t["paid"], "owed": t["owed"]})


# ---------- profit (approximate) ----------
def profit(db, start, end, lang="en"):
    """Shipped value minus materials consumed (at the average purchase price) minus operating expenses."""
    price_sum, qty_sum = defaultdict(Decimal), defaultdict(Decimal)
    for r in db.query(Receipt).filter(Receipt.status == "posted"):
        if end and r.date > end:
            continue
        for x in r.rows:
            price_sum[x.item_id] += x.qty * x.price
            qty_sum[x.item_id] += x.qty
    avg = {i: price_sum[i] / qty_sum[i] for i in qty_sum if qty_sum[i]}
    revenue = sum((_amt(v.rows) for v in db.query(Invoice).filter(Invoice.status == "posted") if _in(v.date, start, end)), Decimal(0))
    material = Decimal(0)
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if _in(p.date, start, end):
            material += sum((c.qty * avg.get(c.material_id, Decimal(0)) for c in p.consumption), Decimal(0))
    lost = losses_value(db, start, end)
    exp = defaultdict(Decimal)
    for f in db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind == "out", FinDoc.article.in_(["sal", "tax", "fee", "oout"])):
        if _in(f.date, start, end):
            exp[f.article] += f.amount
    rows = [{"line": {"uz": "Sotuv (jo‘natilgan)", "ru": "Выручка (отгрузки)", "en": "Revenue (shipped)"}[lang if lang in LANGS else "en"], "amount": _f(revenue)},
            {"line": {"uz": "Material tannarxi", "ru": "Себестоимость материалов", "en": "Material cost"}[lang if lang in LANGS else "en"], "amount": -_f(material)}]
    if lost:
        rows.append({"line": {"uz": "Hisobdan chiqarish va kamomad", "ru": "Списания и недостачи", "en": "Write-offs and shortages"}[lang if lang in LANGS else "en"], "amount": -_f(lost)})
    rows += [{"line": _t(ARTICLES[a], lang), "amount": -_f(v)} for a, v in exp.items()]
    result = _f(revenue - material - lost - sum(exp.values(), Decimal(0)))
    rows.append({"line": {"uz": "Taxminiy foyda", "ru": "Ориентировочная прибыль", "en": "Estimated profit"}[lang if lang in LANGS else "en"], "amount": result})
    return _table("profit", [("line", "text"), ("amount", "money")], rows, {"amount": result})


# ---------- stock-out forecast ----------
def forecast(db, lang="en", now=None):
    """Days of cover per item at the last 30 days' average use (materials consumed in production, goods shipped)."""
    from datetime import timedelta
    from sqlalchemy import func, select
    now = now or datetime.now()
    since = now - timedelta(days=30)
    used = defaultdict(Decimal)
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted", ProductionDoc.date >= since, ProductionDoc.date <= now):
        for c in p.consumption:
            used[c.material_id] += c.qty
    for v in db.query(Invoice).filter(Invoice.status == "posted", Invoice.date >= since, Invoice.date <= now):
        for r in v.rows:
            used[r.item_id] += r.qty
    have = {k: Decimal(v or 0) for k, v in db.execute(select(StockBalance.item_id, func.sum(StockBalance.qty)).group_by(StockBalance.item_id))}
    items = {i.id: i for i in db.query(Item)}
    rows = []
    for iid, u in used.items():
        it = items.get(iid)
        if it is None or not it.is_active or u <= 0:
            continue
        rate, stock = u / 30, have.get(iid, Decimal(0))
        days = float(stock / rate) if stock > 0 else 0.0
        rows.append({"item": _name(it, lang), "kind": _t(KINDS[it.kind], lang), "unit": it.unit.name, "in_stock": _f(stock),
                     "daily": _f(rate), "days_left": round(days, 1), "min_stock": _f(it.min_stock)})
    rows.sort(key=lambda r: r["days_left"])
    cols = [("item", "text"), ("kind", "text"), ("unit", "text"), ("in_stock", "num"), ("daily", "num"), ("days_left", "num"), ("min_stock", "num")]
    return _table("forecast", cols, rows)


# ---------- debts ----------
def debts(db, who="customer", lang="en"):
    if who == "customer":
        data = [{"customer": d["name"], "sold": d["shipped"], "paid": d["paid"], "debt": d["debt"]} for d in base.customer_debts(db)]
        cols = [("customer", "text"), ("sold", "money"), ("paid", "money"), ("debt", "money")]
    else:
        data = [{"supplier": d["name"], "bought": d["bought"], "paid": d["paid"], "debt": d["debt"]} for d in base.supplier_debts(db)]
        cols = [("supplier", "text"), ("bought", "money"), ("paid", "money"), ("debt", "money")]
    data = [d for d in data if d["debt"] or d.get("sold") or d.get("bought")]
    data.sort(key=lambda d: -d["debt"])
    return _table("debts_" + who, cols, data, {"debt": _f(sum(d["debt"] for d in data))})


def aging(db, lang="en", today=None):
    data = [{"customer": a["name"], "current": a["current"], "d30": a["d30"], "d60": a["d60"], "d90": a["d90"], "overdue": a["overdue"],
             "advance": a["advance"], "debt": a["debt"]} for a in base.aging(db, today)]
    data.sort(key=lambda d: (-d["overdue"], -d["debt"]))
    cols = [("customer", "text"), ("current", "money"), ("d30", "money"), ("d60", "money"), ("d90", "money"), ("overdue", "money"), ("advance", "money"), ("debt", "money")]
    return _table("aging", cols, data, {k: _f(sum(d[k] for d in data)) for k in ("current", "d30", "d60", "d90", "overdue", "advance", "debt")})


# ---------- production plan ----------
def _plan(db):
    """Open orders minus what was already shipped against them, minus finished goods in stock -> what to produce."""
    from sqlalchemy import select
    from app.models import Norm, Order, OrderRow
    from app.services import stock
    orders = db.scalars(select(Order).where(Order.status == "open")).all()
    open_qty: dict[int, Decimal] = defaultdict(Decimal)
    nums: dict[int, set] = defaultdict(set)
    due: dict[int, datetime] = {}
    from app.services.sales import shipped_bulk
    sh = shipped_bulk(db, [o.id for o in orders])
    for o in orders:
        shipped: dict[int, Decimal] = defaultdict(Decimal, sh[o.id])
        for r in o.rows:
            left = r.qty - shipped[r.item_id]
            shipped[r.item_id] = max(Decimal(0), shipped[r.item_id] - r.qty)
            if left > 0:
                open_qty[r.item_id] += left
                nums[r.item_id].add(o.number)
                if o.due_date and (r.item_id not in due or o.due_date < due[r.item_id]):
                    due[r.item_id] = o.due_date
    held = stock.totals_by_item(db)
    have = lambda i: Decimal(str(sum(held.get(i, {}).values())))
    make = {i: max(Decimal(0), q - have(i)) for i, q in open_qty.items()}
    need: dict[int, Decimal] = defaultdict(Decimal)
    for n in db.query(Norm).filter(Norm.product_id.in_(list(make) or [0])).all():
        need[n.material_id] += n.qty * make[n.product_id]
    return open_qty, make, nums, due, have, need


def plan(db, lang="en"):
    open_qty, make, nums, due, have, _ = _plan(db)
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_(list(open_qty) or [0])).all()}
    rows = [{"item": _name(items[i], lang), "unit": items[i].unit.name, "orders": ", ".join(sorted(nums[i])), "due": due[i].date().isoformat() if i in due else "",
             "open_qty": _f(open_qty[i]), "in_stock": _f(have(i)), "to_make": _f(make[i])} for i in open_qty if i in items]
    rows.sort(key=lambda r: (r["due"] or "9999", r["item"]))
    return _table("plan", [("item", "text"), ("unit", "text"), ("orders", "text"), ("due", "date"), ("open_qty", "num"), ("in_stock", "num"), ("to_make", "num")], rows)


def plan_materials(db, lang="en"):
    _, _, _, _, _, need = _plan(db)
    from app.services import stock
    held = stock.totals_by_item(db)
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_(list(need) or [0])).all()}
    rows = []
    for m, q in need.items():
        if m in items and q > 0:
            have = Decimal(str(sum(held.get(m, {}).values())))
            rows.append({"item": _name(items[m], lang), "unit": items[m].unit.name, "need": _f(q), "in_stock": _f(have), "short": _f(max(Decimal(0), q - have))})
    rows.sort(key=lambda r: (-r["short"], r["item"]))
    return _table("plan_materials", [("item", "text"), ("unit", "text"), ("need", "num"), ("in_stock", "num"), ("short", "num")], rows)


# ---------- dispatch ----------
def run(db, name, *, start=None, end=None, group=None, warehouse_id=None, kind=None, who="customer", lang="en", levels=None, item_id=None, doc=None):
    if name == "movements":
        return movements(db, start, end, warehouse_id, kind, item_id, doc, lang)
    if name == "turnover":
        return turnover(db, start, end, warehouse_id, kind, lang)
    if name == "sales":
        return sales(db, start, end, group or "customer", lang)
    if name == "purchases":
        return purchases(db, start, end, group or "supplier", lang)
    if name == "cashflow":
        return cashflow(db, start, end, group or "article", lang, levels)
    if name == "profit":
        return profit(db, start, end, lang)
    if name == "debts":
        return debts(db, who, lang)
    if name == "aging":
        return aging(db, lang)
    if name == "forecast":
        return forecast(db, lang)
    if name == "losses":
        return losses(db, start, end, lang)
    if name == "production":
        return production(db, start, end, group or "item", warehouse_id, lang)
    if name == "scrap":
        return scrap(db, start, end, warehouse_id, lang)
    if name == "cost":
        return cost_sheet(db, end, lang)
    if name == "profit_products":
        return profit_products(db, start, end, lang)
    if name == "payroll":
        return payroll_report(db, start, end, lang)
    if name == "plan":
        return plan(db, lang)
    if name == "plan_materials":
        return plan_materials(db, lang)
    raise bad("invalid", "Unknown report")


NEEDS = {"turnover": ("wh",), "movements": ("wh",), "sales": ("inv",), "purchases": ("rec",), "cashflow": ("bank", "cash"), "profit": ("inv", "bank"), "debts": ("cus", "sup"), "aging": ("cus",), "forecast": ("wh",), "losses": ("adj",), "production": ("prod",), "scrap": ("prod",), "cost": ("prod", "inv"), "profit_products": ("inv", "bank"), "payroll": ("pay",), "plan": ("prod",), "plan_materials": ("prod",)}


def allowed(levels: dict, name: str, who: str = "customer") -> bool:
    """Whether a role (given as section levels) may open the report."""
    if name not in NEEDS:
        return False
    if name == "debts":
        return levels.get("cus" if who == "customer" else "sup", 0) >= 1
    if name == "cashflow":
        return any(levels.get(s, 0) >= 1 for s in NEEDS[name])
    return all(levels.get(s, 0) >= 1 for s in NEEDS[name])
