from __future__ import annotations

from typing import TYPE_CHECKING

from .base import Metric
from .exact_match import ExactMatchMetric
from .keyword import KeywordCoverageMetric
from .llm_judge import LLMJudgeMetric
from .semantic_similarity import SemanticSimilarityMetric

if TYPE_CHECKING:  # pragma: no cover
    from ..registry import MetricRegistry


def register_default_metrics(registry: "MetricRegistry") -> None:
    """Register built-in metric implementations into the given registry.

    This helper is idempotent: if a metric name is already registered it will
    simply be skipped. This allows callers (CLI/tests) to call it freely.
    """

    from ..registry import MetricRegistry as _MetricRegistry  # type: ignore

    if not isinstance(registry, _MetricRegistry):  # defensive, but cheap
        return

    def _safe_register(name: str, factory):
        try:
            registry.register(name, factory)
        except ValueError:
            # Ignore duplicate registrations so this function is idempotent.
            return

    _safe_register("exact_match", lambda cfg: ExactMatchMetric(**cfg))
    _safe_register("keyword_coverage", lambda cfg: KeywordCoverageMetric(**cfg))
    _safe_register("llm_judge", lambda cfg: LLMJudgeMetric(**cfg))
    _safe_register("semantic_similarity", lambda cfg: SemanticSimilarityMetric(**cfg))


__all__ = [
    "Metric",
    "ExactMatchMetric",
    "KeywordCoverageMetric",
    "LLMJudgeMetric",
    "SemanticSimilarityMetric",
    "register_default_metrics",
]
