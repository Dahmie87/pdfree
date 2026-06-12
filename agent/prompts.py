"""Prompt templates for the book generation agent."""

WORD_COUNT_TARGETS = {
    "super_fast": 1500,
    "fast": 3000,
    "balanced": 5000,
    "length": 8000,
}

WRITING_MODE_GUIDANCE = {
    "casual": "Casual, warm, approachable, and easy to read. Keep the tone conversational and clear.",
    "professional": "Professional, polished, authoritative, and structured. Keep the tone confident and refined.",
    "creative": "Creative, vivid, expressive, and engaging. Use richer imagery and a more stylized voice.",
    "technical": "Technical, precise, concise, and methodical. Prioritize accuracy and terminology over flourish.",
}

TITLE_EXTRACTION_PROMPT = """Extract a concise, compelling title for a book based on this prompt: {user_prompt}

Writing mode: {mode_guidance}

Provide ONLY the title, nothing else. Maximum 10 words."""

SUPER_FAST_BOOK_PROMPT = r"""You are a professional book author.

Write a complete, compact book about: {user_prompt}

Length priority: {length_guidance}
Writing mode: {mode_guidance}
Target total words: approximately {target_words} words

Critical requirements:
1. Make exactly one response that contains the entire book.
2. Do not create a table of contents page.
3. Do not use chapter headers or chapter numbering.
4. Write as one continuous flow from start to finish.
5. You may use occasional short subtitle lines, but no chapter-like breaks.
6. Keep the writing concise, coherent, and complete.
7. Keep section headings minimal; do not add lots of tiny subsections.
8. Return ONLY valid JSON with this exact shape:

{
    "title": "Book Title",
    "content": "Full book text here"
}

Write the super fast book now:"""

TITLE_TOC_PROMPT = """You are a professional book editor. Create a title and table of contents for a book about: {user_prompt}

Length priority: {length_guidance}
Writing mode: {mode_guidance}
Target content length: approximately {target_words} words

Requirements:
1. Provide a concise title
2. Match chapter count to length priority
3. Each chapter should have 2-3 subsections
4. Return ONLY valid JSON

JSON Format:
{{
    "title": "Book Title",
    "chapters": [
        {{
            "number": 1,
            "title": "Chapter Title",
            "sections": ["Section 1", "Section 2"]
        }}
    ]
}}

Generate now:"""

TOC_GENERATION_PROMPT = """You are a professional book editor. Create a table of contents for: {user_prompt}

Length priority: {length_guidance}
Writing mode: {mode_guidance}
Target content length: approximately {target_words} words

Requirements:
1. Match chapter count to length priority
2. Each chapter should have 2-3 subsections
3. Return ONLY valid JSON

JSON Format:
{{
    "chapters": [
        {{
            "number": 1,
            "title": "Chapter Title",
            "sections": ["Section 1", "Section 2"]
        }}
    ]
}}

Generate now:"""

CHAPTER_CONTENT_PROMPT = r"""You are an expert writer creating Chapter {chapter_num} for a book about: {topic}

Chapter Title: {chapter_title}

Length priority: {length_guidance}
Target words: {chapter_word_target}

Write the chapter with this structure:

- Start with opening paragraph
- Each section title must be on its own line
- Body text must follow after a blank line
- Never inline section titles with paragraphs

Sections:
{sections_list}

STRICT OUTPUT RULES:
- No markdown formatting (** or * or ###)
- No decorative separators
- No inline headings
- Section headers must be plain text lines only
- Do not repeat chapter title

Write chapter now:"""

FULL_BOOK_PROMPT = """You are a professional book author. Write a complete book about: {topic}

Table of Contents:
{toc_text}

Length priority: {length_guidance}
Writing mode: {mode_guidance}
Target total words: approximately {target_words} words

Requirements:
1. Follow the table of contents structure
2. Include clear chapter breaks
3. Each chapter starts with a chapter header line
4. Each section title must be on its own line
5. No markdown formatting
6. Keep structure consistent and simple
7. Ensure TOC matches final structure

OUTPUT RULES:
- Chapter header format: CHAPTER X: Title
- Section headers: plain line only
- No special symbols, no regex-style enforcement language
- No JSON output

Write the complete book now:"""

PROMPT_MAP: dict = {}

for _mode, _guidance in WRITING_MODE_GUIDANCE.items():
    PROMPT_MAP[_mode] = {
        "title": TITLE_EXTRACTION_PROMPT.replace("{mode_guidance}", _guidance),
        "super_fast": SUPER_FAST_BOOK_PROMPT.replace("{mode_guidance}", _guidance),
        "title_toc": TITLE_TOC_PROMPT.replace("{mode_guidance}", _guidance),
        "toc": TOC_GENERATION_PROMPT.replace("{mode_guidance}", _guidance),
        "chapter": CHAPTER_CONTENT_PROMPT.replace("{mode_guidance}", _guidance),
        "full_book": FULL_BOOK_PROMPT.replace("{mode_guidance}", _guidance),
    }


def get_prompt_for_mode(prompt_key: str, writing_mode: str | None, **kwargs) -> str:
    mode = writing_mode or "casual"
    if mode not in PROMPT_MAP:
        mode = "casual"
    template = PROMPT_MAP[mode][prompt_key]
    return template.format(**kwargs)


def get_title_prompt(user_prompt: str, writing_mode: str | None = None) -> str:
    return get_prompt_for_mode("title", writing_mode, user_prompt=user_prompt)


def get_super_fast_book_prompt(user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None) -> str:
    return get_prompt_for_mode(
        "super_fast",
        writing_mode,
        user_prompt=user_prompt,
        length_guidance="minimal",
        target_words=WORD_COUNT_TARGETS.get(
            length_priority or "super_fast", 1500),
    )


def _get_length_guidance(length_priority: str | None) -> str:
    if length_priority == "length":
        return "Very detailed"
    if length_priority == "fast":
        return "Focused and concise"
    if length_priority == "super_fast":
        return "Ultra brief"
    return "Balanced"


def _get_word_count_target(length_priority: str | None) -> int:
    return WORD_COUNT_TARGETS.get(length_priority or "balanced", 5000)


def _get_chapter_word_target(length_priority: str | None, num_chapters: int) -> int:
    total = _get_word_count_target(length_priority)
    return total // max(num_chapters, 1)


def get_title_toc_prompt(user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None) -> str:
    return get_prompt_for_mode(
        "title_toc",
        writing_mode,
        user_prompt=user_prompt,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority),
    )


def get_toc_prompt(user_prompt: str, length_priority: str | None = None, writing_mode: str | None = None) -> str:
    return get_prompt_for_mode(
        "toc",
        writing_mode,
        user_prompt=user_prompt,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority),
    )


def get_chapter_prompt(
    topic: str,
    chapter_num: int,
    chapter_title: str,
    sections: list,
    length_priority: str | None = None,
    num_chapters: int = 5,
    writing_mode: str | None = None,
) -> str:
    sections_list = "\n".join([f"- {s}" for s in sections])
    chapter_target = _get_chapter_word_target(length_priority, num_chapters)

    return get_prompt_for_mode(
        "chapter",
        writing_mode,
        chapter_num=chapter_num,
        topic=topic,
        chapter_title=chapter_title,
        sections_list=sections_list,
        length_guidance=_get_length_guidance(length_priority),
        chapter_word_target=chapter_target,
    )


def get_full_book_prompt(
    topic: str,
    toc_text: str,
    length_priority: str | None = None,
    writing_mode: str | None = None,
) -> str:
    return get_prompt_for_mode(
        "full_book",
        writing_mode,
        topic=topic,
        toc_text=toc_text,
        length_guidance=_get_length_guidance(length_priority),
        target_words=_get_word_count_target(length_priority),
    )
