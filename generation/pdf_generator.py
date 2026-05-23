"""PDF generation module using ReportLab."""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
import random
from datetime import datetime
import re
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

PDF_VERSION = (1, 3)


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

    def generate_pdf(self, title: str, content: str, author: str = "PDFree", writing_mode: str | None = None) -> bytes:
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
        story.append(Paragraph(f"By {author}", styles['CustomSubtitle']))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y %H:%M:%S')}",
            styles['CustomSubtitle']
        ))
        story.append(PageBreak())

        story.extend(self._parse_content(content, styles))

        doc.build(story)
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
