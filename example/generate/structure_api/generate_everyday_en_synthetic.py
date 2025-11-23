from __future__ import annotations

import os
from pathlib import Path

from chatbot_tester.generator.synthetic import CacheStrategy, generate_structured_synthetic_dataset


DEFAULT_TOPIC_PROMPT = (
    "Create everyday life chatbot test queries in English. Cover situations such as shopping, "
    "commuting, dining out, healthcare, personal finance, scheduling, and casual conversations."
)


def _parse_cache_strategy(value: str | None) -> CacheStrategy:
    if not value:
        return CacheStrategy.DEFAULT
    try:
        return CacheStrategy[value.strip().upper()]
    except KeyError as exc:  # pragma: no cover - defensive path for example script
        valid = ", ".join(CacheStrategy.__members__.keys())
        raise ValueError(f"Unsupported cache strategy: {value!r}. Choose one of: {valid}") from exc


def main() -> None:
    here = Path(__file__).resolve().parent
    output_dir = here / "outputs"

    dataset_id = os.getenv("EVERYDAY_DATASET_ID", "everyday_en_openai_structure")
    dataset_name = os.getenv(
        "EVERYDAY_DATASET_NAME",
        "Everyday Life English Conversations (OpenAI Structure)",
    )
    dataset_version = os.getenv("EVERYDAY_DATASET_VERSION", "v1")

    topic_prompt = os.getenv("EVERYDAY_TOPIC_PROMPT", DEFAULT_TOPIC_PROMPT).strip()
    language_code = os.getenv("EVERYDAY_LANGUAGE_CODE", "en").strip() or "en"
    sample_count = int(os.getenv("EVERYDAY_SAMPLE_COUNT", "50"))

    seed_env = os.getenv("EVERYDAY_SEED")
    seed = int(seed_env) if seed_env else None

    cache_strategy = _parse_cache_strategy(os.getenv("EVERYDAY_CACHE_STRATEGY"))

    out_root = generate_structured_synthetic_dataset(
        dataset_id=dataset_id,
        name=dataset_name,
        version=dataset_version,
        topic_prompt=topic_prompt,
        language_code=language_code,
        sample_count=sample_count,
        output_dir=output_dir,
        openai_model=os.getenv("OPENAI_MODEL"),
        cache_strategy=cache_strategy,
        seed=seed,
    )

    print(f"Dataset generated under: {out_root}")


if __name__ == "__main__":
    main()
