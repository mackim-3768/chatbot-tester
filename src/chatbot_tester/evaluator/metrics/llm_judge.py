from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Optional

from .base import Metric
from ..domain import EvalScore, LLMJudgeDetail, RunRecord, TestSampleRecord


def _get_nested(mapping: Mapping[str, Any], path: str) -> Optional[Any]:
    cur: Any = mapping
    for part in path.split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur[part]
    return cur


class LLMJudgeMetric(Metric):
    """Metric that consumes pre-computed LLM-judge scores from RunRecord.raw.

    이 구현은 **실제 LLM 호출을 하지 않고**, Runner 또는 외부 파이프라인에서
    이미 계산해 둔 점수를 소비하는 역할만 담당한다. 점수는 `score_key`로
    지정된 경로에서 읽어오며, `max_score`로 0~1 범위로 정규화한다.

    Parameters (via config):

    - prompt_id: str
    - prompt_version: str
    - criteria: list[str]
    - max_score: float (default 5.0)
    - score_key: str (default "llm_judge.score")
    """

    requires_reference: bool = False

    def __init__(self, *, name: str, parameters: Mapping[str, Any] | None = None) -> None:
        super().__init__(name=name, parameters=parameters)
        p = self.parameters
        self.prompt_id: str = str(p.get("prompt_id", ""))
        self.prompt_version: str = str(p.get("prompt_version", ""))
        raw_criteria = p.get("criteria") or []
        self.criteria: List[str] = [str(c) for c in raw_criteria]
        self.max_score: float = float(p.get("max_score", 5.0))
        self.score_key: str = str(p.get("score_key", "llm_judge.score"))

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        raw_value = _get_nested(run.raw, self.score_key)
        if raw_value is None:
            return self.make_score(
                sample,
                value=0.0,
                detail={
                    "skipped": True,
                    "reason": "missing_llm_judge_score",
                    "score_key": self.score_key,
                },
            )

        try:
            numeric = float(raw_value)
        except (TypeError, ValueError):
            return self.make_score(
                sample,
                value=0.0,
                detail={
                    "skipped": True,
                    "reason": "non_numeric_llm_judge_score",
                    "score_key": self.score_key,
                },
            )

        if self.max_score > 0:
            value = numeric / self.max_score
        else:
            value = numeric

        detail = {
            "raw_score": numeric,
            "max_score": self.max_score,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "criteria": list(self.criteria),
        }
        return self.make_score(sample, value=value, detail=detail)

    def build_llm_judge_details(self, scores: Iterable[EvalScore]) -> List[LLMJudgeDetail]:
        scores = list(scores)
        if not scores:
            return []

        sample_ids = [s.sample_id for s in scores]
        languages = {s.language for s in scores if s.language}
        language = next(iter(languages)) if len(languages) == 1 else None

        return [
            LLMJudgeDetail(
                metric=self.name,
                prompt_id=self.prompt_id,
                prompt_version=self.prompt_version,
                language=language,
                criteria=list(self.criteria),
                sample_count=len(sample_ids),
                sample_ids=sample_ids,
            )
        ]


__all__ = ["LLMJudgeMetric"]
