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
from reportlab.pdfgen import canvas as rl_canvas
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

# Optional PDF merging library (prefer pypdf / PyPDF2 if available)
PYPDF_AVAILABLE = False
PdfReader = None
PdfWriter = None
try:
    from pypdf import PdfReader, PdfWriter  # modern package name
    PYPDF_AVAILABLE = True
except Exception:
    try:
        from PyPDF2 import PdfFileReader as PdfReader, PdfFileWriter as PdfWriter
        PYPDF_AVAILABLE = True
    except Exception:
        PYPDF_AVAILABLE = False

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

    def generate_pdf(self, title: str, content: str, author: str = "PDFree", writing_mode: str | None = None, logo_path: str | None = None, cover_path: str | None = None) -> bytes:
        """Generate the main PDF. Optional: pass `cover_path` in kwargs to prepend a hard cover PDF page.

        Note: If `pypdf` / `PyPDF2` is available it will be used to merge PDFs. Otherwise
        a fallback is used that inserts the cover image as a first Flowable (still works,
        but merging is preferable).
        """
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

        main_pdf_bytes = buffer.getvalue()

        # If a cover image path param was provided use it, else check attribute on self
        cover_path = cover_path or getattr(self, 'cover_path', None)
        if cover_path and os.path.exists(cover_path):
            try:
                cover_pdf_bytes = self._create_cover_pdf(cover_path)
                if PYPDF_AVAILABLE and PdfReader is not None and PdfWriter is not None:
                    # Merge cover + main using pypdf/PyPDF2
                    try:
                        # pypdf and PyPDF2 have different reader/writer APIs; handle both
                        reader_cover = PdfReader(BytesIO(cover_pdf_bytes))
                        reader_main = PdfReader(BytesIO(main_pdf_bytes))
                        writer = PdfWriter()
                        # modern pypdf: .pages is list-like; PyPDF2 older naming also works
                        if hasattr(reader_cover, 'pages'):
                            writer.add_page(reader_cover.pages[0])
                        else:
                            writer.addPage(reader_cover.getPage(0))

                        if hasattr(reader_main, 'pages'):
                            for p in reader_main.pages:
                                writer.add_page(p)
                        else:
                            for i in range(reader_main.getNumPages()):
                                writer.addPage(reader_main.getPage(i))

                        out = BytesIO()
                        # write method differs: modern pypdf uses .write(fileobj)
                        if hasattr(writer, 'write'):
                            writer.write(out)
                        else:
                            writer.write(out)
                        return out.getvalue()
                    except Exception:
                        # fallback to returning main if merging fails
                        return main_pdf_bytes
                else:
                    # No merging library available: fallback to embedding cover as first Flowable
                    try:
                        styles = self._build_styles(writing_mode)
                        cover_story = []
                        # Full-page image via Image flowable requires specifying width/height
                        from reportlab.platypus import Image
                        page_w, page_h = self.page_size
                        img = Image(cover_path, width=page_w, height=page_h)
                        cover_story.append(img)
                        cover_story.append(PageBreak())

                        # Build a new document that includes cover + original story
                        merged_buffer = BytesIO()
                        merged_doc = SimpleDocTemplate(
                            merged_buffer,
                            pagesize=self.page_size,
                            rightMargin=0.75*inch,
                            leftMargin=0.75*inch,
                            topMargin=1*inch,
                            bottomMargin=0.75*inch,
                            title=title,
                            author=author,
                            pdfVersion=PDF_VERSION,
                        )
                        # prepend cover_story to original story
                        merged_story = cover_story + story
                        merged_doc.build(
                            merged_story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
                        return merged_buffer.getvalue()
                    except Exception:
                        return main_pdf_bytes
            except Exception:
                return main_pdf_bytes

        return main_pdf_bytes

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

    def _create_cover_pdf(self, cover_path: str) -> bytes:
        """Create a one-page PDF containing the cover image sized to fill the page.

        Returns PDF bytes or empty bytes on failure.
        """
        try:
            buf = BytesIO()
            c = rl_canvas.Canvas(buf, pagesize=self.page_size)
            page_w, page_h = self.page_size

            img_reader = None
            try:
                img_reader = ImageReader(cover_path)
            except Exception:
                if PIL_AVAILABLE and PILImage is not None:
                    try:
                        with PILImage.open(cover_path) as im:
                            out = BytesIO()
                            im.convert('RGBA').save(out, format='PNG')
                            out.seek(0)
                            img_reader = ImageReader(out)
                    except Exception:
                        img_reader = None

            if img_reader is None:
                return b''

            try:
                iw, ih = img_reader.getSize()
                # Choose scale to cover the whole page (may crop)
                scale = max(page_w / iw, page_h / ih)
                new_w = iw * scale
                new_h = ih * scale
                x = (page_w - new_w) / 2
                y = (page_h - new_h) / 2
                c.drawImage(img_reader, x, y, width=new_w,
                            height=new_h, mask='auto')
            except Exception:
                # best-effort: try drawing without sizing
                try:
                    c.drawImage(img_reader, 0, 0, width=page_w,
                                height=page_h, mask='auto')
                except Exception:
                    pass

            c.showPage()
            c.save()
            buf.seek(0)
            return buf.getvalue()
        except Exception:
            return b''
