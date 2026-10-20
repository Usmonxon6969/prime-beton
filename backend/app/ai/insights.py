"""Deterministic business signals (no model needed): stock-out forecast, slow movers, sales trend, overdue debts,
cash forecast, anomalies. The AI layer explains and prioritises them; they also work without an API key.

Each insight: {id, severity (crit|warn|info), kind, section, text, data}. Texts are rendered per language here.
"""
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (Account, Customer, FinDoc, Invoice, Item, ProductionDoc, Receipt, StockBalance, Supplier)
from app.services import finance, reports
from app.services.analytics import ARTICLES

L = {"uz": 0, "ru": 1, "en": 2}
MSG = {
    "stockout": ("{item}: qoldiq {have} {unit}, taxminan {days} kunga yetadi (kuniga ~{rate} {unit} sarf).",
                 "{item}: остаток {have} {unit}, хватит примерно на {days} дн. (расход ~{rate} {unit}/день).",
                 "{item}: {have} {unit} left, about {days} days at ~{rate} {unit}/day."),
    "stockout0": ("{item}: qoldiq tugagan, lekin so‘nggi oyda ishlatilgan.",
                  "{item}: остаток закончился, хотя за последний месяц расходовался.",
                  "{item} is out of stock but was used in the last month."),
    "below_min": ("{item}: {have} {unit} — minimal qoldiqdan ({min}) past.",
                  "{item}: {have} {unit} — ниже минимума ({min}).", "{item}: {have} {unit} — below the minimum ({min})."),
    "slow": ("{item}: {have} {unit} omborda, {days} kundan beri jo‘natilmagan.",
             "{item}: {have} {unit} на складе, нет отгрузок {days} дн.", "{item}: {have} {unit} in stock, nothing shipped for {days} days."),
    "sales_down": ("So‘nggi 30 kunda sotuv {pct}% kamaydi ({now} so‘m, oldingi 30 kunda {prev}).",
                   "Отгрузки за 30 дней упали на {pct}% ({now} сум против {prev}).",
                   "Sales fell {pct}% over the last 30 days ({now} vs {prev})."),
    "sales_up": ("So‘nggi 30 kunda sotuv {pct}% o‘sdi ({now} so‘m, oldingi 30 kunda {prev}).",
                 "Отгрузки за 30 дней выросли на {pct}% ({now} сум против {prev}).",
                 "Sales grew {pct}% over the last 30 days ({now} vs {prev})."),
    "debt_old": ("{name}: {debt} so‘m muddati o‘tgan, eng eskisi {days} kun kechikkan.",
                 "{name}: просрочено {debt} сум, самая старая — {days} дн.", "{name}: {debt} overdue, the oldest is {days} days late."),
    "payables": ("Yetkazib beruvchilarga qarz {pay} so‘m, hisoblardagi pul {cash} so‘m — yetmaydi.",
                 "Долг поставщикам {pay} сум, на счетах {cash} сум — не хватает.",
                 "Payables are {pay} but only {cash} is on the accounts."),
    "cash_out": ("Hozirgi tempda pul ~{days} kunda tugaydi (qoldiq {bal}, kunlik o‘rtacha {net}).",
                 "При текущем темпе деньги закончатся примерно через {days} дн. (остаток {bal}, в среднем {net}/день).",
                 "At the current pace the money runs out in about {days} days (balance {bal}, average {net}/day)."),
    "cash_ok": ("30 kunlik prognoz: {proj} so‘m (hozir {bal}, kunlik o‘rtacha {net}).",
                "Прогноз на 30 дней: {proj} сум (сейчас {bal}, в среднем {net}/день).",
                "30-day forecast: {proj} (now {bal}, average {net}/day)."),
    "price": ("{doc}: {item} narxi {price} — odatdagidan {pct}% farq qiladi (odatda ~{typ}).",
              "{doc}: цена {item} {price} отличается на {pct}% от обычной (~{typ}).",
              "{doc}: {item} price {price} is {pct}% off the usual (~{typ})."),
    "duplicate": ("{doc} va {other} deyarli bir xil ({what}). Ikki marta kiritilmaganini tekshiring.",
                  "{doc} и {other} почти одинаковы ({what}). Проверьте, не введён ли документ дважды.",
                  "{doc} and {other} look identical ({what}). Check that it was not entered twice."),
    "big_pay": ("{doc}: «{art}» bo‘yicha {amt} so‘m — odatdagidan ancha katta (odatda ~{typ}).",
                "{doc}: «{art}» на {amt} сум — заметно больше обычного (~{typ}).",
                "{doc}: {amt} on “{art}” is far above the usual (~{typ})."),
}
SEV = {"crit": 0, "warn": 1, "info": 2}


def n(x, d=0) -> str:
    s = f"{x:,.{d}f}".replace(",", " ")
    return s.rstrip("0").rstrip(".") if "." in s else s


def _msg(key, lang, **kw):
    return MSG[key][L.get(lang, 2)].format(**kw)


def _ins(id_, sev, kind, section, key, lang, data=None, **kw):
    return {"id": id_, "severity": sev, "kind": kind, "section": section, "text": _msg(key, lang, **kw), "data": data or {}}


def _stock_totals(db) -> dict[int, Decimal]:
    return {k: Decimal(v or 0) for k, v in db.execute(select(StockBalance.item_id, func.sum(StockBalance.qty)).group_by(StockBalance.item_id))}


def stockout(db, lang, now, items, horizon=14):
    since = now - timedelta(days=30)
    used = defaultdict(Decimal)
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted", ProductionDoc.date >= since, ProductionDoc.date <= now):
        for c in p.consumption:
            used[c.material_id] += c.qty
    for v in db.query(Invoice).filter(Invoice.status == "posted", Invoice.date >= since, Invoice.date <= now):
        for r in v.rows:
            used[r.item_id] += r.qty
    tot, out = _stock_totals(db), []
    for iid, u in used.items():
        it = items.get(iid)
        if it is None or not it.is_active or u <= 0:
            continue
        have, rate = tot.get(iid, Decimal(0)), u / 30
        name = getattr(it, "name_" + lang if lang in L else "name_en")
        if have <= 0:
            out.append(_ins(f"stockout:{iid}", "crit", "stockout", "wh", "stockout0", lang, {"item_id": iid}, item=name))
            continue
        days = float(have / rate)
        if days < horizon:
            out.append(_ins(f"stockout:{iid}", "crit" if days < 5 else "warn", "stockout", "wh", "stockout", lang,
                            {"item_id": iid, "days": round(days, 1)}, item=name, have=n(have, 1), unit=it.unit.name,
                            days=int(days) if days >= 1 else "<1", rate=n(rate, 1)))
    out.sort(key=lambda i: i["data"].get("days", -1))
    return out[:8]


def below_min(db, lang, items):
    out = []
    for d in reports.low_stock(db):
        it = items.get(d["item_id"])
        out.append(_ins(f"min:{d['item_id']}", "warn", "below_min", "wh", "below_min", lang, {"item_id": d["item_id"]},
                        item=getattr(it, "name_" + (lang if lang in L else "en")), have=n(d["have"], 1), unit=d["unit"], min=n(d["min"], 1)))
    return out[:8]


def slow_movers(db, lang, now, items, days=60):
    tot = _stock_totals(db)
    last = {}
    for v in db.query(Invoice).filter(Invoice.status == "posted", Invoice.date <= now):
        for r in v.rows:
            last[r.item_id] = max(last.get(r.item_id, datetime.min), v.date)
    out = []
    for iid, have in tot.items():
        it = items.get(iid)
        if it is None or it.kind != "product" or not it.is_active or have <= 0:
            continue
        gap = (now - last[iid]).days if iid in last else None
        if gap is not None and gap >= days:
            out.append(_ins(f"slow:{iid}", "info", "slow", "wh", "slow", lang, {"item_id": iid, "days": gap},
                            item=getattr(it, "name_" + (lang if lang in L else "en")), have=n(have, 1), unit=it.unit.name, days=gap))
    out.sort(key=lambda i: -i["data"]["days"])
    return out[:5]


def sales_trend(db, lang, now):
    def total(a, b):
        return sum((sum((r.qty * r.price for r in v.rows), Decimal(0)) for v in
                    db.query(Invoice).filter(Invoice.status == "posted", Invoice.date > a, Invoice.date <= b)), Decimal(0))
    cur, prev = total(now - timedelta(days=30), now), total(now - timedelta(days=60), now - timedelta(days=30))
    if prev <= 0:
        return []
    pct = round(float((cur - prev) / prev * 100))
    if pct <= -20:
        return [_ins("sales_trend", "warn", "sales_trend", "inv", "sales_down", lang, {"pct": pct}, pct=abs(pct), now=n(cur), prev=n(prev))]
    if pct >= 20:
        return [_ins("sales_trend", "info", "sales_trend", "inv", "sales_up", lang, {"pct": pct}, pct=pct, now=n(cur), prev=n(prev))]
    return []


def overdue_debts(db, lang, now, days=7):
    """Customers with delivery notes unpaid after their pay-by date (a note without a term is due on the delivery day)."""
    out = []
    for a in reports.aging(db, now):
        if a["overdue"] <= 0 or a["oldest_days"] < days:
            continue
        out.append(_ins(f"debt:{a['customer_id']}", "crit" if a["oldest_days"] >= 60 else "warn", "debt_old", "cus", "debt_old", lang,
                        {"customer_id": a["customer_id"], "debt": a["overdue"], "days": a["oldest_days"]},
                        name=a["name"], debt=n(a["overdue"]), days=a["oldest_days"]))
    out.sort(key=lambda i: -i["data"]["debt"])
    return out[:6]


def _daily_net(db, kinds, now, days=60):
    since = now - timedelta(days=days)
    accs = {a.id: a for a in db.query(Account)}
    net = Decimal(0)
    for f in db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind.in_(["in", "out"]), FinDoc.date > since, FinDoc.date <= now):
        a = accs.get(f.account_id)
        if a and a.kind in kinds:
            net += f.amount if f.kind == "in" else -f.amount
    return net / days


def cash_forecast(db, lang, now, levels):
    kinds = {k for k in ("bank", "cash") if levels.get(k)}
    if not kinds:
        return []
    bal = finance.balances(db)
    have = sum((bal[a.id] for a in db.query(Account).filter(Account.is_active, Account.kind.in_(kinds))), Decimal(0))
    net = _daily_net(db, kinds, now)
    out = []
    section = "bank" if "bank" in kinds else "cash"
    proj = have + net * 30
    if net < 0 and have >= 0:
        days = int(have / -net)
        if days < 60:
            out.append(_ins("cash_forecast", "crit" if days < 14 else "warn", "cash_out", section, "cash_out", lang,
                            {"days": days, "balance": float(have), "net": float(net)}, days=days, bal=n(have), net=n(net)))
            return out
    out.append(_ins("cash_forecast", "info", "cash_ok", section, "cash_ok", lang, {"balance": float(have), "projected": float(proj)},
                    proj=n(proj), bal=n(have), net=n(net)))
    if levels.get("sup") and levels.get("bank"):
        pay = sum((max(0, d["debt"]) for d in reports.supplier_debts(db)), 0)
        if pay > float(have) and pay > 0:
            out.append(_ins("payables", "warn", "payables", "sup", "payables", lang, {"payables": pay, "cash": float(have)}, pay=n(pay), cash=n(have)))
    return out


def anomalies(db, lang, now, items):
    out = []
    prices = defaultdict(list)
    docs = db.query(Invoice).filter(Invoice.status == "posted", Invoice.date <= now).order_by(Invoice.date.desc()).limit(400).all()
    for v in docs:
        for r in v.rows:
            if r.price > 0:
                prices[r.item_id].append((float(r.price), v))
    for iid, lst in prices.items():
        if len(lst) < 4:
            continue
        for price, v in lst[:6]:                      # only the freshest documents
            others = [p for p, d in lst if d.id != v.id]
            med = statistics.median(others)
            if med and abs(price - med) / med > 0.4 and (now - v.date).days <= 30:
                it = items.get(iid)
                out.append(_ins(f"price:{v.id}:{iid}", "warn", "price", "inv", "price", lang, {"invoice_id": v.id, "item_id": iid},
                                doc=v.number, item=getattr(it, "name_" + (lang if lang in L else "en")), price=n(price),
                                pct=round(abs(price - med) / med * 100), typ=n(med)))
    by_art = defaultdict(list)
    accs = {a.id: a for a in db.query(Account)}
    fin_docs = db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.kind == "out", FinDoc.date <= now).all()
    for f in fin_docs:
        by_art[f.article].append(f)
    for art, lst in by_art.items():
        if len(lst) < 5:
            continue
        med = statistics.median([float(f.amount) for f in lst])
        for f in lst:
            if (now - f.date).days <= 30 and med > 0 and float(f.amount) > 3 * med:
                name = ARTICLES.get(art, (art, art, art))[L.get(lang, 2)]
                out.append(_ins(f"bigpay:{f.id}", "warn", "big_pay", "bank", "big_pay", lang, {"fin_id": f.id},
                                doc=f.number, art=name, amt=n(f.amount), typ=n(med)))
    return out[:6]


def _dup_scan(docs, sig, kind_label, section, lang, now, out, seen):
    """docs are newest first; two documents with the same signature on the same day are probably one entered twice."""
    first = {}
    for d in docs:
        if (now - d.date).days > 30:
            continue
        key = sig(d)
        if key in first:
            other = first[key]
            out.append(_ins(f"dup:{d.number}:{other.number}", "warn", "duplicate", section(d), "duplicate", lang,
                            {"doc": d.number, "other": other.number}, doc=other.number, other=d.number, what=kind_label))
        else:
            first[key] = d


def duplicates(db, lang, now):
    out, seen = [], set()
    day = lambda d: d.date.date()      # noqa: E731
    inv = db.query(Invoice).filter(Invoice.status == "posted", Invoice.date <= now).order_by(Invoice.date.desc(), Invoice.id.desc()).limit(300).all()
    _dup_scan(inv, lambda v: (v.customer_id, v.warehouse_id, day(v), tuple(sorted((r.item_id, r.qty, r.price) for r in v.rows))),
              {"uz": "chiqim nakladnoyi", "ru": "накладная", "en": "delivery note"}[lang if lang in L else "en"], lambda d: "inv", lang, now, out, seen)
    rec = db.query(Receipt).filter(Receipt.status == "posted", Receipt.date <= now).order_by(Receipt.date.desc(), Receipt.id.desc()).limit(300).all()
    _dup_scan(rec, lambda v: (v.supplier_id, v.warehouse_id, day(v), tuple(sorted((r.item_id, r.qty, r.price) for r in v.rows))),
              {"uz": "kirim", "ru": "поступление", "en": "receipt"}[lang if lang in L else "en"], lambda d: "rec", lang, now, out, seen)
    accs = {a.id: a.kind for a in db.query(Account)}
    fin = db.query(FinDoc).filter(FinDoc.status == "posted", FinDoc.date <= now, FinDoc.kind != "tr").order_by(FinDoc.date.desc(), FinDoc.id.desc()).limit(400).all()
    _dup_scan(fin, lambda f: (f.account_id, f.kind, f.article, f.amount, f.customer_id, f.supplier_id, f.worker_id, (f.party or "").strip().lower(), day(f)),
              {"uz": "to‘lov", "ru": "платёж", "en": "payment"}[lang if lang in L else "en"], lambda d: accs.get(d.account_id, "bank"), lang, now, out, seen)
    return out[:6]


def collect(db: Session, levels: dict, lang: str = "en", now: datetime | None = None) -> list[dict]:
    now = now or datetime.now()
    items = {i.id: i for i in db.query(Item)}
    out = []
    if levels.get("wh"):
        out += stockout(db, lang, now, items) + below_min(db, lang, items) + slow_movers(db, lang, now, items)
    if levels.get("inv"):
        out += sales_trend(db, lang, now) + anomalies(db, lang, now, items)
    if levels.get("cus"):
        out += overdue_debts(db, lang, now)
    out += duplicates(db, lang, now)
    out += cash_forecast(db, lang, now, levels)
    seen, res = set(), []
    for i in out:
        if i["id"] in seen or not levels.get(i["section"]):
            continue
        seen.add(i["id"])
        res.append(i)
    res.sort(key=lambda i: SEV[i["severity"]])
    return res
