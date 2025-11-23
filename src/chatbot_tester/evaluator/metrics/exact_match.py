from __future__ import annotations

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


class ExactMatchMetric(Metric):
    """Exact string match between expected output and model answer.

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
            # No reference → score is undefined; we record 0.0 with a skip flag.
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

        value = 1.0 if norm_expected == norm_answer else 0.0
        detail = {
            "expected": expected_str,
            "answer": answer_raw,
            "match": bool(value),
        }
        return self.make_score(sample, value=value, detail=detail)


__all__ = ["ExactMatchMetric"]
