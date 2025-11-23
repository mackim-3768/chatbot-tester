from __future__ import annotations

from typing import Any, Iterable, List, Mapping

from .base import Metric
from ..domain import EvalScore, RunRecord, TestSampleRecord


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(v) for v in value]
    return [str(value)]


class KeywordCoverageMetric(Metric):
    """Measure coverage of required keywords in the model answer.

    Parameters (via config):

    - keywords: list[str] (required)
    - case_sensitive: bool (default False)
    """

    requires_reference: bool = False

    def __init__(self, *, name: str, parameters: Mapping[str, Any] | None = None) -> None:
        super().__init__(name=name, parameters=parameters)
        p = self.parameters
        raw_keywords = _to_list(p.get("keywords"))
        self._case_sensitive: bool = bool(p.get("case_sensitive", False))
        if self._case_sensitive:
            self._keywords = raw_keywords
        else:
            self._keywords = [k.lower() for k in raw_keywords]

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        if not self._keywords:
            return self.make_score(
                sample,
                value=0.0,
                detail={"skipped": True, "reason": "no_keywords_configured"},
            )

        text = run.response_text or ""
        haystack = text if self._case_sensitive else text.lower()

        matched = 0
        for kw in self._keywords:
            if kw and kw in haystack:
                matched += 1

        total = len(self._keywords)
        value = matched / total if total else 0.0
        detail = {
            "matched": matched,
            "total_keywords": total,
        }
        return self.make_score(sample, value=value, detail=detail)


__all__ = ["KeywordCoverageMetric"]
