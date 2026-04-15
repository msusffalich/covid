"""
Infographic Generator
=====================
Uses Pillow (PIL) to render a visually structured infographic PNG from
the research data. No external fonts are required — ImageFont falls back
to PIL's built-in bitmap font gracefully.

Layout (top → bottom)
----------------------
 ┌──────────────────────────────────────────┐
 │   HEADER  (dark blue bg, white title)    │
 ├──────────────────────────────────────────┤
 │   EXECUTIVE SUMMARY  (light card)        │
 ├─────────────────┬────────────────────────┤
 │  KEY FINDINGS   │  TOP BULLETS           │
 │  (numbered)     │  from first section    │
 ├─────────────────┴────────────────────────┤
 │   SOURCES  (small, gray)                 │
 └──────────────────────────────────────────┘
"""

import textwrap
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_W, _H = 1200, 1700           # portrait A3-ish at 96 dpi
_MARGIN = 48
_DARK_BLUE = (26, 58, 110)
_MID_BLUE = (52, 119, 189)
_LIGHT_BLUE = (214, 228, 247)
_GOLD = (255, 186, 0)
_LIGHT_GRAY = (245, 246, 248)
_WHITE = (255, 255, 255)
_DARK = (33, 37, 41)
_MID_GRAY = (100, 110, 120)


# ---------------------------------------------------------------------------
# Font helpers — try TrueType; gracefully degrade to bitmap
# ---------------------------------------------------------------------------

def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    try:
        face = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(face, size)
    except (IOError, OSError):
        pass
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except (IOError, OSError):
        pass
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _draw_rounded_rect(draw: ImageDraw.ImageDraw,
                        xy: tuple, fill, radius: int = 12) -> None:
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def _multiline(draw: ImageDraw.ImageDraw, x: int, y: int,
               text: str, font, fill, max_width: int,
               line_spacing: int = 6) -> int:
    """Draw wrapped text; returns new y cursor."""
    try:
        # Pillow >= 10 supports anchor; just wrap manually
        avg_char = max(font.getlength("a"), 1) if hasattr(font, "getlength") else 8
        chars_per_line = max(int(max_width / avg_char), 20)
    except Exception:
        chars_per_line = 60

    for line in textwrap.wrap(text, width=chars_per_line) or [""]:
        draw.text((x, y), line, font=font, fill=fill)
        try:
            _, _, _, lh = font.getbbox(line)
        except Exception:
            lh = font.size if hasattr(font, "size") else 14
        y += lh + line_spacing
    return y


# ---------------------------------------------------------------------------
# Public builder function
# ---------------------------------------------------------------------------


def build_infographic(
    topic: str,
    language: str,
    structured_data: dict,
    sources: list[dict],
    extra_instructions: str,
    output_dir: Path,
) -> Path:
    """
    Render a research infographic as a PNG and save to output_dir.
    Returns path to the saved .png file.
    """
    img = Image.new("RGB", (_W, _H), _WHITE)
    draw = ImageDraw.Draw(img)

    f_title = _font(36, bold=True)
    f_h2 = _font(22, bold=True)
    f_h3 = _font(16, bold=True)
    f_body = _font(14)
    f_small = _font(11)
    f_tiny = _font(10)

    y = 0

    # ---- Header ----------------------------------------------------------------
    header_h = 120
    draw.rectangle([0, 0, _W, header_h], fill=_DARK_BLUE)
    # Gold accent bar
    draw.rectangle([_MARGIN, header_h - 6, _W - _MARGIN, header_h - 2], fill=_GOLD)

    # App label
    app_label = "Investigador Inteligente Multimodal"
    draw.text((_MARGIN, 14), app_label, font=f_small, fill=_GOLD)

    # Topic title (wrapped)
    topic_text = topic[:80]
    y = 38
    y = _multiline(draw, _MARGIN, y, topic_text, f_title, _WHITE, _W - 2 * _MARGIN, line_spacing=4)
    y = header_h + 20

    # ---- Executive summary card ------------------------------------------------
    summary = structured_data.get("executive_summary", "")
    if summary:
        label_sum = "Resumen Ejecutivo" if language == "es" else "Executive Summary"
        card_h = 160
        _draw_rounded_rect(draw, (_MARGIN, y, _W - _MARGIN, y + card_h), _LIGHT_BLUE, radius=10)
        draw.text((_MARGIN + 16, y + 12), label_sum, font=f_h2, fill=_DARK_BLUE)
        y_inner = y + 44
        _multiline(draw, _MARGIN + 16, y_inner, summary[:400], f_body, _DARK, _W - 2 * _MARGIN - 32)
        y += card_h + 20

    # ---- Two-column layout: key findings | top bullets -------------------------
    col_mid = _W // 2 - 10
    col_top = y

    # Left column: Key findings
    findings = structured_data.get("key_findings", [])
    if findings:
        label_kf = "Hallazgos Clave" if language == "es" else "Key Findings"
        draw.text((_MARGIN, y), label_kf, font=f_h2, fill=_MID_BLUE)
        y_left = y + 36
        for i, f in enumerate(findings[:6], 1):
            # Numbered circle
            cx, cy = _MARGIN + 16, y_left + 10
            draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=_MID_BLUE)
            draw.text((cx - 4, cy - 10), str(i), font=_font(14, bold=True), fill=_WHITE)
            finding_text = f.get("finding", "")[:100]
            y_left = _multiline(draw, _MARGIN + 36, y_left, finding_text, f_small, _DARK,
                                 col_mid - _MARGIN - 36, line_spacing=3)
            y_left += 10

    # Right column: Top bullets from first section
    sections = structured_data.get("sections", [])
    if sections:
        first = sections[0]
        s_label = first.get("title", "")
        bullets = first.get("bullet_points", [])
        draw.text((col_mid + 20, col_top), s_label[:50], font=f_h2, fill=_MID_BLUE)
        y_right = col_top + 36
        for bp in bullets[:6]:
            draw.text((col_mid + 20, y_right), "\u2022", font=f_h3, fill=_GOLD)
            y_right = _multiline(draw, col_mid + 36, y_right, bp[:100], f_small, _DARK,
                                  _W - col_mid - _MARGIN - 36, line_spacing=3)
            y_right += 8

    y = max(y + 20, col_top + max(
        (y_left - col_top) if findings else 0,
        (y_right - col_top) if sections else 0,
    ) + 20)

    # ---- Divider ---------------------------------------------------------------
    draw.rectangle([_MARGIN, y, _W - _MARGIN, y + 2], fill=_MID_BLUE)
    y += 16

    # ---- Extra instructions (if any) -------------------------------------------
    if extra_instructions.strip():
        label_note = "Notas" if language == "es" else "Notes"
        draw.text((_MARGIN, y), label_note, font=f_h3, fill=_MID_BLUE)
        y += 26
        y = _multiline(draw, _MARGIN, y, extra_instructions.strip()[:300], f_body, _DARK,
                       _W - 2 * _MARGIN, line_spacing=4)
        y += 12

    # ---- Sources footer --------------------------------------------------------
    if sources:
        label_src = "Fuentes" if language == "es" else "Sources"
        draw.text((_MARGIN, y), label_src, font=f_h3, fill=_MID_GRAY)
        y += 24
        for i, src in enumerate(sources[:5], 1):
            apa = src.get("citation_apa") or src.get("title", "")
            text = f"[{i}] {apa[:120]}"
            y = _multiline(draw, _MARGIN, y, text, f_tiny, _MID_GRAY, _W - 2 * _MARGIN, 2)
            y += 2

    # ---- Footer bar ------------------------------------------------------------
    if y < _H - 40:
        draw.rectangle([0, _H - 36, _W, _H], fill=_DARK_BLUE)
        gen_label = "Generado por Investigador Inteligente Multimodal" if language == "es" \
            else "Generated by Multimodal Intelligent Researcher"
        draw.text((_MARGIN, _H - 24), gen_label, font=f_tiny, fill=_GOLD)

    # ---- Save ------------------------------------------------------------------
    filename = output_dir / f"{uuid.uuid4().hex}.png"
    # Crop to content if it grew beyond canvas
    img = img.crop((0, 0, _W, min(_H, max(y + 60, 400))))
    img.save(str(filename), format="PNG", optimize=True)
    return filename
