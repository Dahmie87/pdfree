"""LLM initialization - using FREE HuggingFace Inference API."""

import os
import logging
from langchain_community.llms import HuggingFaceEndpoint  # type: ignore

logger = logging.getLogger(__name__)


def get_llm():
    """
    Initialize LLM using FREE HuggingFace Inference API.

    NO PAYMENT REQUIRED - completely free tier available.

    Setup:
    1. Sign up FREE at https://huggingface.co
    2. Get free token at https://huggingface.co/settings/tokens
    3. No credit card needed - free forever with rate limits

    Returns:
        HuggingFaceEndpoint LLM instance
    """
    logger.info("🔧 Initializing LLM...")

    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        logger.error("❌ HUGGINGFACE_API_KEY not set!")
        raise ValueError(
            "HUGGINGFACE_API_KEY not set!\n"
            "1. Sign up FREE: https://huggingface.co\n"
            "2. Get token: https://huggingface.co/settings/tokens\n"
            "3. Add to .env: HUGGINGFACE_API_KEY=your_token\n"
            "NO PAYMENT NEEDED - completely free!"
        )

    model = os.getenv("MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.1")
    logger.info(f"🤖 Using model: {model}")

    try:
        llm = HuggingFaceEndpoint(
            endpoint_url=f"https://api-inference.huggingface.co/models/{model}",
            huggingfacehub_api_token=api_key,
            temperature=0.7,
            max_length=512
        )
        logger.info("✅ LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
        raise
