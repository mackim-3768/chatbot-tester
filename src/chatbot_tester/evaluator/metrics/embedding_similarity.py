from __future__ import annotations

import os
from typing import Any, Mapping

import numpy as np
from openai import OpenAI

from ..domain import EvalScore, RunRecord, TestSampleRecord
from .base import Metric


class EmbeddingSimilarityMetric(Metric):
    """
    Embedding Similarity Metric.

    Computes the cosine similarity between the embeddings of the expected answer
    and the actual response using OpenAI's embedding API.

    Parameters (via config):

    - model: str (default "text-embedding-3-small")
    - api_key: str (optional)
    - base_url: str (optional)
    """

    requires_reference: bool = True

    def __init__(self, *, name: str, parameters: Mapping[str, Any] | None = None) -> None:
        super().__init__(name=name, parameters=parameters)
        p = self.parameters
        self.model = str(p.get("model", "text-embedding-3-small"))
        self.api_key = p.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = p.get("base_url") or os.getenv("OPENAI_BASE_URL")
        self._client = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required for EmbeddingSimilarityMetric")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def _get_embedding(self, text: str) -> list[float]:
        text = text.replace("\n", " ")  # recommended for some models
        if not text.strip():
            return []

        client = self._get_client()
        resp = client.embeddings.create(input=[text], model=self.model)
        return resp.data[0].embedding

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        expected_text = str(sample.expected) if sample.expected else ""
        actual_text = run.response_text or ""

        if not expected_text:
            return self.make_score(
                sample,
                value=0.0,
                detail={"skipped": True, "reason": "no_expected_text"}
            )

        if not actual_text:
             return self.make_score(
                sample,
                value=0.0,
                detail={"skipped": False, "reason": "empty_response"}
            )

        try:
            emb_expected = self._get_embedding(expected_text)
            emb_actual = self._get_embedding(actual_text)

            if not emb_expected or not emb_actual:
                 return self.make_score(sample, value=0.0, detail={"error": "empty_embedding"})

            # Calculate cosine similarity
            # dot(a, b) / (norm(a) * norm(b))
            vec_a = np.array(emb_expected)
            vec_b = np.array(emb_actual)

            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)

            if norm_a == 0 or norm_b == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

            # Ensure within 0-1
            similarity = max(0.0, min(1.0, similarity))

            return self.make_score(
                sample,
                value=similarity,
                detail={
                    "model": self.model,
                    "expected_len": len(expected_text),
                    "actual_len": len(actual_text)
                }
            )

        except Exception as e:
            return self.make_score(
                sample,
                value=0.0,
                detail={"error": str(e), "skipped": True}
            )
