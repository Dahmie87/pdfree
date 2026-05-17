"""Prompt templates for the book generation agent."""

# Word count targets per "page" (1 page ≈ 250 words typical formatting)
WORD_COUNT_TARGETS = {
    "super_fast": 1500,  # ~6 pages
    "fast": 3000,        # ~12 pages
    "balanced": 5000,    # ~20 pages
    "length": 8000,      # ~32 pages
}

TITLE_EXTRACTION_PROMPT = """Extract a concise, compelling title for a book based on this prompt: {user_prompt}

Provide ONLY the title, nothing else. Maximum 10 words."""

SUPER_FAST_BOOK_PROMPT = r"""You are a professional book author.

Write a complete, compact book about: {user_prompt}

Length priority: {length_guidance}
Target total words: approximately {target_words} words

Critical requirements:
1. Make exactly one response that contains the entire book.
2. Do not create a table of contents page.
3. Do not create more than 2 chapters.
4. Each chapter should be substantial enough to read like real book content, not a fragment.
5. Keep the writing concise, coherent, and complete.
6. Use chapter headers in the form `CHAPTER 1: ...` and `CHAPTER 2: ...`.
7. Put chapter headings on their own lines.
8. Keep section headings minimal; do not add lots of tiny subsections.
9. Return ONLY valid JSON with this exact shape:

{{
    "title": "Book Title",
    "content": "Full book text here"
}}

Content rules:
- The `content` field must contain the entire book text.
- Start the book immediately with the first chapter header.
- Keep the whole book compact and polished.
- No commentary, no markdown fences, no extra keys.

Write the super fast book now:"""

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

CHAPTER_CONTENT_PROMPT = r"""You are an expert writer creating Chapter {chapter_num} for a professional book about: {topic}

Chapter Title: {chapter_title}

Length priority: {length_guidance}
Target words for this chapter: approximately {chapter_word_target} words

Write a comprehensive, detailed chapter with ALL these sections. Include clear section headers for readability.

Use this exact sequence for the chapter body:
1. Start with the chapter body only; do not repeat the chapter title line.
2. Write the opening paragraph.
3. For each subtitle/section, put the subtitle on its own line.
4. Put the supporting text below the subtitle after a blank line.
5. Never place a subtitle inline with a paragraph, and never merge a subtitle into body text.

Sections to cover:
{sections_list}

Requirements:
1. Aim for exactly {chapter_word_target} words (±10%)
2. Adjust depth based on length priority
3. Include specific examples and case studies (scale with word count)
4. Use technical terminology appropriately
5. Include clear subsection headers for each section listed above, each on its own line
6. Add practical takeaways
7. Format with double line breaks between sections
8. Use the following exact header formats (regular expressions) for titles and section markers. The LLM must follow these regexes when emitting headers and IDs:

    - Chapter header (plain line): ^CHAPTER\s+\d+:.*$
    - Markdown H1 (chapter-like): ^#\s+.+$
    - Section header (plain/title line): ^[A-Z][A-Za-z0-9\s,:\-()]{{0,80}}$  # human-readable title
    - Section ID marker: ^\[SEC\d+\.\d+\]\s*.*$
    - Chapter ID marker: ^\[CH\d+\]\s*.*$

    When you include a header, put the header text on its own line (no inline content on the same line). If there is inline explanatory content immediately following a header, place it on the next line.

9. Special-character filtering: Remove or normalize any sequence of special characters that does not match the allowed header or ID patterns above. Examples to remove or convert:

    - Markdown inline emphasis like `**bold**`, `*italic*`: convert to plain header or plain text (no Markdown markers).
    - Repeated separators or decorations like `*****`, `-----`, `####` or `~~~`: strip them unless they are an allowed header/ID.
    - Inline bullet markers (e.g., `* Item`) should be output as simple bullet lines (`• Item`) or paragraphs, not with raw asterisks.

10. Output rules summary:
    - Only use the header/ID formats specified above for titles and section markers.
    - Do not emit any other bracketed or punctuation-only lines.
    - Ensure subtopic headings (inline or bolded in source) are output as distinct section/subsection headers on their own lines.
Start with the chapter introduction, then cover each section thoroughly.
Do NOT include chapter number or title - just the content.
Write the chapter content now:"""

FULL_BOOK_PROMPT = r"""You are a professional book author. Write a complete book about: {topic}

Table of Contents:
{toc_text}

Length priority: {length_guidance}
Target total words: approximately {target_words} words

Requirements:
1. Write the full book following the table of contents structure
2. Include chapter headers (Chapter 1, Chapter 2, etc.)
3. Include section headers for each section listed in the TOC
4. Aim for approximately {target_words} words total (±10%)
5. Use professional formatting and clear section divisions
6. Include relevant examples and case studies
7. Maintain consistent depth and quality throughout
8. Add practical takeaways in each chapter
9. Format with double line breaks between major sections
10. Keep chapter titles, subtitles, and body text in this exact order:
    - chapter title on its own line
    - opening paragraph
    - subtitle/section title on its own line
    - body text below it after a blank line

Header and output rules (strict):

    - Use the following exact header formats (regular expressions) for titles and section markers. The LLM must follow these regexes when emitting headers and IDs:

      - Chapter header (plain line): ^CHAPTER\s+\d+:.*$
      - Markdown H1 (chapter-like): ^#\s+.+$
    - Section header (plain/title line): ^[A-Z][A-Za-z0-9\s,:\-()]{{0,80}}$
      - Section ID marker: ^\[SEC\d+\.\d+\]\s*.*$
      - Chapter ID marker: ^\[CH\d+\]\s*.*$

    - When including a header, put the header text on its own line with no inline content. If explanatory text follows immediately, place it on the next line.
    - Do not merge subtitles into the body text.
    - Do not place subtitle text inline with a paragraph.

Special-character filtering and normalization:

    - Strip or normalize any sequence of special characters that does not match the allowed header or ID patterns above.
    - Convert inline markdown emphasis like `**bold**` or `*italic*` to plain text (remove markers).
    - Remove repeated decorations like `*****`, `-----`, `####`, or `~~~` unless they match an allowed header pattern.
    - Convert raw list markers such as `* Item` or `- Item` to simple bullet lines `• Item` or plain paragraphs.
    - Do not emit other bracketed or punctuation-only lines that don't carry semantic meaning.

Output rules summary:
    - Only use the header/ID formats specified above for titles and section markers.
    - Ensure subtopic headings (inline or bolded in source) are output as distinct section/subsection headers on their own lines.
    - Ensure the TOC matches the chapter and section headers used in the content.
Write the complete book now:"""


def get_title_prompt(user_prompt: str) -> str:
    """Get the prompt for title extraction."""
    return TITLE_EXTRACTION_PROMPT.format(user_prompt=user_prompt)


def get_super_fast_book_prompt(user_prompt: str, length_priority: str | None = None) -> str:
    """Get the one-shot prompt for super fast full-book generation."""
    return SUPER_FAST_BOOK_PROMPT.format(
        user_prompt=user_prompt,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority),
    )


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
