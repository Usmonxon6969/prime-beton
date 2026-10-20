from datetime import datetime, timedelta

from app.core.config import settings
from app.models import TelegramLink, User
from app.services import telegram as tg
from tests.conftest import scenario


def make_user(ctx, name, role):
    r = ctx.post("/auth/users", {"username": name, "password": "Strong-pass-123", "full_name": name.title(), "role": role})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def say(db_session, chat, text, now=None):
    """One message through the bot, committed like the bot process does."""
    with db_session() as db:
        r = tg.handle(db, chat, text, now)
        db.commit()
    return r


def test_link_flow_and_commands(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    c = ctx.post("/telegram/code", {})
    assert c.status_code == 200 and len(c.json()["code"]) == 8 and c.json()["expires_in"] == 600
    r = say(db_session, 555, f"/start {c.json()['code']}")
    assert r.startswith("Ulandi: Usmonxon Abbosov")                      # new links start in Uzbek
    with db_session() as db:
        assert db.query(TelegramLink).count() == 1
    assert "Buyruqlar" in say(db_session, 555, "/help")
    assert say(db_session, 555, "/lang en").startswith("Language")
    assert "Cement" in say(db_session, 555, "/stock cement")
    assert "Orient Stroy" in say(db_session, 555, "/debts")
    assert say(db_session, 555, "/cash")
    assert say(db_session, 555, "/stock").startswith("Which item")
    assert say(db_session, 555, "/nonsense").startswith("I did not")
    assert ctx.get("/telegram").json()["linked"] is True
    assert say(db_session, 555, "/unlink").startswith("Disconnected")
    assert "not linked" in say(db_session, 555, "/brief")
    assert ctx.get("/telegram").json()["linked"] is False


def test_code_is_single_use_expires_and_is_throttled(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    code = ctx.post("/telegram/code", {}).json()["code"]
    assert say(db_session, 1, f"/start {code}").startswith("Ulandi")
    assert "noto‘g‘ri" in say(db_session, 2, f"/start {code}")             # already used
    code2 = ctx.post("/telegram/code", {}).json()["code"]
    assert "noto‘g‘ri" in say(db_session, 3, f"/start {code2}", datetime.utcnow() + timedelta(minutes=11))   # expired
    for _ in range(6):
        say(db_session, 9, "/start WRONGWRO")
    code3 = ctx.post("/telegram/code", {}).json()["code"]
    assert "noto‘g‘ri" in say(db_session, 9, f"/start {code3}")            # chat 9 is locked out even with a valid code
    with db_session() as db:
        assert db.query(TelegramLink).filter(TelegramLink.chat_id == 9).count() == 0
    tg._fails.clear()


def test_roles_limit_what_the_bot_says(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    uid = make_user(ctx, "salesman", "sales")
    with db_session() as db:
        code = tg.new_code(db, db.get(User, uid))
        db.commit()
    say(db_session, 77, f"/start {code}")
    say(db_session, 77, "/lang en")
    assert say(db_session, 77, "/cash") == "Your role cannot see this."              # sales has no bank or cash
    assert "Orient Stroy" in say(db_session, 77, "/debts")                              # but customer debts are theirs
    assert "Your role cannot" not in say(db_session, 77, "/stock cement")
    r = ctx.c.patch(f"/api/auth/users/{uid}", json={"is_active": False}, headers=ctx.h)
    assert r.status_code == 200
    assert "disabled" in say(db_session, 77, "/brief")                               # a disabled user is cut off at once


def test_alerts_are_sent_once(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    code = ctx.post("/telegram/code", {}).json()["code"]
    say(db_session, 5, f"/start {code}")
    say(db_session, 5, "/lang en")
    when = datetime(2026, 11, 20)

    def drain(at):
        sent = []
        for _ in range(30):                                                   # a push carries at most 5 signals, so it takes a few rounds
            with db_session() as db:
                got = tg.due_alerts(db, at)
                db.commit()
            if not got:
                break
            sent += got
        return sent

    first = drain(when)
    assert first and first[0][0] == 5 and any("overdue" in m for _, m in first)
    assert drain(when + timedelta(hours=1)) == []                              # the same signals are not repeated
    assert drain(when + timedelta(days=4))                                    # still true after 3 days: a reminder
    say(db_session, 5, "/alerts off")
    assert drain(when + timedelta(days=9)) == []


def test_api_needs_a_token_and_login(ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    assert ctx.post("/telegram/code", {}).status_code == 409
    assert ctx.get("/telegram").json()["enabled"] is False
    assert ctx.c.get("/api/telegram").status_code == 401


# ---------------------------------------------------------------- buttons
def full(db_session, chat, text):
    with db_session() as db:
        r = tg.handle_full(db, chat, text)
        db.commit()
    return r


def tap(db_session, chat, data):
    with db_session() as db:
        r = tg.callback(db, chat, data)
        db.commit()
    return r


def labels(markup):
    return [b["text"] for row in markup["keyboard"] for b in row]


def link_chat(db_session, ctx, chat):
    code = ctx.post("/telegram/code", {}).json()["code"]
    return full(db_session, chat, f"/start {code}")


def test_buttons_follow_the_role_and_language(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    r = link_chat(db_session, ctx, 600)
    assert r["text"].startswith("Ulandi") and "📦 Ombor" in labels(r["markup"])      # admin sees everything
    assert labels(r["markup"]) == ["📋 Signallar", "📦 Ombor", "💳 Qarzlar", "💵 Kassa", "⚙️ Sozlamalar"]
    uid = make_user(ctx, "salesman2", "sales")
    with db_session() as db:
        code = tg.new_code(db, db.get(User, uid))
        db.commit()
    r = full(db_session, 601, f"/start {code}")
    assert "💵 Kassa" not in labels(r["markup"]) and "💳 Qarzlar" in labels(r["markup"])   # sales: no cash buttons
    assert full(db_session, 601, "💵 Kassa") is not None
    assert full(db_session, 601, "💵 Kassa")["text"] == "Rolingiz bu ma’lumotga ruxsat bermaydi."


def test_button_taps_work_like_commands(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    link_chat(db_session, ctx, 610)
    full(db_session, 610, "/lang en")
    assert "Orient Stroy" in full(db_session, 610, "💳 Debts")["text"]
    assert full(db_session, 610, "📋 Signals")["text"]
    assert full(db_session, 610, "💵 Cash")["text"]
    assert "Cement" in full(db_session, 610, "cement")["text"]                              # a plain word is a stock search
    pick = full(db_session, 610, "📦 Stock")
    assert pick["text"].startswith("Pick an item")
    btns = [b for row in pick["markup"]["inline_keyboard"] for b in row]
    cement = next(b for b in btns if "Cement" in b["text"])
    out = tap(db_session, 610, cement["callback_data"])
    assert "Cement" in out[0]["text"] and not out[0]["edit"]


def test_settings_buttons(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    link_chat(db_session, ctx, 620)
    panel = full(db_session, 620, "⚙️ Sozlamalar")
    assert "yoqilgan" in panel["text"]
    out = tap(db_session, 620, "l:ru")
    assert out[0]["edit"] and "Русский" in out[0]["text"]
    assert out[1]["markup"]["keyboard"][0][0]["text"] == "📋 Сигналы"                      # the keyboard is re-sent in the new language
    out = tap(db_session, 620, "a:off")
    assert out[0]["edit"] and "выключены" in out[0]["text"]
    with db_session() as db:
        assert db.query(TelegramLink).one().notify is False
    ask = tap(db_session, 620, "u:ask")
    assert ask[0]["edit"] and "Отвязать" in ask[0]["text"]
    assert tap(db_session, 620, "u:no")[0]["edit"]
    with db_session() as db:
        assert db.query(TelegramLink).count() == 1                                        # cancel keeps the link
    out = tap(db_session, 620, "u:yes")
    assert out[0]["markup"] == {"remove_keyboard": True}
    with db_session() as db:
        assert db.query(TelegramLink).count() == 0
    assert "not linked" in tap(db_session, 620, "a:on")[0]["text"]                       # a tap from an unlinked chat does nothing
    assert tap(db_session, 620, "s:abc") and tap(db_session, 620, "x:1")


def test_bad_callbacks_and_roles(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    tg._fails.clear()
    scenario(ctx)
    link_chat(db_session, ctx, 630)
    assert tap(db_session, 630, "s:999999")[0]["text"] == "Topilmadi."
    assert tap(db_session, 630, "l:xx") == [] and tap(db_session, 630, "garbage") == [] and tap(db_session, 630, "") == []


def test_bot_process_sends_buttons(db_session, ctx, monkeypatch):
    """The HTTP layer: keyboard on a message, edit for the settings panel, answerCallbackQuery for every tap."""
    import app.telegram_bot as bot
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    monkeypatch.setattr(bot, "SessionLocal", db_session)
    tg._fails.clear()
    scenario(ctx)
    calls = []
    monkeypatch.setattr(bot, "_call", lambda client, method, payload, timeout=15: calls.append((method, payload)))
    code = ctx.post("/telegram/code", {}).json()["code"]
    msg = lambda t: {"update_id": 1, "message": {"chat": {"id": 640, "type": "private"}, "text": t}}
    bot.process(None, msg(f"/start {code}"))
    assert calls[-1][0] == "sendMessage" and "keyboard" in calls[-1][1]["reply_markup"]
    bot.process(None, msg("⚙️ Sozlamalar"))
    assert "inline_keyboard" in calls[-1][1]["reply_markup"]
    calls.clear()
    bot.process(None, {"update_id": 2, "callback_query": {"id": "cb1", "data": "a:off", "message": {"message_id": 7, "chat": {"id": 640, "type": "private"}}}})
    assert [c[0] for c in calls] == ["answerCallbackQuery", "editMessageText"] and calls[1][1]["message_id"] == 7
    calls.clear()
    bot.process(None, {"update_id": 3, "callback_query": {"id": "cb2", "data": "a:on", "message": {"message_id": 8, "chat": {"id": -5, "type": "group"}}}})
    assert [c[0] for c in calls] == ["answerCallbackQuery"]                                  # a group tap changes nothing
    with db_session() as db:
        assert db.query(TelegramLink).one().notify is False


# ---------------------------------------------------------------- event messages and the daily summary
def _linked(db_session, ctx, chat, name, role, lang="en"):
    uid = make_user(ctx, name, role)
    with db_session() as db:
        db.add(TelegramLink(user_id=uid, chat_id=chat, lang=lang))
        db.commit()
    return uid


def _order(ctx, sc, qty=2, price=100):
    r = ctx.post("/orders", {"date": "2026-10-15T09:00:00", "customer_id": sc["cus"], "rows": [{"item_id": sc["fbs"], "qty": qty, "price": price}]})
    assert r.status_code in (200, 201), r.text


def test_events_start_from_now_then_announce_new_documents(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    sc = scenario(ctx)                                                     # old documents exist before the bot looks
    _linked(db_session, ctx, 701, "boss", "director")
    with db_session() as db:
        assert tg.due_events(db) == []                                     # first look: cursors start at "now"
        db.commit()
    _order(ctx, sc)
    with db_session() as db:
        msgs = tg.due_events(db)
        db.commit()
    assert len(msgs) == 1 and msgs[0][0] == 701 and "Order" in msgs[0][1] and "200" in msgs[0][1]
    with db_session() as db:
        assert tg.due_events(db) == []                                     # announced once


def test_events_respect_role_and_topics(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    sc = scenario(ctx)
    _linked(db_session, ctx, 702, "maker", "prod")                          # production role has no orders section
    _linked(db_session, ctx, 703, "seller", "sales")
    with db_session() as db:
        tg.due_events(db)
        db.commit()
    _order(ctx, sc, 1, 50)
    with db_session() as db:
        msgs = tg.due_events(db)
        db.commit()
    chats = {c for c, _ in msgs}
    assert 703 in chats and 702 not in chats
    with db_session() as db:                                               # the seller switches the topic off
        out = tg.callback(db, 703, "t:orders")
        assert "▫️ Orders" in str(out[0]["markup"])
        db.commit()
    _order(ctx, sc, 1, 50)
    with db_session() as db:
        assert 703 not in {c for c, _ in tg.due_events(db)}


def test_daily_summary_once_after_the_chosen_hour(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    scenario(ctx)
    _linked(db_session, ctx, 704, "boss2", "director")
    morning = datetime(2026, 10, 15, 9, 0)
    evening = datetime(2026, 10, 15, 19, 0)
    with db_session() as db:
        assert tg.due_summaries(db, morning) == []                          # default hour is 18
        got = tg.due_summaries(db, evening)
        db.commit()
    assert len(got) == 1 and got[0][0] == 704 and got[0][1].startswith("📊 Daily summary, 15.10.2026")
    with db_session() as db:
        assert tg.due_summaries(db, evening + timedelta(minutes=30)) == []   # not twice the same day
        assert len(tg.due_summaries(db, evening + timedelta(days=1))) == 1
    with db_session() as db:                                               # moving the hour to 08:00 works for the next day
        out = tg.callback(db, 704, "h:8")
        assert "✓ 08:00" in str(out[0]["markup"])
        db.commit()
    with db_session() as db:
        assert tg.due_summaries(db, datetime(2026, 10, 17, 8, 5))[0][0] == 704


def test_quiet_night_and_master_switches(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    scenario(ctx)
    _linked(db_session, ctx, 705, "boss3", "director")
    night, day = datetime(2026, 10, 15, 23, 30), datetime(2026, 10, 15, 12, 0)
    with db_session() as db:
        assert tg.silent_chats(db, night) == set()                          # off by default
        tg.callback(db, 705, "q:x")
        db.commit()
    with db_session() as db:
        assert tg.silent_chats(db, night) == {705} and tg.silent_chats(db, day) == set()
        for t in tg.TOPICS:                                          # every kind can be switched off
            tg.callback(db, 705, "t:" + t)
        assert db.query(TelegramLink).filter(TelegramLink.chat_id == 705).one().topics == ""
        tg.callback(db, 705, "a:off")
        assert db.query(TelegramLink).filter(TelegramLink.chat_id == 705).one().notify is False


# ---------------------------------------------------------------- edits, deletions, restores
def test_changes_are_announced_and_controllable(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    sc = scenario(ctx)
    _linked(db_session, ctx, 710, "boss4", "director")
    _linked(db_session, ctx, 711, "maker2", "prod")                        # production role: no orders
    with db_session() as db:
        assert tg.due_changes(db) == []                                    # starts from now
        db.commit()
    o = ctx.post("/orders", {"date": "2026-10-15T09:00:00", "customer_id": sc["cus"], "rows": [{"item_id": sc["fbs"], "qty": 2, "price": 100}]}).json()
    with db_session() as db:
        assert tg.due_changes(db) == []                                    # a new document is not a "change"
        db.commit()
    r = ctx.c.put(f"/api/orders/{o['id']}", headers=ctx.h, json={"date": "2026-10-15T09:00:00", "customer_id": sc["cus"], "comment": "rush", "rows": [{"item_id": sc["fbs"], "qty": 3, "price": 100}]})
    assert r.status_code == 200, r.text
    with db_session() as db:
        msgs = tg.due_changes(db)
        db.commit()
    assert {c for c, _ in msgs} == {710}
    text = msgs[0][1]
    assert "Order" in text and o["number"] in text and "was changed" in text and "3" in text
    ctx.c.delete(f"/api/orders/{o['id']}", headers=ctx.h)
    with db_session() as db:
        d = tg.due_changes(db)
        db.commit()
    assert d and "was deleted" in d[0][1]
    with db_session() as db:                                               # deletions can be switched off on their own
        tg.callback(db, 710, "t:dels")
        db.commit()
    ctx.post(f"/orders/{o['id']}/restore", {})
    with db_session() as db:
        got = tg.due_changes(db)
        db.commit()
    assert got == []
    with db_session() as db:
        out = tg.callback(db, 710, "t:dels")
        assert "✓ Deletions" in str(out[0]["markup"]) and "✓ Edits" in str(out[0]["markup"])


def test_everything_on_or_off_with_one_tap(db_session, ctx, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    scenario(ctx)
    _linked(db_session, ctx, 720, "boss5", "director")
    with db_session() as db:
        tg.callback(db, 720, "t:none")
        lk = db.query(TelegramLink).filter(TelegramLink.chat_id == 720).one()
        assert lk.topics == "" and lk.notify is False
        tg.callback(db, 720, "t:all")
        assert set(lk.topics.split(",")) == set(tg.TOPICS) and lk.notify is True


# ---------------------------------------------------------------- production entered as a list
def _prod_chat(db_session, ctx, chat=900, role="prod", lang="uz"):
    _linked(db_session, ctx, chat, f"u{chat}", role, lang)


BOSS = 800


def _boss(db_session, ctx):
    """An admin linked to the bot: the person who approves lists sent by others."""
    with db_session() as db:
        if db.query(TelegramLink).filter(TelegramLink.chat_id == BOSS).count():
            return
    _linked(db_session, ctx, BOSS, "boss", "admin", "uz")


def _confirm(db_session, ctx, markup, sender=900):
    """The sender taps the first button, then the manager approves; returns the manager-side result messages."""
    _boss(db_session, ctx)
    out = tap(db_session, sender, _msgs(markup)[0])
    ask = [m for m in out if m.get("to") == BOSS]
    assert ask, out
    return out, tap(db_session, BOSS, _msgs(ask[0]["markup"])[0])


def _msgs(markup):
    return [b["callback_data"] for row in markup["inline_keyboard"] for b in row] if markup else []


def test_production_list_is_read_shown_and_recorded_only_after_confirm(db_session, ctx, monkeypatch):
    sc = scenario(ctx)
    _prod_chat(db_session, ctx)
    before = ctx.stock("ФБС 24.4.6-Т", "Завод 1")
    r = full(db_session, 900, "14.10\nФБС 24.4.6-Т - 2")
    assert "14.10." in r["text"] and "ФБС 24.4.6-Т — 2 dona" in r["text"] and "Завод 1" in r["text"]
    ok, no = _msgs(r["markup"])
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before                  # nothing yet
    _boss(db_session, ctx)
    sent = tap(db_session, 900, ok)                                          # a non-admin only sends it to the manager
    assert "Rahbarga yuborildi" in sent[0]["text"] and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before
    ask = [m for m in sent if m.get("to") == BOSS][0]
    assert "ФБС 24.4.6-Т — 2 dona" in ask["text"] and "U900" in ask["text"]
    approve, reject = _msgs(ask["markup"])
    out = tap(db_session, BOSS, approve)
    assert out[0]["edit"] and "Tasdiqlandi" in out[0]["text"]
    to_sender = [m for m in out if m.get("to") == 900][0]
    assert "PRD-" in to_sender["text"] and "Boss" in to_sender["text"]
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before + 2
    prods = ctx.get("/production").json()
    assert prods[0]["comment"] == "Telegram · U900" and prods[0]["date"].startswith("2026-10-14T12")
    assert "allaqachon" in tap(db_session, BOSS, approve)[0]["text"]          # the manager's second tap does nothing
    again = tap(db_session, 900, ok)                                        # a second tap must not record twice
    assert "allaqachon" in again[0]["text"] and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before + 2
    assert sc


def test_production_list_cancel_and_unreadable_lines(db_session, ctx, monkeypatch):
    scenario(ctx)
    _prod_chat(db_session, ctx)
    before = ctx.stock("ФБС 24.4.6-Т", "Завод 1")
    r = full(db_session, 900, "ФБС 24.4.6-Т 3")
    out = tap(db_session, 900, _msgs(r["markup"])[1])
    assert "Bekor" in out[0]["text"] and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before
    bad = full(db_session, 900, "ФБС 24.4.6-Т 3\nNoma'lum mahsulot 5")
    assert bad["markup"] is None and "Noma'lum mahsulot 5" in bad["text"] and "hech narsa kiritilmadi" in bad["text"]
    miss = full(db_session, 900, "ФБС 24.4.6-Т\nФБС 24.4.6-Т 2")
    assert "soni ko‘rsatilmagan" in miss["text"]
    zero = full(db_session, 900, "ФБС 24.4.6-Т 0")
    assert "0 dan katta" in zero["text"]
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before


def test_production_list_understands_spellings_dates_and_totals(db_session, ctx, monkeypatch):
    scenario(ctx)
    _prod_chat(db_session, ctx, lang="ru")
    r = full(db_session, 900, "kecha\n- FBS 24.4.6-T x 2 ta\n2) ФБС 24.4.6-Т: 3 шт")            # Latin spelling, bullets, two lines of the same product add up
    assert "Выпуск" in r["text"] and "— 5 " in r["text"]
    yesterday = (tg.local_now() - timedelta(days=1)).strftime("%d.%m.%Y")
    assert yesterday in r["text"]
    d = full(db_session, 900, "ФБС 24.4.6-Т 1\n25.12.2030")
    assert "в будущем" in d["text"]
    f = full(db_session, 900, "ФБС 24.4.6-T 1\nСклад: Завод 3")
    assert "Завод 3" in f["text"]
    w = full(db_session, 900, "ФБС 24.4.6-Т 1\nСклад: Нет такого")
    assert "склад не найден" in w["text"]


def test_production_list_checks_materials_and_roles(db_session, ctx, monkeypatch):
    scenario(ctx)
    _prod_chat(db_session, ctx)
    big = full(db_session, 900, "ФБС 24.4.6-Т 5000")
    assert big["markup"] is None and "Xomashyo yetmaydi" in big["text"] and "kerak" in big["text"]
    _prod_chat(db_session, ctx, chat=901, role="sales")                     # sales cannot enter production: the text is only a stock search
    s = full(db_session, 901, "ФБС 24.4.6-Т 2")
    assert s["markup"] is None or "inline_keyboard" not in s["markup"]
    _prod_chat(db_session, ctx, chat=902, role="director")                  # view-only
    d = full(db_session, 902, "ФБС 24.4.6-Т 2")
    assert d["markup"] is None or "inline_keyboard" not in d["markup"]
    assert tap(db_session, 902, "pr:ok:1")[0]["text"] == tg.prod_bot._t("denied", "uz")
    assert "/prod" in say(db_session, 900, "/help") and "15.10" in say(db_session, 900, "/prod")
    assert "/prod" not in say(db_session, 901, "/help")


def test_someone_elses_or_old_draft_cannot_be_confirmed(db_session, ctx, monkeypatch):
    scenario(ctx)
    _prod_chat(db_session, ctx, chat=900)
    _prod_chat(db_session, ctx, chat=903)
    r = full(db_session, 900, "ФБС 24.4.6-Т 2")
    ok = _msgs(r["markup"])[0]
    other = tap(db_session, 903, ok)
    assert "allaqachon" in other[0]["text"]
    from app.models import TelegramDraft
    with db_session() as db:
        db.query(TelegramDraft).update({"created_at": datetime.utcnow() - timedelta(hours=3)})
        db.commit()
    assert "allaqachon" in tap(db_session, 900, ok)[0]["text"]


def test_production_list_in_the_plant_shorthand_with_a_total_line(db_session, ctx, monkeypatch):
    scenario(ctx)
    un = ctx.get("/units").json()[0]["id"]
    assert "2ПК 66*12" in ctx.items and "2ПК 56,5*10" in ctx.items and "2ПК 43*10" in ctx.items       # the seeded 2ПК range
    ctx.post("/receipts", {"date": "2026-10-01T09:00:00", "supplier_id": ctx.supplier("Mat Co"), "warehouse_id": ctx.wh["Завод 1"]["id"],
                           "rows": [{"item_id": ctx.items[n]["id"], "qty": 100000, "price": 1} for n in ("Cement", "Crushed stone", "Sand", "Rebar")]})
    _prod_chat(db_session, ctx)
    r = full(db_session, 900, "14.10.2026\n66*12-2\n56,5*10-8\n43*10-9\nJami:19 ta")
    assert r["markup"] and "inline_keyboard" in r["markup"], r["text"]
    assert "2ПК 66*12 — 2" in r["text"] and "2ПК 56,5*10 — 8" in r["text"] and "2ПК 43*10 — 9" in r["text"] and "Jami: 3 xil, 19" in r["text"]
    assert "14.10.2026" in r["text"] and "Brigada" not in r["text"]                     # no crew needed
    _, done = _confirm(db_session, ctx, r["markup"])
    assert "Tasdiqlandi" in done[0]["text"]
    assert ctx.stock("2ПК 66*12", "Завод 1") == 2 and ctx.stock("2ПК 43*10", "Завод 1") == 9
    wrong = full(db_session, 900, "66*12-2\n43*10-9\nJami:19 ta")                       # the total does not add up: nothing is recorded
    assert wrong["markup"] is None and "yig‘indisi 11" in wrong["text"]
    ctx.post("/items", {"kind": "product", "name_uz": "3ПК 66*12", "name_ru": "3ПК 66*12", "name_en": "3ПК 66*12", "unit_id": un})
    amb = full(db_session, 900, "66*12-2\n43*10-1")                                     # two products share the size: the bot asks, it does not guess
    assert amb["markup"] is None and "Shumi" in amb["text"] and "3ПК 66*12" in amb["text"]


def test_manager_can_reject_and_admin_records_at_once(db_session, ctx, monkeypatch):
    scenario(ctx)
    _prod_chat(db_session, ctx)
    before = ctx.stock("ФБС 24.4.6-Т", "Завод 1")
    r = full(db_session, 900, "ФБС 24.4.6-Т 2")
    sent, rejected = None, None
    _boss(db_session, ctx)
    sent = tap(db_session, 900, _msgs(r["markup"])[0])
    ask = [m for m in sent if m.get("to") == BOSS][0]
    rejected = tap(db_session, BOSS, _msgs(ask["markup"])[1])
    assert "Rad etildi" in rejected[0]["text"] and [m for m in rejected if m.get("to") == 900][0]["text"].startswith("✖️ Rahbar rad etdi")
    assert ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before
    assert "allaqachon" in tap(db_session, BOSS, _msgs(ask["markup"])[0])[0]["text"]       # a rejected list cannot be approved later
    # a non-admin cannot approve (not even their own list)
    r2 = full(db_session, 900, "ФБС 24.4.6-Т 1")
    s2 = tap(db_session, 900, _msgs(r2["markup"])[0])
    ap = [m for m in s2 if m.get("to") == BOSS][0]["markup"]
    assert "allaqachon" in tap(db_session, 900, _msgs(ap)[0])[0]["text"] and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before
    # an admin's own list is recorded at once, with no second step
    r3 = full(db_session, BOSS, "ФБС 24.4.6-Т 3")
    assert "Tasdiqlash" in r3["markup"]["inline_keyboard"][0][0]["text"]
    done = tap(db_session, BOSS, _msgs(r3["markup"])[0])
    assert "PRD-" in done[0]["text"] and ctx.stock("ФБС 24.4.6-Т", "Завод 1") == before + 3


def test_without_a_linked_admin_the_list_cannot_be_sent(db_session, ctx, monkeypatch):
    scenario(ctx)
    _prod_chat(db_session, ctx)
    r = full(db_session, 900, "ФБС 24.4.6-Т 2")
    out = tap(db_session, 900, _msgs(r["markup"])[0])
    assert len(out) == 1 and "Tasdiqlovchi" in out[0]["text"]


def test_bot_delivers_the_approval_request_to_the_manager_chat(db_session, ctx, monkeypatch):
    import app.telegram_bot as bot
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    monkeypatch.setattr(bot, "SessionLocal", db_session)
    scenario(ctx)
    _prod_chat(db_session, ctx)
    _boss(db_session, ctx)
    calls = []
    monkeypatch.setattr(bot, "_call", lambda client, method, payload, timeout=15: calls.append((method, payload)))
    r = full(db_session, 900, "ФБС 24.4.6-Т 2")
    bot.process(None, {"update_id": 5, "callback_query": {"id": "c", "data": _msgs(r["markup"])[0], "message": {"message_id": 3, "chat": {"id": 900, "type": "private"}}}})
    sent = [(m, p) for m, p in calls if m != "answerCallbackQuery"]
    assert sent[0][0] == "editMessageText" and sent[0][1]["chat_id"] == 900             # the sender's own message is edited
    assert sent[1][0] == "sendMessage" and sent[1][1]["chat_id"] == BOSS and "inline_keyboard" in sent[1][1]["reply_markup"]


def test_the_same_list_for_the_same_day_is_not_recorded_twice(db_session, ctx, monkeypatch):
    scenario(ctx)
    ctx.post("/receipts", {"date": "2026-10-01T09:00:00", "supplier_id": ctx.supplier("Mat Co"), "warehouse_id": ctx.wh["Завод 1"]["id"],
                           "rows": [{"item_id": ctx.items[n]["id"], "qty": 100000, "price": 1} for n in ("Cement", "Crushed stone", "Sand", "Rebar")]})
    _prod_chat(db_session, ctx)
    text = "14.10.2026\nФБС 24.4.6-Т - 2"
    r = full(db_session, 900, text)
    _confirm(db_session, ctx, r["markup"])
    n = len(ctx.get("/production").json())
    again = full(db_session, 900, text)                                   # the same list, the same date
    assert again["markup"] is None and "allaqachon kiritilgan" in again["text"] and "PRD-" in again["text"]
    assert len(ctx.get("/production").json()) == n
    other_day = full(db_session, 900, "13.10.2026\nФБС 24.4.6-Т - 2")       # another day: fine
    assert other_day["markup"]
    other_qty = full(db_session, 900, "14.10.2026\nФБС 24.4.6-Т - 3")       # another number: fine
    assert other_qty["markup"]
    # a list already waiting for the manager is not sent a second time
    _boss(db_session, ctx)
    p = full(db_session, 900, "12.10.2026\nФБС 24.4.6-Т - 1")
    tap(db_session, 900, _msgs(p["markup"])[0])
    again2 = full(db_session, 900, "12.10.2026\nФБС 24.4.6-Т - 1")
    assert again2["markup"] is None and "rahbarga yuborilgan" in again2["text"]


def test_colon_between_the_numbers_is_the_same_size(db_session, ctx, monkeypatch):
    scenario(ctx)
    ctx.post("/receipts", {"date": "2026-10-01T09:00:00", "supplier_id": ctx.supplier("Mat Co"), "warehouse_id": ctx.wh["Завод 1"]["id"],
                           "rows": [{"item_id": ctx.items[n]["id"], "qty": 100000, "price": 1} for n in ("Cement", "Crushed stone", "Sand", "Rebar")]})
    _prod_chat(db_session, ctx)
    r = full(db_session, 900, "14.10.2026\n66:12-2\n56,5:10 - 8\n43x10 9\nJami: 19")
    assert r["markup"], r["text"]
    assert "2ПК 66*12 — 2" in r["text"] and "2ПК 56,5*10 — 8" in r["text"] and "2ПК 43*10 — 9" in r["text"]


def test_bot_changes_refresh_open_pages_and_are_audited(client, db_session, ctx, monkeypatch):
    """The bot is another process: its commits reach the API's open pages through /live/poke, and what it records is audited."""
    from app.core import audit, events
    from app.core.events import hub, poke_token
    seen = []
    monkeypatch.setattr(hub, "publish", lambda: seen.append(1))
    assert client.post("/api/live/poke").status_code == 403
    assert client.post("/api/live/poke", headers={"X-Poke": "wrong"}).status_code == 403
    assert client.post("/api/live/poke", headers={"X-Poke": poke_token(settings.secret_key)}).status_code == 204 and seen == [1]
    import app.telegram_bot as bot
    sent = []
    monkeypatch.setattr(bot.httpx, "post", lambda url, headers=None, timeout=None: sent.append((url, headers)))
    bot._poke_api()
    assert sent[0][0].endswith("/api/live/poke") and sent[0][1]["X-Poke"] == poke_token(settings.secret_key)
    assert {"telegram_drafts", "telegram_cursors"} <= events.QUIET and "telegram_links" in audit.SKIP


def test_production_from_a_chat_is_in_the_audit_trail(db_session, ctx, monkeypatch):
    from app.models import AuditLog
    scenario(ctx)
    ctx.post("/receipts", {"date": "2026-10-01T09:00:00", "supplier_id": ctx.supplier("Mat Co"), "warehouse_id": ctx.wh["Завод 1"]["id"],
                           "rows": [{"item_id": ctx.items[n]["id"], "qty": 100000, "price": 1} for n in ("Cement", "Crushed stone", "Sand", "Rebar")]})
    _prod_chat(db_session, ctx)
    r = full(db_session, 900, "14.10.2026\nФБС 24.4.6-Т - 2")
    _confirm(db_session, ctx, r["markup"])
    with db_session() as db:
        rows = db.query(AuditLog).filter(AuditLog.entity == "production_docs", AuditLog.action == "create").all()
        assert any(a.username == "boss" for a in rows)               # recorded under the manager who approved it


# ---------------------------------------------------------------- off-site copy of backups
def _owner(db_session, uid):
    from app.models import User
    with db_session() as db:
        db.get(User, uid).is_owner = True
        db.commit()


def _backup(folder, stamp="20261016-043933", ok=True, size=100, ext="sql.gz.enc"):
    f = folder / f"prime-beton-{stamp}.{ext}"
    f.write_bytes(b"x" * size)
    if ok:
        (folder / "last-restore-check.txt").write_text(f"OK 2026-10-16T04:39:42+00:00\n  file: {f.name}\n  tables: 36\n")
    return f


def test_verified_encrypted_backup_is_sent_to_the_owner_only_once(db_session, ctx, tmp_path, monkeypatch):
    scenario(ctx)
    _owner(db_session, _linked(db_session, ctx, 810, "adm", "admin", "uz"))
    _linked(db_session, ctx, 812, "adm2", "admin", "uz")                        # another admin: gets nothing
    _linked(db_session, ctx, 811, "worker", "prod", "uz")                       # not an admin: gets nothing
    with db_session() as db:
        assert tg.due_backups(db, tmp_path) == []                              # no backups yet
    f = _backup(tmp_path)
    with db_session() as db:
        todo = tg.due_backups(db, tmp_path)
        assert [t["chat_id"] for t in todo] == [810] and todo[0]["name"] == f.name and "Shifrlangan" in todo[0]["caption"]
        assert "09:39" in todo[0]["caption"]                                    # 04:39 UTC shown in local time (UTC+5)
        tg.mark_backup_sent(db, todo[0]["user_id"], todo[0]["stamp"])
        db.commit()
    with db_session() as db:
        assert tg.due_backups(db, tmp_path) == []                              # once only
    _backup(tmp_path, stamp="20261016-103933")                                 # the next backup is sent again
    with db_session() as db:
        assert len(tg.due_backups(db, tmp_path)) == 1


def test_unverified_plain_or_failed_backups_are_never_sent(db_session, ctx, tmp_path, monkeypatch):
    scenario(ctx)
    _owner(db_session, _linked(db_session, ctx, 810, "adm", "admin", "uz"))
    _backup(tmp_path, ok=False)                                                # not test-restored yet
    with db_session() as db:
        assert tg.due_backups(db, tmp_path) == []
    f = _backup(tmp_path, ok=True)
    (tmp_path / "BACKUP_FAILED.txt").write_text("failed")                      # the container reports a problem
    with db_session() as db:
        assert tg.due_backups(db, tmp_path) == []
    (tmp_path / "BACKUP_FAILED.txt").unlink()
    f.unlink()
    plain = _backup(tmp_path, stamp="20261016-113933", ext="sql.gz")           # an unencrypted dump must never leave the server
    with db_session() as db:
        assert tg.due_backups(db, tmp_path) == [] and plain.exists()


def test_no_backup_without_a_linked_owner(db_session, ctx, tmp_path):
    scenario(ctx)
    _linked(db_session, ctx, 812, "adm2", "admin", "uz")
    _backup(tmp_path)
    with db_session() as db:
        assert tg.due_backups(db, tmp_path) == []


def test_big_backup_is_announced_not_uploaded_and_the_bot_sends_the_file(db_session, ctx, tmp_path, monkeypatch):
    import app.telegram_bot as bot
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path))
    monkeypatch.setattr(bot, "SessionLocal", db_session)
    scenario(ctx)
    _owner(db_session, _linked(db_session, ctx, 810, "adm", "admin", "uz"))
    f = _backup(tmp_path)
    docs, texts = [], []
    monkeypatch.setattr(bot, "send_document", lambda client, chat, path, cap: docs.append((chat, path, cap)))
    monkeypatch.setattr(bot, "send", lambda client, chat, text, markup=None, silent=False: texts.append((chat, text)))
    bot.push_backups(None)
    bot.push_backups(None)                                                     # the second round finds nothing new
    assert len(docs) == 1 and docs[0][0] == 810 and docs[0][1] == str(f)
    monkeypatch.setattr(tg, "MAX_FILE", 50)
    _backup(tmp_path, stamp="20261016-123933", size=500)
    bot.push_backups(None)
    assert len(docs) == 1 and texts and "juda katta" in texts[0][1]
    monkeypatch.setattr(settings, "telegram_send_backups", False)
    _backup(tmp_path, stamp="20261016-133933")
    bot.push_backups(None)
    assert len(docs) == 1 and len(texts) == 1                                  # switched off: nothing leaves the server


def test_send_document_uploads_the_file_as_multipart(tmp_path, monkeypatch):
    import httpx
    import app.telegram_bot as bot
    monkeypatch.setattr(settings, "telegram_bot_token", "123:TEST")
    f = tmp_path / "prime-beton-20261016-043933.sql.gz.enc"
    f.write_bytes(b"ENCRYPTED")
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["url"], seen["body"], seen["ctype"] = str(req.url), req.read(), req.headers["content-type"]
        return httpx.Response(200, json={"ok": True, "result": {}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        bot.send_document(c, 810, str(f), "caption here")
    assert seen["url"].endswith("/bot123:TEST/sendDocument") and seen["ctype"].startswith("multipart/form-data")
    assert b"ENCRYPTED" in seen["body"] and b'name="chat_id"' in seen["body"] and b"prime-beton-20261016-043933.sql.gz.enc" in seen["body"]
