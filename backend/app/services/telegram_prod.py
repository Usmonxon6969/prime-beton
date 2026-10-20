"""Production entered through Telegram: a person who may edit production sends a plain list, the bot reads it, shows what it
understood and records it only after the sender taps «Confirm».

    15.10
    ФБС 24.4.6-Т - 40
    2ПК 66,5*10 25 dona
    Brigada: Ali, Vali

Reading is strict on purpose. Every line must be understood; if one is not, nothing is recorded and the bot says which line and
what it may have meant. The same stock checks as on the website apply (the confirm step calls the same production service)."""
import json
import re
from datetime import datetime, timedelta
from decimal import Decimal
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import Item, ProductionDoc, TelegramDraft, TelegramLink, User, Warehouse, Worker
from app.schemas.documents import ProdRowIn, ProductionIn
from app.services import production, stock

DRAFT_TTL = timedelta(hours=2)                  # the sender has this long to confirm
PENDING_TTL = timedelta(hours=24)              # and the manager this long to approve
FUZZY_OK, FUZZY_GAP, FUZZY_HINT = 0.88, 0.04, 0.6
LANG = {"uz": 0, "ru": 1, "en": 2}

TXT = {
    "title": ("🏭 Ishlab chiqarish — {date}", "🏭 Выпуск — {date}", "🏭 Production — {date}"),
    "total": ("Jami: {kinds} xil, {qty}", "Итого: {kinds} поз., {qty}", "Total: {kinds} items, {qty}"),
    "crew": ("Brigada: {names}", "Бригада: {names}", "Crew: {names}"),
    "wh": ("Ombor: {name}", "Склад: {name}", "Warehouse: {name}"),
    "guess": ("≈ «{said}» deb tushundim", "≈ понял «{said}» как", "≈ read “{said}” as"),
    "old": ("⚠️ Sana {n} kun oldin. To‘g‘rimi?", "⚠️ Дата {n} дн. назад. Верно?", "⚠️ The date is {n} days ago. Is that right?"),
    "short": ("❌ Xomashyo yetmaydi:", "❌ Не хватает сырья:", "❌ Not enough materials:"),
    "short_row": ("• {name}: kerak {need}, bor {have}", "• {name}: нужно {need}, есть {have}", "• {name}: need {need}, have {have}"),
    "short_tail": ("Avval omborga kirim qiling yoki sonini o‘zgartirib qayta yuboring.", "Сначала оформите приход или измените количество и отправьте заново.",
                   "Receive the materials first, or change the numbers and send again."),
    "ok": ("✅ Tasdiqlash", "✅ Подтвердить", "✅ Confirm"),
    "dup": ("⚠️ Bu ro‘yxat shu sana bilan allaqachon kiritilgan: {number} ({date}). Qayta kiritilmadi.\nBoshqa mahsulot yoki son bo‘lsa, ro‘yxatni o‘zgartirib yuboring.",
            "⚠️ Этот список с этой датой уже записан: {number} ({date}). Повторно не записан.\nЕсли изделия или количество другие, измените список и отправьте снова.",
            "⚠️ This list with this date was already recorded: {number} ({date}). Not recorded again.\nIf the products or numbers differ, change the list and send it again."),
    "dup_wait": ("⚠️ Bu ro‘yxat allaqachon rahbarga yuborilgan, tasdiqlanishini kuting.", "⚠️ Этот список уже отправлен руководителю, ждите подтверждения.",
                 "⚠️ This list was already sent to the manager; wait for the approval."),
    "send": ("✅ Rahbarga yuborish", "✅ Отправить руководителю", "✅ Send to the manager"),
    "sent": ("📨 Rahbarga yuborildi. Tasdiqlansa xabar beraman, hozircha hisobga tushmadi.", "📨 Отправлено руководителю. Сообщу, когда подтвердит; пока в учёт не попало.",
             "📨 Sent to the manager. I will tell you when it is approved; nothing is recorded yet."),
    "no_boss": ("Tasdiqlovchi (admin) botga ulanmagan, shuning uchun yuborib bo‘lmadi. Admin botni ulashi kerak.", "Утверждающий (админ) не подключён к боту, отправить нельзя.",
                "No approver (admin) is linked to the bot, so it cannot be sent."),
    "ask": ("📝 Tasdiqlash so‘ralmoqda — {who}", "📝 Нужно подтверждение — {who}", "📝 Approval needed — {who}"),
    "approve": ("✅ Tasdiqlayman", "✅ Подтверждаю", "✅ Approve"),
    "reject": ("✖️ Rad etish", "✖️ Отклонить", "✖️ Reject"),
    "approved": ("✅ Tasdiqlandi va kiritildi: {number}\n{date}\n{rows}\n(tasdiqladi: {who})", "✅ Подтверждено и записано: {number}\n{date}\n{rows}\n(подтвердил: {who})",
                 "✅ Approved and recorded: {number}\n{date}\n{rows}\n(approved by {who})"),
    "approved_ok": ("✅ Tasdiqlandi: {number}", "✅ Подтверждено: {number}", "✅ Approved: {number}"),
    "rejected": ("✖️ Rahbar rad etdi ({who}). Hech narsa kiritilmadi.", "✖️ Руководитель отклонил ({who}). Ничего не записано.", "✖️ The manager rejected it ({who}). Nothing was recorded."),
    "rejected_ok": ("✖️ Rad etildi, hech narsa kiritilmadi.", "✖️ Отклонено, ничего не записано.", "✖️ Rejected, nothing was recorded."),
    "no": ("✖️ Bekor qilish", "✖️ Отмена", "✖️ Cancel"),
    "done": ("✅ Kiritildi: {number}\n{date}\n{rows}", "✅ Записано: {number}\n{date}\n{rows}", "✅ Recorded: {number}\n{date}\n{rows}"),
    "cancelled": ("Bekor qilindi, hech narsa kiritilmadi.", "Отменено, ничего не записано.", "Cancelled, nothing was recorded."),
    "gone": ("Bu ro‘yxat allaqachon bajarilgan yoki eskirgan. Qayta yuboring.", "Этот список уже обработан или устарел. Отправьте заново.",
             "This list was already handled or has expired. Send it again."),
    "denied": ("Ishlab chiqarish kiritishga ruxsatingiz yo‘q.", "У вас нет права вводить выпуск.", "You may not enter production."),
    "bad_head": ("Ro‘yxatni to‘liq tushunmadim, hech narsa kiritilmadi:", "Не удалось разобрать список, ничего не записано:",
                 "I could not read the whole list, nothing was recorded:"),
    "e_unknown": ("• «{line}» — mahsulot topilmadi", "• «{line}» — изделие не найдено", "• “{line}” — product not found"),
    "e_maybe": ("• «{line}» — topilmadi. Shumi: {options}?", "• «{line}» — не найдено. Это: {options}?", "• “{line}” — not found. Did you mean: {options}?"),
    "e_qty": ("• «{line}» — soni ko‘rsatilmagan", "• «{line}» — не указано количество", "• “{line}” — no quantity"),
    "e_zero": ("• «{line}» — soni 0 dan katta bo‘lishi kerak", "• «{line}» — количество должно быть больше 0", "• “{line}” — quantity must be above 0"),
    "e_future": ("• «{line}» — kelajak sanasi", "• «{line}» — дата в будущем", "• “{line}” — a date in the future"),
    "e_date": ("• «{line}» — sana noto‘g‘ri", "• «{line}» — неверная дата", "• “{line}” — not a valid date"),
    "e_worker": ("• «{line}» — ishchi topilmadi", "• «{line}» — работник не найден", "• “{line}” — worker not found"),
    "e_wh": ("• «{line}» — ombor topilmadi", "• «{line}» — склад не найден", "• “{line}” — warehouse not found"),
    "e_wh_none": ("Ishlab chiqarish ombori topilmadi.", "Производственный склад не найден.", "No workshop warehouse found."),
    "e_total": ("• «Jami: {said}» deb yozilgan, lekin qatorlar yig‘indisi {real}", "• «Итого: {said}», но сумма строк {real}", "• “Total: {said}” but the lines add up to {real}"),
    "e_none": ("Ro‘yxatda mahsulot yo‘q.", "В списке нет изделий.", "No products in the list."),
    "help_line": ("/prod — ishlab chiqarishni ro‘yxat bilan kiritish", "/prod — ввод выпуска списком", "/prod — enter production as a list"),
    "format": ("Ishlab chiqarishni shunday yuboring (har bir qatorda bitta mahsulot):\n\n15.10\nФБС 24.4.6-Т - 40\n2ПК 66,5*10 25 dona\nBrigada: Ali, Vali\n\n"
               "Sana yozilmasa — bugun. «bugun», «kecha» ham bo‘ladi. Brigada va ombor qatorlari ixtiyoriy. "
               "Men o‘qib, ko‘rsataman — «Tasdiqlash»ni bossangizgina kiritiladi.",
               "Отправьте выпуск так (в каждой строке одно изделие):\n\n15.10\nФБС 24.4.6-Т - 40\n2ПК 66,5*10 25 шт\nБригада: Али, Вали\n\n"
               "Без даты — сегодня. Можно «сегодня», «вчера». Строки бригады и склада необязательны. "
               "Я прочитаю и покажу — запись появится только после «Подтвердить».",
               "Send production like this (one product per line):\n\n15.10\nФБС 24.4.6-Т - 40\n2ПК 66,5*10 25 pcs\nCrew: Ali, Vali\n\n"
               "No date means today; “today” and “yesterday” work. Crew and warehouse lines are optional. "
               "I read it and show it back; nothing is recorded until you tap Confirm."),
}


def _t(key: str, lang: str, **kw) -> str:
    return TXT[key][LANG.get(lang, 0)].format(**kw)


# ---------------------------------------------------------------- reading names
_TRANSLIT = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
                     ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u", "f", "h", "ts", "ch", "sh", "sh", "", "y", "", "e", "yu", "ya"]))
_LOOKS = dict(zip("авекмнорстух", "abekmhopctyx"))             # Cyrillic letters that look like Latin ones (typed by mistake)
_TIMES = re.compile(r"(?<=\d)\s*[x×х:]\s*(?=\d)", re.I)          # 66*12, 66x12 and 66:12 are the same size


def _base(s: str) -> str:
    s = _TIMES.sub("*", (s or "").lower().replace(",", ".").replace("ў", "у").replace("қ", "к").replace("ғ", "г").replace("ҳ", "х"))
    return re.sub(r"[\s\-_–—\"'«»“”`’‘]+", "", s)


def keys(s: str) -> set[str]:
    """Spellings that should be treated as the same name: Cyrillic spelled in Latin, and look-alike letters."""
    b = _base(s)
    return {"".join(_TRANSLIT.get(c, c) for c in b), "".join(_LOOKS.get(c, c) for c in b)}


def _score(a: str, b: str) -> float:
    return max((SequenceMatcher(None, x, y).ratio() for x in keys(a) for y in keys(b)), default=0.0)


def _item_names(it: Item) -> list[str]:
    return [n for n in (it.name_uz, it.name_ru, it.name_en) if n]


def _digits(s: str) -> str:
    return "".join(re.findall(r"\d", s or ""))


def _inside(items: list[Item], said: str) -> list[Item]:
    """Products whose name contains what was said as a whole size, e.g. «66*12» in «2ПК 66*12» (not in «166*12»)."""
    if not re.search(r"\d", said):
        return []
    pat = re.compile(r"(?<![\d.*])" + re.escape(_base(said)) + r"(?![\d.*])")
    return [it for it in items if any(pat.search(_base(n)) for n in _item_names(it))]


def match_item(items: list[Item], said: str, fuzzy: bool = True):
    """(item, guessed, hints): the item, whether it was a fuzzy guess, and close names if nothing was clear.
    A guess is only made between names with the very same digits: a different size is a different product."""
    ks = keys(said)
    exact = {it.id: it for it in items if any(keys(n) & ks for n in _item_names(it))}
    if len(exact) == 1:
        return next(iter(exact.values())), False, []
    if len(exact) > 1:
        return None, False, list(exact.values())[:3]
    if not fuzzy:
        return None, False, []
    part = _inside(items, said)
    if len(part) == 1:
        return part[0], True, []
    if len(part) > 1:
        return None, False, part[:3]
    ranked = sorted(((max((_score(said, n) for n in _item_names(it) if _digits(n) == _digits(said)), default=0.0), it) for it in items), key=lambda x: -x[0])
    if ranked and ranked[0][0] >= FUZZY_OK and (len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= FUZZY_GAP):
        return ranked[0][1], True, []
    return None, False, [it for sc, it in ranked[:3] if sc >= FUZZY_HINT]


# ---------------------------------------------------------------- reading lines
_QTY = re.compile(r"^(?P<name>.+?)[\s:=\-–—]*[xх×]?\s*(?P<q>\d+(?:[.,]\d+)?)\s*(?:ta|dona|dn|sht|pcs|шт|штук[и]?)?\.?\s*$", re.I)
_QTY_FIRST = re.compile(r"^(?P<q>\d+(?:[.,]\d+)?)\s*(?:ta|dona|dn|sht|pcs|шт|штук[и]?)\.?\s+(?P<name>.+)$", re.I)
_BULLET = re.compile(r"^\s*(?:[•\-–—*]+|\d{1,2}[.)])\s+")
_DATE = re.compile(r"^(?:(?:sana|дата|date)\s*[:\-]?\s*)?(?P<d>\d{1,2})[./-](?P<m>\d{1,2})(?:[./-](?P<y>\d{2,4}))?$", re.I)
_DAYWORD = {"bugun": 0, "сегодня": 0, "today": 0, "kecha": -1, "вчера": -1, "yesterday": -1}
_TOTAL = re.compile(r"^(?:jami|итого|всего|total|summa)\s*[:\-=]?\s*(?P<n>\d+(?:[.,]\d+)?)\s*(?:ta|dona|dn|sht|pcs|шт|штук[и]?)?\.?$", re.I)
_CREW = re.compile(r"^(?:brigada|бригада|crew|ishchilar|рабочие)\s*[:\-]\s*(?P<v>.+)$", re.I)
_WH = re.compile(r"^(?:ombor|sklad|склад|zavod|завод|warehouse)\s*[:\-]\s*(?P<v>.+)$", re.I)


def _split_qty(line: str, items: list[Item]):
    """(name, qty, guess) for one product line, or (name, None, ..) when the quantity is missing."""
    whole, _, _ = match_item(items, line, fuzzy=False)
    if whole is not None:
        return line, None, whole
    m = _QTY_FIRST.match(line) or _QTY.match(line)
    if not m:
        return line, None, None
    return m.group("name").strip(" :=-–—xх×"), Decimal(m.group("q").replace(",", ".")), None


def parse(db: Session, text: str, lang: str, now: datetime):
    """Returns (draft dict, errors, notes). `errors` empty means the list was fully understood."""
    items = db.query(Item).filter(Item.kind == "product", Item.is_active).all()
    day, errors, guesses, known, said_total = now.date(), [], [], False, None
    rows: dict[int, Decimal] = {}
    crew_line = wh_line = None
    for raw in (text or "").splitlines():
        line = _BULLET.sub("", raw.strip()).strip()
        if not line:
            continue
        w = _DAYWORD.get(line.lower().rstrip(".:"))
        if w is not None:
            day = now.date() + timedelta(days=w)
            continue
        m = _DATE.match(line)
        if m:
            try:
                y = int(m.group("y") or now.year)
                y += 2000 if y < 100 else 0
                day = datetime(y, int(m.group("m")), int(m.group("d"))).date()
            except ValueError:
                errors.append(_t("e_date", lang, line=line))
                continue
            if day > now.date() + timedelta(days=1):
                errors.append(_t("e_future", lang, line=line))
            continue
        tm = _TOTAL.match(line)
        if tm:
            said_total = Decimal(tm.group("n").replace(",", "."))
            continue
        if _CREW.match(line):
            crew_line = _CREW.match(line).group("v")
            continue
        if _WH.match(line):
            wh_line = _WH.match(line).group("v")
            continue
        name, qty, whole = _split_qty(line, items)
        if whole is not None:
            errors.append(_t("e_qty", lang, line=line))
            continue
        if qty is None:
            _, _, hints = match_item(items, line)
            errors.append(_t("e_maybe", lang, line=line, options=", ".join(f"«{_label(h, lang)}»" for h in hints)) if hints else _t("e_unknown", lang, line=line))
            continue
        it, guessed, hints = match_item(items, name)
        if it is None:
            errors.append(_t("e_maybe", lang, line=line, options=", ".join(f"«{_label(h, lang)}»" for h in hints)) if hints else _t("e_unknown", lang, line=line))
            continue
        known = True
        if qty <= 0:
            errors.append(_t("e_zero", lang, line=line))
            continue
        if guessed:
            guesses.append(_t("guess", lang, said=name) + f" «{_label(it, lang)}»")
        rows[it.id] = rows.get(it.id, Decimal(0)) + qty
    if not rows and not errors:
        errors.append(_t("e_none", lang))
    if said_total is not None and rows and not errors and sum(rows.values()) != said_total:
        errors.append(_t("e_total", lang, said=_num(said_total), real=_num(sum(rows.values()))))
    wh = _warehouse(db, wh_line, lang, errors) if rows or errors else None
    crew = _crew(db, crew_line, lang, errors) if crew_line else []
    draft = {"date": day.isoformat(), "wh": wh.id if wh else None, "rows": {str(k): str(v) for k, v in rows.items()}, "crew": crew}
    draft["known"] = known
    return draft, errors, guesses


def _warehouse(db: Session, said: str | None, lang: str, errors: list[str]):
    shops = db.query(Warehouse).filter(Warehouse.is_active).order_by(Warehouse.sort_order, Warehouse.id).all()
    if said:
        ks = keys(said)
        hit = [w for w in shops if keys(w.name) & ks] or [w for w in shops if any(k in kk for k in ks for kk in keys(w.name))]
        if len(hit) == 1:
            return hit[0]
        errors.append(_t("e_wh", lang, line=said))
        return None
    work = [w for w in shops if w.is_workshop] or (shops if len(shops) == 1 else [])
    if work:
        return work[0]                                                   # the first workshop; the preview always names it
    errors.append(_t("e_wh_none", lang))
    return None


def _crew(db: Session, said: str, lang: str, errors: list[str]) -> list[int]:
    people = db.query(Worker).filter(Worker.is_active).all()
    out: list[int] = []
    for part in re.split(r"[,;\n]+|\s+va\s+|\s+и\s+|\s+and\s+", said):
        part = part.strip()
        if not part:
            continue
        ks = keys(part)
        hit = [p for p in people if keys(p.name) & ks] or [p for p in people if any(k and k in kk for k in ks for kk in keys(p.name))]
        if len(hit) == 1:
            out.append(hit[0].id)
        else:
            errors.append(_t("e_worker", lang, line=part))
    return list(dict.fromkeys(out))


# ---------------------------------------------------------------- preview, confirm, cancel
def _label(it: Item, lang: str) -> str:
    return getattr(it, "name_" + lang, None) or it.name_uz


def _num(x) -> str:
    x = Decimal(str(x))
    return f"{x:f}".rstrip("0").rstrip(".") if x != x.to_integral() else f"{int(x)}"


def _shortages(db: Session, draft: dict, lang: str) -> list[str]:
    made = {int(k): Decimal(v) for k, v in draft["rows"].items()}
    out = []
    for mid, need in production.material_need(db, made).items():
        have = stock.balance(db, mid, draft["wh"])
        if need > have:
            it = db.get(Item, mid)
            out.append(_t("short_row", lang, name=_label(it, lang), need=_num(need), have=_num(have)))
    return out


def _same_rows(a: dict[int, Decimal], b: dict[int, Decimal]) -> bool:
    return {k: v for k, v in a.items() if v} == {k: v for k, v in b.items() if v}


def duplicate_of(db: Session, draft: dict):
    """A production document already recorded for the same day and warehouse with exactly the same products and numbers."""
    day = datetime.fromisoformat(draft["date"])
    mine = {int(k): Decimal(v) for k, v in draft["rows"].items()}
    docs = db.query(ProductionDoc).filter(ProductionDoc.status == "posted", ProductionDoc.warehouse_id == draft["wh"],
                                          ProductionDoc.date >= day.replace(hour=0, minute=0, second=0, microsecond=0),
                                          ProductionDoc.date < day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).all()
    for d in docs:
        theirs: dict[int, Decimal] = {}
        for r in d.rows:
            theirs[r.item_id] = theirs.get(r.item_id, Decimal(0)) + Decimal(r.qty)
        if _same_rows(mine, theirs):
            return d
    return None


def _waiting_twin(db: Session, draft: dict, exclude_id: int | None = None) -> bool:
    for dr in db.query(TelegramDraft).filter(TelegramDraft.status == "pending").all():
        if dr.id != exclude_id and datetime.utcnow() - dr.created_at <= PENDING_TTL:
            other = json.loads(dr.payload)
            if other["date"] == draft["date"] and other["wh"] == draft["wh"] and _same_rows({int(k): Decimal(v) for k, v in other["rows"].items()}, {int(k): Decimal(v) for k, v in draft["rows"].items()}):
                return True
    return False


def _lines(db: Session, draft: dict, lang: str, now: datetime) -> list[str]:
    d = datetime.fromisoformat(draft["date"])
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_([int(k) for k in draft["rows"]]))}
    body = [f"• {_label(items[int(k)], lang)} — {_num(v)} {items[int(k)].unit.name}" for k, v in draft["rows"].items()]
    qty = sum(Decimal(v) for v in draft["rows"].values())
    out = [_t("title", lang, date=d.strftime("%d.%m.%Y")), *body, _t("total", lang, kinds=len(body), qty=_num(qty)),
           _t("wh", lang, name=db.get(Warehouse, draft["wh"]).name)]
    if draft["crew"]:
        out.append(_t("crew", lang, names=", ".join(w.name for w in db.query(Worker).filter(Worker.id.in_(draft["crew"])))))
    out += draft.get("guesses", [])
    age = (now.date() - d.date()).days
    if age > 7:
        out.append(_t("old", lang, n=age))
    return out


def is_approver(user) -> bool:
    """Admins enter production directly; everyone else's list goes to an admin first."""
    return user.role == "admin"


def preview(db: Session, user, chat_id: int, text: str, lang: str, now: datetime) -> dict | None:
    """The reply to a message that may be a production list; None = it is not one (the caller treats it as a normal message)."""
    lines = [x for x in (text or "").splitlines() if x.strip()]
    draft, errors, guesses = parse(db, text, lang, now)
    known = draft.pop("known")
    looks_like = bool(draft["rows"]) or known or (len(lines) >= 2 and any(re.search(r"\d", x) for x in lines))
    if not looks_like:
        return None
    if errors:
        return {"text": _t("bad_head", lang) + "\n" + "\n".join(errors), "markup": None, "edit": False}
    draft["guesses"] = guesses
    out = _lines(db, draft, lang, now)
    twin = duplicate_of(db, draft)
    if twin is not None:
        return {"text": "\n".join(out + ["", _t("dup", lang, number=twin.number, date=twin.date.strftime("%d.%m.%Y"))]), "markup": None, "edit": False}
    if _waiting_twin(db, draft):
        return {"text": "\n".join(out + ["", _t("dup_wait", lang)]), "markup": None, "edit": False}
    short = _shortages(db, draft, lang)
    if short:
        return {"text": "\n".join(out + ["", _t("short", lang), *short, _t("short_tail", lang)]), "markup": None, "edit": False}
    db.query(TelegramDraft).filter(TelegramDraft.user_id == user.id, TelegramDraft.status == "draft").delete()   # one unsent list per person
    dr = TelegramDraft(user_id=user.id, chat_id=chat_id, payload=json.dumps(draft), status="draft")
    db.add(dr)
    db.flush()
    kb = [[{"text": _t("ok" if is_approver(user) else "send", lang), "callback_data": f"pr:ok:{dr.id}"}, {"text": _t("no", lang), "callback_data": f"pr:no:{dr.id}"}]]
    return {"text": "\n".join(out), "markup": {"inline_keyboard": kb}, "edit": False}


def _msg(text: str, edit: bool = True, to: int | None = None, markup: dict | None = None) -> dict:
    m = {"text": text, "markup": markup, "edit": edit}
    if to is not None:
        m["to"] = to
    return m


def _lang_of(db: Session, user_id: int) -> str:
    lk = db.get(TelegramLink, user_id)
    return lk.lang if lk else "uz"


def _record(db: Session, draft: dict, who: str, now: datetime):
    """Create the production document through the same service as the website. Returns (doc, None) or (None, error text)."""
    twin = duplicate_of(db, draft)
    if twin is not None:
        return None, _t("dup", "uz", number=twin.number, date=twin.date.strftime("%d.%m.%Y"))
    data = ProductionIn(date=_when(draft["date"], now), warehouse_id=draft["wh"], comment=f"Telegram · {who}", worker_ids=draft["crew"],
                        rows=[ProdRowIn(item_id=int(k), qty=float(v)) for k, v in draft["rows"].items()])
    sp = db.begin_nested()
    try:
        doc = production.create_production(db, data)
        sp.commit()
        return doc, None
    except ApiError as e:
        sp.rollback()
        d = e.detail if isinstance(e.detail, dict) else {}
        return None, "❌ " + str(d.get("message") or e.detail)


def _rows_text(db: Session, doc, lang: str) -> str:
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_([r.item_id for r in doc.rows]))}
    return "\n".join(f"• {_label(items[r.item_id], lang)} — {_num(r.qty)} {items[r.item_id].unit.name}" for r in doc.rows)


def answer(db: Session, user, chat_id: int, lang: str, action: str, draft_id: int, now: datetime) -> list[dict]:
    """A tap on a production list. ok/no: the sender (admins record at once, others send it to an admin).
    ap/rj: an admin approves or rejects a list that is waiting. Messages with `to` go to another chat."""
    dr = db.get(TelegramDraft, draft_id)
    gone = [_msg(_t("gone", lang))]
    if dr is None:
        return gone
    age = datetime.utcnow() - dr.created_at
    if age > (PENDING_TTL if dr.status == "pending" else DRAFT_TTL):
        return gone
    draft = json.loads(dr.payload)
    sender = db.get(User, dr.user_id)
    slang = _lang_of(db, dr.user_id)
    if action in ("ap", "rj"):
        if not is_approver(user) or dr.status != "pending":
            return gone
        db.delete(dr)
        if action == "rj":
            return [_msg(_t("rejected_ok", lang)), _msg(_t("rejected", slang, who=user.full_name), edit=False, to=dr.chat_id)]
        doc, err = _record(db, draft, sender.full_name, now)
        if err:
            return [_msg(err), _msg(err, edit=False, to=dr.chat_id)]
        return [_msg(_t("approved_ok", lang, number=doc.number)),
                _msg(_t("approved", slang, number=doc.number, date=doc.date.strftime("%d.%m.%Y"), rows=_rows_text(db, doc, slang), who=user.full_name), edit=False, to=dr.chat_id)]
    if dr.user_id != user.id or dr.chat_id != chat_id:
        return gone
    if action == "no":
        db.delete(dr)
        return [_msg(_t("cancelled", lang))]
    if dr.status != "draft":
        return gone
    if is_approver(user):
        db.delete(dr)
        doc, err = _record(db, draft, user.full_name, now)
        return [_msg(err or _t("done", lang, number=doc.number, date=doc.date.strftime("%d.%m.%Y"), rows=_rows_text(db, doc, lang)))]
    bosses = [(b, lk) for b, lk in db.query(User, TelegramLink).join(TelegramLink, TelegramLink.user_id == User.id).filter(User.role == "admin", User.is_active)]
    if not bosses:
        return [_msg(_t("no_boss", lang))]
    dr.status, dr.created_at = "pending", datetime.utcnow()
    out = [_msg(_t("sent", lang))]
    for _, lk in bosses:
        kb = {"inline_keyboard": [[{"text": _t("approve", lk.lang), "callback_data": f"pr:ap:{dr.id}"}, {"text": _t("reject", lk.lang), "callback_data": f"pr:rj:{dr.id}"}]]}
        text = _t("ask", lk.lang, who=sender.full_name) + "\n" + "\n".join(_lines(db, draft, lk.lang, now))
        out.append(_msg(text, edit=False, to=lk.chat_id, markup=kb))
    return out


def _when(day_iso: str, now: datetime) -> datetime:
    """Today keeps the current time, another day is recorded at noon."""
    d = datetime.fromisoformat(day_iso)
    return now.replace(microsecond=0) if d.date() == now.date() else d.replace(hour=12)
