from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Sequence

from ..domain import EvalScore, LLMJudgeDetail, RunRecord, TestSampleRecord


class Metric(ABC):
    """Base metric abstraction.

    Concrete metrics should override :meth:`score` to return an :class:`EvalScore`
    constructed via :meth:`make_score`. Metrics may also opt into LLM-judge style
    reporting by overriding :meth:`build_llm_judge_details`.
    """

    requires_reference: bool = False

    def __init__(self, *, name: str, parameters: Dict[str, Any] | None = None) -> None:
        self.name = name
        self.parameters = dict(parameters or {})

    @abstractmethod
    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        raise NotImplementedError

    def make_score(self, sample: TestSampleRecord, *, value: float, detail: Dict[str, Any] | None = None) -> EvalScore:
        return EvalScore(
            sample_id=sample.id,
            metric=self.name,
            value=float(value),
            tags=list(sample.tags),
            language=sample.language,
            length_bucket=sample.length_bucket,
            detail=detail or {},
        )

    def build_llm_judge_details(self, scores: Sequence[EvalScore]) -> List[LLMJudgeDetail]:
        return []


__all__ = ["Metric"]
