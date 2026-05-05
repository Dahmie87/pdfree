"""LLM initialization - using FREE HuggingFace Inference API with direct HTTP calls."""

import os
import logging
import requests

logger = logging.getLogger(__name__)


class SimpleHFLM:
    """Direct HTTP to HuggingFace Inference Providers (new OpenAI-compatible API)."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        # NEW endpoint: OpenAI-compatible chat completions API
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info(f"🔧 Initialized LLM with model: {model}")
        logger.info(f"📡 Using endpoint: {self.api_url}")

    def invoke(self, prompt: str) -> str:
        """Call the HuggingFace Inference Providers API and return response."""
        logger.info(f"🌐 Calling HuggingFace Inference Providers API")
        logger.debug(f"   Model: {self.model}")
        logger.debug(f"   Prompt: {prompt[:100]}...")

        try:
            # OpenAI-compatible message format (CORRECT format for new API)
            payload = {
                "model": f"{self.model}:fastest",  # Auto-select fastest provider
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 512,
                "temperature": 0.7
            }

            logger.debug(f"   URL: {self.api_url}")
            logger.debug(f"   Payload: {payload}")

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120  # Longer timeout for first inference
            )

            logger.debug(f"   Response status: {response.status_code}")

            if response.status_code not in [200, 201]:
                logger.error(
                    f"❌ API Error {response.status_code}: {response.text[:500]}")
                raise Exception(
                    f"HuggingFace API Error {response.status_code}: {response.text[:500]}")

            result = response.json()
            logger.debug(f"   Response: {str(result)[:200]}...")

            # Parse OpenAI-compatible response
            if "choices" in result and len(result["choices"]) > 0:
                text = result["choices"][0]["message"]["content"]
            else:
                logger.error(f"❌ Unexpected response format: {result}")
                raise Exception(f"Unexpected API response format: {result}")

            if not text or not text.strip():
                logger.error(f"❌ Empty response from API: {result}")
                raise Exception("HuggingFace API returned empty response")

            logger.info(f"✅ Got response: {len(text)} characters")
            return text
        except requests.exceptions.Timeout:
            logger.error("❌ API call timed out - model may be cold starting")
            raise Exception(
                "HuggingFace API timeout - model may be loading, try again in a moment")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {e}")
            raise Exception(f"Request failed: {e}")
        except Exception as e:
            logger.error(f"❌ API call failed: {e}", exc_info=True)
            raise


def get_llm():
    """
    Initialize LLM using FREE HuggingFace Inference API.

    NO PAYMENT REQUIRED - completely free tier available.

    Setup:
    1. Sign up FREE at https://huggingface.co
    2. Get free token at https://huggingface.co/settings/tokens
    3. No credit card needed - free forever with rate limits

    Returns:
        SimpleHFLM instance
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
        llm = SimpleHFLM(api_key, model)
        logger.info("✅ LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM: {e}")
        raise
