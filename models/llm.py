"""LLM initialization - using Groq API with Llama 3.1 model."""

import os
import logging
from groq import Groq#type: ignore

logger = logging.getLogger(__name__)


class GroqLLM:
    """Groq LLM client for fast inference."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=api_key)
        logger.info(f"🔧 Initialized Groq LLM with model: {model}")

    def invoke(self, prompt: str) -> str:
        """Call the Groq API and return response."""
        logger.info(f"🚀 Calling Groq API")
        logger.debug(f"   Model: {self.model}")
        logger.debug(f"   Prompt: {prompt[:100]}...")

        try:
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                max_tokens=2048,
                temperature=0.7,
            )

            text = message.choices[0].message.content
            logger.info(f"✅ Got response: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"❌ Groq API call failed: {e}", exc_info=True)
            raise


def get_llm():
    """
    Initialize LLM using Groq API.

    Setup:
    1. Get API key from https://console.groq.com/keys
    2. Add to .env: GROQ_API_KEY=your_key

    Returns:
        GroqLLM instance
    """
    logger.info("🔧 Initializing Groq LLM...")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("❌ GROQ_API_KEY not set!")
        raise ValueError(
            "GROQ_API_KEY not set!\n"
            "1. Get API key: https://console.groq.com/keys\n"
            "2. Add to .env: GROQ_API_KEY=your_key"
        )

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    logger.info(f"🤖 Using model: {model}")

    try:
        llm = GroqLLM(api_key, model)
        logger.info("✅ Groq LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq LLM: {e}")
        raise
