from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.deps import current_user, need
from app.core.errors import not_found
from app.core.roles import ROLES, SECTIONS
from app.db.session import get_db
from app.models import Customer, Invoice, Item, Supplier, User, Warehouse
from app.api.company import get_company
from app.ai import meeting_ai
from app.core.premium import premium, spend
from app.services import analytics, exports, meeting, meeting_pptx, reports

from app.core.roles import level

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/dashboard")
def dashboard(days: int = Query(14, ge=7, le=60), db: Session = Depends(get_db), user: User = Depends(need("dash", 1))):
    lv = {s: ROLES.get(user.role, {}).get(s, 0) for s in SECTIONS}
    return reports.dashboard(db, lv, days)


@router.get("/customer-debts")
def customer_debts(db: Session = Depends(get_db), _: User = Depends(need("cus", 1))):
    return reports.customer_debts(db)


@router.get("/supplier-debts")
def supplier_debts(db: Session = Depends(get_db), _: User = Depends(need("sup", 1))):
    return reports.supplier_debts(db)


@router.get("/customers/{cid}/statement")
def customer_statement(cid: int, start: datetime | None = None, end: datetime | None = None,
                       db: Session = Depends(get_db), _: User = Depends(need("cus", 1))):
    c = db.get(Customer, cid)
    if not c:
        raise not_found("customer")
    return {"customer": c.name, **reports.statement(db, customer_id=cid, supplier_id=None, start=start, end=end)}


@router.get("/suppliers/{sid}/statement")
def supplier_statement(sid: int, start: datetime | None = None, end: datetime | None = None,
                       db: Session = Depends(get_db), _: User = Depends(need("sup", 1))):
    s = db.get(Supplier, sid)
    if not s:
        raise not_found("supplier")
    return {"supplier": s.name, **reports.statement(db, customer_id=None, supplier_id=sid, start=start, end=end)}


# ---------- reports center ----------
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _allowed(user: User, name: str, who: str) -> None:
    from fastapi import HTTPException
    if name not in analytics.NEEDS:
        raise not_found("report")
    if not analytics.allowed({s: level(user.role, s) for s in SECTIONS}, name, who):
        raise HTTPException(403, {"code": "forbidden", "message": "Your role cannot do this", "params": {"section": name}})


def _levels(user: User) -> dict:
    return {s: level(user.role, s) for s in SECTIONS}


def _run(db, user, name, p):
    _allowed(user, name, p["who"])
    return analytics.run(db, name, start=p["start"], end=p["end"], group=p["group"], warehouse_id=p["warehouse_id"],
                         kind=p["kind"], who=p["who"], lang=p["lang"], levels=_levels(user), item_id=p["item_id"], doc=p["doc"])


def _params(start: datetime | None = None, end: datetime | None = None, group: str | None = None,
            warehouse_id: int | None = None, kind: str | None = None, item_id: int | None = None,
            doc: str | None = Query(None, pattern="^(production|receipt|invoice|adjust)$"), who: str = Query("customer", pattern="^(customer|supplier)$"),
            lang: str = Query("en", pattern="^(uz|ru|en)$")):
    return dict(start=start, end=end, group=group, warehouse_id=warehouse_id, kind=kind, item_id=item_id, doc=doc, who=who, lang=lang)


@router.get("/center/{name}")
def center(name: str, p: dict = Depends(_params), db: Session = Depends(get_db), user: User = Depends(current_user)):
    t = _run(db, user, name, p)
    t["labels"] = {c["key"]: analytics.label(c["key"], p["lang"]) for c in t["columns"]}
    return t


@router.get("/center/{name}/export.xlsx")
def center_xlsx(name: str, p: dict = Depends(_params), db: Session = Depends(get_db), user: User = Depends(current_user)):
    t = _run(db, user, name, p)
    sub = " — ".join(x for x in (p["start"] and f"{p['start']:%d.%m.%Y}", p["end"] and f"{p['end']:%d.%m.%Y}") if x)
    data = exports.table_xlsx(t, name.capitalize(), p["lang"], sub)
    return Response(data, media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{name}.xlsx"'})


# ---------- monthly meeting ----------
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _meeting(db, user, month, lang):
    spend(db, user, "meeting", month)                  # a month not held yet costs one of the user's uses; the same month again is free
    return meeting.build(db, month, lang, _levels(user))


@router.get("/meeting")
def monthly_meeting(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), lang: str = Query("en", pattern="^(uz|ru|en)$"),
                    db: Session = Depends(get_db), user: User = Depends(premium("meeting"))):
    return _meeting(db, user, month, lang)


@router.get("/meeting/ai")
def monthly_meeting_ai(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), lang: str = Query("en", pattern="^(uz|ru|en)$"),
                       db: Session = Depends(get_db), user: User = Depends(premium("meeting"))):
    """Remarks and discussion questions written by the AI from the same figures the slides show (empty when no AI key is set)."""
    return meeting_ai.enrich(_meeting(db, user, month, lang), lang)


@router.get("/meeting/export.pptx")
def monthly_meeting_pptx(month: str = Query(..., pattern=r"^\d{4}-\d{2}$"), lang: str = Query("en", pattern="^(uz|ru|en)$"),
                         ai: bool = False, db: Session = Depends(get_db), user: User = Depends(premium("meeting"))):
    deck = _meeting(db, user, month, lang)
    data = meeting_pptx.build(deck, meeting_ai.enrich(deck, lang) if ai else None)
    return Response(data, media_type=PPTX, headers={"Content-Disposition": f'attachment; filename="meeting-{month}.pptx"'})


# ---------- printing ----------
PDF = "application/pdf"


@router.get("/print/invoice/{iid}.pdf")
def print_invoice(iid: int, lang: str = Query("en", pattern="^(uz|ru|en)$"), db: Session = Depends(get_db),
                  _: User = Depends(need("inv", 1))):
    inv = db.get(Invoice, iid)
    if not inv:
        raise not_found("invoice")
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_([r.item_id for r in inv.rows]))}
    order_no = inv.order.number if getattr(inv, "order", None) else ""
    if not order_no and inv.order_id:
        from app.models import Order
        o = db.get(Order, inv.order_id)
        order_no = o.number if o else ""
    pdf = exports.invoice_pdf(inv, db.get(Customer, inv.customer_id), db.get(Warehouse, inv.warehouse_id), items, lang, order_no)
    return Response(pdf, media_type=PDF, headers={"Content-Disposition": f'inline; filename="{inv.number}.pdf"'})


@router.get("/print/waybill/{iid}.pdf")
def print_waybill(iid: int, db: Session = Depends(get_db), _: User = Depends(need("inv", 1))):
    inv = db.get(Invoice, iid)
    if not inv:
        raise not_found("invoice")
    items = {i.id: i for i in db.query(Item).filter(Item.id.in_([r.item_id for r in inv.rows]))}
    pdf = exports.waybill_pdf(inv, db.get(Customer, inv.customer_id), db.get(Warehouse, inv.warehouse_id), items, get_company(db))
    return Response(pdf, media_type=PDF, headers={"Content-Disposition": f'inline; filename="{inv.number}.pdf"'})


@router.get("/print/statement.pdf")
def print_statement(customer_id: int | None = None, supplier_id: int | None = None, start: datetime | None = None,
                    end: datetime | None = None, lang: str = Query("en", pattern="^(uz|ru|en)$"),
                    db: Session = Depends(get_db), user: User = Depends(current_user)):
    from fastapi import HTTPException
    if bool(customer_id) == bool(supplier_id):
        raise HTTPException(422, {"code": "invalid", "message": "Give a customer or a supplier", "params": {}})
    sec = "cus" if customer_id else "sup"
    if level(user.role, sec) < 1:
        raise HTTPException(403, {"code": "forbidden", "message": "Your role cannot do this", "params": {"section": sec}})
    party = db.get(Customer if customer_id else Supplier, customer_id or supplier_id)
    if not party:
        raise not_found("customer" if customer_id else "supplier")
    data = reports.statement(db, customer_id=customer_id, supplier_id=supplier_id, start=start, end=end, lang=lang)
    pdf = exports.statement_pdf("customer" if customer_id else "supplier", party.name, data, start, end, lang)
    return Response(pdf, media_type=PDF, headers={"Content-Disposition": 'inline; filename="statement.pdf"'})
