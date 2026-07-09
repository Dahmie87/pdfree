"""
Five new book cover designs for PDFGenerator.
Each function is a self-contained `onFirstPage` callback with the same
signature as the existing `_draw_cover_page`:

    def _draw_<name>(canvas, doc_obj): ...

To use one, pass it to doc.build():

    doc.build(story, onFirstPage=self._draw_split, onLaterPages=_draw_footer)

All designs use only standard ReportLab primitives — no Pillow required.
They honour the same `display_title`, `display_subtitle`, `author`, and
`styles` variables that are already in scope inside `generate_pdf()`.

Add these methods to the PDFGenerator class and wire up the choice via a
`cover_design` parameter in `generate_pdf()`.  A routing example is
included at the bottom of this file.
"""

from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.units import inch
import math


# ---------------------------------------------------------------------------
# 1. SPLIT  —  Diagonal horizon + coastal‑dark palette
#    Cold navy top half, near‑black bottom half, gold accent rule.
#    Mood: literary thriller / narrative non‑fiction.
# ---------------------------------------------------------------------------
def _draw_split(self, canvas, doc_obj, display_title, display_subtitle,
                author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    NAVY = colors.HexColor("#1a3a5c")
    DARK = colors.HexColor("#0f1923")
    GOLD = colors.HexColor("#e8c97a")
    WHITE = colors.white
    MUTED = colors.HexColor("#8ab4d4")

    # Backgrounds
    canvas.setFillColor(NAVY)
    canvas.rect(0, H * 0.42, W, H * 0.58, fill=1, stroke=0)
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, W, H * 0.42, fill=1, stroke=0)

    # Diagonal seam (polygon: full‑width wedge)
    canvas.setFillColor(DARK)
    p = canvas.beginPath()
    p.moveTo(0, H * 0.44)
    p.lineTo(W, H * 0.38)
    p.lineTo(W, H * 0.42)
    p.lineTo(0, H * 0.42)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)

    # Gold vertical + horizontal bracket
    # tighten margins to use more page real estate
    margin = W * 0.08
    bracket_top = H * 0.74
    bracket_h = H * 0.22
    canvas.setFillColor(GOLD)
    canvas.rect(margin, bracket_top - bracket_h,
                3, bracket_h, fill=1, stroke=0)
    canvas.rect(margin, bracket_top - 3, W * 0.14, 3, fill=1, stroke=0)

    # Title block — wrap title into multiple lines and use more space
    lines = _wrap_title(display_title, max_chars=26)
    max_lines = 5
    font_size = 30
    leading = font_size + 6
    y_start = H * 0.68
    for i, line in enumerate(lines[:max_lines]):
        color = GOLD if i == min(
            len(lines[:max_lines]) - 1, max_lines - 1) else WHITE
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", font_size)
        canvas.drawString(margin + 10, y_start - i * leading, line)

    # Series / genre note
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(margin + 10, H * 0.38, "A NOVEL")

    # Author
    canvas.setFillColor(colors.HexColor("#c0d8ee"))
    canvas.setFont("Helvetica", 13)
    canvas.drawString(margin + 10, H * 0.30, author)

    # Thin rule (keep for balance). publisher line removed to avoid
    # showing stale or injected metadata like vendor/agent strings.
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.75)
    canvas.line(margin, H * 0.22, margin + W * 0.55, H * 0.22)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# 2. FRAME  —  Double‑border classic with medallion
#    Cream page, dark header panel, gold circular ornament.
#    Mood: literary fiction / historical / essay collection.
# ---------------------------------------------------------------------------
def _draw_frame(self, canvas, doc_obj, display_title, display_subtitle,
                author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    CREAM = colors.HexColor("#f5f0e8")
    DARK = colors.HexColor("#2c1a0e")
    BROWN = colors.HexColor("#3d2512")
    GOLD = colors.HexColor("#c8a96e")
    TAN = colors.HexColor("#5a3e28")

    BORDER = W * 0.05          # outer border inset
    BORDER2 = W * 0.08          # inner border inset

    # Cream background
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Outer dark border
    canvas.setStrokeColor(DARK)
    canvas.setLineWidth(2.5)
    canvas.rect(BORDER, BORDER, W - 2*BORDER, H - 2*BORDER, fill=0, stroke=1)

    # Inner thin border
    canvas.setLineWidth(0.75)
    canvas.rect(BORDER2, BORDER2, W - 2*BORDER2,
                H - 2*BORDER2, fill=0, stroke=1)

    # Dark header panel
    header_h = H * 0.38
    canvas.setFillColor(DARK)
    canvas.rect(BORDER, H - BORDER - header_h, W -
                2*BORDER, header_h, fill=1, stroke=0)
    canvas.setFillColor(BROWN)
    canvas.rect(BORDER2, H - BORDER2 - (header_h - (BORDER2 - BORDER)),
                W - 2*BORDER2, header_h - (BORDER2 - BORDER), fill=1, stroke=0)

    # Medallion (two concentric circles)
    cx = W / 2
    cy = H - BORDER2 - (header_h - (BORDER2 - BORDER)) / 2
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(1.2)
    canvas.circle(cx, cy, W * 0.155, fill=0, stroke=1)
    canvas.setLineWidth(0.5)
    canvas.circle(cx, cy, W * 0.13, fill=0, stroke=1)

    # Ornament text inside circle
    canvas.setFillColor(GOLD)
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(cx, cy + 4, "✦  ✦  ✦")
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(cx, cy - 10, "EST. MMXXIV")

    # Title — centred in lower 3/5
    title_cy = H * 0.44
    lines = _wrap_title(display_title, max_chars=18)
    for i, line in enumerate(lines[:3]):
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica-Bold", 22)
        canvas.drawCentredString(W / 2, title_cy - i * 30, line)

    # Double rule under title
    rule_y = title_cy - len(lines[:3]) * 30 - 10
    canvas.setStrokeColor(DARK)
    canvas.setLineWidth(0.75)
    canvas.line(W * 0.22, rule_y, W * 0.78, rule_y)
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.5)
    canvas.line(W * 0.28, rule_y - 5, W * 0.72, rule_y - 5)

    # Author
    canvas.setFillColor(TAN)
    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(W / 2, rule_y - 25, author)

    # Edition note
    canvas.setFillColor(colors.HexColor("#7a6248"))
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, H * 0.12, "SECOND EDITION")

    # Bottom rule
    canvas.setStrokeColor(DARK)
    canvas.setLineWidth(0.5)
    canvas.line(W * 0.22, H * 0.09, W * 0.78, H * 0.09)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# 3. STACK  —  Stacked bold type on deep forest green + abstract sigil
#    Dark botanical palette, concentric‑circle motif.
#    Mood: short stories / poetry / literary debut.
# ---------------------------------------------------------------------------
def _draw_stack(self, canvas, doc_obj, display_title, display_subtitle,
                author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    FOREST = colors.HexColor("#1c2b1e")
    DARK = colors.HexColor("#0f1a10")
    GREEN = colors.HexColor("#4a9e5c")
    LIGHT = colors.HexColor("#e8f5e4")
    MUTED = colors.HexColor("#7ab888")

    # Background
    canvas.setFillColor(FOREST)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Dark footer band
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, W, H * 0.22, fill=1, stroke=0)

    # Top accent bar
    canvas.setFillColor(GREEN)
    canvas.rect(0, H - 8, W, 8, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#3a7a48"))
    canvas.rect(0, H - 11, W, 3, fill=1, stroke=0)

    # Thin rule below title area
    margin = W * 0.085
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(1.5)
    canvas.setDash(1, 0)
    canvas.line(margin, H * 0.56, W - margin, H * 0.56)
    canvas.setLineWidth(0.5)
    canvas.line(margin, H * 0.555, W - margin, H * 0.555)

    # Sigil: concentric circles + crosshair
    cx = W / 2
    cy = H * 0.37
    for r, op in [(W*0.27, 0.40), (W*0.19, 0.30), (W*0.10, 0.20)]:
        canvas.setStrokeColor(GREEN)
        canvas.setLineWidth(0.75)
        canvas.setFillColor(colors.Color(0.29, 0.62, 0.36, alpha=0))
        canvas.circle(cx, cy, r, fill=0, stroke=1)
    canvas.setFillColor(GREEN)
    canvas.circle(cx, cy, 6, fill=1, stroke=0)
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(0.5)
    canvas.line(cx, cy + W*0.27 + 2, cx, cy - W*0.27 - 2)
    canvas.line(cx - W*0.27 - 2, cy, cx + W*0.27 + 2, cy)

    # Title stacked
    words = display_title.split()
    y_start = H * 0.85
    for i, word in enumerate(words[:4]):
        color = GREEN if i == len(words[:4]) - 1 else LIGHT
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", 32)
        canvas.drawString(margin, y_start - i * 40, word)

    # Subtitle / tagline
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 11)
    canvas.drawString(margin, H * 0.57 + 8, display_subtitle[:42])

    # Author
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 12)
    canvas.drawString(margin, H * 0.17, author)

    # Publisher
    canvas.setFillColor(GREEN)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(margin, H * 0.07, "THORNFIELD BOOKS")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# 4. BLEED  —  Bold vertical colour‑split + radial orb
#    Deep aubergine / dark violet two‑panel composition.
#    Mood: speculative fiction / mystery / genre fiction.
# ---------------------------------------------------------------------------
def _draw_bleed(self, canvas, doc_obj, display_title, display_subtitle,
                author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    PANEL_L = colors.HexColor("#3d1254")   # left panel
    PANEL_R = colors.HexColor("#1e0828")   # right panel
    SEAM = colors.HexColor("#8b3ab8")   # vertical seam accent
    LILAC = colors.HexColor("#c17ae0")
    PARCHMT = colors.HexColor("#f0d6ff")

    SPLIT = W * 0.57                     # vertical split x position

    # Left panel
    canvas.setFillColor(PANEL_L)
    canvas.rect(0, 0, SPLIT, H, fill=1, stroke=0)

    # Right panel
    canvas.setFillColor(PANEL_R)
    canvas.rect(SPLIT, 0, W - SPLIT, H, fill=1, stroke=0)

    # Seam bar
    canvas.setFillColor(SEAM)
    canvas.rect(SPLIT - 2, 0, 4, H, fill=1, stroke=0)

    # Orb (concentric on left panel)
    cx = SPLIT * 0.5
    cy = H * 0.50
    canvas.setFillColor(colors.HexColor("#5a1878"))
    canvas.circle(cx, cy, W * 0.19, fill=1, stroke=0)
    canvas.setStrokeColor(SEAM)
    canvas.setLineWidth(0.75)
    canvas.circle(cx, cy, W * 0.29, fill=0, stroke=1)
    canvas.setLineWidth(0.5)
    canvas.circle(cx, cy, W * 0.38, fill=0, stroke=1)

    # Volume badge (top left)
    margin = W * 0.085
    canvas.setFillColor(LILAC)
    canvas.setFont("Helvetica", 10)
    canvas.drawString(margin, H - W * 0.10, "VOLUME II")

    # Title (bottom‑left, bleeds into orb area)
    lines = _wrap_title(display_title, max_chars=12)
    y = H * 0.33
    for i, line in enumerate(lines[:4]):
        color = LILAC if i == len(lines[:4]) - 1 else PARCHMT
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", 28)
        canvas.drawString(margin, y - i * 34, line)

    # Author on right panel (rotated vertically)
    canvas.setFillColor(SEAM)
    canvas.setFont("Helvetica", 9)
    author_parts = author.split()
    right_cx = SPLIT + (W - SPLIT) / 2
    for j, part in enumerate(author_parts[:2]):
        canvas.drawCentredString(right_cx, H * 0.78 - j * 16,
                                 " ".join(part.upper()))

    # Publisher (right panel, bottom)
    canvas.setFillColor(SEAM)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(right_cx, H * 0.09, "OBSIDIAN PRESS")
    canvas.setStrokeColor(SEAM)
    canvas.setLineWidth(0.5)
    canvas.line(SPLIT + 8, H * 0.11, W - 12, H * 0.11)

    canvas.restoreState()


# ---------------------------------------------------------------------------
# 5. ARCH  —  Arched window frame, warm terracotta footer
#    Cream background with an arched panel, dark red base band.
#    Mood: historical fiction / memoir / illustrated gift book.
# ---------------------------------------------------------------------------
def _draw_arch(self, canvas, doc_obj, display_title, display_subtitle,
               author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    CREAM = colors.HexColor("#f7f3ec")
    TERRA = colors.HexColor("#c8402a")
    ARCH_BG = colors.HexColor("#e8dfc8")
    STROKE = colors.HexColor("#8a6a3a")
    DARK = colors.HexColor("#3d2010")
    MID = colors.HexColor("#6a4e2a")
    LIGHT = colors.HexColor("#f7e8e0")

    # Page background
    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Terracotta footer band
    footer_h = H * 0.26
    canvas.setFillColor(TERRA)
    canvas.rect(0, 0, W, footer_h, fill=1, stroke=0)

    # ---- Arched frame ----
    inset = W * 0.11
    ax = inset                        # arch left
    aw = W - 2 * inset               # arch width
    ab = footer_h + H * 0.03         # arch base y
    at = H - H * 0.08               # arch top y (flat part)
    arc_r = aw / 2                      # semicircle radius
    arc_cx = ax + arc_r                  # arc centre x
    arc_cy = at                           # arc centre y

    # Fill arch body (rectangle + semicircle top)
    canvas.setFillColor(ARCH_BG)
    canvas.rect(ax, ab, aw, at - ab, fill=1, stroke=0)

    # Draw semicircle top
    p = canvas.beginPath()
    p.arc(ax, arc_cy - arc_r, ax + aw, arc_cy + arc_r, 0, 180)
    p.lineTo(ax, arc_cy)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)

    # Arch outline stroke
    canvas.setStrokeColor(STROKE)
    canvas.setLineWidth(1.5)
    p2 = canvas.beginPath()
    p2.moveTo(ax, ab)
    p2.lineTo(ax, arc_cy)
    p2.arcTo(ax, arc_cy - arc_r, ax + aw, arc_cy + arc_r, 180, -180)
    p2.lineTo(ax + aw, ab)
    canvas.drawPath(p2, fill=0, stroke=1)

    # Inner arch inset line (thinner)
    inset2 = inset + W * 0.06
    ax2, aw2 = inset2, W - 2 * inset2
    arc_r2 = aw2 / 2
    canvas.setLineWidth(0.75)
    canvas.setStrokeColor(colors.HexColor("#8a6a3a"))
    p3 = canvas.beginPath()
    p3.moveTo(ax2, ab + H*0.02)
    p3.lineTo(ax2, arc_cy)
    p3.arcTo(ax2, arc_cy - arc_r2, ax2 + aw2, arc_cy + arc_r2, 180, -180)
    p3.lineTo(ax2 + aw2, ab + H*0.02)
    canvas.drawPath(p3, fill=0, stroke=1)

    # "THE MEMOIRS OF" label near arch top
    canvas.setFillColor(STROKE)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, arc_cy + arc_r * 0.52, "THE MEMOIRS OF")

    # Title centred in arch body
    title_cy = ab + (at - ab) * 0.68
    lines = _wrap_title(display_title, max_chars=16)
    for i, line in enumerate(lines[:3]):
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawCentredString(W / 2, title_cy - i * 28, line)

    # Year / date subtitle
    canvas.setFillColor(MID)
    canvas.setFont("Helvetica", 9)
    date_y = title_cy - len(lines[:3]) * 28 - 6
    canvas.drawCentredString(W / 2, date_y, "1842 – 1901")

    # Rule above date
    canvas.setStrokeColor(STROKE)
    canvas.setLineWidth(0.75)
    canvas.line(W * 0.30, date_y + 14, W * 0.70, date_y + 14)

    # Author in footer
    canvas.setFillColor(LIGHT)
    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(W / 2, footer_h * 0.56, f"Edited by {author}")

    # Publisher at bottom
    canvas.setFillColor(LIGHT)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(W / 2, footer_h * 0.22, "IRONWOOD EDITIONS")

    canvas.restoreState()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _wrap_title(title: str, max_chars: int = 16) -> list[str]:
    """Split a title into lines of at most max_chars characters."""
    words = title.split()
    lines, current = [], ""
    for w in words:
        if current and len(current) + 1 + len(w) > max_chars:
            lines.append(current)
            current = w
        else:
            current = (current + " " + w).strip() if current else w
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Routing — wire this into PDFGenerator.generate_pdf()
# ---------------------------------------------------------------------------
COVER_DESIGNS = {
    "split":       _draw_split,
    "frame":       _draw_frame,
    "stack":       _draw_stack,
    "bleed":       _draw_bleed,
    "arch":        _draw_arch,
    # keep the original design under its own key:
    # "default":   _draw_cover_page,
}


def pick_cover(design_name: str):
    """
    Returns the cover-drawing callable for the given name.
    Falls back to 'split' if the name is unknown.

    Usage inside generate_pdf():

        from cover_designs import pick_cover
        _cover = pick_cover(cover_design)
        doc.build(
            story,
            onFirstPage=lambda c, d: _cover(self, c, d,
                                            display_title, display_subtitle,
                                            author, styles),
            onLaterPages=_draw_footer,
        )
    """
    return COVER_DESIGNS.get(design_name, _draw_split)
