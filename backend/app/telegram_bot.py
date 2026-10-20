"""Telegram bot process: long-polls Telegram, answers through app.services.telegram, pushes new alerts.

    python -m app.telegram_bot

Needs TELEGRAM_BOT_TOKEN in .env (from @BotFather). It only calls out to Telegram; nothing has to be opened to the internet.
The token is part of Telegram's URLs, so request logging is switched off here and errors are logged by type only.
"""
import logging
import sys
import time
from datetime import datetime

import httpx

from app.core.config import settings
from app.core.events import poke_token
from app.db.session import SessionLocal
from app.services import telegram

log = logging.getLogger("telegram_bot")
for noisy in ("httpx", "httpcore"):
    logging.getLogger(noisy).setLevel(logging.WARNING)       # their INFO lines contain the full URL, i.e. the token


def _call(client: httpx.Client, method: str, payload: dict, timeout: float = 15):
    r = client.post(f"{settings.telegram_api_base.rstrip('/')}/bot{settings.telegram_bot_token}/{method}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json().get("result")


def send(client: httpx.Client, chat_id: int, text: str, markup: dict | None = None, silent: bool = False) -> None:
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or [""]   # Telegram's limit is 4096 characters
    for n, chunk in enumerate(chunks):
        body = {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True}
        if silent:
            body["disable_notification"] = True                # arrives, but the phone stays quiet
        if markup and n == len(chunks) - 1:                   # the buttons go with the last piece
            body["reply_markup"] = markup
        _call(client, "sendMessage", body)


def deliver(client: httpx.Client, chat_id: int, msg: dict, message_id: int | None = None) -> None:
    """One reply dict from the service: edit the button message in place when asked, otherwise send a new one."""
    if msg.get("edit") and message_id:
        body = {"chat_id": chat_id, "message_id": message_id, "text": msg["text"]}
        if msg.get("markup"):
            body["reply_markup"] = msg["markup"]
        try:
            _call(client, "editMessageText", body)
            return
        except httpx.HTTPStatusError:                         # "message is not modified" and the like: not worth a crash
            return
    send(client, chat_id, msg["text"], msg.get("markup"))


def process(client: httpx.Client, update: dict) -> None:
    cb = update.get("callback_query")
    if cb:
        return process_callback(client, cb)
    msg = update.get("message") or {}
    chat = msg.get("chat") or {}
    if chat.get("type") != "private" or "text" not in msg:     # groups and channels are ignored: a group must never see business data
        return
    with SessionLocal() as db:
        reply = telegram.handle_full(db, chat["id"], msg["text"])
        db.commit()
    if reply:
        deliver(client, chat["id"], reply)


def process_callback(client: httpx.Client, cb: dict) -> None:
    m = cb.get("message") or {}
    chat = m.get("chat") or {}
    try:
        _call(client, "answerCallbackQuery", {"callback_query_id": cb["id"]})   # stops the button's spinner
    except httpx.HTTPError:
        pass
    if chat.get("type") != "private":
        return
    with SessionLocal() as db:
        out = telegram.callback(db, chat["id"], cb.get("data") or "")
        db.commit()
    for reply in out:
        if reply.get("to"):                                   # a message for somebody else (the manager, or the sender when it is decided)
            send(client, reply["to"], reply["text"], reply.get("markup"))
        else:
            deliver(client, chat["id"], reply, m.get("message_id"))


def push_alerts(client: httpx.Client) -> None:
    with SessionLocal() as db:
        todo = telegram.due_alerts(db, datetime.now())
        quiet = telegram.silent_chats(db)
        db.commit()
    for chat_id, text in todo:
        try:
            send(client, chat_id, text, silent=chat_id in quiet)
        except httpx.HTTPError as e:
            log.warning("alert not delivered: %s", type(e).__name__)


def push_events(client: httpx.Client) -> None:
    """New orders, shipments, payments, production batches, and the daily summary."""
    with SessionLocal() as db:
        todo = telegram.due_events(db) + telegram.due_changes(db) + telegram.due_summaries(db)
        quiet = telegram.silent_chats(db)
        db.commit()                                           # the cursors move even if a send fails: no endless repeats
    for chat_id, text in todo:
        try:
            send(client, chat_id, text, silent=chat_id in quiet)
        except httpx.HTTPError as e:
            log.warning("event not delivered: %s", type(e).__name__)


def send_document(client: httpx.Client, chat_id: int, path: str, caption: str) -> None:
    url = f"{settings.telegram_api_base.rstrip('/')}/bot{settings.telegram_bot_token}/sendDocument"
    with open(path, "rb") as fh:
        r = client.post(url, data={"chat_id": chat_id, "caption": caption, "disable_notification": "true"}, files={"document": (path.rsplit("/", 1)[-1], fh)}, timeout=180)
    r.raise_for_status()


def push_backups(client: httpx.Client) -> None:
    """The newest verified (encrypted) backup goes to the main admin's (owner's) chat once."""
    if not settings.telegram_send_backups:
        return
    with SessionLocal() as db:
        todo = telegram.due_backups(db)
    for it in todo:
        try:
            if it.get("notice"):
                send(client, it["chat_id"], it["notice"])
            else:
                send_document(client, it["chat_id"], it["path"], it["caption"])
        except (httpx.HTTPError, OSError) as e:
            log.warning("backup not delivered: %s", type(e).__name__)
            continue
        with SessionLocal() as db:                            # remembered only after Telegram accepted it
            telegram.mark_backup_sent(db, it["user_id"], it["stamp"])
            db.commit()


def _poke_api() -> None:
    """Tell the API that data changed, so every open page reloads (the live hub lives in the API process)."""
    try:
        httpx.post(f"{settings.internal_api_url}/api/live/poke", headers={"X-Poke": poke_token(settings.secret_key)}, timeout=3)
    except Exception as e:                                    # the page just refreshes a little later
        log.warning("live update not sent: %s", type(e).__name__)


def enable_live_bridge() -> None:
    """Everything the bot records (production from a chat) gets the same audit trail and live refresh as a change made on the website."""
    from app.core import audit, events
    audit.install()
    events.hub.publish = _poke_api
    events.install()


def run(once: bool = False) -> None:
    enable_live_bridge()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if not settings.telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is empty: the bot is off. Put the token from @BotFather into .env and start again.")
        sys.exit(0 if once else 1)
    offset, last_alert, last_event, last_backup = 0, 0.0, 0.0, 0.0
    with httpx.Client() as client:
        log.info("Telegram bot started")
        while True:
            try:
                for upd in _call(client, "getUpdates", {"offset": offset, "timeout": 0 if once else 25, "allowed_updates": ["message", "callback_query"]}, timeout=45) or []:
                    offset = upd["update_id"] + 1
                    try:
                        process(client, upd)
                    except Exception as e:                    # one bad message must not stop the bot
                        log.warning("message failed: %s", type(e).__name__)
                if time.time() - last_event > 15:
                    last_event = time.time()
                    try:
                        push_events(client)
                    except Exception as e:                    # a database hiccup must not stop the bot
                        log.warning("events failed: %s", type(e).__name__)
                if time.time() - last_backup > 300:
                    last_backup = time.time()
                    try:
                        push_backups(client)
                    except Exception as e:
                        log.warning("backups failed: %s", type(e).__name__)
                if time.time() - last_alert > settings.telegram_alert_minutes * 60:
                    last_alert = time.time()
                    push_alerts(client)
            except httpx.HTTPError as e:
                log.warning("Telegram not reachable: %s", type(e).__name__)
                time.sleep(5)
            if once:
                return


if __name__ == "__main__":
    run()
