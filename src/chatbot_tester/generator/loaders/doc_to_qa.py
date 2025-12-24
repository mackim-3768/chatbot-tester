from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from ..types import Message, TestSample
from ..utils import gen_id_from_messages


class DocToQALoader:
    """
    Loads text from a document file and generates Q&A pairs using an LLM.
    """

    def __init__(self, model: str = "gpt-4-turbo", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required for DocToQALoader")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def load(self, file_path: Path, count: int = 10, language: str = "en") -> List[TestSample]:
        """
        Reads file content and generates `count` Q&A pairs.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found")

        text = file_path.read_text(encoding="utf-8")
        # Truncate text if too long (simple approach for now)
        # 100k chars is a rough safe limit for GPT-4-turbo context (128k tokens) but let's be safe
        if len(text) > 50000:
            text = text[:50000] + "...(truncated)"

        return self._generate_qa(text, count, language, file_path.name)

    def _generate_qa(self, text: str, count: int, language: str, source_name: str) -> List[TestSample]:
        prompt = (
            f"Generate {count} high-quality Q&A pairs based on the text below.\n"
            f"Language: {language}\n"
            "The questions should be what a user might ask about this document.\n"
            "The answers should be correct based on the text.\n"
            "Output strictly a JSON object with a key 'pairs' containing a list of objects, "
            "where each object has 'question' and 'answer' keys.\n\n"
            "--- TEXT BEGIN ---\n"
            f"{text}\n"
            "--- TEXT END ---"
        )

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Q&A generator assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content or "{}"
            data = json.loads(content)
            pairs = data.get("pairs", [])

            samples = []
            for p in pairs:
                q = p.get("question")
                a = p.get("answer")
                if not q or not a:
                    continue

                msgs = [Message(role="user", content=q)]
                sample_id = gen_id_from_messages([m.to_dict() for m in msgs])

                samples.append(TestSample(
                    id=sample_id,
                    messages=msgs,
                    expected=a,
                    tags=["doc_generated", language],
                    metadata={"source_file": source_name}
                ))
            return samples

        except Exception:
            return []
