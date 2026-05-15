"""PDF generation module using ReportLab."""

from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import re


class PDFGenerator:
    """Generate PDF books from text content."""

    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for better formatting."""
        # Title style (cover page)
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=32,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            spaceBefore=30,
            alignment=1  # Center
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            fontName='Helvetica',
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=1
        ))

        # Chapter heading style
        self.styles.add(ParagraphStyle(
            name='ChapterHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=12,
            spaceBefore=12,
            alignment=0,  # Left
            borderPadding=10,
            borderColor=colors.HexColor('#1f4788'),
            borderWidth=2,
            borderRadius=5
        ))

        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2d5aa0'),
            spaceAfter=8,
            spaceBefore=10,
            alignment=0
        ))

        # Subsection heading style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#3d6ab0'),
            spaceAfter=6,
            spaceBefore=8,
            alignment=0
        ))

        # Body style with better formatting
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            fontName='Helvetica',
            leading=16,
            spaceAfter=10,
            alignment=4  # Justify
        ))

        # Quote style
        self.styles.add(ParagraphStyle(
            name='Quote',
            parent=self.styles['BodyText'],
            fontSize=10,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#555555'),
            leading=14,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10,
            borderLeft=3,
            borderColor=colors.HexColor('#1f4788')
        ))

    def generate_pdf(self, title: str, content: str, author: str = "AI Generated") -> bytes:
        """
        Generate PDF from content with proper chapter formatting.

        Args:
            title: Book title
            content: Book content with chapter headers (====CHAPTER X: TITLE====)
            author: Author name

        Returns:
            PDF as bytes
        """
        pdf_buffer = BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=self.page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=1*inch,
            bottomMargin=0.75*inch,
            title=title,
            author=author
        )

        # Build story (content elements)
        story = []

        # Add title page
        story.append(Spacer(1, 1*inch))
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"By {author}", self.styles['CustomSubtitle']))
        story.append(Paragraph(
            f"Generated with PDFree on {datetime.now().strftime('%B %d, %Y')}",
            self.styles['CustomSubtitle']
        ))
        story.append(Spacer(1, 1*inch))
        story.append(PageBreak())

        # Parse and add content
        story.extend(self._parse_content(content))

        # Build PDF
        doc.build(story)
        return pdf_buffer.getvalue()

    def _parse_content(self, content: str):
        """Parse content and create story elements with proper formatting."""
        story = []
        lines = content.split('\n')
        i = 0
        in_toc = False
        prev_was_sec_id = False

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check for TABLE OF CONTENTS
            if "TABLE OF CONTENTS" in line.upper():
                in_toc = True
                story.append(PageBreak())
                story.append(Paragraph("TABLE OF CONTENTS",
                             self.styles['ChapterHeading']))
                story.append(Spacer(1, 0.2*inch))
                i += 1
                continue

            # Handle Markdown headings (#, ##, ###) and split inline content
            if line.startswith('#'):
                m = re.match(r'^(#+)\s*(.*)$', line)
                if m:
                    level = len(m.group(1))
                    rest = m.group(2).strip()
                    # Try to split header from inline content at first sentence-ending punctuation
                    parts = re.split(r'([.?!:])\s+', rest, maxsplit=1)
                    if len(parts) >= 3:
                        header_text = (parts[0] + parts[1]).strip()
                        remaining = parts[2].strip()
                    else:
                        header_text = rest
                        remaining = ''

                    if level == 1:
                        story.append(PageBreak())
                        story.append(Paragraph(header_text, self.styles['ChapterHeading']))
                        story.append(Spacer(1, 0.2*inch))
                    elif level == 2:
                        story.append(Spacer(1, 0.15*inch))
                        story.append(Paragraph(header_text, self.styles['SectionHeading']))
                        story.append(Spacer(1, 0.1*inch))
                    else:
                        story.append(Spacer(1, 0.12*inch))
                        story.append(Paragraph(header_text, self.styles['SubsectionHeading']))
                        story.append(Spacer(1, 0.08*inch))

                    if remaining:
                        story.append(Paragraph(remaining, self.styles['CustomBody']))
                        story.append(Spacer(1, 0.08*inch))

                    i += 1
                    continue

            # Parse TOC entries (Chapter X: Title or • Section)
            if in_toc:
                if line.startswith("="):
                    i += 1
                    continue
                if line.startswith("Chapter"):
                    story.append(
                        Paragraph(line, self.styles['SectionHeading']))
                    story.append(Spacer(1, 0.05*inch))
                    i += 1
                    continue
                if line.startswith("•"):
                    story.append(Paragraph(line, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.03*inch))
                    i += 1
                    continue
                # End of TOC (empty line after chapters)
                if not line and i > 0:
                    in_toc = False

            # Check for chapter ID marker [CH#]
            if line.startswith('[CH') and ']' in line:
                story.append(PageBreak())
                prev_was_sec_id = False
                i += 1
                continue

            # Check for section ID marker [SEC#.#]
            if line.startswith('[SEC') and ']' in line:
                prev_was_sec_id = True
                i += 1
                continue

            # Check for chapter headers (lines containing 'CHAPTER') or
            # the common pattern where a line of === separators surrounds the CHAPTER line.
            if line.startswith('='):
                # look ahead for a CHAPTER line after the separator
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and 'CHAPTER' in lines[j].upper():
                    chapter_title = lines[j].strip()
                    story.append(PageBreak())
                    story.append(Paragraph(chapter_title, self.styles['ChapterHeading']))
                    story.append(Spacer(1, 0.2*inch))
                    prev_was_sec_id = False
                    i = j + 1
                    continue

            if line.upper().startswith('CHAPTER '):
                chapter_title = line
                story.append(PageBreak())
                story.append(Paragraph(chapter_title, self.styles['ChapterHeading']))
                story.append(Spacer(1, 0.2*inch))
                prev_was_sec_id = False
                i += 1
                continue

            # Check for section headers (ALL CAPS with underscores or standalone short lines)
            if self._is_section_header(line):
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(line, self.styles['SectionHeading']))
                story.append(Spacer(1, 0.1*inch))
                prev_was_sec_id = False
                i += 1
                continue

            # Handle simple bullet lines
            if line.startswith('•') or line.startswith('- '):
                story.append(Paragraph(line, self.styles['CustomBody']))
                story.append(Spacer(1, 0.03*inch))
                i += 1
                continue

            # Collect paragraph text (combine until double newline or header)
            paragraph_lines = []
            while i < len(lines):
                current_line = lines[i].strip()

                if not current_line:
                    i += 1
                    break

                if (current_line.startswith('=') and 'CHAPTER' in current_line.upper()) or self._is_section_header(current_line) or (current_line.startswith('[CH') and ']' in current_line) or (current_line.startswith('[SEC') and ']' in current_line):
                    break

                paragraph_lines.append(current_line)
                i += 1

            # Format based on whether this follows a section ID
            if prev_was_sec_id and paragraph_lines:
                # This is a section title, format it accordingly
                title_text = ' '.join(paragraph_lines)
                story.append(Spacer(1, 0.15*inch))
                story.append(
                    Paragraph(title_text, self.styles['SectionHeading']))
                story.append(Spacer(1, 0.1*inch))
                prev_was_sec_id = False
            elif paragraph_lines:
                para_text = ' '.join(paragraph_lines)
                story.append(Paragraph(para_text, self.styles['CustomBody']))
                story.append(Spacer(1, 0.08*inch))

        return story

    def _is_section_header(self, line: str) -> bool:
        """Check if a line looks like a section header."""
        # Short lines (less than 80 chars) with mostly capitalized words
        if len(line) < 80:
            words = line.split()
            if len(words) <= 6:  # Max 6 words for header
                # Count uppercase words
                caps_words = sum(1 for w in words if w[0].isupper())
                if caps_words >= len(words) * 0.7:  # At least 70% uppercase
                    return True
        return False
