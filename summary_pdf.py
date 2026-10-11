"""Doctor-ready symptom summary PDF (reportlab). Latin text only, like the V2 report PDF."""
import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

NAVY = colors.HexColor("#0b2a55")


def _p(text, style):
    # reportlab's base fonts cannot draw Bangla, so non-Latin characters become "?"
    safe = escape(str(text)).encode("latin-1", "replace").decode("latin-1")
    return Paragraph(safe, style)


def build_summary_pdf(d):
    """d: dict with region, severity, answers, free_text, age, sex, date, result (assess output)."""
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=NAVY, fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], textColor=NAVY, fontSize=12, spaceBefore=10, spaceAfter=3)
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14)
    small = ParagraphStyle("s", parent=body, fontSize=8, textColor=colors.grey)
    red = ParagraphStyle("r", parent=body, textColor=colors.HexColor("#b00020"), fontName="Helvetica-Bold")

    r = d.get("result") or {}
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=16 * mm, title="Symptom summary for your doctor")
    s = [_p("Symptom summary for your doctor", h1),
         _p("Made with ReportSimple V3. Information typed by the patient. Not a diagnosis.", small), Spacer(1, 6)]

    who = [f"Date: {str(d.get('date', ''))[:10]}"]
    if d.get("age"):
        who.append(f"Age: {str(d['age'])[:3]}")
    if d.get("sex"):
        who.append(f"Sex: {str(d['sex'])[:10]}")
    s.append(_p("  |  ".join(who), body))

    flags = ((r.get("safety") or {}).get("flags")) or []
    if flags:
        s.append(_p("Warning signs noted", h2))
        for f in flags[:6]:
            s.append(_p("- " + f.get("message", ""), red))

    s.append(_p("Main complaint", h2))
    line = f"Body area: {str(d.get('region', '')) or 'not selected'}"
    if d.get("severity") not in (None, ""):
        line += f"   Severity: {d['severity']}/10"
    s.append(_p(line, body))
    if d.get("free_text"):
        s.append(_p("In the patient's words: " + str(d["free_text"])[:600], body))
    if r.get("summary"):
        s.append(_p(r["summary"], body))

    if d.get("answers"):
        s.append(_p("Interview answers", h2))
        for k, v in list((d.get("answers") or {}).items())[:15]:
            s.append(_p(f"- {str(k)[:30]}: {str(v)[:100]}", body))

    conds = r.get("possible_conditions") or []
    if conds:
        s.append(_p("Possible conditions to discuss (not a diagnosis)", h2))
        for c in conds[:4]:
            s.append(_p(f"- {c.get('name', '')} ({c.get('likelihood', '')})", body))
            if c.get("supports"):
                s.append(_p("  Fits: " + c["supports"], small))
            if c.get("missing"):
                s.append(_p("  Still needed: " + c["missing"], small))

    for title, key in (("Tests to discuss", "tests_to_discuss"), ("Questions to ask the doctor", "questions_for_doctor")):
        items = r.get(key) or []
        if items:
            s.append(_p(title, h2))
            for it in items[:6]:
                s.append(_p("- " + str(it), body))

    srcs = r.get("sources") or []
    if srcs:
        s.append(_p("Sources found", h2))
        for x in srcs[:6]:
            s.append(_p(f"- {x.get('title', '')} ({x.get('source', '')}, {x.get('year', '')}) {x.get('url', '')}", small))

    s += [Spacer(1, 10), _p("Educational tool only. It does not diagnose and is not a substitute for a doctor. "
                            "Do not start or stop any medicine without a registered doctor's advice.", small)]
    doc.build(s)
    return out.getvalue()
