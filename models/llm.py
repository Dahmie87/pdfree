"""LLM initialization - using Groq API with Llama 3.3 model."""

import os
import logging
from groq import Groq  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PREFERENCE = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
]


def _parse_model_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [value.strip() for value in raw_value.split(",") if value.strip()]


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _get_error_status_code(error: Exception) -> int | None:
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    response = getattr(error, "response", None)
    if response is not None:
        response_status = getattr(response, "status_code", None)
        if isinstance(response_status, int):
            return response_status
    return None


def _get_error_text(error: Exception) -> str:
    return str(error).lower()


def is_groq_retryable_error(error: Exception) -> bool:
    """Return True for Groq errors that should fall back to another model."""
    status_code = _get_error_status_code(error)
    error_text = _get_error_text(error)

    if status_code == 429:
        return True

    retry_markers = [
        "rate limit",
        "rate_limit_exceeded",
        "temporarily unavailable",
        "server error",
        "service unavailable",
        "timeout",
        "timed out",
        "model not found",
        "does not exist",
        "permission denied",
    ]
    return any(marker in error_text for marker in retry_markers)


def is_groq_daily_quota_error(error: Exception) -> bool:
    """Return True only for Groq daily token/quota exhaustion errors."""
    error_text = _get_error_text(error)

    payloads = []
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        payloads.append(body)
    elif isinstance(body, str):
        payloads.append({"message": body})

    response = getattr(error, "response", None)
    if response is not None:
        try:
            response_payload = response.json()
            if isinstance(response_payload, dict):
                payloads.append(response_payload)
        except Exception:
            pass

    for payload in payloads:
        payload_text = str(payload).lower()
        payload_code = str(payload.get("code", "")).lower()
        payload_type = str(payload.get("type", "")).lower()

        if (
            payload_code == "rate_limit_exceeded"
            and payload_type == "tokens"
            and (
                "tokens per day" in payload_text
                or "tpd" in payload_text
            )
        ):
            return True

    return (
        "tokens per day" in error_text
        and "rate_limit_exceeded" in error_text
    )


def list_groq_models(api_key: str) -> list[str]:
    """Return the list of model IDs accessible to this API key."""
    client = Groq(api_key=api_key)
    response = client.models.list()
    return [model.id for model in response.data]


def resolve_best_groq_model(
    api_key: str,
    requested_model: str | None = None,
    fallback_models: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Pick the best accessible model using a preference-ordered candidate list."""
    requested_model = (requested_model or "").strip()
    candidates: list[str] = []

    if requested_model and requested_model.lower() != "auto":
        candidates.append(requested_model)

    if fallback_models:
        candidates.extend(fallback_models)
    elif not candidates:
        candidates.extend(DEFAULT_MODEL_PREFERENCE)
    else:
        candidates.extend([model for model in DEFAULT_MODEL_PREFERENCE if model != requested_model])

    candidates = _unique_preserve_order(candidates)

    try:
        available_models = set(list_groq_models(api_key))
    except Exception as error:
        logger.warning(
            f"⚠️ Could not list Groq models; using configured preference order: {error}"
        )
        return candidates[0], candidates

    accessible_candidates = [model for model in candidates if model in available_models]
    if accessible_candidates:
        return accessible_candidates[0], accessible_candidates

    if candidates:
        return candidates[0], candidates

    return DEFAULT_MODEL_PREFERENCE[0], DEFAULT_MODEL_PREFERENCE


class GroqLLM:
    """LLM client for fast inference."""

    def __init__(
        self,
        api_key: str,
        model: str = "auto",
        fallback_models: list[str] | None = None,
    ):
        self.api_key = api_key
        self.model, self.model_candidates = resolve_best_groq_model(
            api_key,
            requested_model=model,
            fallback_models=fallback_models,
        )
        self._clients: dict[str, Groq] = {}
        logger.info(f"🔧 Initialized Groq LLM with model: {self.model}")
        logger.info(f"🤖 Model candidates: {', '.join(self.model_candidates)}")

    def _get_client(self, model: str) -> Groq:
        if model not in self._clients:
            self._clients[model] = Groq(api_key=self.api_key)
        return self._clients[model]

    def invoke(self, prompt: str) -> str:
        """Call the Groq API and return response."""
        logger.info("🚀 Calling Groq API")
        logger.debug(f"   Prompt: {prompt[:100]}...")

        last_error: Exception | None = None

        for index, model in enumerate(self.model_candidates):
            try:
                if model != self.model:
                    logger.warning(f"↪️ Switching to fallback model: {model}")

                message = self._get_client(model).chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=model,
                    max_tokens=4096,
                    temperature=0.9,
                )

                text = message.choices[0].message.content
                self.model = model
                logger.info(f"✅ Got response: {len(text)} characters")
                return text
            except Exception as error:
                last_error = error
                logger.warning(f"⚠️ Groq call failed on {model}: {error}")
                if index < len(self.model_candidates) - 1 and is_groq_retryable_error(error):
                    continue
                logger.error(f"❌ Groq API call failed: {error}", exc_info=True)
                raise

        if last_error is not None:
            raise last_error

        raise RuntimeError("Groq call failed without a captured exception")


def get_llm():
    """
    Initialize LLM using Groq API.
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

    model = os.getenv("GROQ_MODEL", "auto")
    fallback_models = _parse_model_list(os.getenv("GROQ_MODEL_FALLBACKS"))
    logger.info(f"🤖 Requested model: {model}")
    if fallback_models:
        logger.info(f"🤖 Configured fallbacks: {', '.join(fallback_models)}")

    try:
        llm = GroqLLM(api_key, model, fallback_models=fallback_models)
        logger.info("✅ Groq LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"❌ Failed to initialize Groq LLM: {e}")
        raise
