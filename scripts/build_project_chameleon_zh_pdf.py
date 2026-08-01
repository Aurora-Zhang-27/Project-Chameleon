#!/usr/bin/env python3
"""Build the complete Chinese Project Chameleon report as a typeset PDF."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/paper/PROJECT_CHAMELEON_COMPLETE_PROCESS_AND_RESULTS_ZH.md"
OUTPUT = ROOT / "output/pdf/Project_Chameleon_完整研究过程与成果_中文.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT = 18 * mm
RIGHT = 18 * mm
TOP = 18 * mm
BOTTOM = 17 * mm
CONTENT_WIDTH = PAGE_WIDTH - LEFT - RIGHT

INK = colors.HexColor("#17212B")
TEAL = colors.HexColor("#0E6670")
BLUE = colors.HexColor("#245A7A")
PALE_TEAL = colors.HexColor("#E8F4F3")
PALE_BLUE = colors.HexColor("#EDF3F8")
WARM = colors.HexColor("#F7F4EE")
MUTED = colors.HexColor("#65727D")
RULE = colors.HexColor("#C7D1D8")


def clean_text(text: str) -> str:
    """Normalize unsupported typography without changing mathematical meaning."""
    return (
        text.replace("\u2011", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2212", "-")
        .replace("\u00a0", " ")
    )


def inline_markup(text: str) -> str:
    text = html.escape(clean_text(text))
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


class ChameleonDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            LEFT,
            BOTTOM,
            CONTENT_WIDTH,
            PAGE_HEIGHT - TOP - BOTTOM,
            id="body",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="normal", frames=[frame], onPage=self._decorate_page),
            ]
        )

    def _decorate_page(self, canvas, doc):
        page = canvas.getPageNumber()
        if page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(LEFT, PAGE_HEIGHT - 12 * mm, PAGE_WIDTH - RIGHT, PAGE_HEIGHT - 12 * mm)
        canvas.setFont("STHeiti", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(LEFT, PAGE_HEIGHT - 9.5 * mm, "PROJECT CHAMELEON")
        canvas.drawRightString(
            PAGE_WIDTH - RIGHT,
            PAGE_HEIGHT - 9.5 * mm,
            "完整研究过程与成果 - 中文技术总报告",
        )
        canvas.line(LEFT, 11 * mm, PAGE_WIDTH - RIGHT, 11 * mm)
        canvas.drawString(LEFT, 7.3 * mm, "版本 2026-08-01")
        canvas.drawRightString(PAGE_WIDTH - RIGHT, 7.3 * mm, f"第 {page} 页")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        level = getattr(flowable, "_toc_level", None)
        title = getattr(flowable, "_toc_title", None)
        if level is None or title is None:
            return
        key = f"h-{self.page}-{abs(hash((title, self.page))) % 1000000}"
        self.canv.bookmarkPage(key)
        if level == 0:
            self.canv.addOutlineEntry(clean_text(title), key, level=0, closed=False)
        elif level == 1:
            self.canv.addOutlineEntry(clean_text(title), key, level=1, closed=True)
        self.notify("TOCEntry", (level, clean_text(title), self.page, key))


def make_styles():
    base = getSampleStyleSheet()
    styles = {}
    styles["body"] = ParagraphStyle(
        "BodyZH",
        parent=base["BodyText"],
        fontName="STHeiti",
        fontSize=9.6,
        leading=15,
        textColor=INK,
        alignment=TA_JUSTIFY,
        wordWrap="CJK",
        spaceAfter=4.5,
        allowWidows=0,
        allowOrphans=0,
    )
    styles["small"] = ParagraphStyle(
        "SmallZH",
        parent=styles["body"],
        fontSize=7.6,
        leading=11,
        textColor=MUTED,
    )
    styles["title"] = ParagraphStyle(
        "TitleZH",
        parent=styles["body"],
        fontSize=21,
        leading=29,
        alignment=TA_LEFT,
        textColor=TEAL,
        spaceAfter=9 * mm,
    )
    styles["subtitle"] = ParagraphStyle(
        "SubtitleZH",
        parent=styles["body"],
        fontSize=12,
        leading=19,
        textColor=BLUE,
        spaceAfter=3 * mm,
    )
    styles["h1"] = ParagraphStyle(
        "H1ZH",
        parent=styles["body"],
        fontSize=17,
        leading=24,
        textColor=TEAL,
        spaceBefore=11,
        spaceAfter=7,
        keepWithNext=True,
    )
    styles["h2"] = ParagraphStyle(
        "H2ZH",
        parent=styles["body"],
        fontSize=12.6,
        leading=18,
        textColor=BLUE,
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True,
    )
    styles["h3"] = ParagraphStyle(
        "H3ZH",
        parent=styles["body"],
        fontSize=10.7,
        leading=16,
        textColor=TEAL,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )
    styles["quote"] = ParagraphStyle(
        "QuoteZH",
        parent=styles["body"],
        leftIndent=8 * mm,
        rightIndent=5 * mm,
        borderColor=TEAL,
        borderWidth=1.6,
        borderPadding=(4, 7, 4, 9),
        backColor=PALE_TEAL,
        textColor=BLUE,
        spaceBefore=4,
        spaceAfter=7,
    )
    styles["bullet"] = ParagraphStyle(
        "BulletZH",
        parent=styles["body"],
        leftIndent=6 * mm,
        firstLineIndent=-3.7 * mm,
        bulletIndent=1 * mm,
        spaceAfter=2.5,
    )
    styles["equation"] = ParagraphStyle(
        "EquationZH",
        parent=styles["body"],
        fontName="STHeiti",
        fontSize=9.2,
        leading=14,
        alignment=TA_CENTER,
        leftIndent=6 * mm,
        rightIndent=6 * mm,
        backColor=WARM,
        borderColor=RULE,
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=7,
    )
    styles["code"] = ParagraphStyle(
        "CodeZH",
        parent=styles["body"],
        fontName="Courier",
        fontSize=7.7,
        leading=11,
        leftIndent=3 * mm,
        rightIndent=3 * mm,
        backColor=colors.HexColor("#F2F4F6"),
        borderColor=RULE,
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=7,
    )
    styles["caption"] = ParagraphStyle(
        "CaptionZH",
        parent=styles["small"],
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceBefore=3,
        spaceAfter=8,
    )
    styles["toc_title"] = ParagraphStyle(
        "TOCTitleZH",
        parent=styles["h1"],
        fontSize=20,
        leading=26,
        spaceAfter=8 * mm,
    )
    return styles


def heading_para(text: str, level: int, styles):
    style = styles[{1: "h1", 2: "h2", 3: "h3"}[level]]
    para = Paragraph(inline_markup(text), style)
    para._toc_level = 0 if level == 1 else 1 if level == 2 else None
    para._toc_title = clean_text(text) if level <= 2 else None
    return para


def table_widths(rows, width):
    n = max(len(r) for r in rows)
    header = [c.lower() for c in rows[0]]
    if n == 2:
        return [0.27 * width, 0.73 * width]
    if n == 3:
        return [0.22 * width, 0.38 * width, 0.40 * width]
    if n == 4 and any("proposition" in c or "命题" in c for c in header):
        return [0.10 * width, 0.24 * width, 0.43 * width, 0.23 * width]
    if n == 4:
        return [0.19 * width, 0.23 * width, 0.33 * width, 0.25 * width]
    if n == 5:
        return [0.13 * width, 0.13 * width, 0.22 * width, 0.32 * width, 0.20 * width]
    if n == 6:
        return [0.12 * width, 0.13 * width, 0.18 * width, 0.18 * width, 0.18 * width, 0.21 * width]
    return [width / n] * n


def build_table(raw_rows, styles):
    n = max(len(r) for r in raw_rows)
    normalized = [r + [""] * (n - len(r)) for r in raw_rows]
    data = []
    for ridx, row in enumerate(normalized):
        style = ParagraphStyle(
            f"Cell-{ridx}",
            parent=styles["small"],
            fontSize=7.2 if n >= 5 else 7.7,
            leading=10.2 if n >= 5 else 11,
            textColor=colors.white if ridx == 0 else INK,
            alignment=TA_CENTER if ridx == 0 else TA_LEFT,
        )
        data.append([Paragraph(inline_markup(cell), style) for cell in row])
    table = LongTable(
        data,
        colWidths=table_widths(raw_rows, CONTENT_WIDTH),
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=True,
    )
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for idx in range(1, len(data)):
        if idx % 2 == 0:
            commands.append(("BACKGROUND", (0, idx), (-1, idx), PALE_BLUE))
    table.setStyle(TableStyle(commands))
    return table


def parse_markdown(text: str, styles):
    lines = clean_text(text).splitlines()
    story = []
    i = 0
    first_heading_seen = False
    list_counter = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("[[FIGURE:") and stripped.endswith("]]"):
            rel = stripped[len("[[FIGURE:") : -2].strip()
            image_path = ROOT / rel
            if image_path.exists():
                img = Image(str(image_path))
                max_w = CONTENT_WIDTH
                max_h = 92 * mm
                scale = min(max_w / img.imageWidth, max_h / img.imageHeight)
                img.drawWidth = img.imageWidth * scale
                img.drawHeight = img.imageHeight * scale
                img.hAlign = "CENTER"
                story.extend([Spacer(1, 4), img, Spacer(1, 2)])
            i += 1
            continue

        if stripped == "---":
            story.extend([Spacer(1, 4), HRFlowable(width="100%", color=RULE, thickness=0.6), Spacer(1, 5)])
            i += 1
            continue

        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if not first_heading_seen:
                first_heading_seen = True
                story.extend(
                    [
                        Spacer(1, 31 * mm),
                        Paragraph(inline_markup(title), styles["title"]),
                        Paragraph("完整研究过程、理论结果、实验修订与最终证据", styles["subtitle"]),
                        Spacer(1, 7 * mm),
                        HRFlowable(width="28%", color=TEAL, thickness=2.2, hAlign="LEFT"),
                        Spacer(1, 14 * mm),
                        Paragraph(
                            "Capability contracts as information projections of physical flexibility",
                            styles["subtitle"],
                        ),
                        Spacer(1, 42 * mm),
                        Paragraph("中文技术总报告与项目事实底稿", styles["subtitle"]),
                        Paragraph("版本：2026-08-01", styles["body"]),
                        Paragraph("研究状态：理论与轻量 full-binary 数值验证完成", styles["body"]),
                        PageBreak(),
                    ]
                )
                toc = TableOfContents()
                toc.levelStyles = [
                    ParagraphStyle(
                        "TOC0",
                        fontName="STHeiti",
                        fontSize=10,
                        leading=15,
                        leftIndent=0,
                        firstLineIndent=0,
                        textColor=TEAL,
                        spaceBefore=3,
                    ),
                    ParagraphStyle(
                        "TOC1",
                        fontName="STHeiti",
                        fontSize=8.6,
                        leading=12.5,
                        leftIndent=6 * mm,
                        firstLineIndent=0,
                        textColor=INK,
                    ),
                ]
                story.extend(
                    [
                        Paragraph("目录", styles["toc_title"]),
                        toc,
                        PageBreak(),
                    ]
                )
            else:
                story.append(heading_para(title, 1, styles))
            i += 1
            continue

        if stripped.startswith("## "):
            story.append(heading_para(stripped[3:].strip(), 1, styles))
            i += 1
            continue
        if stripped.startswith("### "):
            story.append(heading_para(stripped[4:].strip(), 2, styles))
            i += 1
            continue
        if stripped.startswith("#### "):
            story.append(heading_para(stripped[5:].strip(), 3, styles))
            i += 1
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            story.append(Paragraph(inline_markup(" ".join(quote_lines)), styles["quote"]))
            continue

        if stripped == "$$":
            eq_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != "$$":
                eq_lines.append(lines[i].strip())
                i += 1
            i += 1
            eq = " ".join(eq_lines).replace("\\qquad", "    ")
            eq = eq.replace("\\text{", "").replace("}", "")
            story.append(Paragraph(inline_markup(eq), styles["equation"]))
            continue

        if stripped.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            story.append(XPreformatted(html.escape("\n".join(code_lines)), styles["code"]))
            continue

        if stripped.startswith("|") and "|" in stripped[1:]:
            raw_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                parts = [p.strip() for p in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", p or "") for p in parts):
                    raw_rows.append(parts)
                i += 1
            if raw_rows:
                story.extend([build_table(raw_rows, styles), Spacer(1, 6)])
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        number_match = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if bullet_match or number_match:
            if number_match:
                bullet = f"{number_match.group(1)}."
                content = number_match.group(2)
            else:
                bullet = "•"
                content = bullet_match.group(1)
            story.append(
                Paragraph(
                    f'<font color="#0E6670">{bullet}</font> {inline_markup(content)}',
                    styles["bullet"],
                )
            )
            i += 1
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith("#")
                or nxt.startswith(">")
                or nxt == "$$"
                or nxt.startswith("```")
                or nxt.startswith("|")
                or nxt == "---"
                or nxt.startswith("[[FIGURE:")
                or re.match(r"^[-*]\s+", nxt)
                or re.match(r"^\d+\.\s+", nxt)
            ):
                break
            para_lines.append(nxt)
            i += 1
        paragraph = " ".join(para_lines)
        style = styles["caption"] if paragraph.startswith(("图 ", "表 ")) else styles["body"]
        story.append(Paragraph(inline_markup(paragraph), style))

    return story


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing source: {SOURCE}", file=sys.stderr)
        return 2
    pdfmetrics.registerFont(
        TTFont("STHeiti", "/System/Library/Fonts/STHeiti Medium.ttc", subfontIndex=0)
    )
    registerFontFamily(
        "STHeiti",
        normal="STHeiti",
        bold="STHeiti",
        italic="STHeiti",
        boldItalic="STHeiti",
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    story = parse_markdown(SOURCE.read_text(encoding="utf-8"), styles)
    doc = ChameleonDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Project Chameleon 完整研究过程与成果",
        author="Project Chameleon",
        subject="能力合同、信息投影与可组合灵活性的充分状态",
    )
    doc.multiBuild(story)
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
