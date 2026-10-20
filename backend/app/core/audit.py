"""Automatic audit trail.

A SQLAlchemy session hook records every create / update / delete / restore of business records together with the
signed-in user (taken from `session.info["user"]`, set by the `current_user` dependency). Row tables of documents
are folded into their parent ("rows changed"). Stock tables, counters and the log itself are never logged.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models import AuditLog

SKIP = {"audit_log", "user_sessions", "stock_balances", "stock_moves", "counters", "production_consumption", "telegram_codes", "telegram_sent", "telegram_drafts", "telegram_cursors", "telegram_links"}
CHILD = {"order_rows": ("orders", "order_id"), "invoice_rows": ("invoices", "invoice_id"),
         "receipt_rows": ("receipts", "receipt_id"), "production_rows": ("production_docs", "doc_id"),
         "stock_adjust_rows": ("stock_adjusts", "adjust_id"), "production_crew": ("production_docs", "doc_id")}
HIDDEN = {"password_hash"}
STATE_FIELDS = ("status", "is_active")


def _plain(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _label(o) -> str:
    for a in ("number", "name", "name_en", "username"):
        v = getattr(o, a, None)
        if v:
            return str(v)[:160]
    return ""


def _diff(o) -> dict:
    out = {}
    for attr in inspect(o).mapper.column_attrs:
        if attr.key in HIDDEN or attr.key == "id":
            continue
        h = inspect(o).attrs[attr.key].history
        if h.has_changes() and h.deleted:
            out[attr.key] = [_plain(h.deleted[0]), _plain(h.added[0]) if h.added else None]
    return out


def _before_flush(session: Session, ctx, instances):
    user = session.info.get("user")
    if not user:
        return
    pend = session.info.setdefault("_audit", [])
    parents: dict[tuple[str, int], object] = {}
    for o in list(session.new):
        t = o.__table__.name
        if t in SKIP:
            continue
        if t in CHILD:
            p = CHILD[t]
            parents[(p[0], getattr(o, p[1]))] = o
            continue
        pend.append(("create", o, None))
    for o in list(session.dirty):
        t = o.__table__.name
        if t in SKIP or t in CHILD:
            continue
        d = _diff(o)
        for rel in inspect(o).mapper.relationships:
            if rel.key == "rows" and inspect(o).attrs[rel.key].history.has_changes():
                d["rows"] = True
        if not d:
            continue
        action = "update"
        if "status" in d:
            old, new = d["status"]
            action = "delete" if new == "deleted" else "restore" if old == "deleted" else "update"
        elif "is_active" in d:
            action = "restore" if d["is_active"][1] else "delete"
        pend.append((action, o, d))
    for o in list(session.deleted):
        t = o.__table__.name
        if t in CHILD:
            p = CHILD[t]
            parents[(p[0], getattr(o, p[1]))] = o
        elif t not in SKIP:
            pend.append(("delete", o, None))
    for (table, pid), _ in parents.items():
        if pid is None:
            continue                       # parent is new: the create entry covers it
        parent = next((x for x in session.identity_map.values() if getattr(x, "__table__", None) is not None
                       and x.__table__.name == table and x.id == pid), None)
        if parent is not None and not any(p[1] is parent for p in pend):
            pend.append(("update", parent, {"rows": True}))


def _after_flush_postexec(session: Session, ctx):
    pend = session.info.pop("_audit", None)
    user = session.info.get("user")
    if not pend or not user:
        return
    for action, o, d in pend:
        session.add(AuditLog(user_id=user.get("id"), username=user.get("username", ""), action=action,
                             entity=o.__table__.name, entity_id=getattr(o, "id", None), label=_label(o), changes=d))


def install() -> None:
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "after_flush_postexec", _after_flush_postexec)


def record(session: Session, user, action: str, entity: str, entity_id: int | None = None, label: str = "", changes=None):
    """Explicit entry (login, AI draft accepted ...)."""
    session.add(AuditLog(user_id=getattr(user, "id", None), username=getattr(user, "username", "") or "",
                         action=action, entity=entity, entity_id=entity_id, label=label, changes=changes))
