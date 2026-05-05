"""LangChain agent for book generation."""

import logging
from models.llm import get_llm
from generation.pdf_generator import PDFGenerator
from agent.prompts import get_book_generation_prompt, get_title_prompt

logger = logging.getLogger(__name__)


class BookGenerationAgent:
    """Agent that generates PDF books from user prompts."""

    def __init__(self):
        logger.info("📚 Initializing BookGenerationAgent...")
        try:
            self.llm = get_llm()
            logger.info("✅ LLM loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load LLM: {e}")
            raise

        try:
            self.pdf_generator = PDFGenerator()
            logger.info("✅ PDF Generator loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load PDF Generator: {e}")
            raise

    def _generate_title(self, user_prompt: str) -> str:
        """Generate a title for the book."""
        logger.info(f"📝 Generating title for prompt: {user_prompt[:50]}...")
        try:
            title_prompt = get_title_prompt(user_prompt)
            logger.debug(f"   Title prompt: {title_prompt[:100]}...")
            title = self.llm.invoke(title_prompt)
            logger.info(f"   ✅ Title generated: {title}")
            return title.strip()
        except Exception as e:
            logger.error(f"   ❌ Title generation failed: {e}")
            raise

    def _generate_content(self, user_prompt: str) -> str:
        """Generate the book content."""
        logger.info("✍️  Generating content...")
        try:
            content_prompt = get_book_generation_prompt(user_prompt)
            logger.debug(f"   Content prompt: {content_prompt[:100]}...")
            content = self.llm.invoke(content_prompt)
            logger.info(f"   ✅ Content generated: {len(content)} characters")
            return content.strip()
        except Exception as e:
            logger.error(f"   ❌ Content generation failed: {e}")
            raise

    def generate_pdf_book(self, user_prompt: str) -> tuple[bytes, str]:
        """
        Generate a complete PDF book from a user prompt.

        Args:
            user_prompt: User's input describing what the book should be about

        Returns:
            Tuple of (pdf_bytes, title)
        """
        logger.info(
            f"🚀 Starting book generation for prompt: {user_prompt[:50]}...")

        try:
            # Step 1: Generate title
            logger.info("📝 Step 1: Generating title...")
            title = self._generate_title(user_prompt)

            # Step 2: Generate content
            logger.info("✍️  Step 2: Generating content...")
            content = self._generate_content(user_prompt)

            # Step 3: Create PDF
            logger.info("📄 Step 3: Creating PDF...")
            try:
                pdf_bytes = self.pdf_generator.generate_pdf(
                    title=title,
                    content=content,
                    author="AI Agent"
                )
                logger.info(f"   ✅ PDF created: {len(pdf_bytes)} bytes")
            except Exception as e:
                logger.error(f"   ❌ PDF generation failed: {e}")
                raise

            logger.info("✅ Book generation complete!")
            return pdf_bytes, title
        except Exception as e:
            logger.error(f"❌ Book generation failed: {e}")
            raise
