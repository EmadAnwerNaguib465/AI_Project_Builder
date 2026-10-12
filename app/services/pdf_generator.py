"""
app/services/pdf_generator.py

Generates professional, publication-quality PDF reports from Planorai JSON data.
Can be used via CLI, FastAPI endpoint, or internal services.
"""

from __future__ import annotations

import html
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    along with running header and footer.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header for page 2 and later
        if self._pageNumber > 1:
            self.drawString(42, 804, "Planorai — Technical Blueprint")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.6)
            self.line(42, 796, 553, 796)

        # Footer on all pages
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(553, 30, footer_text)
        self.drawString(42, 30, "Confidential — Designed with Planorai")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.6)
        self.line(42, 40, 553, 40)

        self.restoreState()


def _format_markdown_inline(text: str) -> str:
    """Safely escapes text and translates basic Markdown into ReportLab XML."""
    if not text:
        return ""
    # 1. Escape HTML special characters
    safe = html.escape(str(text))
    # 2. Inline code: `code`
    safe = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier" color="#1E293B"><b>\1</b></font>',
        safe,
    )
    # 3. Bold: **text** or __text__
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"__([^_]+)__", r"<b>\1</b>", safe)
    # 4. Italic: *text* or _text_
    safe = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", safe)
    safe = re.sub(r"_([^_]+)_", r"<i>\1</i>", safe)
    # 5. Links: [label](url)
    safe = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" color="#4F46E5"><u>\1</u></a>',
        safe,
    )
    return safe


def _markdown_to_flowables(
    md_text: str,
    base_style: ParagraphStyle,
    h2_style: ParagraphStyle,
    h3_style: ParagraphStyle,
    bullet_style: ParagraphStyle,
) -> list[Any]:
    """Converts a Markdown block into a series of ReportLab flowable elements."""
    elements: list[Any] = []
    lines = md_text.strip().split("\n")
    buffer: list[str] = []

    def flush_buffer() -> None:
        if buffer:
            joined = " ".join(buffer).strip()
            if joined:
                elements.append(Paragraph(_format_markdown_inline(joined), base_style))
                elements.append(Spacer(1, 6))
            buffer.clear()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_buffer()
            continue

        if line.startswith("### "):
            flush_buffer()
            elements.append(Paragraph(_format_markdown_inline(line[4:]), h3_style))
            elements.append(Spacer(1, 4))
        elif line.startswith("## "):
            flush_buffer()
            elements.append(Paragraph(_format_markdown_inline(line[3:]), h2_style))
            elements.append(Spacer(1, 4))
        elif line.startswith("# "):
            flush_buffer()
            elements.append(Paragraph(_format_markdown_inline(line[2:]), h2_style))
            elements.append(Spacer(1, 4))
        elif line.startswith(("- ", "* ", "+ ")):
            flush_buffer()
            bullet_text = f"&bull;  {_format_markdown_inline(line[2:].strip())}"
            elements.append(Paragraph(bullet_text, bullet_style))
            elements.append(Spacer(1, 3))
        elif re.match(r"^\d+\.\s+", line):
            flush_buffer()
            m = re.match(r"^(\d+\.)\s+(.*)", line)
            if m:
                num_prefix, content = m.groups()
                item_text = f"<b>{num_prefix}</b> {_format_markdown_inline(content.strip())}"
                elements.append(Paragraph(item_text, bullet_style))
                elements.append(Spacer(1, 3))
        else:
            buffer.append(line)

    flush_buffer()
    return elements


def generate_pdf_from_dict(
    data: Dict[str, Any],
    output_target: Union[str, Path, io.BytesIO],
) -> None:
    """
    Renders a complete, beautifully designed PDF from a project plan dictionary.
    
    Args:
        data: Dictionary conforming to ProjectReport / FinalProjectPlan schema.
        output_target: File path (str/Path) or BytesIO buffer.
    """
    # Defensive normalization
    title = str(data.get("project_title") or "Technical Project Plan")
    summary = str(data.get("executive_summary") or "")
    timeline = data.get("estimated_timeline_weeks", 0)
    roadmap = data.get("implementation_roadmap") or []
    sources = data.get("sources") or []
    revisions = data.get("revision_count", 0)
    objectives = data.get("objectives") or []
    metrics = data.get("success_metrics") or []
    skills = data.get("required_skills") or []
    tools = data.get("recommended_tools") or []
    architecture = str(data.get("technical_architecture") or "")
    dataset_plan = str(data.get("dataset_plan") or "")
    datasets = data.get("dataset_recommendations") or []
    dataset_note = data.get("dataset_discovery_note") or ""
    model_plan = str(data.get("model_plan") or "")
    risks = data.get("risks_and_mitigations") or []

    # Page setup
    doc = SimpleDocTemplate(
        output_target,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=52,
        bottomMargin=52,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    style_eyebrow = ParagraphStyle(
        "DocEyebrow",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#4F46E5"),
        spaceAfter=4,
    )
    style_title = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8,
    )
    style_summary = ParagraphStyle(
        "DocSummary",
        fontName="Helvetica",
        fontSize=10,
        leading=14.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=14,
    )
    style_h1 = ParagraphStyle(
        "DocH1",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )
    style_h2 = ParagraphStyle(
        "DocH2",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    style_h3 = ParagraphStyle(
        "DocH3",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "DocBody",
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
    )
    style_bullet = ParagraphStyle(
        "DocBullet",
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        leftIndent=12,
        textColor=colors.HexColor("#334155"),
    )
    style_badge_num = ParagraphStyle(
        "DocBadgeNum",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        alignment=1,  # Center
        textColor=colors.HexColor("#4F46E5"),
    )
    style_badge_label = ParagraphStyle(
        "DocBadgeLabel",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        alignment=1,
        textColor=colors.HexColor("#64748B"),
    )

    story: list[Any] = []

    # 1. Header & Title Block (with Logo if available)
    logo_path = Path("Logo.png")
    if not logo_path.exists():
        logo_path = Path(__file__).resolve().parent.parent.parent / "Logo.png"
    if logo_path.exists():
        try:
            story.append(RLImage(str(logo_path), width=120, height=60))
            story.append(Spacer(1, 8))
        except Exception:
            pass

    story.append(Paragraph("PLANORAI &bull; BLUEPRINT", style_eyebrow))
    story.append(Paragraph(_format_markdown_inline(title), style_title))
    if summary:
        story.append(Paragraph(_format_markdown_inline(summary), style_summary))

    # 2. Metrics Bar (KPI Table)
    metric_cells = [
        [
            Paragraph(f"{timeline} <font size=9>weeks</font>", style_badge_num),
            Paragraph(str(len(roadmap)), style_badge_num),
            Paragraph(str(len(sources)), style_badge_num),
            Paragraph(str(revisions), style_badge_num),
        ],
        [
            Paragraph("ESTIMATED TIMELINE", style_badge_label),
            Paragraph("BUILD STEPS", style_badge_label),
            Paragraph("RESEARCH SOURCES", style_badge_label),
            Paragraph("REVIEW CYCLES", style_badge_label),
        ],
    ]
    col_width = (511) / 4.0
    metrics_table = Table(metric_cells, colWidths=[col_width] * 4)
    metrics_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
            ("TOPPADDING", (0, 1), (-1, 1), 2),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )
    story.append(metrics_table)
    story.append(Spacer(1, 14))

    # Helper function for section headings
    def add_section_header(label: str) -> None:
        story.append(
            KeepTogether([
                Paragraph(label, style_h1),
                HRFlowable(
                    width="100%",
                    thickness=1,
                    color=colors.HexColor("#E2E8F0"),
                    spaceBefore=2,
                    spaceAfter=8,
                ),
            ])
        )

    # 3. Overview Section
    add_section_header("1. Project Overview & Strategy")

    if objectives:
        story.append(Paragraph("Key Objectives", style_h2))
        for idx, obj in enumerate(objectives, 1):
            story.append(
                Paragraph(
                    f"<b>{idx:02d}.</b>  {_format_markdown_inline(obj)}",
                    style_bullet,
                )
            )
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 6))

    if metrics:
        story.append(Paragraph("Success Metrics", style_h2))
        for m in metrics:
            story.append(
                Paragraph(
                    f"&bull;  {_format_markdown_inline(m)}",
                    style_bullet,
                )
            )
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 6))

    if skills or tools:
        story.append(Paragraph("Required Skills & Recommended Stack", style_h2))
        if skills:
            skills_txt = ", ".join(f"<b>{html.escape(s)}</b>" for s in skills)
            story.append(Paragraph(f"Skills: {skills_txt}", style_body))
            story.append(Spacer(1, 3))
        if tools:
            tools_txt = ", ".join(f"<b>{html.escape(t)}</b>" for t in tools)
            story.append(Paragraph(f"Recommended Tools: {tools_txt}", style_body))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 6))

    # 4. Architecture Section
    if architecture:
        add_section_header("2. Technical Architecture")
        story.extend(
            _markdown_to_flowables(
                architecture, style_body, style_h2, style_h3, style_bullet
            )
        )
        story.append(Spacer(1, 6))

    # 5. Dataset Strategy Section
    add_section_header("3. Dataset Strategy")

    if dataset_note:
        story.append(
            Paragraph(
                f"<i>Note: {_format_markdown_inline(dataset_note)}</i>",
                style_body,
            )
        )
        story.append(Spacer(1, 6))

    # Recommended datasets cards
    if datasets:
        story.append(Paragraph(f"Recommended Datasets ({len(datasets)})", style_h2))
        for ds in datasets:
            ds_name = html.escape(str(ds.get("name") or "Unnamed Dataset"))
            ds_url = str(ds.get("url") or "")
            ds_provider = html.escape(str(ds.get("provider") or "Catalog"))
            ds_desc = _format_markdown_inline(str(ds.get("description") or ""))
            ds_relevance = _format_markdown_inline(str(ds.get("relevance") or ""))
            ds_type = html.escape(str(ds.get("data_type") or "N/A"))
            ds_size = html.escape(str(ds.get("size") or "N/A"))
            ds_license = html.escape(str(ds.get("license") or "N/A"))

            title_html = (
                f'<b>{ds_name}</b> &nbsp;&nbsp;'
                f'<font size=7.5 color="#4F46E5">[{ds_provider}]</font>'
            )
            if ds_url.startswith("http"):
                title_html += f' &nbsp;&bull;&nbsp; <a href="{ds_url}" color="#4F46E5"><u>View Dataset Link</u></a>'

            card_content = [
                [Paragraph(title_html, style_body)],
                [Paragraph(f"<b>Description:</b> {ds_desc}", style_body)],
                [Paragraph(f"<b>Project Fit:</b> {ds_relevance}", style_body)],
                [
                    Paragraph(
                        f"<font size=8 color='#64748B'><b>Type:</b> {ds_type} &nbsp;|&nbsp; <b>Size:</b> {ds_size} &nbsp;|&nbsp; <b>License:</b> {ds_license}</font>",
                        style_body,
                    )
                ],
            ]

            card_table = Table(card_content, colWidths=[511])
            card_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )
            story.append(KeepTogether([card_table, Spacer(1, 6)]))

    if dataset_plan:
        story.append(Paragraph("Dataset Plan & Pipeline", style_h2))
        story.extend(
            _markdown_to_flowables(
                dataset_plan, style_body, style_h2, style_h3, style_bullet
            )
        )
        story.append(Spacer(1, 6))

    # 6. Model Strategy Section
    if model_plan:
        add_section_header("4. Model Strategy & Evaluation")
        story.extend(
            _markdown_to_flowables(
                model_plan, style_body, style_h2, style_h3, style_bullet
            )
        )
        story.append(Spacer(1, 6))

    # 7. Roadmap & Risks Section
    add_section_header("5. Implementation Roadmap & Risks")

    if roadmap:
        story.append(Paragraph("Implementation Steps", style_h2))
        for idx, step in enumerate(roadmap, 1):
            story.append(
                Paragraph(
                    f"<b>Step {idx:02d}:</b>  {_format_markdown_inline(step)}",
                    style_bullet,
                )
            )
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 6))

    if risks:
        story.append(Paragraph("Risks & Mitigations", style_h2))
        for risk in risks:
            story.append(
                Paragraph(
                    f"&bull;  {_format_markdown_inline(risk)}",
                    style_bullet,
                )
            )
            story.append(Spacer(1, 3))
        story.append(Spacer(1, 6))

    # 8. Sources Section
    if sources:
        add_section_header("6. Research Sources & References")
        for idx, src in enumerate(sources, 1):
            src_str = str(src).strip()
            if src_str.startswith("http"):
                src_html = f'<a href="{src_str}" color="#4F46E5"><u>{html.escape(src_str)}</u></a>'
            else:
                src_html = html.escape(src_str)
            story.append(
                Paragraph(
                    f"<b>[{idx}]</b>  {src_html}",
                    style_bullet,
                )
            )
            story.append(Spacer(1, 2))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)


def generate_pdf_from_json_file(
    json_path: Union[str, Path],
    output_pdf_path: Union[str, Path, None] = None,
) -> Path:
    """Reads a JSON file and writes out a formatted PDF file."""
    src = Path(json_path)
    if not src.exists():
        raise FileNotFoundError(f"JSON report file not found: {src}")

    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)

    if output_pdf_path is None:
        out_path = src.with_suffix(".pdf")
    else:
        out_path = Path(output_pdf_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    generate_pdf_from_dict(data, str(out_path))
    return out_path
