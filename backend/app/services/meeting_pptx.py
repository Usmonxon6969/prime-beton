"""The monthly meeting deck as a PowerPoint file (16:9). Same numbers as the on-screen slides (services/meeting.py)."""
from io import BytesIO

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

INK, MUTED, LINE = RGBColor(0x0F, 0x10, 0x12), RGBColor(0x56, 0x5B, 0x61), RGBColor(0xD4, 0xD7, 0xDA)
ACCENT, GOOD, BAD = RGBColor(0xC2, 0x41, 0x0C), RGBColor(0x1F, 0x7A, 0x4A), RGBColor(0xB4, 0x23, 0x18)
PAPER, SOFT = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xF1, 0xF2, 0xF3)
W, H = Inches(13.333), Inches(7.5)
FONT = "Calibri"


def _num(v, kind="num"):
    """Whole numbers with a space between thousands; under 10 one decimal; never a trailing ",0"."""
    if v is None:
        return "—"
    if isinstance(v, str):
        return v
    a = abs(v)
    q = int(a + 0.5) if (kind == "money" or a >= 10) else int(a * 10 + 0.5) / 10
    if isinstance(q, float) and q == int(q):
        q = int(q)
    txt = f"{q:,}".replace(",", " ") if isinstance(q, int) else str(q).replace(".", ",")
    sign = "-" if v < 0 and q else ("+" if kind == "pct" and q else "")
    return sign + txt + ("%" if kind == "pct" else "")


def _text(slide, x, y, w, h, text, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, FONT
    return tb


def _rect(slide, x, y, w, h, fill=None, line=None):
    s = slide.shapes.add_shape(1, x, y, w, h)
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s


def _header(prs, deck, title, n):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(s, 0, 0, Inches(0.18), H, ACCENT)
    _text(s, Inches(0.7), Inches(0.45), Inches(10), Inches(0.8), title, 32, True)
    _text(s, Inches(9.2), Inches(0.55), Inches(3.5), Inches(0.4), deck["label"], 14, False, MUTED, PP_ALIGN.RIGHT)
    _text(s, Inches(0.7), Inches(7.0), Inches(6), Inches(0.3), "Prime Beton", 10, False, MUTED)
    _text(s, Inches(11.7), Inches(7.0), Inches(1), Inches(0.3), str(n), 10, False, MUTED, PP_ALIGN.RIGHT)
    return s


def _kpis(s, kpis, vs, y=Inches(1.5)):
    """Cards in rows of at most five (a sixth starts a new row)."""
    for r0 in range(0, len(kpis), 5):
        row = kpis[r0:r0 + 5]
        n = max(len(row), 1)
        gap = Inches(0.25)
        w = min(int((Inches(11.9) - gap * (n - 1)) / n), Inches(3.9))
        for i, k in enumerate(row):
            x = Inches(0.7) + (w + gap) * i
            _rect(s, x, y, w, Inches(1.5), PAPER, LINE)
            _text(s, x + Inches(0.2), y + Inches(0.15), w - Inches(0.4), Inches(0.3), k["label"], 12, False, MUTED)
            val = _num(k["value"]) + (f" {k['unit']}" if k.get("unit") else "")
            _text(s, x + Inches(0.2), y + Inches(0.45), w - Inches(0.4), Inches(0.6), val, 26 if len(val) <= 9 else 22 if len(val) <= 12 else 18 if len(val) <= 16 else 14, True)
            if k.get("delta") is not None:
                up = k["delta"] >= 0
                col = (BAD if up else GOOD) if k.get("bad_up") else (GOOD if up else BAD)
                _text(s, x + Inches(0.2), y + Inches(1.1), w - Inches(0.4), Inches(0.3), f"{'▲' if up else '▼'} {_num(abs(k['delta']))}% {vs}", 11, True, col)
            elif k.get("prev") is not None:
                _text(s, x + Inches(0.2), y + Inches(1.1), w - Inches(0.4), Inches(0.3), f"{_num(k['prev'])} {vs}", 11, False, MUTED)
            if k.get("target"):
                _text(s, x + Inches(0.2), y + Inches(1.28), w - Inches(0.4), Inches(0.2), ("✓ " if k["target"]["ok"] else "▼ ") + k["target"]["text"], 10, True, GOOD if k["target"]["ok"] else BAD)
        y += Inches(1.75)
    return y


def _spots(s, spots, y):
    """Highlight cards: who or what stood out (top plant, best day, best worker ...)."""
    n = max(len(spots), 1)
    gap = Inches(0.25)
    w = min(int((Inches(11.9) - gap * (n - 1)) / n), Inches(3.9))
    for i, sp in enumerate(spots):
        x = Inches(0.7) + (w + gap) * i
        _rect(s, x, y, w, Inches(1.2), SOFT, None)
        _rect(s, x, y, Inches(0.06), Inches(1.2), ACCENT)
        _text(s, x + Inches(0.2), y + Inches(0.1), w - Inches(0.35), Inches(0.25), sp["label"], 10, False, MUTED)
        name = str(sp["name"])
        _text(s, x + Inches(0.2), y + Inches(0.36), w - Inches(0.35), Inches(0.32), name, 16 if len(name) <= 20 else 13 if len(name) <= 30 else 11, True)
        _text(s, x + Inches(0.2), y + Inches(0.72), w - Inches(0.35), Inches(0.25), (_num(sp["value"]) + (f" {sp['unit']}" if sp.get("unit") else "")) if sp.get("value") is not None else "", 13, True, ACCENT)
        if sp.get("note"):
            _text(s, x + Inches(0.2), y + Inches(0.95), w - Inches(0.35), Inches(0.2), sp["note"], 9, False, MUTED)
    return y + Inches(1.45)


def _table(s, t, x, y, w, max_rows=10):
    cols, rows = t["columns"], t["rows"][:max_rows]
    if not rows:
        return y
    if t.get("title"):
        _text(s, x, y, w, Inches(0.28), t["title"], 12, True, MUTED)
        y += Inches(0.32)
    h = Inches(0.34) * (len(rows) + 1)
    gt = s.shapes.add_table(len(rows) + 1, len(cols), x, y, w, h).table
    for j, c in enumerate(cols):
        gt.columns[j].width = int(w * (0.4 if j == 0 else 0.6 / max(len(cols) - 1, 1)))
    for j, c in enumerate(cols):
        cell = gt.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = INK
        cell.text = c["label"]
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if c["type"] == "text" else PP_ALIGN.RIGHT
        p.runs[0].font.size, p.runs[0].font.bold, p.runs[0].font.color.rgb, p.runs[0].font.name = Pt(11), True, PAPER, FONT
    for i, r in enumerate(rows, 1):
        for j, c in enumerate(cols):
            cell = gt.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = SOFT if i % 2 == 0 else PAPER
            v = r.get(c["key"])
            cell.text = _num(v, c["type"]) if c["type"] != "text" else str(v if v is not None else "")
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c["type"] == "text" else PP_ALIGN.RIGHT
            f = p.runs[0].font
            f.size, f.name, f.color.rgb = Pt(11), FONT, INK
            if c["type"] == "pct" and v is not None:
                f.color.rgb = GOOD if v >= 0 else BAD
    return y + h + Inches(0.2)


def _fade(slide):
    """A soft fade between slides, so the file feels like the on-screen deck."""
    from lxml import etree
    ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    sld = slide._element
    tr = etree.SubElement(sld, f"{{{ns}}}transition")
    tr.set("spd", "med")
    etree.SubElement(tr, f"{{{ns}}}fade")


def _remark(s, text):
    n = len(text)
    size, h = (14, 0.62) if n <= 170 else (12, 0.8) if n <= 300 else (11, 0.95)
    y = 6.85 - h
    _rect(s, Inches(0.7), Inches(y), Inches(0.08), Inches(h), ACCENT)
    _text(s, Inches(0.95), Inches(y), Inches(11.6), Inches(h), text, size, False, MUTED, PP_ALIGN.LEFT, MSO_ANCHOR.MIDDLE)


def build(deck: dict, ai: dict | None = None) -> bytes:
    ai = ai if ai and ai.get("ai") else None
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    # cover
    s = prs.slides.add_slide(prs.slide_layouts[6])
    _rect(s, 0, 0, W, H, INK)
    _rect(s, Inches(0.9), Inches(3.0), Inches(0.9), Inches(0.08), ACCENT)
    _text(s, Inches(0.9), Inches(1.6), Inches(11), Inches(1.2), deck["title"], 48, True, PAPER)
    _text(s, Inches(0.9), Inches(3.3), Inches(11), Inches(0.8), deck["label"], 30, False, PAPER)
    if deck.get("note"):
        _text(s, Inches(0.9), Inches(4.2), Inches(11), Inches(0.6), deck["note"], 16, False, RGBColor(0xC9, 0xCC, 0xD0))
    _text(s, Inches(0.9), Inches(6.5), Inches(8), Inches(0.4), "Prime Beton", 14, False, RGBColor(0x9A, 0xA0, 0xA6))
    n = 1
    for sl in deck["slides"]:
        tabs = [t for t in sl.get("tables", []) if t["rows"]]
        ser = sl.get("series") if sl.get("series") and sl["series"]["points"] else None
        top = 1.75 * (-(-len(sl.get("kpis") or []) // 5)) + (1.45 if sl.get("spots") else 0)
        room = 4.6 - top                                                   # inches left for tables under the figures (the remark takes the bottom)
        fit = int(room / 0.34) - 1                                         # table rows that fit there
        pages = [(sl["title"], True, True)]
        nk = len(sl.get("kpis") or []) + len(sl.get("spots") or [])
        need = max(len(t["rows"]) for t in tabs) + 2 if len(tabs) == 2 and not ser else sum(len(t["rows"]) + 2 for t in tabs) if tabs else 0
        if tabs and sl.get("kpis") and nk >= 3 and need > fit + 1:
            pages = [(sl["title"], True, False), (f"{sl['title']}: {deck['labels'].get('more', '')}".rstrip(": "), False, True)]    # figures first, the tables on a page of their own
        for page, (ptitle, figures, detail) in enumerate(pages):
            n += 1
            s = _header(prs, deck, ptitle, n)
            y = Inches(1.5)
            if figures and sl.get("kpis"):
                y = _kpis(s, sl["kpis"], deck["vs"], y)
            if figures and sl.get("spots"):
                y = _spots(s, sl["spots"], y)
            if figures and sl.get("empty") and not sl.get("kpis") and not sl.get("spots"):
                _text(s, Inches(0.7), y, Inches(10), Inches(0.5), deck["empty_text"], 16, False, MUTED)
            if figures and (sl.get("bullets") or (ai and sl["id"] == "summary" and ai["points"])):
                for bl in (sl.get("bullets") or []) + ((ai or {}).get("points", []) if sl["id"] == "summary" else []):
                    _rect(s, Inches(0.75), y + Inches(0.12), Inches(0.12), Inches(0.12), ACCENT)
                    _text(s, Inches(1.1), y, Inches(11.4), Inches(0.5), bl, 16 if len(sl.get("bullets") or []) > 6 else 18)
                    y += Inches(0.5) if len(sl.get("bullets") or []) > 6 else Inches(0.55)
            rows_cap = 10 if not (sl.get("kpis") or sl.get("spots")) or not figures else max(fit, 3)
            if page == 1:
                y, rows_cap = Inches(1.5), 12 if len(tabs) == 1 else 11
            if ser and (figures or not (sl.get("kpis") or sl.get("spots"))) and not (pages[0][2] is False and page == 1):
                cd = CategoryChartData()
                cd.categories = [p["x"] for p in ser["points"]]
                cd.add_series(ser["label"], [p["y"] for p in ser["points"]])
                if tabs and page == 0 and len(pages) == 1:
                    cx, cw, ch_h = Inches(7.4), Inches(5.3), Inches(3.6)
                else:
                    cx, cw, ch_h = Inches(0.7), Inches(11.9), max(Inches(2.2), min(Inches(3.4), Inches(6.1) - y))
                gf = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, cx, y, cw, ch_h, cd)
                ch = gf.chart
                ch.has_legend = False
                ch.has_title = True
                ch.chart_title.text_frame.text = ser["label"]
                ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(12)
                ch.series[0].format.line.color.rgb = ACCENT
                ch.series[0].smooth = False
                ch.category_axis.tick_labels.font.size = Pt(9)
                ch.value_axis.tick_labels.font.size = Pt(9)
                ch.value_axis.major_gridlines.format.line.color.rgb = LINE
                if tabs and len(pages) == 1:
                    yy = y
                    for t in tabs:
                        yy = _table(s, t, Inches(0.7), yy, Inches(6.4), max(3, rows_cap // len(tabs) - 1))
                    tabs_done = True
                else:
                    tabs_done = False
            else:
                tabs_done = False
            if detail and tabs and not tabs_done:
                if len(tabs) == 2:
                    _table(s, tabs[0], Inches(0.7), y, Inches(5.9), rows_cap)
                    _table(s, tabs[1], Inches(6.9), y, Inches(5.8), rows_cap)
                else:
                    for t in tabs:
                        y = _table(s, t, Inches(0.7), y, Inches(11.9), rows_cap)
            if ai and ai["slides"].get(sl["id"]) and (page == len(pages) - 1 or len(pages) == 1):
                _remark(s, ai["slides"][sl["id"]])
    if ai and ai["questions"]:
        s = _header(prs, deck, deck["labels"].get("questions", "?"), n + 1)
        y = Inches(1.6)
        for q in ai["questions"]:
            _text(s, Inches(0.7), y, Inches(0.6), Inches(0.6), "?", 28, True, ACCENT)
            _text(s, Inches(1.4), y + Inches(0.05), Inches(11), Inches(0.9), q, 20)
            y += Inches(1.1)
    for sl in prs.slides:
        _fade(sl)
    out = BytesIO()
    prs.save(out)
    return out.getvalue()
