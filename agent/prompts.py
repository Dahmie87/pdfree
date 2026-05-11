"""Prompt templates for the book generation agent."""

import json

TITLE_EXTRACTION_PROMPT = """Extract a concise, compelling title for a book based on this prompt: {user_prompt}

Provide ONLY the title, nothing else. Maximum 10 words."""

TOC_GENERATION_PROMPT = """You are a professional book editor. Create a detailed table of contents for a comprehensive book about: {user_prompt}

Requirements:
1. Create 15-20 chapters (NOT fewer, we want a LONG book)
2. Each chapter should have 3-5 subsections
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

Write a comprehensive, detailed chapter with ALL these sections:
{sections_list}

Requirements:
1. Write 3000-4000 words (be VERBOSE and detailed)
2. Include specific examples and case studies
3. Use technical terminology appropriately
4. Include subsection headers
5. Add practical takeaways
6. Format with double line breaks between sections

Start with the chapter introduction, then cover each section thoroughly.
Do NOT include chapter number or title - just the content.
Write the chapter content now:"""


def get_title_prompt(user_prompt: str) -> str:
    """Get the prompt for title extraction."""
    return TITLE_EXTRACTION_PROMPT.format(user_prompt=user_prompt)


def get_toc_prompt(user_prompt: str) -> str:
    """Get the prompt for generating table of contents."""
    return TOC_GENERATION_PROMPT.format(user_prompt=user_prompt)


def get_chapter_prompt(topic: str, chapter_num: int, chapter_title: str, sections: list) -> str:
    """Get the prompt for generating a single chapter."""
    sections_list = "\n".join([f"- {section}" for section in sections])
    return CHAPTER_CONTENT_PROMPT.format(
        chapter_num=chapter_num,
        topic=topic,
        chapter_title=chapter_title,
        sections_list=sections_list
    )
