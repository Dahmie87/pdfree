"""PDF generation module using ReportLab."""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import random
from datetime import datetime
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import tempfile
PILImage = None
PIL_AVAILABLE = False
try:
    import importlib
    _pil = importlib.import_module('PIL')
    PILImage = getattr(_pil, 'Image', None)
    PIL_AVAILABLE = PILImage is not None
except Exception:
    PILImage = None
    PIL_AVAILABLE = False

PDF_VERSION = (1, 4)


class PDFGenerator:
    """Generate PDF books from text content."""

    def __init__(self, page_size=A4):
        self.page_size = page_size

    def _build_styles(self, writing_mode: str | None = None):
        """Build paragraph styles for the requested writing mode."""

        repo_root = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..'))
        fonts_dir = os.path.join(repo_root, 'fonts')

        mode = (writing_mode or 'casual').strip().lower()

        style_profiles = {
            'casual': {
                'body_font': 'Helvetica',
                'bold_font': 'Helvetica-Bold',
                'title_size': 40,
                'subtitle_size': 15,
                'chapter_size': 22,
                'section_size': 17,
                'body_size': 13,
                'body_leading': 20,
                'accent_colors': ['#1f4788', '#163a63', '#223f5a', '#1f4f3a'],
            },
            'professional': {
                'body_font': 'Times-Roman',
                'bold_font': 'Times-Bold',
                'title_size': 38,
                'subtitle_size': 14,
                'chapter_size': 21,
                'section_size': 16,
                'body_size': 12.5,
                'body_leading': 18,
                'accent_colors': ['#17324d', '#274060', '#334e68'],
            },
            'creative': {
                'body_font': 'Helvetica',
                'bold_font': 'Helvetica-Bold',
                'title_size': 44,
                'subtitle_size': 16,
                'chapter_size': 23,
                'section_size': 18,
                'body_size': 13.5,
                'body_leading': 21,
                'accent_colors': ['#7a2e8e', '#b23a48', '#1f6f78'],
            },
            'technical': {
                'body_font': 'Courier',
                'bold_font': 'Courier-Bold',
                'title_size': 36,
                'subtitle_size': 13,
                'chapter_size': 20,
                'section_size': 16,
                'body_size': 11.5,
                'body_leading': 16,
                'accent_colors': ['#0f4c5c', '#1d3557', '#264653'],
            },
        }

        profile = style_profiles.get(mode, style_profiles['casual'])

        body_font = profile['body_font']
        bold_font = profile['bold_font']

        try:
            roboto_regular = os.path.join(fonts_dir, 'Roboto-Regular.ttf')
            roboto_bold = os.path.join(fonts_dir, 'Roboto-Bold.ttf')

            if os.path.exists(roboto_regular) and os.path.exists(roboto_bold):
                pdfmetrics.registerFont(TTFont('Roboto', roboto_regular))
                pdfmetrics.registerFont(TTFont('Roboto-Bold', roboto_bold))
                body_font = 'Roboto'
                bold_font = 'Roboto-Bold'
        except Exception:
            pass

        title_color = colors.HexColor(random.choice(profile['accent_colors']))

        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=profile['title_size'],
            fontName=bold_font,
            textColor=title_color,
            spaceAfter=30,
            alignment=1
        ))

        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=profile['subtitle_size'],
            fontName=body_font,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=1
        ))

        styles.add(ParagraphStyle(
            name='VersionNote',
            parent=styles['Normal'],
            fontSize=9,
            fontName=body_font,
            textColor=colors.HexColor('#666666'),
            spaceAfter=12,
            alignment=1,
            italic=True,
        ))

        styles.add(ParagraphStyle(
            name='ChapterHeading',
            parent=styles['Heading1'],
            fontSize=profile['chapter_size'],
            fontName=bold_font,
            textColor=title_color,
            spaceAfter=12,
            spaceBefore=12,
        ))

        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=profile['section_size'],
            fontName=bold_font,
            textColor=title_color,
            spaceAfter=8,
            spaceBefore=10,
        ))

        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=profile['body_size'],
            fontName=body_font,
            leading=profile['body_leading'],
            spaceAfter=10,
            alignment=4
        ))

        return styles

    def generate_pdf(self, title: str, content: str, author: str = "PDFree", writing_mode: str | None = None, logo_path: str | None = None) -> bytes:
        buffer = BytesIO()
        styles = self._build_styles(writing_mode)

        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch,
            title=title,
            author=author,
            pdfVersion=PDF_VERSION,
        )

        story = []

        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(title, styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))

        # Version / changelog note for this generated file
        story.append(PageBreak())

        story.extend(self._parse_content(content, styles))

        # Resolve logo: if no logo_path provided, check default assets/logo.webp
        if not logo_path:
            repo_root = os.path.abspath(os.path.join(
                os.path.dirname(__file__), '..', '..'))
            # common location: pdf_backend/assets/logo.webp
            default_logo = os.path.join(
                repo_root, 'pdf_backend', 'assets', 'logo.webp')
            if os.path.exists(default_logo):
                logo_path = default_logo

        # Try to prepare an ImageReader for the logo (with Pillow fallback for WebP)
        _resolved_logo = None
        if logo_path and os.path.exists(logo_path):
            try:
                _resolved_logo = ImageReader(logo_path)
            except Exception:
                if PIL_AVAILABLE and PILImage is not None:
                    try:
                        with PILImage.open(logo_path) as im:
                            out = BytesIO()
                            im.convert('RGBA').save(out, format='PNG')
                            out.seek(0)
                            _resolved_logo = ImageReader(out)
                    except Exception:
                        _resolved_logo = None

        # Footer drawing: place author and generation timestamp at bottom-right.
        def _draw_footer(canvas, doc_obj):
            try:
                canvas.saveState()
                page_width, page_height = doc_obj.pagesize
                x = page_width - doc_obj.rightMargin
                y = doc_obj.bottomMargin * 0.25

                gen_text = f"pdffreev1.4 — Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                # If a resolved logo is available, draw it to the left of the text.
                if _resolved_logo is not None:
                    try:
                        img_h = 0.35 * inch
                        img_w = img_h
                        text_width = canvas.stringWidth(
                            gen_text, 'Helvetica', 8)
                        img_x = x - img_w - 6 - text_width
                        img_y = y - (img_h * 0.2)
                        canvas.drawImage(
                            _resolved_logo, img_x, img_y, width=img_w, height=img_h, mask='auto')
                        text_x = img_x - 6
                    except Exception:
                        text_x = x
                else:
                    text_x = x

                # Draw right-aligned text
                canvas.setFont('Helvetica', 8)
                canvas.setFillColor(colors.HexColor('#333333'))
                canvas.drawRightString(text_x, y, gen_text)
            finally:
                canvas.restoreState()

        doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
        return buffer.getvalue()

    def _parse_content(self, content: str, styles):
        story = []
        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            if line.upper() == '[PAGE_BREAK]':
                story.append(PageBreak())
                i += 1
                continue

            if line.upper().startswith('CHAPTER'):
                story.append(Paragraph(line, styles['ChapterHeading']))
                story.append(Spacer(1, 0.2*inch))
                i += 1
                continue

            if self._is_section_header(line):
                story.append(Paragraph(line, styles['SectionHeading']))
                story.append(Spacer(1, 0.1*inch))
                i += 1
                continue

            paragraph = []
            while i < len(lines) and lines[i].strip():
                if lines[i].strip().upper().startswith('CHAPTER'):
                    break
                paragraph.append(lines[i].strip())
                i += 1

            if paragraph:
                story.append(
                    Paragraph(" ".join(paragraph), styles['CustomBody']))
                story.append(Spacer(1, 0.08*inch))

        return story

    def _is_section_header(self, line: str) -> bool:
        line = line.strip()
        if len(line) > 80:
            return False
        if line.endswith(('.', '!', '?')):
            return False

        words = line.split()
        if not (1 <= len(words) <= 6):
            return False

        score = sum(1 for w in words if w[:1].isupper())
        return score >= len(words) * 0.8
