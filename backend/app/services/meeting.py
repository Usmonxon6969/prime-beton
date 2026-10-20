"""Monthly management meeting: the figures of one month against the month before, as a ready deck of slides.

Everything is calculated from the posted documents with the same functions the reports centre uses, so a slide can never disagree with a report.
A slide is only built when the person asking may see its numbers (production / sales / debts / warehouse / pay levels).
"""
import calendar
import re
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.errors import bad
from app.models import Item, ProductionDoc, Warehouse, Worker
from app.services import analytics as an, reports as base

L = {
    "title": ("Oylik majlis", "Ежемесячное совещание", "Monthly meeting"),
    "vs": ("o‘tgan oyga nisbatan", "к прошлому месяцу", "vs last month"),
    "s_overview": ("Umumiy ko‘rinish", "Общая картина", "Overview"),
    "s_production": ("Ishlab chiqarish", "Производство", "Production"),
    "s_scrap": ("Brak", "Брак", "Scrap"),
    "s_sales": ("Sotuv", "Продажи", "Sales"),
    "s_debts": ("Qarzlar", "Долги", "Debts"),
    "s_stock": ("Ombor", "Склад", "Warehouse"),
    "s_people": ("Ishchilar", "Работники", "Workers"),
    "s_summary": ("Xulosa", "Выводы", "Summary"),
    "made": ("Ishlab chiqarildi", "Произведено", "Produced"),
    "scrap_units": ("Brak (dona)", "Брак (шт.)", "Scrap (units)"),
    "scrap_pct": ("Brak ulushi, %", "Доля брака, %", "Scrap share, %"),
    "shipped": ("Jo‘natilgan summa", "Отгружено на сумму", "Shipped value"),
    "notes": ("Yuk xatlari", "Накладных", "Delivery notes"),
    "cus_owe": ("Mijozlar qarzi", "Долг покупателей", "Customers owe us"),
    "sup_owe": ("Bizning qarzimiz", "Наш долг поставщикам", "We owe suppliers"),
    "late": ("Muddati o‘tgan mijozlar", "Покупателей с просрочкой", "Customers overdue"),
    "low": ("Kam qolgan pozitsiyalar", "Позиций ниже минимума", "Items below minimum"),
    "payroll": ("Hisoblangan ish haqi", "Начислено зарплаты", "Pay earned"),
    "plant": ("Zavod", "Завод", "Plant"), "item": ("Pozitsiya", "Позиция", "Item"),
    "cur": ("Shu oy", "Этот месяц", "This month"), "prev": ("O‘tgan oy", "Прошлый месяц", "Last month"),
    "delta": ("Farq, %", "Изм., %", "Change, %"), "good": ("Yaroqli", "Годных", "Good"), "scrap": ("Brak", "Брак", "Scrap"),
    "customer": ("Mijoz", "Покупатель", "Customer"), "amount": ("Summa", "Сумма", "Amount"), "share": ("Ulushi, %", "Доля, %", "Share, %"),
    "debt": ("Qarz", "Долг", "Debt"), "overdue": ("Muddati o‘tgan", "Просрочено", "Overdue"),
    "have": ("Omborda", "На складе", "In stock"), "min": ("Minimum", "Минимум", "Minimum"), "days": ("Necha kunga yetadi", "Хватит дней", "Days of cover"),
    "worker": ("Ishchi", "Работник", "Worker"), "earned": ("Hisoblandi", "Начислено", "Earned"),
    "daily": ("Kunlik ishlab chiqarish", "Выпуск по дням", "Daily output"),
    "pcs": ("dona", "шт.", "pcs"), "uzs": ("so‘m", "сум", "UZS"),
    "no_data": ("Bu oyda ma‘lumot yo‘q", "За этот месяц данных нет", "No data for this month"),
    "up": ("{what} o‘tgan oyga nisbatan {p}% ga oshdi", "{what}: рост на {p}% к прошлому месяцу", "{what} rose {p}% vs last month"),
    "down": ("{what} o‘tgan oyga nisbatan {p}% ga kamaydi", "{what}: снижение на {p}% к прошлому месяцу", "{what} fell {p}% vs last month"),
    "flat": ("{what} o‘tgan oy darajasida", "{what}: на уровне прошлого месяца", "{what} is level with last month"),
    "top_item": ("Eng ko‘p ishlab chiqarilgan: {x}", "Больше всего произведено: {x}", "Most produced: {x}"),
    "top_cus": ("Eng yirik mijoz: {x}", "Крупнейший покупатель: {x}", "Biggest customer: {x}"),
    "scrap_high": ("Brak ulushi {p}%: eng ko‘p {x} da", "Доля брака {p}%: больше всего у {x}", "Scrap share {p}%: highest on {x}"),
    "late_n": ("Muddati o‘tgan qarzdor mijozlar: {n} ta", "Покупателей с просрочкой: {n}", "Customers with overdue debt: {n}"),
    "low_n": ("Minimumdan kam qolgan pozitsiyalar: {n} ta", "Позиций ниже минимума: {n}", "Items below minimum stock: {n}"),
    "mtd": ("Oy hali tugamagan: 1–{d} {a} o‘tgan oyning 1–{d} {b} kunlari bilan taqqoslanadi",
            "Месяц не закончен: 1–{d} {a} сравниваются с 1–{d} {b} прошлого месяца",
            "Month in progress: 1–{d} {a} is compared with 1–{d} {b} of the month before"),
    "questions": ("Majlisda muhokama uchun savollar", "Вопросы для обсуждения на совещании", "Questions for the meeting"),
    "s_plants": ("Zavodlar", "Заводы", "Plants"),
    "s_products": ("Mahsulotlar", "Продукция", "Products"),
    "s_purchases": ("Xaridlar (kirim)", "Закупки (приход)", "Purchases (receipts)"),
    "s_materials": ("Material sarfi", "Расход материалов", "Materials used"),
    "avg_day": ("Kunlik o‘rtacha", "В среднем за рабочий день", "Average per working day"),
    "best_day_qty": ("Eng yaxshi kun (dona)", "Лучший день (шт.)", "Best day (units)"),
    "avg_note": ("O‘rtacha yuk xati summasi", "Средняя сумма накладной", "Average note value"),
    "top3": ("Eng yirik 3 mijoz ulushi, %", "Доля 3 крупнейших покупателей, %", "Top 3 customers’ share, %"),
    "cus_n": ("Faol mijozlar", "Активных покупателей", "Active customers"),
    "recv": ("Kirim qilingan summa", "Принято на сумму", "Received value"),
    "rec_notes": ("Kirim nakladnoylari", "Приходных накладных", "Receipts"),
    "sup_n": ("Yetkazib beruvchilar", "Поставщиков", "Suppliers"),
    "workers_n": ("Ish bilan band ishchilar", "Работников с выпуском", "Workers who produced"),
    "avg_pay": ("Ishchiga o‘rtacha", "В среднем на работника", "Average per worker"),
    "plants_n": ("Ishlagan zavodlar", "Работавших заводов", "Plants at work"),
    "type": ("Tur", "Вид", "Type"), "days_c": ("Kunlar", "Дни", "Days"), "pieces": ("Dona", "Шт.", "Units"), "avg": ("O‘rtacha/kun", "В день", "Per day"),
    "scrap_c": ("Brak, %", "Брак, %", "Scrap, %"), "qty": ("Miqdor", "Кол-во", "Qty"), "docs": ("Yuk xati", "Накладных", "Notes"),
    "unit": ("Birlik", "Ед.", "Unit"), "supplier": ("Yetkazib beruvchi", "Поставщик", "Supplier"), "consumed": ("Sarflandi", "Израсходовано", "Used"),
    "product": ("Mahsulot", "Изделие", "Product"), "units_d": ("Farq (dona)", "Изм. (шт.)", "Change (units)"), "bought": ("Xarid", "Закуплено", "Bought"),
    "slab_avg": ("Plita, kuniga o‘rtacha", "Плит в день (в среднем)", "Slabs per day (average)"),
    "target_ok": ("Me‘yor {n}+ · yaxshi", "Норма {n}+ · хорошо", "Target {n}+ · good"),
    "target_low": ("Me‘yor {n}+ · past", "Норма {n}+ · ниже", "Target {n}+ · below"),
    "f_slab_ok": ("Plita kuniga o‘rtacha {a} ta: me‘yordan ({n}) yuqori, yaxshi natija", "Плит в день в среднем {a}: выше нормы ({n}), хороший результат", "Slabs per day average {a}: above the {n} target, a good result"),
    "f_slab_low": ("Plita kuniga o‘rtacha {a} ta: me‘yor ({n}) dan past", "Плит в день в среднем {a}: ниже нормы ({n})", "Slabs per day average {a}: below the {n} target"),
    "t_slab": ("Plita", "Плита", "Slab"), "t_tray": ("Lotok", "Лоток", "Tray"), "t_pole": ("Stolba", "Опора", "Pole"), "t_block": ("Blok", "Блок", "Block"), "t_other": ("Boshqa", "Прочее", "Other"),
    "sp_plant": ("Eng ko‘p ishlab chiqargan zavod", "Лидирующий завод", "Top plant"),
    "sp_stable": ("Kunlik o‘rtachasi eng yuqori zavod", "Завод с лучшим средним в день", "Highest daily average"),
    "sp_scrapplant": ("Brak ulushi eng yuqori zavod", "Завод с наибольшей долей брака", "Highest scrap share"),
    "sp_day": ("Eng yaxshi kun", "Лучший день", "Best day"),
    "sp_item": ("Eng ko‘p ishlab chiqarilgan mahsulot", "Самое производимое изделие", "Most produced product"),
    "sp_grow": ("Eng ko‘p o‘sgan mahsulot", "Больше всего вырос", "Biggest riser"),
    "sp_fall": ("Eng ko‘p kamaygan mahsulot", "Сильнее всего снизился", "Biggest faller"),
    "sp_scrap": ("Brak eng ko‘p mahsulot", "Больше всего брака", "Most scrap"),
    "sp_worker": ("Eng yaxshi ishchi", "Лучший работник", "Best worker"),
    "sp_days": ("Eng ko‘p ish kuni", "Больше всего рабочих дней", "Most working days"),
    "sp_earner": ("Eng ko‘p topgan ishchi", "Больше всех заработал", "Top earner"),
    "sp_cus": ("Eng yirik mijoz", "Крупнейший покупатель", "Top customer"),
    "sp_sday": ("Eng yaxshi savdo kuni", "Лучший день продаж", "Best sales day"),
    "sp_sup": ("Eng yirik yetkazib beruvchi", "Крупнейший поставщик", "Top supplier"),
    "sp_debtor": ("Eng katta qarzdor", "Крупнейший должник", "Biggest debtor"),
    "sp_used": ("Eng ko‘p sarflangan material", "Больше всего израсходовано", "Most used material"),
    "of_total": ("jami ishlab chiqarishning {p}%", "{p}% всего выпуска", "{p}% of all output"),
    "of_sales": ("jami jo‘natmaning {p}%", "{p}% всех отгрузок", "{p}% of all shipments"),
    "of_buy": ("jami xaridning {p}%", "{p}% всех закупок", "{p}% of all purchases"),
    "avg_n": ("kunlik o‘rtacha {n} dona, {d} kun", "в среднем {n} шт. в день, {d} дн.", "{n} units a day on average, {d} days"),
    "scrap_n": ("brak {p}%", "брак {p}%", "scrap {p}%"),
    "days_n": ("{d} kun ishlagan, {n} dona", "{d} дн., {n} шт.", "{d} days, {n} units"),
    "earned_n": ("{m} so‘m topgan", "заработал {m} сум", "earned {m} UZS"),
    "pcs_n": ("{n} dona", "{n} шт.", "{n} units"),
    "plus_n": ("{n} dona ko‘proq", "на {n} шт. больше", "{n} units more"),
    "minus_n": ("{n} dona kamroq", "на {n} шт. меньше", "{n} units fewer"),
    "note_n": ("{n} ta yuk xati", "{n} накладных", "{n} notes"),
    "f_plant": ("Eng ko‘p ishlab chiqargan zavod: {x} ({n} dona, {p}%)", "Больше всех выпустил завод {x}: {n} шт. ({p}%)", "Top plant: {x} ({n} units, {p}%)"),
    "f_day": ("Eng yaxshi kun: {x} — {n} dona", "Лучший день: {x} — {n} шт.", "Best day: {x} with {n} units"),
    "f_worker": ("Eng yaxshi ishchi: {x} ({n} dona, {d} kun)", "Лучший работник: {x} ({n} шт., {d} дн.)", "Best worker: {x} ({n} units, {d} days)"),
    "f_cus": ("Eng yirik mijoz: {x} — jo‘natmaning {p}%", "Крупнейший покупатель: {x} — {p}% отгрузок", "Biggest customer: {x} with {p}% of shipments"),
    "f_top3": ("Eng yirik 3 mijoz jo‘natmaning {p}% ini tashkil qiladi", "На 3 крупнейших покупателей приходится {p}% отгрузок", "The 3 biggest customers make up {p}% of shipments"),
    "f_used": ("Eng ko‘p sarflangan material: {x}", "Больше всего израсходовано: {x}", "Most used material: {x}"),
    "f_sup": ("Eng yirik yetkazib beruvchi: {x}", "Крупнейший поставщик: {x}", "Biggest supplier: {x}"),
    "f_types": ("Turlar bo‘yicha: {x}", "По видам: {x}", "By type: {x}"),
    "more": ("batafsil", "подробно", "details"),
    "tb_top_items": ("Eng ko‘p ishlab chiqarilganlar", "Больше всего выпущено", "Most produced"),
    "tb_movers": ("Eng katta o‘zgarishlar", "Самые большие изменения", "Biggest changes"),
    "tb_scrap_items": ("Brak ulushi bo‘yicha mahsulotlar", "Изделия по доле брака", "Products by scrap share"),
    "tb_scrap_plants": ("Zavodlar bo‘yicha brak", "Брак по заводам", "Scrap by plant"),
    "tb_customers": ("Mijozlar bo‘yicha", "По покупателям", "By customer"),
    "tb_products": ("Mahsulotlar bo‘yicha", "По изделиям", "By product"),
    "tb_suppliers": ("Yetkazib beruvchilar bo‘yicha", "По поставщикам", "By supplier"),
    "tb_materials": ("Materiallar bo‘yicha", "По материалам", "By material"),
    "tb_debtors": ("Mijozlar qarzi", "Долги покупателей", "Customer debts"),
    "tb_we_owe": ("Bizning qarzimiz", "Наши долги поставщикам", "What we owe suppliers"),
    "tb_low": ("Minimumdan kam qolganlar", "Ниже минимума", "Below minimum"),
    "tb_cover": ("Necha kunga yetadi (30 kunlik sarf bo‘yicha)", "На сколько дней хватит (по расходу за 30 дней)", "Days of cover (at the last 30 days’ use)"),
    "none": ("Ishlab chiqarish hujjatlari yo‘q", "Документов выпуска нет", "No production documents"),
}
MONTHS = {
    "uz": ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun", "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"],
    "ru": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}


def _i(lang):
    return {"uz": 0, "ru": 1, "en": 2}.get(lang, 2)


SLAB_TARGET = 40          # slabs a working day: at or above this the plant is doing well


def _q(x):
    """A figure for the slides: whole numbers from 10 up, one decimal below that (and never a trailing ",0")."""
    x = float(x)
    sign = -1 if x < 0 else 1
    a = abs(x)
    if a >= 10:
        return sign * int(a + 0.5)                      # half up, the same as the browser
    a = int(a * 10 + 0.5) / 10
    return sign * (int(a) if a == int(a) else a)


def _nf(x):
    q = _q(x)
    return f"{q:,}".replace(",", " ") if isinstance(q, int) else str(q).replace(".", ",")


def _tr(k, lang, **kw):
    s = L[k][_i(lang)]
    if kw:
        kw = {a: (_nf(b) if isinstance(b, float) else b) for a, b in kw.items()}
        return s.format(**kw)
    return s


def _span(month: str):
    try:
        y, m = int(month[:4]), int(month[5:7])
        if not (1 <= m <= 12) or month[4] != "-":
            raise ValueError
    except (ValueError, IndexError):
        raise bad("invalid", "month must look like 2026-10")
    last = calendar.monthrange(y, m)[1]
    return y, m, datetime(y, m, 1), datetime(y, m, last, 23, 59, 59)


def _prev(y, m):
    return (y - 1, 12) if m == 1 else (y, m - 1)


def _pct(cur, prev):
    return round((cur - prev) * 100 / prev, 1) if prev else None


def _kpi(key, lang, cur, prev=None, unit="", target=None):
    k = {"bad_up": key in ("scrap_units", "scrap_pct"), "label": _tr(key, lang), "value": _q(cur), "prev": None if prev is None else _q(prev),
         "delta": None if prev is None else _pct(float(cur), float(prev)), "unit": unit}
    if target is not None:
        ok = float(cur) >= target
        k["target"] = {"n": target, "ok": ok, "text": _tr("target_ok" if ok else "target_low", lang, n=target)}
    return k


def _cols(lang, *spec):
    return [{"key": k, "label": _tr(k, lang), "type": t} for k, t in spec]


def _label(lang, y, m):
    return f"{MONTHS[lang if lang in MONTHS else 'en'][m - 1]} {y}"


def _share(rows, key):
    tot = sum(r[key] for r in rows) or 1
    for r in rows:
        r["share"] = round(r[key] * 100 / tot, 1)


_TYPE_RX = (("slab", r"(^|\s)2\s*[пp][кk]|плит|plita"), ("tray", r"лот[о]?к|lotok|tray"),
            ("pole", r"опор|стойк|столб|ustun|stolba|pole"), ("block", r"фбс|fbs|блок|blok"))


def _ptype(it) -> str:
    """The kind of product, read from its name (there is no category field): slab, tray, pole, block or other."""
    names = " ".join(n for n in (getattr(it, "name_ru", ""), getattr(it, "name_uz", ""), getattr(it, "name_en", "")) if n).lower()
    for key, rx in _TYPE_RX:
        if re.search(rx, names):
            return key
    return "other"


def _facts(db, start, end, lang, items, whs):
    """Everything the plant made in the period, cut every way the slides need (one pass over the posted production documents)."""
    f = {"good": 0.0, "scrap": 0.0, "day": defaultdict(float), "type": defaultdict(float),
         "item": defaultdict(lambda: {"good": 0.0, "scrap": 0.0}),
         "plant": defaultdict(lambda: {"good": 0.0, "scrap": 0.0, "days": set()}),
         "worker": defaultdict(lambda: {"days": set(), "pieces": 0.0}), "slab_days": set()}
    for p in db.query(ProductionDoc).filter(ProductionDoc.status == "posted"):
        if not an._in(p.date, start, end):
            continue
        d, pl, doc_good = p.date.date(), whs.get(p.warehouse_id, "?"), 0.0
        for x in p.rows:
            it = items.get(x.item_id)
            g, sc = float(x.qty), float(x.scrap or 0)
            doc_good += g
            f["good"] += g
            f["scrap"] += sc
            f["day"][d] += g
            kind = _ptype(it) if it else "other"
            f["type"][kind] += g
            if kind == "slab" and g > 0:
                f["slab_days"].add(d)
            a = f["item"][an._name(it, lang) if it else "?"]
            a["good"] += g
            a["scrap"] += sc
            q = f["plant"][pl]
            q["good"] += g
            q["scrap"] += sc
        if doc_good or p.rows:
            f["plant"][pl]["days"].add(d)
        if p.crew:
            share = doc_good / len(p.crew)
            for c in p.crew:
                w = f["worker"][c.worker_id]
                w["days"].add(d)
                w["pieces"] += share
    f["days"] = len([d for d, v in f["day"].items() if v > 0])
    return f


def _r(x, n=1):
    return round(float(x), n)


def _spot(lang, label, name, value, unit="", note=""):
    return {"label": _tr(label, lang), "name": name, "value": _q(value) if value is not None else None, "unit": unit, "note": note}


def _fmtn(v):
    return f"{int(round(v)):,}".replace(",", " ")


def _dmy(d):
    return f"{d.day:02d}.{d.month:02d}"


def build(db: Session, month: str, lang: str, levels: dict, today: datetime | None = None) -> dict:
    y, m, start, end = _span(month)
    py, pm = _prev(y, m)
    _, _, pstart, pend = _span(f"{py:04d}-{pm:02d}")
    today, note = today or datetime.now(), ""
    if (today.year, today.month) == (y, m):                  # the running month is compared with the same days of the month before
        end = today.replace(hour=23, minute=59, second=59, microsecond=0)
        pend = datetime(py, pm, min(today.day, calendar.monthrange(py, pm)[1]), 23, 59, 59)
        names = MONTHS[lang if lang in MONTHS else "en"]
        note = _tr("mtd", lang, d=today.day, a=names[m - 1], b=names[pm - 1])
    can = lambda *s: all(levels.get(x, 0) >= 1 for x in s)       # noqa: E731
    pcs, uzs = _tr("pcs", lang), _tr("uzs", lang)
    slides, facts, spots_ov = [], [], []

    # ================= production side (needs the production level) =================
    cf = pf = None
    if can("prod"):
        items = {i.id: i for i in db.query(Item)}
        whs = {w.id: w.name for w in db.query(Warehouse)}
        cf, pf = _facts(db, start, end, lang, items, whs), _facts(db, pstart, pend, lang, items, whs)
        tg, pg, ts, ps = cf["good"], pf["good"], cf["scrap"], pf["scrap"]
        spct = round(ts * 100 / (tg + ts), 2) if tg + ts else 0
        pspct = round(ps * 100 / (pg + ps), 2) if pg + ps else 0
        nd, pnd = cf["days"], pf["days"]
        avg, pavg = (tg / nd if nd else 0), (pg / pnd if pnd else 0)
        sdn, psdn = len(cf["slab_days"]), len(pf["slab_days"])
        slab_avg = cf["type"].get("slab", 0.0) / sdn if sdn else 0.0
        pslab_avg = pf["type"].get("slab", 0.0) / psdn if psdn else 0.0
        best_day = max(cf["day"].items(), key=lambda kv: kv[1]) if cf["day"] else None
        plants = []
        for name, a in cf["plant"].items():
            prev_good = pf["plant"][name]["good"] if name in pf["plant"] else 0.0
            dn = len(a["days"])
            plants.append({"plant": name, "good": _r(a["good"], 0), "share": round(a["good"] * 100 / tg, 1) if tg else 0, "prev": _r(prev_good, 0),
                           "delta": _pct(a["good"], prev_good), "days_c": dn, "avg": _q(a["good"] / dn) if dn else 0,
                           "scrap_c": round(a["scrap"] * 100 / (a["good"] + a["scrap"]), 1) if a["good"] + a["scrap"] else 0})
        plants.sort(key=lambda r: -r["good"])
        top_plant = plants[0] if plants else None
        items_rows = sorted(cf["item"].items(), key=lambda kv: -kv[1]["good"])

        if tg or pg:
            spots = []
            if top_plant:
                spots.append(_spot(lang, "sp_plant", top_plant["plant"], top_plant["good"], pcs, _tr("of_total", lang, p=top_plant["share"])))
                facts.append(_tr("f_plant", lang, x=top_plant["plant"], n=_fmtn(top_plant["good"]), p=top_plant["share"]))
            if best_day:
                spots.append(_spot(lang, "sp_day", _dmy(best_day[0]), best_day[1], pcs))
                facts.append(_tr("f_day", lang, x=_dmy(best_day[0]), n=_fmtn(best_day[1])))
            spots_ov += spots

        # ---- production: the total, then one card for every kind of product (slabs, trays, poles ...) against last month
        tkpis = []
        for k in ("slab", "tray", "pole", "block", "other"):
            c, pv = cf["type"].get(k, 0.0), pf["type"].get(k, 0.0)
            if c or pv:
                tkpis.append(_kpi("t_" + k, lang, c, pv, pcs))
        slides.append({
            "id": "production", "title": _tr("s_production", lang),
            "kpis": [_kpi("made", lang, tg, pg, pcs)] + ([_kpi("slab_avg", lang, slab_avg, pslab_avg, pcs, SLAB_TARGET)] if sdn else []) + tkpis,
            "series": {"label": _tr("daily", lang), "points": [{"x": _dmy(d), "y": _q(v)} for d, v in sorted(cf["day"].items())]},
            "empty": not (tg or pg),
        })
        if sdn:
            facts.append(_tr("f_slab_ok" if slab_avg >= SLAB_TARGET else "f_slab_low", lang, a=slab_avg, n=SLAB_TARGET))
        tnow = [(k, cf["type"][k]) for k in ("slab", "tray", "pole", "block", "other") if cf["type"].get(k)]
        if len(tnow) > 1:
            facts.append(_tr("f_types", lang, x=", ".join(f"{_tr('t_' + k, lang)} {_fmtn(v)}" for k, v in tnow)))

        # ---- plants
        if plants:
            sp = [_spot(lang, "sp_plant", top_plant["plant"], top_plant["good"], pcs, _tr("of_total", lang, p=top_plant["share"]))]
            st = max(plants, key=lambda r: r["avg"])
            sp.append(_spot(lang, "sp_stable", st["plant"], st["avg"], pcs, _tr("avg_n", lang, n=_fmtn(st["avg"]), d=st["days_c"])))
            sc = max(plants, key=lambda r: r["scrap_c"])
            if sc["scrap_c"] > 0:
                sp.append(_spot(lang, "sp_scrapplant", sc["plant"], sc["scrap_c"], "%"))
            slides.append({
                "id": "plants", "title": _tr("s_plants", lang),
                "kpis": [_kpi("made", lang, tg, pg, pcs), _kpi("plants_n", lang, len(plants))],
                "spots": sp,
                "tables": [{"rows": plants, "columns": _cols(lang, ("plant", "text"), ("good", "num"), ("share", "num"), ("prev", "num"), ("delta", "pct"),
                                                             ("days_c", "num"), ("avg", "num"), ("scrap_c", "num"))}],
                "empty": False,
            })

        # ---- products: leaders and movers
        if items_rows:
            prev_i = pf["item"]
            top = [{"item": n, "good": _r(a["good"], 0), "prev": _r(prev_i[n]["good"], 0) if n in prev_i else 0,
                    "delta": _pct(a["good"], prev_i[n]["good"]) if n in prev_i else None, "share": round(a["good"] * 100 / tg, 1) if tg else 0}
                   for n, a in items_rows[:10]]
            ch = []
            for n in set(cf["item"]) | set(prev_i):
                c = cf["item"][n]["good"] if n in cf["item"] else 0.0
                pv = prev_i[n]["good"] if n in prev_i else 0.0
                if c != pv:
                    ch.append({"item": n, "good": _r(c, 0), "prev": _r(pv, 0), "units_d": _r(c - pv, 0), "delta": _pct(c, pv)})
            ch.sort(key=lambda r: -r["units_d"])
            movers = ch[:4] + [r for r in ch[::-1][:4] if r["units_d"] < 0 and r not in ch[:4]][::-1]
            sp = [_spot(lang, "sp_item", items_rows[0][0], items_rows[0][1]["good"], pcs, _tr("of_total", lang, p=top[0]["share"]))]
            if ch and ch[0]["units_d"] > 0 and ch[0]["prev"] > 0:
                sp.append(_spot(lang, "sp_grow", ch[0]["item"], ch[0]["units_d"], pcs, _tr("plus_n", lang, n=_fmtn(ch[0]["units_d"]))))
            if ch and ch[-1]["units_d"] < 0:
                sp.append(_spot(lang, "sp_fall", ch[-1]["item"], ch[-1]["units_d"], pcs, _tr("minus_n", lang, n=_fmtn(-ch[-1]["units_d"]))))
            slides.append({
                "id": "products", "title": _tr("s_products", lang), "spots": sp,
                "tables": [{"title": _tr("tb_top_items", lang), "rows": top, "columns": _cols(lang, ("item", "text"), ("good", "num"), ("prev", "num"), ("delta", "pct"), ("share", "num"))},
                           {"title": _tr("tb_movers", lang), "rows": movers, "columns": _cols(lang, ("item", "text"), ("good", "num"), ("prev", "num"), ("units_d", "num"), ("delta", "pct"))}],
                "empty": False,
            })
            facts.append(_tr("top_item", lang, x=items_rows[0][0]))

        # ---- scrap
        worst = sorted(((n, a) for n, a in cf["item"].items() if a["scrap"]), key=lambda kv: -(kv[1]["scrap"] * 100 / (kv[1]["good"] + kv[1]["scrap"])))[:8]
        scr_plants = [{"plant": r["plant"], "good": r["good"], "scrap": _r(cf["plant"][r["plant"]]["scrap"], 0), "share": r["scrap_c"]} for r in plants if cf["plant"][r["plant"]]["scrap"]]
        sp = []
        if worst:
            ws = max(worst, key=lambda kv: kv[1]["scrap"])
            sp.append(_spot(lang, "sp_scrap", ws[0], ws[1]["scrap"], pcs, _tr("scrap_n", lang, p=round(ws[1]["scrap"] * 100 / (ws[1]["good"] + ws[1]["scrap"]), 1))))
        slides.append({
            "id": "scrap", "title": _tr("s_scrap", lang),
            "kpis": [_kpi("scrap_units", lang, ts, ps, pcs), _kpi("scrap_pct", lang, spct, pspct, "%")], "spots": sp,
            "tables": [{"title": _tr("tb_scrap_items", lang), "rows": [{"item": n, "good": _r(a["good"], 0), "scrap": _r(a["scrap"], 0), "share": round(a["scrap"] * 100 / (a["good"] + a["scrap"]), 1)} for n, a in worst],
                        "columns": _cols(lang, ("item", "text"), ("good", "num"), ("scrap", "num"), ("share", "num"))},
                       {"title": _tr("tb_scrap_plants", lang), "rows": scr_plants, "columns": _cols(lang, ("plant", "text"), ("good", "num"), ("scrap", "num"), ("share", "num"))}],
            "empty": not worst,
        })
        if ts and worst:
            w = max(worst, key=lambda kv: kv[1]["scrap"] * 100 / (kv[1]["good"] + kv[1]["scrap"]))
            facts.append(_tr("scrap_high", lang, p=spct, x=w[0]))

    # ================= sales =================
    sales_cur = sales_prev = None
    if can("inv"):
        sales_cur = an.sales(db, start, end, "customer", lang)
        sales_prev = an.sales(db, pstart, pend, "customer", lang)
        s_amt, p_amt = sales_cur["totals"].get("amount", 0), sales_prev["totals"].get("amount", 0)
        s_docs, p_docs = sales_cur["totals"].get("docs", 0), sales_prev["totals"].get("docs", 0)
        prods = [{"item": r["item"], "qty": r["qty"], "amount": r["amount"]} for r in an.sales(db, start, end, "item", lang)["rows"][:8]]
        _share(prods, "amount")
        days = an.sales(db, start, end, "day", lang)["rows"]
        sp = []
        if days:                                                         # sales are shown as figures only: no customers, no names
            bd = max(days, key=lambda r: r["amount"])
            sp.append(_spot(lang, "sp_sday", bd["date"][8:10] + "." + bd["date"][5:7], bd["amount"], uzs, _tr("note_n", lang, n=bd["docs"])))
        slides.append({
            "id": "sales", "title": _tr("s_sales", lang),
            "kpis": [_kpi("shipped", lang, s_amt, p_amt, uzs), _kpi("notes", lang, s_docs, p_docs),
                     _kpi("avg_note", lang, s_amt / s_docs if s_docs else 0, p_amt / p_docs if p_docs else 0, uzs)],
            "spots": sp,
            "tables": [{"title": _tr("tb_products", lang), "rows": prods, "columns": _cols(lang, ("item", "text"), ("qty", "num"), ("amount", "money"), ("share", "num"))}],
            "series": {"label": _tr("shipped", lang) + ", " + uzs, "points": [{"x": r["date"][8:10] + "." + r["date"][5:7], "y": r["amount"]} for r in days]},
            "empty": not prods,
        })

    # ================= purchases (receipts) =================
    if can("rec"):
        pc, pp = an.purchases(db, start, end, "supplier", lang), an.purchases(db, pstart, pend, "supplier", lang)
        c_amt, p_amt2 = pc["totals"].get("amount", 0), pp["totals"].get("amount", 0)
        sup = [{"supplier": r["supplier"] or "?", "docs": r["docs"], "amount": r["amount"]} for r in pc["rows"][:8]]
        _share(sup, "amount")
        mats = [{"item": r["item"], "qty": r["qty"], "amount": r["amount"]} for r in an.purchases(db, start, end, "item", lang)["rows"][:8]]
        _share(mats, "amount")
        sp = [_spot(lang, "sp_sup", sup[0]["supplier"], sup[0]["amount"], uzs, _tr("of_buy", lang, p=sup[0]["share"]))] if sup else []
        if sup:
            facts.append(_tr("f_sup", lang, x=sup[0]["supplier"]))
        slides.append({
            "id": "purchases", "title": _tr("s_purchases", lang),
            "kpis": [_kpi("recv", lang, c_amt, p_amt2, uzs), _kpi("rec_notes", lang, pc["totals"].get("docs", 0), pp["totals"].get("docs", 0)),
                     _kpi("sup_n", lang, len(pc["rows"]), len(pp["rows"]))],
            "spots": sp,
            "tables": [{"title": _tr("tb_suppliers", lang), "rows": sup, "columns": _cols(lang, ("supplier", "text"), ("docs", "num"), ("amount", "money"), ("share", "num"))},
                       {"title": _tr("tb_materials", lang), "rows": mats, "columns": _cols(lang, ("item", "text"), ("qty", "num"), ("amount", "money"), ("share", "num"))}],
            "empty": not sup,
        })

    # ================= debts (balances today, not movements) =================
    dk, dt, sp = [], [], []
    cus_d = late = None
    if can("cus"):
        cus_d = an.debts(db, "customer", lang)
        ag = an.aging(db, lang)
        late = [r for r in ag["rows"] if r["overdue"] > 0]
        dk += [_kpi("cus_owe", lang, cus_d["totals"]["debt"], None, uzs), _kpi("late", lang, len(late))]
        top = [{"customer": r["customer"], "debt": r["debt"], "overdue": next((a["overdue"] for a in ag["rows"] if a["customer"] == r["customer"]), 0)}
               for r in cus_d["rows"][:8] if r["debt"] > 0]
        dt.append({"title": _tr("tb_debtors", lang), "rows": top, "columns": _cols(lang, ("customer", "text"), ("debt", "money"), ("overdue", "money"))})
        if top:
            sp.append(_spot(lang, "sp_debtor", top[0]["customer"], top[0]["debt"], uzs))
    if can("sup"):
        sup_d = an.debts(db, "supplier", lang)
        dk.append(_kpi("sup_owe", lang, sup_d["totals"]["debt"], None, uzs))
        owe = [{"supplier": r["supplier"], "bought": r["bought"], "debt": r["debt"]} for r in sup_d["rows"][:8] if r["debt"] > 0]
        dt.append({"title": _tr("tb_we_owe", lang), "rows": owe, "columns": _cols(lang, ("supplier", "text"), ("bought", "money"), ("debt", "money"))})
    if dk:
        slides.append({"id": "debts", "title": _tr("s_debts", lang), "kpis": dk, "spots": sp, "tables": dt, "empty": False})

    # ================= warehouse =================
    low_n = 0
    if can("wh"):
        low = base.low_stock(db)
        low_n = len(low)
        nm = {i.id: an._name(i, lang) for i in db.query(Item).filter(Item.id.in_([x["item_id"] for x in low] or [0]))}
        rows = [{"item": nm.get(x["item_id"], "?"), "have": round(x["have"], 2), "min": round(x["min"], 2)} for x in low[:12]]
        fc = [r for r in an.forecast(db, lang)["rows"] if r["days_left"] < 30][:8]
        slides.append({
            "id": "stock", "title": _tr("s_stock", lang), "kpis": [_kpi("low", lang, low_n)],
            "tables": [{"title": _tr("tb_low", lang), "rows": rows, "columns": _cols(lang, ("item", "text"), ("have", "num"), ("min", "num"))},
                       {"title": _tr("tb_cover", lang), "rows": [{"item": r["item"], "have": r["in_stock"], "days": r["days_left"]} for r in fc],
                        "columns": _cols(lang, ("item", "text"), ("have", "num"), ("days", "num"))}],
            "empty": not rows and not fc,
        })
        # materials consumed by production: this month against the month before, in their own units
        cur_t = {r["item"]: r for r in an.turnover(db, start, end, None, "material", lang)["rows"]}
        prv_t = {r["item"]: r for r in an.turnover(db, pstart, pend, None, "material", lang)["rows"]}
        used = [{"item": n, "unit": r["unit"], "good": r["consumed"], "prev": prv_t[n]["consumed"] if n in prv_t else 0,
                 "delta": _pct(r["consumed"], prv_t[n]["consumed"]) if n in prv_t else None}
                for n, r in cur_t.items() if r["consumed"] > 0]
        used.sort(key=lambda r: -r["good"])
        if used:
            slides.append({
                "id": "materials", "title": _tr("s_materials", lang),
                "spots": [_spot(lang, "sp_used", used[0]["item"], used[0]["good"], used[0]["unit"])],
                "tables": [{"rows": used[:12], "columns": [{"key": "item", "label": _tr("item", lang), "type": "text"}, {"key": "unit", "label": _tr("unit", lang), "type": "text"},
                                                           {"key": "good", "label": _tr("consumed", lang), "type": "num"}, {"key": "prev", "label": _tr("prev", lang), "type": "num"},
                                                           {"key": "delta", "label": _tr("delta", lang), "type": "pct"}]}],
                "empty": False,
            })
            facts.append(_tr("f_used", lang, x=used[0]["item"]))

    # ================= workers =================
    if can("pay"):
        pr = an.payroll_report(db, start, end, lang)
        pprev = an.payroll_report(db, pstart, pend, lang)
        earned = {r["worker"]: r["earned"] for r in pr["rows"]}
        names = {w.id: w.name for w in db.query(Worker)}
        rows = []
        if cf is not None:
            for wid, a in cf["worker"].items():
                n = names.get(wid, "?")
                rows.append({"worker": n, "days_c": len(a["days"]), "pieces": _r(a["pieces"], 0), "earned": earned.get(n, 0)})
        else:
            rows = [{"worker": r["worker"], "days_c": 0, "pieces": 0, "earned": r["earned"]} for r in pr["rows"] if r["earned"]]
        rows.sort(key=lambda r: (-r["pieces"], -r["earned"]))
        tot_pcs = sum(r["pieces"] for r in rows) or 1
        for r in rows:
            r["share"] = round(r["pieces"] * 100 / tot_pcs, 1)
        paid = [r for r in pr["rows"] if r["earned"]]
        sp = []
        if rows and cf is not None:
            b = rows[0]
            sp.append(_spot(lang, "sp_worker", b["worker"], b["pieces"], pcs, _tr("days_n", lang, d=b["days_c"], n=_fmtn(b["pieces"]))))
            facts.append(_tr("f_worker", lang, x=b["worker"], n=_fmtn(b["pieces"]), d=b["days_c"]))
            spots_ov.append(sp[0])
            md = max(rows, key=lambda r: (r["days_c"], r["pieces"]))
            if md["worker"] != b["worker"] and md["days_c"] > b["days_c"]:
                sp.append(_spot(lang, "sp_days", md["worker"], md["days_c"], _tr("days_c", lang).lower(), _tr("pcs_n", lang, n=_fmtn(md["pieces"]))))
        if paid:
            te = max(paid, key=lambda r: r["earned"])
            sp.append(_spot(lang, "sp_earner", te["worker"], te["earned"], uzs))
        n_paid, pn_paid = len(paid), len([r for r in pprev["rows"] if r["earned"]])
        total, ptotal = pr["totals"]["earned"], pprev["totals"]["earned"]
        slides.append({
            "id": "people", "title": _tr("s_people", lang),
            "kpis": [_kpi("payroll", lang, total, ptotal, uzs), _kpi("workers_n", lang, n_paid, pn_paid),
                     _kpi("avg_pay", lang, total / n_paid if n_paid else 0, ptotal / pn_paid if pn_paid else 0, uzs)],
            "spots": sp,
            "tables": [{"rows": rows[:12], "columns": _cols(lang, ("worker", "text"), ("days_c", "num"), ("pieces", "num"), ("share", "num"), ("earned", "money"))}],
            "empty": not rows,
        })

    # ================= overview (first slide: the headline figures and who stood out) =================
    ov = []
    if cf is not None:
        ov += [_kpi("made", lang, tg, pg, pcs)]
        ov.append(_kpi("slab_avg", lang, slab_avg, pslab_avg, pcs, SLAB_TARGET) if sdn else _kpi("avg_day", lang, avg, pavg, pcs))
        ov.append(_kpi("scrap_pct", lang, spct, pspct, "%"))
    if sales_cur is not None:
        ov.append(_kpi("shipped", lang, s_amt, p_amt, uzs))
    if ov:
        slides.insert(0, {"id": "overview", "title": _tr("s_overview", lang), "kpis": ov, "spots": spots_ov[:4]})

    # ================= summary: plain sentences built from the numbers above (no guessing) =================
    def trend(key, cur, prev):
        p = _pct(cur, prev)
        if p is None:
            return None
        if abs(p) < 0.5:
            return _tr("flat", lang, what=_tr(key, lang))
        return _tr("up" if p > 0 else "down", lang, what=_tr(key, lang), p=abs(p))
    lead = []
    if cf is not None and (tg or pg):
        lead.append(trend("made", tg, pg))
    if sales_cur is not None:
        lead.append(trend("shipped", s_amt, p_amt))
    if cus_d is not None and late:
        facts.append(_tr("late_n", lang, n=len(late)))
    if low_n:
        facts.append(_tr("low_n", lang, n=low_n))
    facts = [f for f in lead + facts if f]
    slides.append({"id": "summary", "title": _tr("s_summary", lang), "bullets": facts, "empty": not facts})

    return {"month": month, "label": _label(lang, y, m), "prev_label": _label(lang, py, pm), "title": _tr("title", lang),
            "vs": _tr("vs", lang), "note": note, "slides": slides, "empty_text": _tr("no_data", lang), "labels": {"cur": _tr("cur", lang), "prev": _tr("prev", lang), "questions": _tr("questions", lang), "more": _tr("more", lang)}}
