"""LangChain agent for book generation."""

import logging
import json
import random
from models.llm import get_llm
from generation.pdf_generator import PDFGenerator
from agent.prompts import (
    get_title_prompt,
    get_title_toc_prompt,
    get_toc_prompt,
    get_chapter_prompt,
    get_full_book_prompt,
    get_super_fast_book_prompt,
)

logger = logging.getLogger(__name__)


class BookGenerationAgent:
    """Agent that generates PDF books from user prompts using reiteration."""

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
        logger.info(f"📝 Step 1: Generating title...")
        try:
            title_prompt = get_title_prompt(user_prompt)
            title = self.llm.invoke(title_prompt)
            logger.info(f"   ✅ Title: {title.strip()}")
            return title.strip()
        except Exception as e:
            logger.error(f"   ❌ Title generation failed: {e}")
            raise

    def _generate_toc(self, user_prompt: str, length_priority: str | None = None) -> list:
        """Generate table of contents with multiple chapters."""
        logger.info(f"📋 Step 2: Generating table of contents...")
        try:
            toc_prompt = get_toc_prompt(
                user_prompt, length_priority=length_priority)
            toc_response = self.llm.invoke(toc_prompt)

            # Parse JSON response
            toc_data = json.loads(toc_response)
            chapters = toc_data.get("chapters", [])

            logger.info(f"   ✅ Generated {len(chapters)} chapters")
            for chapter in chapters:
                logger.debug(
                    f"      - Chapter {chapter['number']}: {chapter['title']}")

            return chapters
        except json.JSONDecodeError:
            logger.error(
                "   ❌ Failed to parse TOC JSON, retrying with simpler format")
            # Fallback: create default chapters
            return self._generate_default_toc()
        except Exception as e:
            logger.error(f"   ❌ TOC generation failed: {e}")
            raise

    def _generate_title_and_toc(self, user_prompt: str, length_priority: str | None = None) -> tuple[str, list]:
        """Generate title and table of contents in a single call."""
        logger.info("📋 Step 1: Generating title + table of contents...")
        try:
            combined_prompt = get_title_toc_prompt(
                user_prompt, length_priority=length_priority)
            response = self.llm.invoke(combined_prompt)
            data = json.loads(response)
            title = str(data.get("title", "")).strip(
            ) or self._generate_title(user_prompt)
            chapters = data.get("chapters", [])
            if not chapters:
                chapters = self._generate_toc(
                    user_prompt, length_priority=length_priority)
            return title, chapters
        except json.JSONDecodeError:
            logger.error(
                "   ❌ Failed to parse title+TOC JSON, retrying separately")
            return self._generate_title(user_prompt), self._generate_toc(
                user_prompt,
                length_priority=length_priority
            )
        except Exception as e:
            logger.error(f"   ❌ Title+TOC generation failed: {e}")
            raise

    def _generate_default_toc(self) -> list:
        """Generate a default table of contents if TOC generation fails."""
        logger.info("   📌 Using default chapter structure...")
        default_chapters = [
            {
                "number": 1,
                "title": "Introduction & Fundamentals",
                "sections": ["Overview", "Key Concepts", "Historical Context"]
            },
            {
                "number": 2,
                "title": "Core Principles & Theory",
                "sections": ["Theory", "Best Practices", "Common Misconceptions"]
            },
            {
                "number": 3,
                "title": "Practical Implementation",
                "sections": ["Getting Started", "Real-world Examples", "Common Challenges"]
            },
            {
                "number": 4,
                "title": "Advanced Topics",
                "sections": ["Advanced Techniques", "Optimization", "Scaling"]
            },
            {
                "number": 5,
                "title": "Case Studies & Examples",
                "sections": ["Case Study 1", "Case Study 2", "Lessons Learned"]
            },
        ]
        return default_chapters

    def _generate_chapter(self, user_prompt: str, chapter: dict, length_priority: str | None = None, num_chapters: int = 5) -> str:
        """Generate content for a single chapter."""
        chapter_num = chapter["number"]
        chapter_title = chapter["title"]
        sections = chapter.get("sections", [])

        logger.info(
            f"   📖 Generating Chapter {chapter_num}: {chapter_title}...")
        try:
            chapter_prompt = get_chapter_prompt(
                topic=user_prompt,
                chapter_num=chapter_num,
                chapter_title=chapter_title,
                sections=sections,
                length_priority=length_priority,
                num_chapters=num_chapters
            )
            content = self.llm.invoke(chapter_prompt)
            logger.debug(f"      ✅ Generated {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"      ❌ Failed to generate chapter: {e}")
            return f"[Error generating Chapter {chapter_num}: {chapter_title}]"

    def _generate_chapters(self, user_prompt: str, chapters: list, length_priority: str | None = None) -> str:
        """Generate content for all chapters and combine them."""
        logger.info(f"✍️  Step 3: Generating {len(chapters)} chapters...")

        combined_content = []
        num_chapters = len(chapters)
        for i, chapter in enumerate(chapters, 1):
            logger.info(
                f"   [{i}/{len(chapters)}] Generating Chapter {chapter['number']}...")
            chapter_content = self._generate_chapter(
                user_prompt,
                chapter,
                length_priority=length_priority,
                num_chapters=num_chapters
            )

            # Add chapter header
            chapter_header = f"\n\n{'='*50}\nCHAPTER {chapter['number']}: {chapter['title'].upper()}\n{'='*50}\n\n"
            combined_content.append(chapter_header + chapter_content)

        logger.info(f"   ✅ All {len(chapters)} chapters generated!")
        return "".join(combined_content)

    def _generate_super_fast_book(self, user_prompt: str, length_priority: str | None = None) -> tuple[str, list, str]:
        """Generate the entire super_fast book in one LLM call."""
        logger.info("⚡ Step 1-3: Generating super_fast book in a single call...")
        prompt = get_super_fast_book_prompt(
            user_prompt,
            length_priority=length_priority,
        )
        response = self.llm.invoke(prompt)

        try:
            data = json.loads(response)
            title = str(data.get("title", "")).strip() or user_prompt.strip()
            content = str(data.get("content", "")).strip() or response.strip()
        except json.JSONDecodeError:
            logger.warning("   ⚠️ super_fast response was not valid JSON; using raw text fallback")
            title = user_prompt.strip()
            content = response.strip()

        chapters = [
            {"number": 1, "title": "Chapter 1", "sections": []},
            {"number": 2, "title": "Chapter 2", "sections": []},
        ]
        logger.info(f"   ✅ super_fast generated in 1 call: {len(content)} characters")
        return title, chapters, content

    def _create_toc_page(self, chapters: list) -> str:
        """Create a table of contents page from the chapters list."""
        logger.info("📚 Creating table of contents page...")

        toc_lines = [
            "TABLE OF CONTENTS",
            "=" * 50,
            ""
        ]

        for chapter in chapters:
            chapter_num = chapter["number"]
            chapter_title = chapter["title"]
            toc_lines.append(f"Chapter {chapter_num}: {chapter_title}")

            # Add sections if available
            sections = chapter.get("sections", [])
            for section in sections:
                toc_lines.append(f"  • {section}")
            toc_lines.append("")

        toc_content = "\n".join(toc_lines)
        logger.debug(f"   ✅ TOC created: {len(toc_content)} characters")
        return toc_content

    def _format_toc_for_prompt(self, chapters: list) -> str:
        """Format TOC lines for the full-book prompt."""
        toc_lines = []
        for chapter in chapters:
            chapter_num = chapter["number"]
            chapter_title = chapter["title"]
            toc_lines.append(f"Chapter {chapter_num}: {chapter_title}")
            sections = chapter.get("sections", [])
            for section in sections:
                toc_lines.append(f"- {section}")
        return "\n".join(toc_lines)

    def _pick_total_calls(self, length_priority: str | None) -> int:
        """Pick a total call count based on priority ranges."""
        if length_priority == "super_fast":
            return 1
        if length_priority == "fast":
            return random.randint(2, 3)
        if length_priority == "length":
            return random.randint(4, 6)
        return random.randint(3, 4)

    def _split_chapters(self, chapters: list, parts: int) -> list[list]:
        """Split chapters into roughly even parts."""
        if parts <= 1:
            return [chapters]
        buckets = [[] for _ in range(parts)]
        for idx, chapter in enumerate(chapters):
            buckets[idx % parts].append(chapter)
        return buckets

    def generate_book_content(
        self,
        user_prompt: str,
        length_priority: str | None = None
    ) -> tuple[str, list, str]:
        """
        Generate the book content and metadata without creating a PDF.

        Returns:
            Tuple of (title, chapters, content)
        """
        logger.info(f"🚀 Starting book generation for: {user_prompt[:50]}...")
        if length_priority is not None:
            logger.info(f"🧭 Length priority: {length_priority}")

        # Step 1: Generate title
        title = self._generate_title(user_prompt)

        # Step 2: Generate table of contents
        if length_priority == "super_fast":
            return self._generate_super_fast_book(
                user_prompt,
                length_priority=length_priority,
            )

        chapters = self._generate_toc(
            user_prompt, length_priority=length_priority)

        # Step 3: Generate content (fast path uses a single call)
        if length_priority == "fast":
            # For fast/super_fast, use full book generation with explicit length targets
            toc_text = self._format_toc_for_prompt(chapters)
            full_prompt = get_full_book_prompt(
                topic=user_prompt,
                toc_text=toc_text,
                length_priority=length_priority
            )
            full_content = self.llm.invoke(full_prompt)

            toc_page = self._create_toc_page(chapters)
            content = toc_page + "\n\n" + full_content
        else:
            chapter_content = self._generate_chapters(
                user_prompt,
                chapters,
                length_priority=length_priority
            )

            # Step 4: Create TOC page
            toc_page = self._create_toc_page(chapters)

            # Combine: TOC page + all chapters
            content = toc_page + "\n\n" + chapter_content

        return title, chapters, content

    def generate_pdf_book(self, user_prompt: str, length_priority: str | None = None) -> tuple[bytes, str]:
        """
        Generate a complete PDF book from a user prompt using reiteration.

        Process:
        1. Generate title
        2. Generate table of contents (multiple chapters)
        3. Generate each chapter as separate LLM calls
        4. Create TOC page
        5. Combine into final PDF

        Args:
            user_prompt: User's input describing what the book should be about
            length_priority: Optional length priority (length, balanced, speed, super fast)

        Returns:
            Tuple of (pdf_bytes, title)
        """
        try:
            title, chapters, content = self.generate_book_content(
                user_prompt,
                length_priority=length_priority
            )

            total_calls = self._pick_total_calls(length_priority)
            logger.info(f"📞 Target LLM calls: {total_calls}")

            # Step 5: Create PDF
            logger.info("📄 Step 5: Creating PDF...")
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
