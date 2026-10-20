"""Excel export of report tables and PDF printing of delivery notes and reconciliation acts."""
import io
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.analytics import label

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_ready = False

T = {  # printing words: uz, ru, en
    "invoice": ("Yuk xati (nakladnoy)", "Накладная на отгрузку", "Delivery note"),
    "act": ("Solishtirma dalolatnoma", "Акт сверки взаиморасчётов", "Reconciliation statement"),
    "no": ("№", "№", "No."), "date": ("Sana", "Дата", "Date"), "customer": ("Mijoz", "Покупатель", "Customer"),
    "supplier": ("Yetkazib beruvchi", "Поставщик", "Supplier"), "warehouse": ("Ombor", "Склад", "Warehouse"),
    "order": ("Buyurtma", "Заказ", "Order"), "item": ("Mahsulot", "Наименование", "Item"),
    "unit": ("Birlik", "Ед.", "Unit"), "qty": ("Miqdor", "Кол-во", "Qty"), "price": ("Narx", "Цена", "Price"),
    "sum": ("Summa", "Сумма", "Amount"), "total": ("Jami", "Итого", "Total"),
    "gave": ("Topshirdi", "Отпустил", "Released by"), "took": ("Qabul qildi", "Получил", "Received by"),
    "period": ("Davr", "Период", "Period"), "opening": ("Boshlang‘ich qoldiq", "Сальдо на начало", "Opening balance"),
    "closing": ("Oxirgi qoldiq", "Сальдо на конец", "Closing balance"), "doc": ("Hujjat", "Документ", "Document"),
    "debit": ("Qarz oshdi", "Начислено", "Charged"), "credit": ("To‘landi", "Оплачено", "Paid"),
    "balance": ("Qoldiq", "Остаток", "Balance"), "invoice_k": ("Jo‘natma", "Отгрузка", "Shipment"),
    "receipt_k": ("Kirim", "Поступление", "Receipt"), "payment_k": ("To‘lov", "Оплата", "Payment"),
    "signa": ("Tomon 1", "Сторона 1", "Party 1"), "sigb": ("Tomon 2", "Сторона 2", "Party 2"),
    "owes": ("Mijoz qarzi", "Задолженность покупателя", "Customer owes"),
    "we_owe": ("Bizning qarzimiz", "Наша задолженность", "We owe"),
}
L = {"uz": 0, "ru": 1, "en": 2}


def tr(key, lang):
    return T[key][L.get(lang, 2)]


def money(x) -> str:
    return f"{x:,.2f}".replace(",", " ")


def qty(x) -> str:
    return (f"{x:,.3f}".rstrip("0").rstrip(".")).replace(",", " ")


def _fonts():
    global _ready
    if not _ready:
        pdfmetrics.registerFont(TTFont("DV", str(FONTS / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DV-B", str(FONTS / "DejaVuSans-Bold.ttf")))
        for name, file in (("SF", "DejaVuSerif.ttf"), ("SF-B", "DejaVuSerif-Bold.ttf"), ("SF-BI", "DejaVuSerif-BoldItalic.ttf")):
            pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
        _ready = True


# ---------- Excel ----------
def table_xlsx(table: dict, title: str, lang: str, subtitle: str = "") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]
    ws.append([title])
    ws["A1"].font = Font(bold=True, size=14)
    if subtitle:
        ws.append([subtitle])
    ws.append([])
    head_row = ws.max_row + 1
    ws.append([label(c["key"], lang) for c in table["columns"]])
    for cell in ws[head_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F4858")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    fmt = {"money": "#,##0.00", "num": "#,##0.###", "int": "0"}
    for r in table["rows"]:
        ws.append([r.get(c["key"]) for c in table["columns"]])
    for row in ws.iter_rows(min_row=head_row + 1):
        for cell, c in zip(row, table["columns"]):
            if c["type"] in fmt:
                cell.number_format = fmt[c["type"]]
    if table["totals"]:
        tot = [None] * len(table["columns"])
        tot[0] = tr("total", lang)
        for i, c in enumerate(table["columns"]):
            if c["key"] in table["totals"]:
                tot[i] = table["totals"][c["key"]]
        ws.append(tot)
        for cell, c in zip(ws[ws.max_row], table["columns"]):
            cell.font = Font(bold=True)
            if c["type"] in fmt:
                cell.number_format = fmt[c["type"]]
    for i, c in enumerate(table["columns"], 1):
        width = max([len(str(label(c["key"], lang)))] + [len(str(r.get(c["key"], ""))) for r in table["rows"]]) + 3
        ws.column_dimensions[get_column_letter(i)].width = min(max(width, 10), 48)
    ws.freeze_panes = ws.cell(row=head_row + 1, column=1)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- PDF ----------
def _styles():
    _fonts()
    return (ParagraphStyle("t", fontName="DV-B", fontSize=15, leading=19, spaceAfter=4),
            ParagraphStyle("n", fontName="DV", fontSize=9.5, leading=13),
            ParagraphStyle("b", fontName="DV-B", fontSize=9.5, leading=13))


def _grid(data, widths, right_cols=(), total=True):
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("FONT", (0, 0), (-1, -1), "DV", 8.5), ("FONT", (0, 0), (-1, 0), "DV-B", 8.5),
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf0")),
          ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8a98a0")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    for c in right_cols:
        st.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    if total:
        st.append(("FONT", (0, -1), (-1, -1), "DV-B", 8.5))
    t.setStyle(TableStyle(st))
    return t


def _build(story, landscape_: bool = False) -> bytes:
    buf = io.BytesIO()
    if landscape_:
        SimpleDocTemplate(buf, pagesize=(A4[1], A4[0]), leftMargin=7 * mm, rightMargin=7 * mm, topMargin=6 * mm, bottomMargin=6 * mm).build(story)
    else:
        SimpleDocTemplate(buf, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm, bottomMargin=14 * mm).build(story)
    return buf.getvalue()


def invoice_pdf(inv, customer, warehouse, items: dict, lang: str, order_no: str = "") -> bytes:
    title, n, b = _styles()
    nm = lambda it: getattr(it, "name_" + (lang if lang in L else "en"))   # noqa: E731
    story = [Paragraph(f"{tr('invoice', lang)} {tr('no', lang)} {inv.number}", title),
             Paragraph(f"{tr('date', lang)}: {inv.date:%d.%m.%Y %H:%M}", n),
             Paragraph(f"{tr('customer', lang)}: <b>{customer.name}</b>", n),
             Paragraph(f"{tr('warehouse', lang)}: {warehouse.name}", n)]
    if order_no:
        story.append(Paragraph(f"{tr('order', lang)}: {order_no}", n))
    story.append(Spacer(1, 6 * mm))
    data = [["#", tr("item", lang), tr("unit", lang), tr("qty", lang), tr("price", lang), tr("sum", lang)]]
    total = 0
    for i, r in enumerate(inv.rows, 1):
        it = items[r.item_id]
        s = r.qty * r.price
        total += s
        data.append([i, nm(it), it.unit.name, qty(r.qty), money(r.price), money(s)])
    data.append(["", tr("total", lang), "", "", "", money(total)])
    story.append(_grid(data, [9 * mm, 78 * mm, 17 * mm, 24 * mm, 26 * mm, 26 * mm], right_cols=(3, 4, 5)))
    story += [Spacer(1, 16 * mm), Table([[f"{tr('gave', lang)}: ____________", f"{tr('took', lang)}: ____________"]],
                                        colWidths=[90 * mm, 90 * mm], style=[("FONT", (0, 0), (-1, -1), "DV", 9)])]
    return _build(story)


MONTHS_UZ = ("yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentyabr", "oktyabr", "noyabr", "dekabr")
LOGO = Path(__file__).resolve().parent.parent / "assets" / "prime-beton-logo.png"


def waybill_pdf(inv, customer, warehouse, items: dict, company: dict) -> bytes:
    """The loading waybill (yuk xati / накладная): no prices, driver and vehicle, signatures. Uzbek and Russian side by side.
    One landscape A4 sheet carries two identical copies: one stays with us, one goes with the driver."""
    _fonts()
    ink = colors.HexColor("#111111")
    W = 139 * mm                                                      # width of one copy
    st = lambda size, font="SF", align=0, lead=None: ParagraphStyle("w", fontName=font, fontSize=size, leading=lead or size * 1.22, alignment=align, textColor=ink)  # noqa: E731
    small, label_s = st(7.6, align=1, lead=9.6), st(8.8)
    story = []
    if LOGO.exists():
        w = 58 * mm
        story.append(Image(str(LOGO), width=w, height=w * 560 / 1768, hAlign="CENTER"))
        story.append(Spacer(1, 1 * mm))
    line1 = " ".join(x for x in (
        (_esc(company.get("address", "")) + ".") if company.get("address") else "",
        f"<b>Pochta manzili:</b> {_esc(company['postcode'])}." if company.get("postcode") else "",
        f"<b>OKONX:</b> {_esc(company['okonh'])}." if company.get("okonh") else "") if x)
    line2 = " ".join(x for x in (
        f"<b>Hisob raqami:</b> {_esc(company['account'])}," if company.get("account") else "",
        (_esc(company["bank"]) + ".") if company.get("bank") else "") if x)
    line3 = ", ".join(x for x in (
        f"<b>MFO:</b> {_esc(company['mfo'])}" if company.get("mfo") else "",
        f"<b>INN:</b> {_esc(company['inn'])}" if company.get("inn") else "",
        f"<b>Tel.:</b> {_esc(company['phone'])}" if company.get("phone") else "") if x)
    for ln in (line1, line2, line3):
        if ln:
            story.append(Paragraph(ln, small))
    rule = Table([[""]], colWidths=[W], rowHeights=[2], style=[("LINEBELOW", (0, 0), (-1, -1), 0.8, ink)])
    story += [Spacer(1, 1 * mm), rule, Spacer(1, 2.5 * mm)]
    d = inv.date
    story += [Paragraph(f"{d.day:02d} / {MONTHS_UZ[d.month - 1]} / {d.year} yil", label_s), Spacer(1, 2 * mm),
              Paragraph(f"YUK XATI / НАКЛАДНАЯ &nbsp;№ {_esc(inv.number)}", st(11.5, "SF-B", 1)), Spacer(1, 2.5 * mm)]
    frm = company.get("name") or "Prime Beton"
    who = Table([[Paragraph("Kimdan/От кого :", label_s), Paragraph(_esc(frm), st(9, "SF-BI"))],
                 [Paragraph("Kimga/Кому :", label_s), Paragraph(_esc(customer.name), st(12, "SF-BI", lead=14.5))]],
                colWidths=[34 * mm, W - 34 * mm], hAlign="LEFT",
                style=[("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LINEBELOW", (1, 1), (1, 1), 0.6, ink), ("LEFTPADDING", (0, 0), (-1, -1), 2),
                       ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)])
    story += [who, Spacer(1, 3 * mm)]
    hs, hc = st(8.6, "SF-B", 0, 10), st(8.6, "SF-B", 1, 10)
    data = [[Paragraph("№", hs), Paragraph("Nomi<br/>Наименование", hs), Paragraph("Ulcham bir<br/>Ед.изм", hc), Paragraph("Soni<br/>Кол-во", hc)]]
    totals: dict[str, float] = {}
    cell, cellc = st(9.4, "SF-B"), st(9.4, "SF-B", 1)
    for i, r in enumerate(inv.rows, 1):
        it = items[r.item_id]
        unit = it.unit.name_ru or it.unit.name
        totals[unit] = totals.get(unit, 0) + float(r.qty)
        data.append([Paragraph(str(i), cell), Paragraph(_esc(it.name_ru or it.name_uz), cell), Paragraph(_esc(unit), cellc), Paragraph(qty(r.qty), cellc)])
    while len(data) < 9:                                              # the form always shows at least 8 lines
        data.append([Paragraph(str(len(data)), cell), "", Paragraph(_esc(next(iter(totals), "")), cellc), ""])
    data.append(["", Paragraph("Jami / Итого", cell), Paragraph(" + ".join(totals) or "", cellc), Paragraph(" + ".join(qty(v) for v in totals.values()), cellc)])
    row_h = 6.6 * mm if len(data) <= 11 else 5.4 * mm
    t = Table(data, colWidths=[9 * mm, 72 * mm, 29 * mm, W - 110 * mm], hAlign="LEFT", rowHeights=[None] + [row_h] * (len(data) - 1))
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.8, ink), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    story += [t, Spacer(1, 4 * mm)]
    trans = Table([[Paragraph("Haydovchi/ Водитель :", label_s), Paragraph(_esc(inv.driver or ""), st(10, "SF-BI"))],
                   [Paragraph("Mashina raqami/Номер машины :", label_s), Paragraph(_esc(inv.vehicle or ""), st(10, "SF-BI"))]],
                  colWidths=[64 * mm, 56 * mm], hAlign="LEFT",
                  style=[("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LINEBELOW", (1, 0), (1, -1), 0.6, ink), ("LEFTPADDING", (0, 0), (-1, -1), 2),
                         ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)])
    note = company.get("receive_note", "")
    sign = Table([[Paragraph("Berdim/Отпустил", label_s), "", ""],
                  [Paragraph("Oldim/Получил", label_s), "", Paragraph(f"({_esc(note)})" if note else "", st(7.8))]],
                 colWidths=[34 * mm, 34 * mm, W - 68 * mm], hAlign="LEFT",
                 style=[("LINEBELOW", (1, 0), (1, 1), 0.6, ink), ("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)])
    story += [trans, Spacer(1, 2 * mm), sign]
    # two identical copies side by side, with a thin cut line between them
    sheet = Table([[story, "", _copy_of(story)]], colWidths=[W, 10 * mm, W], hAlign="CENTER",
                  style=[("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                         ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                         ("LINEAFTER", (0, 0), (0, 0), 0.4, colors.HexColor("#9aa4aa"), None, (2, 3))])
    return _build([sheet], landscape_=True)


def _copy_of(story):
    """A flowable list cannot be placed in two cells; make a second one with the same content."""
    import copy
    return [copy.deepcopy(f) for f in story]


def _esc(x) -> str:
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def statement_pdf(kind: str, party: str, data: dict, start, end, lang: str) -> bytes:
    title, n, b = _styles()
    word = {"invoice": "invoice_k", "receipt": "receipt_k", "payment": "payment_k"}
    first = start or (data["rows"][0]["date"] if data["rows"] else (end or datetime.now()))
    period = f"{first:%d.%m.%Y} — " + (f"{end:%d.%m.%Y}" if end else f"{datetime.now():%d.%m.%Y}")
    story = [Paragraph(tr("act", lang), title), Paragraph(f"{tr('customer' if kind == 'customer' else 'supplier', lang)}: <b>{party}</b>", n),
             Paragraph(f"{tr('period', lang)}: {period}", n), Spacer(1, 5 * mm)]
    rows = [[tr("date", lang), tr("doc", lang), tr("debit", lang), tr("credit", lang), tr("balance", lang)],
            [tr("opening", lang), "", "", "", money(data["opening"])]]
    small = ParagraphStyle("s", fontName="DV", fontSize=7.5, leading=9.5, textColor=colors.HexColor("#46545c"))
    sub = []                                                         # rows that list what a document contained
    for r in data["rows"]:
        rows.append([f"{r['date']:%d.%m.%Y}", f"{tr(word[r['kind']], lang)} {r['number']}",
                     money(r["debit"]) if r["debit"] else "", money(r["credit"]) if r["credit"] else "", money(r["balance"])])
        for it in r.get("items", []):
            sub.append(len(rows))
            rows.append(["", Paragraph(f"&nbsp;&nbsp;{_esc(it['name'])}", small),
                         Paragraph(f"{qty(it['qty'])} {_esc(it['unit'])} × {money(it['price'])} = <b>{money(it['amount'])}</b>",
                                   ParagraphStyle("sr", parent=small, alignment=2)), "", ""])
    rows.append([tr("closing", lang), "", money(data["debit"]), money(data["credit"]), money(data["closing"])])
    t = _grid(rows, [40 * mm, 52 * mm, 29 * mm, 29 * mm, 30 * mm], right_cols=(2, 3, 4))
    extra = []
    for i in sub:
        extra += [("SPAN", (2, i), (4, i)), ("TOPPADDING", (0, i), (-1, i), 1.5), ("BOTTOMPADDING", (0, i), (-1, i), 1.5),
                  ("LINEABOVE", (0, i), (-1, i), 0.2, colors.HexColor("#d5dce0")), ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f6f8f9"))]
    if extra:
        t.setStyle(TableStyle(extra))
    story.append(t)
    owe = tr("owes" if kind == "customer" else "we_owe", lang)
    story += [Spacer(1, 5 * mm), Paragraph(f"{owe}: <b>{money(max(data['closing'], 0))}</b>", n), Spacer(1, 16 * mm),
              Table([[f"{tr('signa', lang)}: ____________", f"{tr('sigb', lang)}: ____________"]], colWidths=[90 * mm, 90 * mm],
                    style=[("FONT", (0, 0), (-1, -1), "DV", 9)])]
    return _build(story)
