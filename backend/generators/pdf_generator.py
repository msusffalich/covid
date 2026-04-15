"""
PDF Generator
=============
Uses fpdf2 to produce a professional, multi-page PDF report from the
structured research data produced by the research agent.

Design decisions
----------------
- All text is written using built-in Helvetica so no external font files
  are required (zero-dependency on system fonts).
- Long strings are wrapped automatically via FPDF's multi_cell.
- Sources / bibliography section is appended as the last page.
- Extra user instructions (if any) are used as a "Foreword" section.
"""

import re
import uuid
from pathlib import Path

from fpdf import FPDF  # fpdf2

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_DARK_BLUE = (26, 58, 110)
_MID_BLUE = (52, 119, 189)
_LIGHT_GRAY = (245, 246, 248)
_WHITE = (255, 255, 255)
_TEXT = (33, 37, 41)


class _ResearchPDF(FPDF):
    """Custom FPDF subclass with branded header/footer."""

    def __init__(self, title: str, language: str):
        super().__init__()
        self._doc_title = title
        self._lang = language
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_fill_color(*_DARK_BLUE)
        self.rect(0, 0, 210, 14, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*_WHITE)
        self.set_xy(10, 3)
        self.cell(0, 8, self._doc_title[:90], align="L")
        self.set_text_color(*_TEXT)
        self.ln(14)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        label = "Página" if self._lang == "es" else "Page"
        self.cell(0, 10, f"{label} {self.page_no()}", align="C")

    # ---- Helpers -----------------------------------------------------------

    def section_title(self, text: str) -> None:
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*_MID_BLUE)
        self.set_fill_color(*_LIGHT_GRAY)
        self.multi_cell(0, 8, text, fill=True)
        self.set_text_color(*_TEXT)
        self.ln(2)

    def body_text(self, text: str) -> None:
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*_TEXT)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def bullet(self, text: str) -> None:
        self.set_font("Helvetica", "", 10)
        self.set_x(18)
        self.multi_cell(0, 6, f"\u2022  {text}")

    def citation_text(self, text: str) -> None:
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(90, 90, 90)
        self.multi_cell(0, 5, text)
        self.set_text_color(*_TEXT)

    def divider(self) -> None:
        self.set_draw_color(*_MID_BLUE)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def draw_table(self, headers: list[str], rows: list[list[str]]) -> None:
        if not headers or not rows:
            return
        col_w = (self.epw) / max(len(headers), 1)
        # Header row
        self.set_fill_color(*_MID_BLUE)
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 9)
        for h in headers:
            self.cell(col_w, 7, str(h)[:25], border=1, fill=True)
        self.ln()
        # Data rows
        self.set_text_color(*_TEXT)
        self.set_fill_color(*_LIGHT_GRAY)
        self.set_font("Helvetica", "", 8)
        for i, row in enumerate(rows):
            fill = i % 2 == 0
            for cell in row:
                self.cell(col_w, 6, str(cell)[:30], border=1, fill=fill)
            self.ln()
        self.ln(2)


# ---------------------------------------------------------------------------
# Public builder function
# ---------------------------------------------------------------------------


def build_pdf(
    topic: str,
    language: str,
    structured_data: dict,
    sources: list[dict],
    extra_instructions: str,
    output_dir: Path,
) -> Path:
    """
    Assemble and save a PDF report.

    Parameters
    ----------
    topic              : research topic string
    language           : 'es' | 'en'
    structured_data    : JSON dict from research agent
    sources            : list of source dicts with citation fields
    extra_instructions : optional user notes to include as foreword
    output_dir         : directory to save the file

    Returns
    -------
    Path to the saved .pdf file
    """
    label_summary = "Resumen Ejecutivo" if language == "es" else "Executive Summary"
    label_findings = "Hallazgos Clave" if language == "es" else "Key Findings"
    label_bib = "Bibliografía" if language == "es" else "Bibliography"
    label_foreword = "Notas Adicionales" if language == "es" else "Additional Notes"
    label_credibility = "Nota de Credibilidad" if language == "es" else "Credibility Note"

    pdf = _ResearchPDF(title=topic, language=language)
    pdf.add_page()

    # ---- Cover-style title --------------------------------------------------
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(*_DARK_BLUE)
    pdf.multi_cell(0, 10, topic, align="C")
    pdf.ln(4)
    pdf.divider()

    # ---- Optional foreword -------------------------------------------------
    if extra_instructions.strip():
        pdf.section_title(label_foreword)
        pdf.body_text(extra_instructions.strip())
        pdf.divider()

    # ---- Executive summary -------------------------------------------------
    summary = structured_data.get("executive_summary", "")
    if summary:
        pdf.section_title(label_summary)
        pdf.body_text(summary)
        pdf.divider()

    # ---- Key findings -------------------------------------------------------
    findings = structured_data.get("key_findings", [])
    if findings:
        pdf.section_title(label_findings)
        for f in findings:
            pdf.bullet(f.get("finding", ""))
            apa = f.get("citation_apa", "")
            if apa:
                pdf.citation_text(f"    {apa}")
        pdf.divider()

    # ---- Sections -----------------------------------------------------------
    for section in structured_data.get("sections", []):
        title = section.get("title", "")
        content = section.get("content", "")
        bullets = section.get("bullet_points", [])
        citations = section.get("citations", [])

        if title:
            pdf.section_title(title)
        if content:
            pdf.body_text(content)
        for bp in bullets:
            pdf.bullet(bp)
        for cit in citations:
            pdf.citation_text(cit)
        pdf.ln(2)

    # ---- Data tables -------------------------------------------------------
    for table in structured_data.get("data_tables", []):
        t_title = table.get("title", "")
        headers = table.get("headers", [])
        rows = table.get("rows", [])
        if t_title:
            pdf.section_title(t_title)
        pdf.draw_table(headers, rows)

    # ---- Credibility note --------------------------------------------------
    credibility = structured_data.get("credibility_note", "")
    if credibility:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(90, 90, 90)
        pdf.multi_cell(0, 5, f"{label_credibility}: {credibility}")
        pdf.set_text_color(*_TEXT)

    # ---- Bibliography page -------------------------------------------------
    if sources:
        pdf.add_page()
        pdf.section_title(label_bib)
        for i, src in enumerate(sources, 1):
            apa = src.get("citation_apa") or src.get("title", "Source")
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(*_MID_BLUE)
            pdf.cell(0, 5, f"[{i}]", ln=True)
            pdf.set_text_color(*_TEXT)
            pdf.citation_text(apa)
            url = src.get("url", "")
            if url:
                pdf.set_font("Helvetica", "U", 8)
                pdf.set_text_color(*_MID_BLUE)
                pdf.multi_cell(0, 5, url)
                pdf.set_text_color(*_TEXT)
            pdf.ln(1)

    # ---- Save ---------------------------------------------------------------
    filename = output_dir / f"{uuid.uuid4().hex}.pdf"
    pdf.output(str(filename))
    return filename
