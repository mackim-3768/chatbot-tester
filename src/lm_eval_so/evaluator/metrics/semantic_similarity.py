from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Mapping

from .base import Metric
from ..domain import EvalScore, RunRecord, TestSampleRecord


def _normalize_text(value: str, *, normalize_whitespace: bool, case_sensitive: bool) -> str:
    text = value
    if normalize_whitespace:
        text = " ".join(text.split())
    if not case_sensitive:
        text = text.lower()
    return text


class SemanticSimilarityMetric(Metric):
    """Soft string similarity between expected output and model answer.

    Parameters (via config):

    - normalize_whitespace: bool (default True)
    - case_sensitive: bool (default False)
    """

    requires_reference: bool = True

    def __init__(self, *, name: str, parameters: Mapping[str, Any] | None = None) -> None:
        super().__init__(name=name, parameters=parameters)
        p = self.parameters
        self._normalize_ws: bool = bool(p.get("normalize_whitespace", True))
        self._case_sensitive: bool = bool(p.get("case_sensitive", False))

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        expected = sample.expected
        if expected is None:
            return self.make_score(
                sample,
                value=0.0,
                detail={"skipped": True, "reason": "no_expected_reference"},
            )

        answer_raw = run.response_text or ""
        expected_str = expected if isinstance(expected, str) else str(expected)

        norm_expected = _normalize_text(
            expected_str,
            normalize_whitespace=self._normalize_ws,
            case_sensitive=self._case_sensitive,
        )
        norm_answer = _normalize_text(
            answer_raw,
            normalize_whitespace=self._normalize_ws,
            case_sensitive=self._case_sensitive,
        )

        similarity = SequenceMatcher(None, norm_expected, norm_answer).ratio()
        detail = {
            "expected": expected_str,
            "answer": answer_raw,
            "similarity": similarity,
        }
        return self.make_score(sample, value=float(similarity), detail=detail)
