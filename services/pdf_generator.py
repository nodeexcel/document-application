"""
PDF Generator Service — exports all content as a formatted PDF using ReportLab.
"""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# ─── Color Palette ────────────────────────────────────────────────────────────
DARK_BG = colors.HexColor("#1a1a2e")
PURPLE = colors.HexColor("#7c3aed")
LIGHT_PURPLE = colors.HexColor("#a78bfa")
WHITE = colors.white
GRAY = colors.HexColor("#888888")
LIGHT_GRAY = colors.HexColor("#cccccc")


def build_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=26,
        textColor=PURPLE,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=GRAY,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName="Helvetica",
    )

    section_header = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=PURPLE,
        spaceBefore=20,
        spaceAfter=10,
        fontName="Helvetica-Bold",
        borderPad=4,
    )

    script_title = ParagraphStyle(
        "ScriptTitle",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=LIGHT_PURPLE,
        spaceBefore=14,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6,
        leading=15,
        fontName="Helvetica",
    )

    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=GRAY,
        spaceAfter=4,
        fontName="Helvetica-Oblique",
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "section": section_header,
        "script_title": script_title,
        "body": body_style,
        "meta": meta_style,
    }


def text_to_paragraphs(text: str, style) -> list:
    """Convert multi-line text into a list of Paragraph flowables."""
    elements = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elements.append(Paragraph(safe_line, style))
        else:
            elements.append(Spacer(1, 4))
    return elements


def generate_pdf(results: dict, product_data: dict) -> bytes:
    """
    Generate a complete PDF document from all scripts and B-roll prompts.
    Returns PDF as bytes for Streamlit download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = build_styles()
    story = []

    # ── Cover Page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("🎬 Content Creator Automation", styles["title"]))
    story.append(Paragraph(f"Scripts &amp; B-Roll Prompts for: {product_data['title']}", styles["subtitle"]))
    story.append(Paragraph(f"Audience: {product_data['audience']}", styles["meta"]))
    story.append(HRFlowable(width="100%", thickness=1, color=PURPLE, spaceAfter=20))
    story.append(Spacer(1, 0.3 * inch))

    # Product summary box
    story.append(Paragraph("PRODUCT OVERVIEW", styles["section"]))
    overview_lines = [
        f"<b>Title:</b> {product_data['title']}",
        f"<b>Audience:</b> {product_data['audience']}",
        f"<b>CTA:</b> {product_data['cta']}",
        f"<b>Link:</b> {product_data.get('link', 'N/A')}",
        f"<b>Description:</b> {product_data['description'][:200]}...",
    ]
    for line in overview_lines:
        safe = line.replace("&", "&amp;").replace("<b>", "<b>").replace("</b>", "</b>")
        story.append(Paragraph(safe, styles["body"]))
    story.append(PageBreak())

    # ── Scripts Section ───────────────────────────────────────────────────────
    scripts = results.get("scripts", {})
    script_labels = [
        ("problem_promise", "Script 1: Problem → Promise"),
        ("three_mistakes", "Script 2: Three Mistakes"),
        ("before_after", "Script 3: Before → After"),
        ("myth_truth", "Script 4: Myth vs Truth"),
        ("fast_tip", "Script 5: Fast Tip → Sell"),
    ]

    story.append(Paragraph("VIDEO SCRIPTS", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_PURPLE, spaceAfter=10))

    for key, label in script_labels:
        if key in scripts:
            story.append(Paragraph(label, styles["script_title"]))
            story.extend(text_to_paragraphs(scripts[key], styles["body"]))
            story.append(Spacer(1, 0.2 * inch))
            story.append(HRFlowable(width="80%", thickness=0.3, color=LIGHT_GRAY, spaceAfter=10))

    story.append(PageBreak())

    # ── B-Roll Section ────────────────────────────────────────────────────────
    broll = results.get("broll", {})
    broll_labels = [
        ("broll_problem_promise", "B-Roll: Problem → Promise"),
        ("broll_three_mistakes", "B-Roll: Three Mistakes"),
        ("broll_before_after", "B-Roll: Before → After"),
        ("broll_myth_truth", "B-Roll: Myth vs Truth"),
        ("broll_fast_tip", "B-Roll: Fast Tip → Sell"),
    ]

    story.append(Paragraph("CINEMATIC B-ROLL PROMPTS", styles["section"]))
    story.append(Paragraph("Optimized for Kling 2.6 / Runway / Veo", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_PURPLE, spaceAfter=10))

    for key, label in broll_labels:
        if key in broll:
            story.append(Paragraph(label, styles["script_title"]))
            story.extend(text_to_paragraphs(broll[key], styles["body"]))
            story.append(Spacer(1, 0.2 * inch))
            story.append(HRFlowable(width="80%", thickness=0.3, color=LIGHT_GRAY, spaceAfter=10))

    story.append(PageBreak())

    # ── Extras Section ────────────────────────────────────────────────────────
    extras = results.get("extras", {})
    story.append(Paragraph("GUIDES & REFERENCES", styles["section"]))

    if "talking_head" in extras:
        story.append(Paragraph("HeyGen Talking Head Guide", styles["script_title"]))
        story.extend(text_to_paragraphs(extras["talking_head"], styles["body"]))
        story.append(Spacer(1, 0.3 * inch))

    if "image_guide" in extras:
        story.append(Paragraph("Image Style Guide", styles["script_title"]))
        story.extend(text_to_paragraphs(extras["image_guide"], styles["body"]))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.read()