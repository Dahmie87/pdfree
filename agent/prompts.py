"""Prompt templates for the book generation agent."""

BOOK_PROMPT_TEMPLATE = """You are an expert book writer. Given a user's prompt, generate a complete, well-structured book chapter or short book.

User Request: {user_prompt}

Instructions:
1. Generate a comprehensive and engaging response
2. Structure the content with clear sections and logical flow
3. Aim for approximately 2000-3000 words
4. Use professional writing style
5. Include an introduction and conclusion
6. Format with double line breaks between sections for better readability

Generate the book content now:"""


TITLE_EXTRACTION_PROMPT = """Extract a concise, compelling title for a book based on this prompt: {user_prompt}

Provide ONLY the title, nothing else. Maximum 10 words."""


def get_book_generation_prompt(user_prompt: str) -> str:
    """Get the full prompt for book generation."""
    return BOOK_PROMPT_TEMPLATE.format(user_prompt=user_prompt)


def get_title_prompt(user_prompt: str) -> str:
    """Get the prompt for title extraction."""
    return TITLE_EXTRACTION_PROMPT.format(user_prompt=user_prompt)
