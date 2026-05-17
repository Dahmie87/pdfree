import os
from dotenv import load_dotenv  # type: ignore

from models.llm import (
    DEFAULT_MODEL_PREFERENCE,
    list_groq_models,
    resolve_best_groq_model,
)


def main() -> None:
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    requested_model = os.getenv("GROQ_MODEL", "auto")
    fallback_models = os.getenv("GROQ_MODEL_FALLBACKS", "")
    fallback_list = [model.strip() for model in fallback_models.split(",") if model.strip()]

    available_models = list_groq_models(api_key)
    selected_model, candidates = resolve_best_groq_model(
        api_key,
        requested_model=requested_model,
        fallback_models=fallback_list,
    )

    print("Available Groq models:")
    for model in available_models:
        print(f"- {model}")

    print()
    print("Preferred candidates:")
    for model in candidates or DEFAULT_MODEL_PREFERENCE:
        print(f"- {model}")

    print()
    print(f"Selected model: {selected_model}")


if __name__ == "__main__":
    main()
