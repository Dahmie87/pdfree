"""Prompt templates for the book generation agent."""

# Word count targets per "page" (1 page ≈ 250 words typical formatting)
WORD_COUNT_TARGETS = {
    "super_fast": 1500,  # ~6 pages
    "fast": 2500,        # ~10 pages
    "balanced": 5000,    # ~20 pages
    "length": 8000,      # ~32 pages
}

TITLE_EXTRACTION_PROMPT = """Extract a concise, compelling title for a book based on this prompt: {user_prompt}

Provide ONLY the title, nothing else. Maximum 10 words."""

TITLE_TOC_PROMPT = """You are a professional book editor. Create a title and table of contents for a book about: {user_prompt}

Length priority: {length_guidance}
Target content length: approximately {target_words} words

Requirements:
1. Provide a concise title
2. Match chapter count to length priority:
    - super_fast: 2-3 very short chapters only (NO table of contents page needed)
    - fast: 3-4 chapters (include TOC page)
    - balanced: 5-6 chapters (include TOC page)
    - length: 7-8 chapters (include TOC page)
3. Each chapter should have 2-3 subsections (fewer for super_fast)
4. Return ONLY valid JSON, no other text

JSON Format (EXACTLY):
{{
  "title": "Book Title",
  "chapters": [
    {{
      "number": 1,
      "title": "Chapter Title",
      "sections": ["Section 1", "Section 2", "Section 3"]
    }}
  ]
}}

Generate the title and table of contents now:"""

TOC_GENERATION_PROMPT = """You are a professional book editor. Create a detailed table of contents for a comprehensive book about: {user_prompt}

Length priority: {length_guidance}
Target content length: approximately {target_words} words

Requirements:
1. Match chapter count to length priority:
    - super_fast: 2-3 very short chapters only
    - fast: 3-4 chapters
    - balanced: 5-6 chapters
    - length: 7-8 chapters
2. Each chapter should have 2-3 subsections (fewer for super_fast, up to 5 for balanced/length)
3. Return ONLY valid JSON, no other text

JSON Format (EXACTLY):
{{
  "chapters": [
    {{
      "number": 1,
      "title": "Chapter Title",
      "sections": ["Section 1", "Section 2", "Section 3"]
    }}
  ]
}}

Generate the table of contents now:"""

CHAPTER_CONTENT_PROMPT = """You are an expert writer creating Chapter {chapter_num} for a professional book about: {topic}

Chapter Title: {chapter_title}

Length priority: {length_guidance}
Target words for this chapter: approximately {chapter_word_target} words

Write a comprehensive, detailed chapter with ALL these sections:
{sections_list}

Requirements:
1. Aim for exactly {chapter_word_target} words (±10%)
2. Adjust depth based on length priority
3. Include specific examples and case studies (scale with word count)
4. Use technical terminology appropriately
5. Include subsection headers
6. Add practical takeaways
7. Format with double line breaks between sections

Start with the chapter introduction, then cover each section thoroughly.
Do NOT include chapter number or title - just the content.
Write the chapter content now:"""

FULL_BOOK_PROMPT = """You are an expert writer. Write the full book content about: {topic}

Use this table of contents:
{toc_text}

Length priority: {length_guidance}
Target total content length: approximately {target_words} words

Requirements:
1. Follow the table of contents order
2. Aim for exactly {target_words} words total (±5%)
3. Include clear section headers for each chapter and section
4. Use double line breaks between sections
5. Do NOT include the book title or a separate table of contents
6. For super_fast priority: be ultra-concise, skip examples if needed

Write the full book content now:"""


def get_title_prompt(user_prompt: str) -> str:
    """Get the prompt for title extraction."""
    return TITLE_EXTRACTION_PROMPT.format(user_prompt=user_prompt)


def _get_length_guidance(length_priority: str | None) -> str:
    """Return a concise guideline for desired length."""
    if length_priority == "length":
        return "Very detailed and thorough; favor more depth and breadth. Maximum depth and examples."
    if length_priority == "fast":
        return "Concise and focused; fewer sections and tighter explanations. Moderate depth."
    if length_priority == "super_fast":
        return "ULTRA-BRIEF; only essential content; NO elaboration or examples; minimal sections."
    return "Balanced length; clear, practical depth without being exhaustive. Moderate examples."

def _get_word_count_target(length_priority: str | None) -> int:
    """Get target word count for the entire book."""
    if length_priority in WORD_COUNT_TARGETS:
        return WORD_COUNT_TARGETS[length_priority]
    return WORD_COUNT_TARGETS["balanced"]

def _get_chapter_word_target(length_priority: str | None, num_chapters: int) -> int:
    """Get target word count per chapter."""
    total_target = _get_word_count_target(length_priority)
    return total_target // max(num_chapters, 1)


def get_title_toc_prompt(user_prompt: str, length_priority: str | None = None) -> str:
    """Get the prompt for generating title and table of contents."""
    return TITLE_TOC_PROMPT.format(
        user_prompt=user_prompt,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority)
    )


def get_toc_prompt(user_prompt: str, length_priority: str | None = None) -> str:
    """Get the prompt for generating table of contents."""
    return TOC_GENERATION_PROMPT.format(
        user_prompt=user_prompt,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority)
    )


def get_chapter_prompt(
    topic: str,
    chapter_num: int,
    chapter_title: str,
    sections: list,
    length_priority: str | None = None,
    num_chapters: int = 5
) -> str:
    """Get the prompt for generating a single chapter."""
    sections_list = "\n".join([f"- {section}" for section in sections])
    chapter_target = _get_chapter_word_target(length_priority, num_chapters)
    return CHAPTER_CONTENT_PROMPT.format(
        chapter_num=chapter_num,
        topic=topic,
        chapter_title=chapter_title,
        sections_list=sections_list,
        length_guidance=_get_length_guidance(length_priority),
        chapter_word_target=chapter_target
    )


def get_full_book_prompt(
    topic: str,
    toc_text: str,
    length_priority: str | None = None
) -> str:
    """Get the prompt for generating a full book in a single pass."""
    return FULL_BOOK_PROMPT.format(
        topic=topic,
        toc_text=toc_text,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority)
    )
