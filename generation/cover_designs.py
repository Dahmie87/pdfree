"""
Five safe cover designs for PDFGenerator.
Each function is an `onFirstPage` callback with signature:
    def _draw_<name>(self, canvas, doc_obj, display_title, display_subtitle, author, styles)

Design goals (per user request):
- Use only safe, muted palettes (deep blue, blue, black, deep green).
- Ensure headings/text colors agree with cover accent color.
- Avoid bright/red colors and remove hardcoded publisher/vendor strings.
- Keep designs simple and typographic-focused.
"""

from reportlab.lib import colors
from reportlab.lib.units import inch


# Utility: wrap title into lines with max_chars
def _wrap_title(title: str, max_chars: int = 16) -> list[str]:
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


# 1. SPLIT — diagonal split, navy background, blue accent
def _draw_split(self, canvas, doc_obj, display_title, display_subtitle, author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    NAVY = colors.HexColor("#071a2b")
    MID = colors.HexColor("#0b3758")
    ACCENT = colors.HexColor("#6ea8dd")
    TEXT = colors.white
    MUTED = colors.HexColor("#9fbfe0")

    # Background panels
    canvas.setFillColor(NAVY)
    canvas.rect(0, H * 0.44, W, H * 0.56, fill=1, stroke=0)
    canvas.setFillColor(MID)
    canvas.rect(0, 0, W, H * 0.44, fill=1, stroke=0)

    # Diagonal seam
    p = canvas.beginPath()
    p.moveTo(0, H * 0.46)
    p.lineTo(W, H * 0.40)
    p.lineTo(W, H * 0.44)
    p.lineTo(0, H * 0.44)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)

    # Accent bracket
    margin = W * 0.08
    canvas.setFillColor(ACCENT)
    canvas.rect(margin, H * 0.74 - H * 0.22, 3, H * 0.22, fill=1, stroke=0)
    canvas.rect(margin, H * 0.74 - 3, W * 0.14, 3, fill=1, stroke=0)

    # Title
    lines = _wrap_title(display_title or "Untitled", max_chars=26)
    font_size = 30
    leading = font_size + 6
    y = H * 0.68
    for i, line in enumerate(lines[:5]):
        color = ACCENT if i == len(lines[:5]) - 1 else TEXT
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", font_size)
        canvas.drawString(margin + 8, y - i * leading, line)

    # Subtitle (muted)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 10)
    canvas.drawString(margin + 8, H * 0.38,
                      (display_subtitle or "").strip()[:120])

    # Author
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 12)
    canvas.drawString(margin + 8, H * 0.30, author or "")

    # Thin accent rule for balance
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(0.75)
    canvas.line(margin, H * 0.22, margin + W * 0.55, H * 0.22)

    canvas.restoreState()


# 2. FRAME — classic cream page with deep-blue header and blue accent
def _draw_frame(self, canvas, doc_obj, display_title, display_subtitle, author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    CREAM = colors.HexColor("#f6f3ee")
    HEADER = colors.HexColor("#071227")
    PANEL = colors.HexColor("#0b2a40")
    ACCENT = colors.HexColor("#5f99d6")
    TEXT = colors.HexColor("#111827")
    MUTED = colors.HexColor("#6b7280")

    border = W * 0.06
    inner = W * 0.09

    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Header panel
    header_h = H * 0.36
    canvas.setFillColor(HEADER)
    canvas.rect(border, H - border - header_h, W -
                2 * border, header_h, fill=1, stroke=0)
    canvas.setFillColor(PANEL)
    canvas.rect(inner, H - inner - (header_h - (inner - border)),
                W - 2 * inner, header_h - (inner - border), fill=1, stroke=0)

    # Medallion
    cx = W / 2
    cy = H - inner - (header_h - (inner - border)) / 2
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.0)
    canvas.circle(cx, cy, W * 0.14, fill=0, stroke=1)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(ACCENT)
    canvas.drawCentredString(cx, cy - 4, "✦ ✦ ✦")

    # Title
    title_y = H * 0.46
    lines = _wrap_title(display_title or "Untitled", max_chars=20)
    for i, line in enumerate(lines[:3]):
        canvas.setFillColor(TEXT)
        canvas.setFont("Helvetica-Bold", 22)
        canvas.drawCentredString(W / 2, title_y - i * 30, line)

    # Double rule
    rule_y = title_y - len(lines[:3]) * 30 - 8
    canvas.setStrokeColor(TEXT)
    canvas.setLineWidth(0.75)
    canvas.line(W * 0.22, rule_y, W * 0.78, rule_y)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(0.5)
    canvas.line(W * 0.28, rule_y - 6, W * 0.72, rule_y - 6)

    # Author
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(W / 2, rule_y - 26, author or "")

    canvas.restoreState()


# 3. STACK — deep green, stacked title, simple sigil
def _draw_stack(self, canvas, doc_obj, display_title, display_subtitle, author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    FOREST = colors.HexColor("#0e2a1a")
    FOOTER = colors.HexColor("#07120b")
    ACCENT = colors.HexColor("#2f7b4d")
    LIGHT = colors.HexColor("#dbeeda")
    MUTED = colors.HexColor("#8aa98a")

    canvas.setFillColor(FOREST)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    # Footer band
    canvas.setFillColor(FOOTER)
    canvas.rect(0, 0, W, H * 0.20, fill=1, stroke=0)

    # Sigil
    cx = W / 2
    cy = H * 0.36
    for r in (W * 0.26, W * 0.18, W * 0.09):
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.75)
        canvas.circle(cx, cy, r, fill=0, stroke=1)

    # Stacked title
    words = (display_title or "Untitled").split()
    y = H * 0.84
    for i, w in enumerate(words[:5]):
        color = ACCENT if i == len(words[:5]) - 1 else LIGHT
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", 32)
        canvas.drawString(W * 0.09, y - i * 42, w)

    # Subtitle
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 10)
    canvas.drawString(W * 0.09, H * 0.58,
                      (display_subtitle or "").strip()[:120])

    # Author
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 12)
    canvas.drawString(W * 0.09, H * 0.16, author or "")

    canvas.restoreState()


# 4. BLEED — vertical split, deep blues, calm blue accent
def _draw_bleed(self, canvas, doc_obj, display_title, display_subtitle, author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    LEFT = colors.HexColor("#0b324a")
    RIGHT = colors.HexColor("#071427")
    ACCENT = colors.HexColor("#5aa0dd")
    PALE = colors.HexColor("#dceffb")

    split_x = W * 0.56

    canvas.setFillColor(LEFT)
    canvas.rect(0, 0, split_x, H, fill=1, stroke=0)
    canvas.setFillColor(RIGHT)
    canvas.rect(split_x, 0, W - split_x, H, fill=1, stroke=0)

    # Thin seam
    canvas.setFillColor(ACCENT)
    canvas.rect(split_x - 2, 0, 4, H, fill=1, stroke=0)

    # Orb on left
    cx = split_x * 0.5
    cy = H * 0.52
    canvas.setFillColor(LEFT)
    canvas.circle(cx, cy, W * 0.20, fill=1, stroke=0)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(0.75)
    canvas.circle(cx, cy, W * 0.28, fill=0, stroke=1)

    # Volume badge
    canvas.setFillColor(PALE)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(W * 0.08, H - W * 0.10, "VOLUME II")

    # Title — left
    lines = _wrap_title(display_title or "Untitled", max_chars=14)
    y = H * 0.34
    for i, line in enumerate(lines[:4]):
        color = PALE if i < (len(lines[:4]) - 1) else ACCENT
        canvas.setFillColor(color)
        canvas.setFont("Helvetica-Bold", 28)
        canvas.drawString(W * 0.08, y - i * 34, line)

    # Author on right panel
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(split_x + (W - split_x) / 2,
                             H * 0.78, (author or "").upper())

    canvas.restoreState()


# 5. ARCH — cream background with deep-blue arch and matching headings
def _draw_arch(self, canvas, doc_obj, display_title, display_subtitle, author, styles):
    canvas.saveState()
    W, H = doc_obj.pagesize

    CREAM = colors.HexColor("#f7f3ec")
    FOOT = colors.HexColor("#071a2b")
    ARCH_BG = colors.HexColor("#e9e6da")
    STROKE = colors.HexColor("#0b2a40")
    DARK = colors.HexColor("#071227")
    MID = colors.HexColor("#4e6b88")
    LIGHT = colors.HexColor("#f7e8e0")

    canvas.setFillColor(CREAM)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)

    footer_h = H * 0.24
    canvas.setFillColor(FOOT)
    canvas.rect(0, 0, W, footer_h, fill=1, stroke=0)

    inset = W * 0.10
    ax = inset
    aw = W - 2 * inset
    ab = footer_h + H * 0.03
    at = H - H * 0.08
    arc_r = aw / 2
    arc_cx = ax + arc_r
    arc_cy = at

    # Arch body
    canvas.setFillColor(ARCH_BG)
    canvas.rect(ax, ab, aw, at - ab, fill=1, stroke=0)
    p = canvas.beginPath()
    p.arc(ax, arc_cy - arc_r, ax + aw, arc_cy + arc_r, 0, 180)
    p.lineTo(ax, arc_cy)
    p.close()
    canvas.drawPath(p, fill=1, stroke=0)

    # Arch stroke
    canvas.setStrokeColor(STROKE)
    canvas.setLineWidth(1.2)
    p2 = canvas.beginPath()
    p2.moveTo(ax, ab)
    p2.lineTo(ax, arc_cy)
    p2.arcTo(ax, arc_cy - arc_r, ax + aw, arc_cy + arc_r, 180, -180)
    p2.lineTo(ax + aw, ab)
    canvas.drawPath(p2, fill=0, stroke=1)

    # Title inside arch
    title_cy = ab + (at - ab) * 0.66
    lines = _wrap_title(display_title or "Untitled", max_chars=18)
    for i, line in enumerate(lines[:3]):
        canvas.setFillColor(DARK)
        canvas.setFont("Helvetica-Bold", 20)
        canvas.drawCentredString(W / 2, title_cy - i * 28, line)

    # Small date/subtitle
    canvas.setFillColor(MID)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(
        W / 2, title_cy - len(lines[:3]) * 28 - 6, (display_subtitle or "")[:80])

    # Author in footer
    canvas.setFillColor(LIGHT)
    canvas.setFont("Helvetica", 12)
    canvas.drawCentredString(W / 2, footer_h * 0.56, author or "")

    canvas.restoreState()


# Routing
COVER_DESIGNS = {
    "split": _draw_split,
    "frame": _draw_frame,
    "stack": _draw_stack,
    "bleed": _draw_bleed,
    "arch": _draw_arch,
}


def pick_cover(design_name: str):
    return COVER_DESIGNS.get(design_name, _draw_split)
