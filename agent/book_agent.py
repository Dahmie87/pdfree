"""LangChain agent for book generation."""

import logging
import json
import re
import random
import time
from models.llm import get_llm
from models.llm import is_groq_daily_quota_error
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


def _extract_json_object(text: str) -> str:
    """Extract the first JSON object from model output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned,
                         flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", cleaned, 0)

    return cleaned[start:end + 1]


def _parse_json_response(text: str) -> dict:
    """Parse a model response that may include markdown or extra text around JSON."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(_extract_json_object(text))


def _is_rate_limit_error(error: Exception) -> bool:
    """Return True when the Groq call failed because the daily quota is exhausted."""
    return is_groq_daily_quota_error(error)


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

    def _generate_title(self, user_prompt: str, writing_mode: str | None = None) -> str:
        """Generate a title for the book."""
        logger.info(f"📝 Step 1: Generating title...")
        try:
            title_prompt = get_title_prompt(
                user_prompt, writing_mode=writing_mode)
            title = self.llm.invoke(title_prompt)
            logger.info(f"   ✅ Title: {title.strip()}")
            return title.strip()
        except Exception as e:
            logger.error(f"   ❌ Title generation failed: {e}")
            raise

    def _generate_toc(self, user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None) -> list:
        """Generate table of contents with multiple chapters."""
        logger.info(f"📋 Step 2: Generating table of contents...")
        try:
            toc_prompt = get_toc_prompt(
                user_prompt,
                length_priority=length_priority,
                writing_mode=writing_mode,
            )
            toc_response = self.llm.invoke(toc_prompt)

            # Parse JSON response, allowing for fenced or prefixed output.
            toc_data = _parse_json_response(toc_response)
            chapters = toc_data.get("chapters", [])

            if not chapters:
                raise ValueError("TOC response did not include any chapters")

            logger.info(f"   ✅ Generated {len(chapters)} chapters")
            for chapter in chapters:
                logger.debug(
                    f"      - Chapter {chapter['number']}: {chapter['title']}")

            return chapters
        except (json.JSONDecodeError, ValueError) as error:
            logger.error(
                f"   ❌ Failed to parse TOC JSON: {error}")
            retry_prompt = (
                "Return only valid JSON for the table of contents. "
                "Do not add markdown, commentary, or code fences."
            )
            retry_response = self.llm.invoke(
                toc_prompt + "\n\n" + retry_prompt)
            toc_data = _parse_json_response(retry_response)
            chapters = toc_data.get("chapters", [])
            if not chapters:
                raise ValueError("TOC retry did not include any chapters")
            logger.info(f"   ✅ Generated {len(chapters)} chapters after retry")
            return chapters
        except Exception as e:
            logger.error(f"   ❌ TOC generation failed: {e}")
            raise

    def _generate_title_and_toc(self, user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None) -> tuple[str, list]:
        """Generate title and table of contents in a single call."""
        logger.info("📋 Step 1: Generating title + table of contents...")
        try:
            combined_prompt = get_title_toc_prompt(
                user_prompt,
                length_priority=length_priority,
                writing_mode=writing_mode,
            )
            response = self.llm.invoke(combined_prompt)
            data = _parse_json_response(response)
            title = str(data.get("title", "")).strip(
            ) or self._generate_title(user_prompt, writing_mode=writing_mode)
            chapters = data.get("chapters", [])
            if not chapters:
                raise ValueError(
                    "Combined title+TOC response did not include chapters")
            return title, chapters
        except (json.JSONDecodeError, ValueError) as error:
            logger.error(
                f"   ❌ Failed to parse title+TOC JSON: {error}")
            return self._generate_title(user_prompt, writing_mode=writing_mode), self._generate_toc(
                user_prompt,
                length_priority=length_priority,
                writing_mode=writing_mode,
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

    def _generate_chapter(self, user_prompt: str, chapter: dict, length_priority: str | None = None, num_chapters: int = 5, writing_mode: str | None = None) -> str:
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
                num_chapters=num_chapters,
                writing_mode=writing_mode,
            )
            content = self.llm.invoke(chapter_prompt)
            logger.debug(f"      ✅ Generated {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"      ❌ Failed to generate chapter: {e}")
            if _is_rate_limit_error(e):
                raise
            return f"[Error generating Chapter {chapter_num}: {chapter_title}]"

    def _generate_chapters(self, user_prompt: str, chapters: list, length_priority: str | None = None, writing_mode: str | None = None) -> str:
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
                num_chapters=num_chapters,
                writing_mode=writing_mode,
            )

            # Add chapter header and force the next chapter to start on a new page.
            chapter_header = (
                f"\n\n[PAGE_BREAK]\n"
                f"{'='*50}\n"
                f"CHAPTER {chapter['number']}: {chapter['title'].upper()}\n"
                f"{'='*50}\n\n"
            )
            combined_content.append(chapter_header + chapter_content)

        logger.info(f"   ✅ All {len(chapters)} chapters generated!")
        return "".join(combined_content)

    def _generate_super_fast_book(self, user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None) -> tuple[str, list, str]:
        """Generate the entire super_fast book in one LLM call."""
        logger.info(
            "⚡ Step 1-3: Generating super_fast book in a single call...")
        prompt = get_super_fast_book_prompt(
            user_prompt,
            length_priority=length_priority,
            writing_mode=writing_mode,
        )
        response = self.llm.invoke(prompt)
        # Attempt to robustly extract JSON payload from the LLM response.
        data = None
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find a JSON object substring inside the response
            m = re.search(r"(\{.*\})", response, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                except json.JSONDecodeError:
                    data = None

        if data:
            title = str(data.get("title", "")).strip()
            content = str(data.get("content", "")).strip()
        else:
            logger.warning(
                "   ⚠️ super_fast response was not valid JSON; using raw text fallback")
            title = ""
            content = response.strip()

        # If title is missing or looks identical to the prompt, try a lightweight title extraction.
        if not title or title.strip() == user_prompt.strip():
            try:
                title = self._generate_title(
                    user_prompt, writing_mode=writing_mode)
                logger.info(f"   ℹ️ Regenerated title for super_fast: {title}")
            except Exception:
                title = user_prompt.strip()

        content = self._normalize_super_fast_content(content)

        chapters = [
            {"number": 1, "title": "Main Content", "sections": []},
        ]
        logger.info(
            f"   ✅ super_fast generated in 1 call: {len(content)} characters")
        return title, chapters, content

    def _normalize_super_fast_content(self, content: str) -> str:
        """Normalize super_fast output into one continuous, non-chapter flow."""
        cleaned_lines: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()

            # Never carry explicit page-break markers in super_fast mode.
            if line.upper() == "[PAGE_BREAK]":
                continue

            # Remove chapter framing and chapter title lines.
            if set(line) <= {"="} and len(line) >= 3:
                continue
            if re.match(r"^#{1,6}\s*chapter\b", line, re.IGNORECASE):
                continue
            if re.match(r"^chapter\s+\d+\b", line, re.IGNORECASE):
                continue

            cleaned_lines.append(raw_line)

        normalized = "\n".join(cleaned_lines).strip()
        return normalized

    def _paginate_book_content(self, content: str) -> str:
        """Insert explicit page-break markers before chapter starts."""
        paginated_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and (
                stripped.upper().startswith("CHAPTER ")
                or (stripped.startswith("#") and "CHAPTER" in stripped.upper())
            ):
                paginated_lines.append("[PAGE_BREAK]")
            paginated_lines.append(line)
        return "\n".join(paginated_lines).lstrip()

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
        length_priority: str | None = None,
        writing_mode: str | None = None,
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
        title = self._generate_title(user_prompt, writing_mode=writing_mode)

        # Step 2: Generate table of contents
        if length_priority == "super_fast":
            return self._generate_super_fast_book(
                user_prompt,
                length_priority=length_priority,
                writing_mode=writing_mode,
            )

        chapters = self._generate_toc(
            user_prompt,
            length_priority=length_priority,
            writing_mode=writing_mode,
        )

        # Step 3: Generate content (fast path uses a single call)
        if length_priority == "fast":
            # For fast/super_fast, use full book generation with explicit length targets
            toc_text = self._format_toc_for_prompt(chapters)
            full_prompt = get_full_book_prompt(
                topic=user_prompt,
                toc_text=toc_text,
                length_priority=length_priority,
                writing_mode=writing_mode,
            )
            full_content = self.llm.invoke(full_prompt)
            full_content = self._paginate_book_content(full_content)

            toc_page = self._create_toc_page(chapters)
            content = toc_page + "\n\n" + full_content
        else:
            chapter_content = self._generate_chapters(
                user_prompt,
                chapters,
                length_priority=length_priority,
                writing_mode=writing_mode,
            )

            # Step 4: Create TOC page
            toc_page = self._create_toc_page(chapters)

            # Combine: TOC page + all chapters
            content = toc_page + "\n\n" + chapter_content

        return title, chapters, content

    def generate_pdf_book(self, user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None, cover_design: str | None = "split") -> tuple[bytes, str, float]:
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
            Tuple of (pdf_bytes, title, total_time_seconds)
        """
        start_time = time.time()
        try:
            title, chapters, content = self.generate_book_content(
                user_prompt,
                length_priority=length_priority,
                writing_mode=writing_mode,
            )

            total_calls = self._pick_total_calls(length_priority)
            logger.info(f"📞 Target LLM calls: {total_calls}")

            # Step 5: Create PDF
            logger.info("📄 Step 5: Creating PDF...")
            try:
                pdf_bytes = self.pdf_generator.generate_pdf(
                    title=title,
                    content=content,
                    author="AI Agent",
                    writing_mode=writing_mode,
                    cover_design=cover_design or "split",
                )
                logger.info(f"   ✅ PDF created: {len(pdf_bytes)} bytes")
            except Exception as e:
                logger.error(f"   ❌ PDF generation failed: {e}")
                raise

            total_time = time.time() - start_time
            logger.info(
                f"✅ Book generation complete! Total time: {total_time:.2f}s")
            return pdf_bytes, title, total_time
        except Exception as e:
            logger.error(f"❌ Book generation failed: {e}")
            raise
