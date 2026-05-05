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

    def __init__(self, page_size=letter):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1  # Center
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=1
        ))

        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=16,
            spaceAfter=12,
            alignment=4  # Justify
        ))

    def generate_pdf(self, title: str, content: str, author: str = "AI Generated") -> bytes:
        """
        Generate PDF from content.

        Args:
            title: Book title
            content: Book content (can include line breaks for sections)
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
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"By {author}", self.styles['CustomSubtitle']))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            self.styles['CustomSubtitle']
        ))
        story.append(PageBreak())

        # Add content paragraphs
        # Split content by double line breaks to create sections
        sections = content.split('\n\n')

        for section in sections:
            if section.strip():
                # Check if it looks like a heading (short line)
                lines = section.strip().split('\n')
                if len(lines) == 1 and len(lines[0]) < 100:
                    story.append(Paragraph(lines[0], self.styles['Heading2']))
                    story.append(Spacer(1, 0.2*inch))
                else:
                    # Regular paragraph
                    para_text = section.replace('\n', ' ').strip()
                    story.append(
                        Paragraph(para_text, self.styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))

        # Build PDF
        doc.build(story)
        return pdf_buffer.getvalue()
