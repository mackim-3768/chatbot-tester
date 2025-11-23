from __future__ import annotations

import os
import time
import json
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

from chatbot_tester.generator.types import Message, TestSample
from chatbot_tester.generator.writers import write_jsonl, build_metadata, write_metadata
from chatbot_tester.generator.schema import sample_schema
from chatbot_tester.generator.utils import ensure_dir


PROMPTS: List[Dict[str, Any]] = [
    {
        "id": "openai-001",
        "user": "제 계정 비밀번호를 잊어버렸어요. 어떻게 재설정하나요?",
        "tags": ["support", "account", "ko"],
        "lang": "ko",
    },
    {
        "id": "openai-002",
        "user": "청구서에 이상한 요금이 포함되어 있는데, 어떻게 확인할 수 있나요?",
        "tags": ["support", "billing", "ko"],
        "lang": "ko",
    },
    {
        "id": "openai-003",
        "user": "How can I export all my chat history as a file?",
        "tags": ["support", "export", "en"],
        "lang": "en",
    },
]


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def generate_samples() -> List[TestSample]:
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = "You are a helpful customer support assistant. Answer concisely and clearly."

    samples: List[TestSample] = []

    for i, p in enumerate(PROMPTS, start=1):
        user_text = str(p["user"])

        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.2,
        )

        answer = resp.choices[0].message.content or ""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_text),
        ]

        sample = TestSample(
            id=str(p.get("id") or f"openai-{i:03d}"),
            messages=messages,
            expected=answer,
            tags=p.get("tags"),
            metadata={"language": p.get("lang"), "source": "openai_example"},
        )

        samples.append(sample)

        # 간단한 rate limit 보호
        time.sleep(0.5)

    return samples


def main() -> None:
    here = Path(__file__).resolve().parent
    out_root = here / "outputs" / "openai_support_v1"
    ensure_dir(out_root)

    samples = generate_samples()
    records = [s.to_dict() for s in samples]

    # JSONL 저장
    write_jsonl(records, out_root / "test.jsonl")

    # metadata.json 생성
    meta = build_metadata(
        dataset_id="openai_support",
        name="OpenAI Support QA Example",
        version="v1",
        source={"type": "openai", "note": "example/generate/openai"},
        samples=records,
        filters={},
        sampling={"strategy": "manual_prompts", "count": len(records)},
        repo_dir=here.parents[3],
    )
    write_metadata(meta, out_root / "metadata.json")

    # schema.json 생성
    with (out_root / "schema.json").open("w", encoding="utf-8") as f:
        json.dump(sample_schema(), f, ensure_ascii=False, indent=2)

    print(f"Generated dataset under: {out_root}")


if __name__ == "__main__":
    main()
