"""PDF generation module using ReportLab."""

from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime


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

        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for chapter headers (====CHAPTER X: TITLE====)
            if line.startswith('=') and 'CHAPTER' in line.upper():
                # Extract chapter number and title
                chapter_title = line.strip('=').strip()
                story.append(PageBreak())
                story.append(Paragraph(chapter_title, self.styles['ChapterHeading']))
                story.append(Spacer(1, 0.2*inch))
                i += 1
                continue
            
            # Check for section headers (ALL CAPS with underscores or standalone short lines)
            if self._is_section_header(line):
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(line, self.styles['SectionHeading']))
                story.append(Spacer(1, 0.1*inch))
                i += 1
                continue
            
            # Collect paragraph text (combine until double newline or header)
            paragraph_lines = []
            while i < len(lines):
                current_line = lines[i].strip()
                
                if not current_line:
                    i += 1
                    break
                
                if (current_line.startswith('=') and 'CHAPTER' in current_line.upper()) or self._is_section_header(current_line):
                    break
                
                paragraph_lines.append(current_line)
                i += 1
            
            # Add paragraph if not empty
            if paragraph_lines:
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
