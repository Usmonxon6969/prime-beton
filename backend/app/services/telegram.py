"""Telegram bot logic, kept free of any network code so it can be tested: a message comes in, a reply goes out.

Who is who: a user links a chat by typing a one-time code (made in the web app) to the bot. From then on the chat can ask
only what that user's role may see. Messages from unlinked chats get nothing but the linking instructions.
"""
import hashlib
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai import insights
from app.core.config import settings
from app.core.roles import SECTIONS, level
from app.models import (Account, AuditLog, Customer, FinDoc, Invoice, Item, Order, ProductionDoc, StockBalance, Supplier, TelegramCode,
                        TelegramCursor, TelegramLink, TelegramSent, User)
from app.services import finance, reports
from app.services import telegram_prod as prod_bot

CODE_TTL = timedelta(minutes=10)
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"      # no 0/O/1/I
RESEND_AFTER = timedelta(days=3)
LANGS = ("uz", "ru", "en")
_fails: dict[int, list[datetime]] = {}


def _h(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def new_code(db: Session, user: User, now: datetime | None = None) -> str:
    now = now or datetime.utcnow()
    db.query(TelegramCode).filter(TelegramCode.user_id == user.id).delete()
    code = "".join(secrets.choice(ALPHABET) for _ in range(8))
    db.add(TelegramCode(code_hash=_h(code), user_id=user.id, expires_at=now + CODE_TTL))
    db.flush()
    return code


def _throttled(chat_id: int, now: datetime) -> bool:
    recent = [t for t in _fails.get(chat_id, []) if now - t < timedelta(minutes=10)]
    _fails[chat_id] = recent
    return len(recent) >= 5


def link(db: Session, chat_id: int, code: str, now: datetime | None = None) -> User | None:
    now = now or datetime.utcnow()
    if _throttled(chat_id, now):
        return None
    row = db.get(TelegramCode, _h(code))
    if row is None or row.expires_at < now:
        _fails.setdefault(chat_id, []).append(now)
        return None
    user = db.get(User, row.user_id)
    db.delete(row)
    if user is None or not user.is_active:
        return None
    db.query(TelegramLink).filter(TelegramLink.chat_id == chat_id, TelegramLink.user_id != user.id).delete()
    cur = db.get(TelegramLink, user.id)
    if cur:
        cur.chat_id = chat_id
    else:
        db.add(TelegramLink(user_id=user.id, chat_id=chat_id, digest_hour=settings.telegram_digest_hour))
    db.flush()
    return user


def unlink(db: Session, user_id: int) -> None:
    db.query(TelegramLink).filter(TelegramLink.user_id == user_id).delete()
    db.query(TelegramSent).filter(TelegramSent.user_id == user_id).delete()


TXT = {
    "unlinked": ("Bu chat hali tizimga ulanmagan. Veb-ilovada «Xavfsizlik → Telegram» bo‘limida kod oling va menga yuboring: /start KOD",
                 "Этот чат ещё не привязан. Получите код в веб-приложении («Безопасность → Telegram») и отправьте: /start КОД",
                 "This chat is not linked yet. Get a code in the web app (Security → Telegram) and send: /start CODE"),
    "bad_code": ("Kod noto‘g‘ri yoki muddati o‘tgan. Veb-ilovada yangi kod oling.", "Код неверный или просрочен. Получите новый в веб-приложении.",
                 "The code is wrong or expired. Get a new one in the web app."),
    "linked": ("Ulandi: {name}. Buyruqlar: /help", "Привязано: {name}. Команды: /help", "Linked as {name}. Commands: /help"),
    "help": ("Buyruqlar:\n/brief — muhim signallar\n/stock nom — qoldiq\n/debts — mijoz qarzlari\n/cash — hisoblardagi pul\n/alerts on|off — avto-xabarlar\n/lang uz|ru|en\n/unlink — ulanishni uzish",
             "Команды:\n/brief — важные сигналы\n/stock название — остаток\n/debts — долги покупателей\n/cash — деньги на счетах\n/alerts on|off — авто-уведомления\n/lang uz|ru|en\n/unlink — отвязать",
             "Commands:\n/brief — key signals\n/stock name — stock level\n/debts — customer debts\n/cash — money on accounts\n/alerts on|off — automatic alerts\n/lang uz|ru|en\n/unlink — disconnect"),
    "denied": ("Rolingiz bu ma’lumotga ruxsat bermaydi.", "Ваша роль не позволяет смотреть эти данные.", "Your role cannot see this."),
    "nothing": ("Hozircha muhim signal yo‘q.", "Пока важных сигналов нет.", "No important signals right now."),
    "stock_q": ("Qaysi pozitsiya? Masalan: /stock sement", "Какая позиция? Например: /stock цемент", "Which item? For example: /stock cement"),
    "stock_none": ("Topilmadi.", "Не найдено.", "Nothing found."),
    "no_debts": ("Mijoz qarzlari yo‘q.", "Долгов покупателей нет.", "No customer debts."),
    "alerts_on": ("Avto-xabarlar yoqildi.", "Авто-уведомления включены.", "Automatic alerts are on."),
    "alerts_off": ("Avto-xabarlar o‘chirildi.", "Авто-уведомления выключены.", "Automatic alerts are off."),
    "lang_ok": ("Til: o‘zbekcha.", "Язык: русский.", "Language: English."),
    "unlinked_ok": ("Ulanish uzildi.", "Чат отвязан.", "Disconnected."),
    "unknown": ("Tushunmadim. /help", "Не понял. /help", "I did not get that. /help"),
    "inactive": ("Foydalanuvchi o‘chirilgan.", "Пользователь отключён.", "This user is disabled."),
}
L = {"uz": 0, "ru": 1, "en": 2}


def _t(key: str, lang: str, **kw) -> str:
    return TXT[key][L.get(lang, 0)].format(**kw)


def levels_of(user: User) -> dict:
    return {s: level(user.role, s) for s in SECTIONS}


def _fmt(n) -> str:
    return f"{float(n):,.0f}".replace(",", " ")


MARK = {"crit": "🔴", "warn": "🟠", "info": "🔵"}


def _brief(db, user, lang, now):
    ins = [i for i in insights.collect(db, levels_of(user), lang, now) if i["severity"] != "info"][:8]
    return "\n".join(f"{MARK[i['severity']]} {i['text']}" for i in ins) if ins else _t("nothing", lang)


def _stock(db, lv, lang, q):
    q = q.strip().lower()
    if not q:
        return _t("stock_q", lang)
    tot = {k: v for k, v in db.execute(select(StockBalance.item_id, func.sum(StockBalance.qty)).group_by(StockBalance.item_id))}
    out = []
    for it in db.query(Item).filter(Item.is_active):
        if any(q in (getattr(it, f"name_{c}") or "").lower() for c in LANGS):
            out.append(f"{getattr(it, 'name_' + lang)}: {_fmt(tot.get(it.id, 0))} {it.unit.name}")
    return "\n".join(out[:8]) if out else _t("stock_none", lang)


def _debts(db, lang):
    rows = sorted((d for d in reports.customer_debts(db) if d["debt"] > 0), key=lambda d: -d["debt"])[:8]
    return "\n".join(f"{d['name']}: {_fmt(d['debt'])}" for d in rows) if rows else _t("no_debts", lang)


def _cash(db, lv, lang):
    bal = finance.balances(db)
    rows = [f"{getattr(a, 'name_' + lang, None) or a.name_en}: {_fmt(bal[a.id])}" for a in db.query(Account).filter(Account.is_active) if lv.get(a.kind, 0) >= 1]
    return "\n".join(rows)


def handle(db: Session, chat_id: int, text: str, now: datetime | None = None) -> str | None:
    """Reply for one private message (None = stay silent)."""
    now = now or datetime.utcnow()
    parts = (text or "").strip().split()
    if not parts:
        return None
    cmd = parts[0].lower().split("@")[0]
    arg = " ".join(parts[1:])
    lk = db.query(TelegramLink).filter(TelegramLink.chat_id == chat_id).first()
    if cmd == "/start" and arg:
        u = link(db, chat_id, arg, now)
        if u is None:
            return _t("bad_code", lk.lang if lk else "uz")
        db.info["user"] = {"id": u.id, "username": u.username}
        lk = db.get(TelegramLink, u.id)
        return _t("linked", lk.lang, name=u.full_name) + "\n\n" + _t("help", lk.lang)
    if lk is None:
        return "\n\n".join(_t("unlinked", c) for c in LANGS)       # a stranger's language is unknown: say it in all three
    user = db.get(User, lk.user_id)
    lang = lk.lang
    if user is None or not user.is_active:
        return _t("inactive", lang)
    db.info["user"] = {"id": user.id, "username": user.username}
    lv = levels_of(user)
    if cmd in ("/prod", "/ishlab"):
        return prod_bot._t("format", lang) if lv["prod"] >= 2 else prod_bot._t("denied", lang)
    if cmd in ("/start", "/help"):
        return _t("help", lang) + ("\n" + prod_bot._t("help_line", lang) if lv["prod"] >= 2 else "")
    if cmd == "/lang":
        if arg.lower() in LANGS:
            lk.lang = arg.lower()
            return _t("lang_ok", lk.lang)
        return _t("help", lang)
    if cmd == "/alerts":
        lk.notify = arg.lower() != "off"
        return _t("alerts_on" if lk.notify else "alerts_off", lang)
    if cmd == "/unlink":
        unlink(db, user.id)
        return _t("unlinked_ok", lang)
    if cmd == "/brief":
        return _brief(db, user, lang, now)
    if cmd == "/stock":
        return _t("denied", lang) if lv["wh"] < 1 else _stock(db, lv, lang, arg)
    if cmd == "/debts":
        return _t("denied", lang) if lv["cus"] < 1 else _debts(db, lang)
    if cmd == "/cash":
        r = _cash(db, lv, lang) if (lv["bank"] or lv["cash"]) else ""
        return r or _t("denied", lang)
    return _t("unknown", lang)


def due_alerts(db: Session, now: datetime | None = None) -> list[tuple[int, str]]:
    """New crit/warn signals for every linked user who wants them: [(chat_id, text)]. Each signal is sent once per 3 days."""
    now = now or datetime.now()
    db.query(TelegramSent).filter(TelegramSent.sent_at < now - RESEND_AFTER).delete()
    out = []
    for lk in db.query(TelegramLink).filter(TelegramLink.notify.is_(True)):
        user = db.get(User, lk.user_id)
        if user is None or not user.is_active:
            continue
        done = {k for (k,) in db.execute(select(TelegramSent.key).where(TelegramSent.user_id == user.id))}
        fresh = [i for i in insights.collect(db, levels_of(user), lk.lang, now) if i["severity"] in ("crit", "warn") and i["id"] not in done][:5]
        if not fresh:
            continue
        for i in fresh:
            db.add(TelegramSent(user_id=user.id, key=i["id"][:100], sent_at=now))
        out.append((lk.chat_id, "\n".join(f"{MARK[i['severity']]} {i['text']}" for i in fresh)))
    db.flush()
    return out


# ---------------------------------------------------------------- buttons
# handle() above answers text commands. The functions below put buttons on top of it: a permanent keyboard under the input
# field (only the buttons this user's role may use), inline buttons for picking an item and for settings. Typing a command
# still works. Every message is a dict {"text", "markup", "edit"}; app/telegram_bot.py turns it into Telegram API calls.
TXT.update({
    "pick_item": ("Pozitsiyani tanlang yoki nomini yozing:", "Выберите позицию или напишите название:", "Pick an item or type its name:"),
    "settings": ("Sozlamalar", "Настройки", "Settings"),
    "lang_cur": ("Til", "Язык", "Language"),
    "alerts_cur": ("Avto-xabarlar", "Авто-уведомления", "Automatic alerts"),
    "on": ("yoqilgan", "включены", "on"),
    "off": ("o‘chirilgan", "выключены", "off"),
    "btn_alerts_on": ("🔔 Avto-xabarlarni yoqish", "🔔 Включить уведомления", "🔔 Turn alerts on"),
    "btn_alerts_off": ("🔕 Avto-xabarlarni o‘chirish", "🔕 Выключить уведомления", "🔕 Turn alerts off"),
    "btn_unlink": ("🔌 Ulanishni uzish", "🔌 Отвязать чат", "🔌 Disconnect"),
    "unlink_ask": ("Ulanishni uzasizmi? Bu chatga xabarlar kelmay qoladi.", "Отвязать чат? Уведомления перестанут приходить.",
                   "Disconnect this chat? You will stop getting messages."),
    "yes_unlink": ("Ha, uzish", "Да, отвязать", "Yes, disconnect"),
    "cancel": ("Bekor qilish", "Отмена", "Cancel"),
    "use_buttons": ("Pastdagi tugmalardan foydalaning.", "Пользуйтесь кнопками внизу.", "Use the buttons below."),
})
BTN = {                                           # reply-keyboard labels in every language: a tap arrives as plain text
    "brief": ("📋 Signallar", "📋 Сигналы", "📋 Signals"),
    "stock": ("📦 Ombor", "📦 Склад", "📦 Stock"),
    "debts": ("💳 Qarzlar", "💳 Долги", "💳 Debts"),
    "cash": ("💵 Kassa", "💵 Касса", "💵 Cash"),
    "settings": ("⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings"),
}
_ACTION_OF = {label: act for act, labels in BTN.items() for label in labels}
LANG_NAME = {"uz": "O‘zbekcha", "ru": "Русский", "en": "English"}


def keyboard(user: User, lang: str) -> dict:
    """The permanent keyboard: only what the role may open."""
    lv = levels_of(user)
    acts = ["brief"]
    if lv["wh"] >= 1:
        acts.append("stock")
    if lv["cus"] >= 1:
        acts.append("debts")
    if lv["bank"] or lv["cash"]:
        acts.append("cash")
    acts.append("settings")
    btns = [{"text": BTN[a][L.get(lang, 0)]} for a in acts]
    return {"keyboard": [btns[i:i + 2] for i in range(0, len(btns), 2)], "resize_keyboard": True, "is_persistent": True}


def _msg(text: str, markup: dict | None = None, edit: bool = False) -> dict:
    return {"text": text, "markup": markup, "edit": edit}


def _stock_picker(db, lv, lang):
    if lv["wh"] < 1:
        return _msg(_t("denied", lang))
    tot = {k: v for k, v in db.execute(select(StockBalance.item_id, func.sum(StockBalance.qty)).group_by(StockBalance.item_id))}
    items = [i for i in db.query(Item).filter(Item.is_active) if tot.get(i.id, 0)]
    items.sort(key=lambda i: (getattr(i, "name_" + lang) or "").lower())
    btns = [{"text": (getattr(i, "name_" + lang) or i.name_en)[:40], "callback_data": f"s:{i.id}"} for i in items[:24]]
    if not btns:
        return _msg(_t("stock_none", lang))
    return _msg(_t("pick_item", lang), {"inline_keyboard": [btns[i:i + 2] for i in range(0, len(btns), 2)]})


def _item_line(db, lang, item_id: int):
    it = db.get(Item, item_id)
    if it is None or not it.is_active:
        return _t("stock_none", lang)
    rows = db.query(StockBalance.warehouse_id, StockBalance.qty).filter(StockBalance.item_id == it.id, StockBalance.qty != 0).all()
    from app.models import Warehouse
    names = {w.id: w.name for w in db.query(Warehouse)}
    total = sum(q for _, q in rows)
    lines = [f"{getattr(it, 'name_' + lang) or it.name_en}: {_fmt(total)} {it.unit.name}"]
    if len(rows) > 1:
        lines += [f"  • {names.get(w, w)}: {_fmt(q)}" for w, q in sorted(rows, key=lambda r: -r[1])]
    return "\n".join(lines)


def _topics(lk) -> set:
    return {x for x in (lk.topics or "").split(",") if x}


def _settings_panel(lk, lang, edit=False, user=None):
    state = _t("on" if lk.notify else "off", lang)
    text = f"{_t('settings', lang)}\n{_t('lang_cur', lang)}: {LANG_NAME[lang]}\n{_t('alerts_cur', lang)}: {state}"
    rows = [[{"text": LANG_NAME[c] if c != lang else f"✓ {LANG_NAME[c]}", "callback_data": f"l:{c}"} for c in LANGS],
            [{"text": _t("btn_alerts_off" if lk.notify else "btn_alerts_on", lang), "callback_data": "a:off" if lk.notify else "a:on"}]]
    if user is not None:
        lv, mine = levels_of(user), _topics(lk)
        tb = [{"text": ("✓ " if k in mine else "▫️ ") + TOPIC_LABEL[k][L.get(lang, 0)], "callback_data": f"t:{k}"} for k in TOPICS if _topic_allowed(k, lv)]
        text += "\n" + _t("topics_cur", lang)
        rows += [tb[i:i + 2] for i in range(0, len(tb), 2)]
        rows.append([{"text": _t("all_on", lang), "callback_data": "t:all"}, {"text": _t("all_off", lang), "callback_data": "t:none"}])
        if "digest" in mine:
            text += f"\n{_t('hour_cur', lang)}: {lk.digest_hour:02d}:00"
            rows.append([{"text": (f"✓ {h:02d}:00" if h == lk.digest_hour else f"{h:02d}:00"), "callback_data": f"h:{h}"} for h in DIGEST_HOURS])
        rows.append([{"text": _t("quiet_off" if lk.quiet else "quiet_on", lang), "callback_data": "q:x"}])
    rows.append([{"text": _t("btn_unlink", lang), "callback_data": "u:ask"}])
    return _msg(text, {"inline_keyboard": rows}, edit)


def handle_full(db: Session, chat_id: int, text: str, now: datetime | None = None) -> dict | None:
    """Like handle(), but understands the keyboard buttons and attaches them to the reply."""
    now = now or datetime.utcnow()
    t = (text or "").strip()
    if not t:
        return None
    lk = db.query(TelegramLink).filter(TelegramLink.chat_id == chat_id).first()
    act = _ACTION_OF.get(t)
    if lk is None or t.split()[0].lower().split("@")[0] == "/start":   # strangers and the linking step: the plain flow
        r = handle(db, chat_id, t, now)
        if r is None:
            return None
        lk = db.query(TelegramLink).filter(TelegramLink.chat_id == chat_id).first()
        user = db.get(User, lk.user_id) if lk else None
        return _msg(r, keyboard(user, lk.lang) if user and user.is_active else None)
    user = db.get(User, lk.user_id)
    lang = lk.lang
    if user is None or not user.is_active:
        return _msg(_t("inactive", lang), {"remove_keyboard": True})
    db.info["user"] = {"id": user.id, "username": user.username}
    lv = levels_of(user)
    if act == "settings":
        return _settings_panel(lk, lang, user=user)
    if act == "stock":
        return _stock_picker(db, lv, lang)
    if act:
        t = "/" + act
    elif not t.startswith("/"):
        if lv["prod"] >= 2:                                            # a production list from someone who may enter production
            r = prod_bot.preview(db, user, chat_id, t, lang, local_now(now))
            if r is not None:
                return r
        t = "/stock " + t if lv["wh"] >= 1 else "/help"                # otherwise a plain word is a stock search
    r = handle(db, chat_id, t, now)
    if r is None:
        return None
    lk = db.query(TelegramLink).filter(TelegramLink.chat_id == chat_id).first()
    if lk is None:                                                     # /unlink: take the keyboard away
        return _msg(r, {"remove_keyboard": True})
    return _msg(r, keyboard(user, lk.lang))


def callback(db: Session, chat_id: int, data: str, now: datetime | None = None) -> list[dict]:
    """An inline-button tap. Returns the messages to send/edit; [] = nothing."""
    lk = db.query(TelegramLink).filter(TelegramLink.chat_id == chat_id).first()
    if lk is None:
        return [_msg("\n\n".join(_t("unlinked", c) for c in LANGS))]
    user = db.get(User, lk.user_id)
    lang = lk.lang
    if user is None or not user.is_active:
        return [_msg(_t("inactive", lang), {"remove_keyboard": True})]
    db.info["user"] = {"id": user.id, "username": user.username}
    kind, _, val = (data or "").partition(":")
    if kind == "pr":
        act, _, did = val.partition(":")
        if act in ("ok", "no", "ap", "rj") and did.isdigit():
            if levels_of(user)["prod"] < 2:
                return [_msg(prod_bot._t("denied", lang))]
            return prod_bot.answer(db, user, chat_id, lang, act, int(did), local_now(now))
        return []
    if kind == "s" and val.isdigit():
        if levels_of(user)["wh"] < 1:
            return [_msg(_t("denied", lang))]
        return [_msg(_item_line(db, lang, int(val)))]
    if kind == "l" and val in LANGS:
        lk.lang = val
        return [_settings_panel(lk, val, edit=True, user=user), _msg(_t("lang_ok", val), keyboard(user, val))]
    if kind == "a" and val in ("on", "off"):
        lk.notify = val == "on"
        return [_settings_panel(lk, lang, edit=True, user=user)]
    if kind == "t" and val in ("all", "none"):
        allowed = [k for k in TOPICS if _topic_allowed(k, levels_of(user))]
        lk.topics = ",".join(allowed) if val == "all" else ""
        lk.notify = val == "all"
        return [_settings_panel(lk, lang, edit=True, user=user)]
    if kind == "t" and val in TOPICS:
        cur = _topics(lk)
        cur.symmetric_difference_update({val})
        lk.topics = ",".join(k for k in TOPICS if k in cur)
        return [_settings_panel(lk, lang, edit=True, user=user)]
    if kind == "h" and val.isdigit() and int(val) in DIGEST_HOURS:
        lk.digest_hour = int(val)
        return [_settings_panel(lk, lang, edit=True, user=user)]
    if kind == "q":
        lk.quiet = not lk.quiet
        return [_settings_panel(lk, lang, edit=True, user=user)]
    if kind == "u" and val == "ask":
        rows = [[{"text": _t("yes_unlink", lang), "callback_data": "u:yes"}, {"text": _t("cancel", lang), "callback_data": "u:no"}]]
        return [_msg(_t("unlink_ask", lang), {"inline_keyboard": rows}, edit=True)]
    if kind == "u" and val == "no":
        return [_settings_panel(lk, lang, edit=True, user=user)]
    if kind == "u" and val == "yes":
        unlink(db, user.id)
        return [_msg(_t("unlinked_ok", lang), {"remove_keyboard": True})]
    return []


# ---------------------------------------------------------------- event messages and the daily summary
# The bot process looks for documents it has not announced yet (a cursor per kind remembers the last id) and tells every linked
# person whose role may see that kind of document and who left the topic switched on. On the very first run the cursors start at
# "now", so switching the feature on never floods anybody with old documents.
TOPICS = ("orders", "ship", "pay", "prod", "edits", "dels", "digest")
TXT.update({
    "topics_cur": ("Xabar turlari (bosib yoqing/o‘chiring):", "Типы сообщений (нажмите, чтобы вкл/выкл):", "Message types (tap to switch):"),
    "ev_order": ("🆕 Buyurtma {number}\n{party}: {sum}\n{rows}", "🆕 Заказ {number}\n{party}: {sum}\n{rows}", "🆕 Order {number}\n{party}: {sum}\n{rows}"),
    "ev_ship": ("🚚 Jo‘natma {number}\n{party}: {sum}\n{rows}", "🚚 Отгрузка {number}\n{party}: {sum}\n{rows}", "🚚 Shipment {number}\n{party}: {sum}\n{rows}"),
    "ev_in": ("💰 To‘lov qabul qilindi {number}\n{party}: +{sum}\n{acc}", "💰 Поступил платёж {number}\n{party}: +{sum}\n{acc}", "💰 Payment received {number}\n{party}: +{sum}\n{acc}"),
    "ev_out": ("💸 To‘lov qilindi {number}\n{party}: −{sum}\n{acc}", "💸 Оплачено {number}\n{party}: −{sum}\n{acc}", "💸 Payment made {number}\n{party}: −{sum}\n{acc}"),
    "ev_prod": ("🏭 Ishlab chiqarildi {number}\n{rows}", "🏭 Выпущено {number}\n{rows}", "🏭 Produced {number}\n{rows}"),
    "scrap": ("brak", "брак", "scrap"),
    "more": ("… yana {n} ta", "… ещё {n}", "… {n} more"),
    "d_title": ("📊 Kunlik xulosa, {date}", "📊 Итоги дня, {date}", "📊 Daily summary, {date}"),
    "d_prod": ("🏭 Ishlab chiqarildi", "🏭 Выпущено", "🏭 Produced"),
    "d_ship": ("🚚 Jo‘natildi: {n} ta, {sum}", "🚚 Отгружено: {n}, {sum}", "🚚 Shipped: {n}, {sum}"),
    "d_orders": ("🆕 Yangi buyurtmalar: {n} ta, {sum}", "🆕 Новые заказы: {n}, {sum}", "🆕 New orders: {n}, {sum}"),
    "d_money": ("💵 Kirim {inn}, chiqim {out}", "💵 Приход {inn}, расход {out}", "💵 Money in {inn}, out {out}"),
    "d_signals": ("⚠️ Muhim signallar: {n} (/brief)", "⚠️ Важных сигналов: {n} (/brief)", "⚠️ Important signals: {n} (/brief)"),
    "d_quiet": ("Bugun hujjatlar bo‘lmadi.", "Сегодня документов не было.", "No documents today."),
})
DIGEST_HOURS = (8, 12, 17, 18, 20, 22)
QUIET_FROM, QUIET_TO = 22, 7                      # quiet night: from 22:00 to 07:00 local time
TXT.update({
    "all_on": ("✅ Hammasini yoqish", "✅ Включить всё", "✅ Turn everything on"),
    "all_off": ("⛔ Hammasini o‘chirish", "⛔ Выключить всё", "⛔ Turn everything off"),
    "hour_cur": ("Kunlik xulosa vaqti", "Время итогов дня", "Daily summary time"),
    "quiet_on": ("🌙 Tunda ovozsiz (22:00–07:00): o‘chiq", "🌙 Ночью без звука (22:00–07:00): выкл", "🌙 Silent at night (22:00–07:00): off"),
    "quiet_off": ("🌙 Tunda ovozsiz (22:00–07:00): yoqilgan", "🌙 Ночью без звука (22:00–07:00): вкл", "🌙 Silent at night (22:00–07:00): on"),
})
TOPIC_LABEL = {
    "orders": ("Buyurtmalar", "Заказы", "Orders"),
    "ship": ("Jo‘natmalar", "Отгрузки", "Shipments"),
    "pay": ("To‘lovlar", "Платежи", "Payments"),
    "prod": ("Ishlab chiqarish", "Производство", "Production"),
    "digest": ("Kunlik xulosa", "Итоги дня", "Daily summary"),
    "edits": ("Tahrirlar", "Изменения", "Edits"),
    "dels": ("O‘chirishlar", "Удаления", "Deletions"),
}
TXT.update({
    "ch_edit": ("✏️ {kind} {number} o‘zgartirildi ({who})", "✏️ {kind} {number} изменён(а) ({who})", "✏️ {kind} {number} was changed ({who})"),
    "ch_delete": ("🗑 {kind} {number} o‘chirildi ({who})", "🗑 {kind} {number} удалён(а) ({who})", "🗑 {kind} {number} was deleted ({who})"),
    "ch_restore": ("♻️ {kind} {number} tiklandi ({who})", "♻️ {kind} {number} восстановлен(а) ({who})", "♻️ {kind} {number} was restored ({who})"),
    "now": ("Hozir:", "Сейчас:", "Now:"),
    "k_orders": ("Buyurtma", "Заказ", "Order"), "k_invoices": ("Jo‘natma", "Отгрузка", "Shipment"),
    "k_fin_docs": ("To‘lov", "Платёж", "Payment"), "k_production_docs": ("Ishlab chiqarish", "Выпуск", "Production"),
    "f_amount": ("Summa", "Сумма", "Amount"), "f_date": ("Sana", "Дата", "Date"), "f_comment": ("Izoh", "Комментарий", "Comment"),
    "f_customer_id": ("Mijoz", "Покупатель", "Customer"), "f_supplier_id": ("Yetkazib beruvchi", "Поставщик", "Supplier"),
    "f_account_id": ("Hisob", "Счёт", "Account"), "f_warehouse_id": ("Ombor", "Склад", "Warehouse"), "f_due_date": ("Muddat", "Срок", "Due"),
    "f_rows": ("Qatorlar o‘zgargan", "Строки изменены", "Rows changed"),
})


def _topic_allowed(topic: str, lv: dict) -> bool:
    seeing = bool(lv["ord"] or lv["inv"] or lv["cash"] or lv["bank"] or lv["prod"])
    return {"orders": lv["ord"] >= 1, "ship": lv["inv"] >= 1, "pay": bool(lv["cash"] or lv["bank"]), "prod": lv["prod"] >= 1,
            "edits": seeing, "dels": seeing, "digest": True}[topic]


def local_now(now: datetime | None = None) -> datetime:
    return now or (datetime.utcnow() + timedelta(hours=settings.telegram_utc_offset))


def _name(obj, lang):
    return getattr(obj, "name_" + lang, None) or getattr(obj, "name_en", None) or getattr(obj, "name", "") if obj is not None else ""


def _rows_text(db, rows, lang, items, price=False, limit=4):
    lines = []
    for r in rows[:limit]:
        it = items.get(r.item_id)
        line = f"• {_name(it, lang)}: {_fmt(r.qty)} {it.unit.name if it else ''}"
        if getattr(r, "scrap", 0):
            line += f" (+{_fmt(r.scrap)} {_t('scrap', lang)})"
        lines.append(line)
    if len(rows) > limit:
        lines.append(_t("more", lang, n=len(rows) - limit))
    return "\n".join(lines)


def _total(rows) -> float:
    return sum(float(r.qty) * float(r.price) for r in rows)


def _cursor(db, kind: str, newest: int) -> tuple[TelegramCursor, bool]:
    c = db.get(TelegramCursor, kind)
    if c is None:                                    # first run: start from now, announce nothing old
        c = TelegramCursor(kind=kind, last_id=newest)
        db.add(c)
        return c, True
    return c, False


def _events(db: Session) -> list[tuple[str, str, object]]:
    """New documents since the last look: [(topic, section_needed, build(lang, lv) -> text|None)]."""
    items = {i.id: i for i in db.query(Item)}
    out = []

    def fresh(kind, model, extra=()):
        newest = db.query(func.max(model.id)).scalar() or 0
        cur, first = _cursor(db, kind, newest)
        if first:
            return []
        rows = db.query(model).filter(model.id > cur.last_id, *extra).order_by(model.id).limit(20).all()
        if rows:
            cur.last_id = rows[-1].id
        return [r for r in rows if r.status != "deleted"]

    for o in fresh("orders", Order):
        cu = db.get(Customer, o.customer_id)
        out.append(("orders", lambda lv, lang, o=o, cu=cu: _t("ev_order", lang, number=o.number, party=cu.name if cu else "", sum=_fmt(_total(o.rows)), rows=_rows_text(db, o.rows, lang, items)), None))
    for v in fresh("ship", Invoice):
        cu = db.get(Customer, v.customer_id)
        out.append(("ship", lambda lv, lang, v=v, cu=cu: _t("ev_ship", lang, number=v.number, party=cu.name if cu else "", sum=_fmt(_total(v.rows)), rows=_rows_text(db, v.rows, lang, items)), None))
    for f in fresh("pay", FinDoc):
        if f.kind == "tr":
            continue
        acc = db.get(Account, f.account_id)
        party = f.party or _name(db.get(Customer, f.customer_id), "uz") or _name(db.get(Supplier, f.supplier_id), "uz")
        out.append(("pay", lambda lv, lang, f=f, acc=acc, party=party: (_t("ev_" + f.kind, lang, number=f.number, party=party or "—", sum=_fmt(f.amount), acc=_name(acc, lang)) if lv.get(acc.kind, 0) >= 1 else None), acc))
    for d in fresh("prod", ProductionDoc):
        out.append(("prod", lambda lv, lang, d=d: _t("ev_prod", lang, number=d.number, rows=_rows_text(db, d.rows, lang, items)), None))
    return out


def due_events(db: Session) -> list[tuple[int, str]]:
    """Messages about new documents: [(chat_id, text)]."""
    todo = _events(db)
    if not todo:
        return []
    out = []
    for lk in db.query(TelegramLink):
        user = db.get(User, lk.user_id)
        if user is None or not user.is_active:
            continue
        lv, mine = levels_of(user), _topics(lk)
        for topic, build, _ in todo:
            if topic in mine and _topic_allowed(topic, lv):
                text = build(lv, lk.lang)
                if text:
                    out.append((lk.chat_id, text))
    db.flush()
    return out


def _day_bounds(local: datetime):
    start = datetime(local.year, local.month, local.day)
    return start, start + timedelta(days=1)


def summary_text(db: Session, user: User, lang: str, local: datetime) -> str:
    lv = levels_of(user)
    a, b = _day_bounds(local)
    items = {i.id: i for i in db.query(Item)}
    lines = [_t("d_title", lang, date=local.strftime("%d.%m.%Y"))]
    body = []
    if lv["prod"] >= 1:
        docs = db.query(ProductionDoc).filter(ProductionDoc.status != "deleted", ProductionDoc.date >= a, ProductionDoc.date < b).all()
        tot: dict[int, list[float]] = {}
        for d in docs:
            for r in d.rows:
                t = tot.setdefault(r.item_id, [0.0, 0.0])
                t[0] += float(r.qty)
                t[1] += float(r.scrap or 0)
        if tot:
            body.append(_t("d_prod", lang))
            for iid, (q, sc) in sorted(tot.items(), key=lambda kv: -kv[1][0])[:6]:
                it = items.get(iid)
                body.append(f"  • {_name(it, lang)}: {_fmt(q)} {it.unit.name if it else ''}" + (f" (+{_fmt(sc)} {_t('scrap', lang)})" if sc else ""))
    if lv["inv"] >= 1:
        inv = db.query(Invoice).filter(Invoice.status != "deleted", Invoice.date >= a, Invoice.date < b).all()
        if inv:
            body.append(_t("d_ship", lang, n=len(inv), sum=_fmt(sum(_total(v.rows) for v in inv))))
    if lv["ord"] >= 1:
        od = db.query(Order).filter(Order.status != "deleted", Order.date >= a, Order.date < b).all()
        if od:
            body.append(_t("d_orders", lang, n=len(od), sum=_fmt(sum(_total(o.rows) for o in od))))
    if lv["cash"] or lv["bank"]:
        accs = {x.id: x for x in db.query(Account)}
        inn = out = 0.0
        for f in db.query(FinDoc).filter(FinDoc.status != "deleted", FinDoc.kind != "tr", FinDoc.date >= a, FinDoc.date < b):
            acc = accs.get(f.account_id)
            if acc is None or lv.get(acc.kind, 0) < 1:
                continue
            if f.kind == "in":
                inn += float(f.amount)
            else:
                out += float(f.amount)
        if inn or out:
            body.append(_t("d_money", lang, inn=_fmt(inn), out=_fmt(out)))
    sig = [i for i in insights.collect(db, lv, lang, local) if i["severity"] in ("crit", "warn")]
    if sig:
        body.append(_t("d_signals", lang, n=len(sig)))
    return "\n".join(lines + (body or [_t("d_quiet", lang)]))


def due_summaries(db: Session, now: datetime | None = None) -> list[tuple[int, str]]:
    """Once a day per person, from the hour they picked (local time): the day's totals."""
    local = local_now(now)
    day = int(local.strftime("%Y%m%d"))
    out = []
    for lk in db.query(TelegramLink):
        if local.hour < lk.digest_hour or lk.digest_day >= day or "digest" not in _topics(lk):
            continue
        user = db.get(User, lk.user_id)
        if user is None or not user.is_active:
            continue
        lk.digest_day = day
        out.append((lk.chat_id, summary_text(db, user, lk.lang, local)))
    db.flush()
    return out


def silent_chats(db: Session, now: datetime | None = None) -> set[int]:
    """Chats that asked for a quiet night and where it is night now: their messages are sent without sound."""
    h = local_now(now).hour
    if not (h >= QUIET_FROM or h < QUIET_TO):
        return set()
    return {c for (c,) in db.execute(select(TelegramLink.chat_id).where(TelegramLink.quiet.is_(True)))}


# ---------------------------------------------------------------- edited, deleted and restored documents
# The audit log already records every change with who made it. The bot keeps a cursor in it and tells people about changes to
# orders, shipments, payments and production batches. The first message about a document is never edited afterwards (Telegram
# would not tell anybody), so a change always arrives as a new message that names the document number.
_AUDIT_ENTITY = {"orders": "ord", "invoices": "inv", "production_docs": "prod", "fin_docs": None}
_FIELDS = ("amount", "date", "due_date", "comment", "customer_id", "supplier_id", "account_id", "warehouse_id")


def _fmt_val(db, key, v, lang):
    if v is None or v == "":
        return "—"
    if key in ("date", "due_date"):
        return str(v)[:10]
    if key == "amount":
        return _fmt(v)
    model = {"customer_id": Customer, "supplier_id": Supplier, "account_id": Account}.get(key)
    if model is not None:
        return _name(db.get(model, v), lang) or str(v)
    if key == "warehouse_id":
        from app.models import Warehouse
        w = db.get(Warehouse, v)
        return w.name if w else str(v)
    return str(v)[:60]


def _change_text(db, a: AuditLog, lang: str, items: dict) -> str:
    kind = _t("k_" + a.entity, lang)
    head = _t("ch_" + {"update": "edit"}.get(a.action, a.action), lang, kind=kind, number=a.label, who=a.username or "—")
    if a.action != "update":
        return head
    lines = [head]
    ch = a.changes or {}
    for k in _FIELDS:
        if k in ch and isinstance(ch[k], list) and len(ch[k]) == 2:
            lines.append(f"{_t('f_' + k, lang)}: {_fmt_val(db, k, ch[k][0], lang)} → {_fmt_val(db, k, ch[k][1], lang)}")
    if ch.get("rows"):
        model = {"orders": Order, "invoices": Invoice, "production_docs": ProductionDoc}.get(a.entity)
        doc = db.get(model, a.entity_id) if model else None
        if doc is not None and doc.rows:
            lines.append(_t("now", lang))
            lines.append(_rows_text(db, doc.rows, lang, items))
        else:
            lines.append(_t("f_rows", lang))
    return "\n".join(lines)


def _may_see(db, lv: dict, a: AuditLog) -> bool:
    need = _AUDIT_ENTITY.get(a.entity, "?")
    if need is None:                                     # money documents: the account decides (bank or cash)
        f = db.get(FinDoc, a.entity_id)
        acc = db.get(Account, f.account_id) if f else None
        return bool(acc and lv.get(acc.kind, 0) >= 1)
    return need != "?" and lv.get(need, 0) >= 1


def due_changes(db: Session) -> list[tuple[int, str]]:
    """Messages about edited / deleted / restored documents: [(chat_id, text)]."""
    newest = db.query(func.max(AuditLog.id)).scalar() or 0
    cur, first = _cursor(db, "audit", newest)
    if first:
        return []
    rows = (db.query(AuditLog).filter(AuditLog.id > cur.last_id, AuditLog.entity.in_(list(_AUDIT_ENTITY)),
                                      AuditLog.action.in_(("update", "delete", "restore"))).order_by(AuditLog.id).limit(60).all())
    cur.last_id = max(cur.last_id, rows[-1].id) if rows and len(rows) == 60 else newest
    last: dict[tuple, AuditLog] = {}
    for a in rows:                                        # five saves of one document in a row make one message
        last[(a.entity, a.entity_id, a.action)] = a
    if not last:
        return []
    items = {i.id: i for i in db.query(Item)}
    out = []
    for lk in db.query(TelegramLink):
        user = db.get(User, lk.user_id)
        if user is None or not user.is_active:
            continue
        lv, mine = levels_of(user), _topics(lk)
        for a in last.values():
            topic = "edits" if a.action == "update" else "dels"
            if topic in mine and _may_see(db, lv, a):
                out.append((lk.chat_id, _change_text(db, a, lk.lang, items)))
    db.flush()
    return out


# ---------------------------------------------------------------- off-site copy of the backups
# A copy of every verified backup goes ONLY to the main admin's (owner's) Telegram chat, so the data survives even if the whole server is lost.
# Only ENCRYPTED backups (.enc) are ever sent, and only after the backup container has test-restored them.
MAX_FILE = 48 * 1024 * 1024                       # Telegram bots may upload up to 50 MB
TXT.update({
    "bk_cap": ("🔐 Zaxira nusxa {when}\nShifrlangan: parolsiz ochilmaydi. Parolni serverdan tashqarida saqlang. Bu faylni o‘chirmang.",
               "🔐 Резервная копия {when}\nЗашифрована: без пароля не открыть. Храните пароль вне сервера. Не удаляйте файл.",
               "🔐 Backup {when}\nEncrypted: unreadable without the passphrase. Keep the passphrase off the server. Do not delete this file."),
    "bk_big": ("⚠️ Zaxira nusxa {name} Telegram uchun juda katta ({mb} MB), yuborilmadi. Uni serverdan oling: ~/prime-beton/backups",
               "⚠️ Резервная копия {name} слишком велика для Telegram ({mb} МБ), не отправлена. Заберите её с сервера: ~/prime-beton/backups",
               "⚠️ Backup {name} is too big for Telegram ({mb} MB) and was not sent. Copy it from the server: ~/prime-beton/backups"),
})
_BK_TS = re.compile(r"(\d{8})-(\d{6})")


def _verified(folder: Path, name: str) -> bool:
    """The backup container writes last-restore-check.txt only after the file restored and matched the live database."""
    try:
        head = (folder / "last-restore-check.txt").read_text().splitlines()
    except OSError:
        return False
    return bool(head) and head[0].startswith("OK") and any(name in line for line in head[1:3]) and not (folder / "BACKUP_FAILED.txt").exists()


def due_backups(db: Session, folder: str | Path | None = None) -> list[dict]:
    """[{chat_id, user_id, path, name, caption | notice}] for the newest verified encrypted backup the main admin (owner) has not got yet. Nobody else ever gets it."""
    folder = Path(folder or settings.backup_dir)
    try:
        files = sorted((f for f in folder.glob("*.sql.gz.enc") if f.is_file()), key=lambda f: f.stat().st_mtime)
    except OSError:
        return []
    if not files:
        return []
    f = files[-1]
    m = _BK_TS.search(f.name)
    if not m or not _verified(folder, f.name):
        return []
    stamp = int(m.group(1) + m.group(2))
    out = []
    for user, lk in db.query(User, TelegramLink).join(TelegramLink, TelegramLink.user_id == User.id).filter(User.is_owner.is_(True), User.is_active):
        cur = db.get(TelegramCursor, f"bk{user.id}")
        if cur is not None and cur.last_id >= stamp:
            continue
        local = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S") + timedelta(hours=settings.telegram_utc_offset)
        item = {"chat_id": lk.chat_id, "user_id": user.id, "path": str(f), "name": f.name, "stamp": stamp}
        if f.stat().st_size > MAX_FILE:
            item["notice"] = _t("bk_big", lk.lang, name=f.name, mb=f.stat().st_size // (1024 * 1024))
        else:
            item["caption"] = _t("bk_cap", lk.lang, when=local.strftime("%d.%m.%Y %H:%M"))
        out.append(item)
    return out


def mark_backup_sent(db: Session, user_id: int, stamp: int) -> None:
    cur = db.get(TelegramCursor, f"bk{user_id}")
    if cur is None:
        db.add(TelegramCursor(kind=f"bk{user_id}", last_id=stamp))
    else:
        cur.last_id = stamp
