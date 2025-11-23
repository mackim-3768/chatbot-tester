from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Tuple

from .config import EvaluatorConfig
from .domain import (
    DatasetMetadata,
    ErrorCase,
    EvalScore,
    EvaluationReport,
    EvaluationResult,
    ExperimentMetadata,
    LLMJudgeDetail,
    MetricBreakdown,
    MetricSummary,
    RunRecord,
    TestSampleRecord,
    compute_stats,
)
from .registry import MetricRegistry, metric_registry


class EvaluationOrchestrator:
    """Run configured metrics over samples and run results.

    This class is intentionally lightweight: it joins `TestSampleRecord` and
    `RunRecord` by `sample_id`, delegates metric computation to Metric plugins,
    and aggregates scores into an `EvaluationResult` containing both
    per-sample scores and an `EvaluationReport` summary.
    """

    def __init__(self, config: EvaluatorConfig, registry: MetricRegistry | None = None) -> None:
        self._config = config
        self._registry = registry or metric_registry

    def evaluate(
        self,
        samples: Iterable[TestSampleRecord],
        runs: Iterable[RunRecord],
        dataset: DatasetMetadata,
    ) -> EvaluationResult:
        sample_map: Dict[str, TestSampleRecord] = {s.id: s for s in samples}
        run_map: Dict[str, RunRecord] = {r.sample_id: r for r in runs}

        scores: List[EvalScore] = []
        summaries: List[MetricSummary] = []
        breakdowns: List[MetricBreakdown] = []
        error_cases: List[ErrorCase] = []
        llm_details: List[LLMJudgeDetail] = []

        # Collect error cases (non-ok statuses are treated as execution errors).
        for run in run_map.values():
            if run.status != "ok":
                message = None
                if run.error is not None:
                    message = str(run.error.get("message", ""))
                error_cases.append(
                    ErrorCase(
                        sample_id=run.sample_id,
                        status=run.status,
                        trace_id=run.trace_id,
                        message=message,
                        latency_ms=run.latency_ms,
                        backend=run.backend,
                    )
                )

        # Pairs available for metric evaluation (only successful runs).
        eval_pairs: List[Tuple[TestSampleRecord, RunRecord]] = [
            (sample_map[sid], run)
            for sid, run in run_map.items()
            if sid in sample_map and run.status == "ok"
        ]

        if not eval_pairs:
            experiment = ExperimentMetadata(
                dataset=dataset,
                run_config=self._config.run_config,
                evaluator_config=self._config.model_dump(),
            )
            report = EvaluationReport(
                experiment=experiment,
                summaries=[],
                breakdowns=[],
                error_cases=error_cases,
                llm_judge_details=[],
            )
            return EvaluationResult(scores=[], report=report)

        # Run each configured metric.
        for metric_cfg in self._config.metrics:
            metric = self._registry.create(
                metric_cfg.type,
                name=metric_cfg.resolved_name,
                parameters=metric_cfg.parameters,
            )

            metric_scores: List[EvalScore] = []
            for sample, run in eval_pairs:
                try:
                    score = metric.score(sample, run)
                except Exception:
                    # Metric implementations are expected to be robust, but we
                    # isolate failures so that a single metric does not break
                    # the whole evaluation.
                    continue
                metric_scores.append(score)
                scores.append(score)

            if not metric_scores:
                continue

            values = [s.value for s in metric_scores]
            mean_value, std_value = compute_stats(values)
            summaries.append(
                MetricSummary(
                    metric=metric.name,
                    mean=mean_value,
                    std=std_value,
                    sample_count=len(metric_scores),
                )
            )

            # Build breakdowns according to configured dimensions.
            self._build_breakdowns(metric.name, metric_scores, breakdowns)

            # Optional LLM-judge details.
            llm_details.extend(metric.build_llm_judge_details(metric_scores))

        experiment = ExperimentMetadata(
            dataset=dataset,
            run_config=self._config.run_config,
            evaluator_config=self._config.model_dump(),
        )
        report = EvaluationReport(
            experiment=experiment,
            summaries=summaries,
            breakdowns=breakdowns,
            error_cases=error_cases,
            llm_judge_details=llm_details,
        )
        return EvaluationResult(scores=scores, report=report)

    def _build_breakdowns(
        self,
        metric_name: str,
        scores: Sequence[EvalScore],
        out: List[MetricBreakdown],
    ) -> None:
        dimensions = set(self._config.breakdown.dimensions)

        if "tag" in dimensions:
            tag_buckets: Dict[str, List[float]] = defaultdict(list)
            for s in scores:
                for tag in s.tags:
                    tag_buckets[tag].append(s.value)
            for tag, values in tag_buckets.items():
                mean_value, std_value = compute_stats(values)
                out.append(
                    MetricBreakdown(
                        metric=metric_name,
                        dimension="tag",
                        bucket=tag,
                        mean=mean_value,
                        std=std_value,
                        sample_count=len(values),
                    )
                )

        if "language" in dimensions:
            lang_buckets: Dict[str, List[float]] = defaultdict(list)
            for s in scores:
                key = s.language or "unknown"
                lang_buckets[key].append(s.value)
            for lang, values in lang_buckets.items():
                mean_value, std_value = compute_stats(values)
                out.append(
                    MetricBreakdown(
                        metric=metric_name,
                        dimension="language",
                        bucket=lang,
                        mean=mean_value,
                        std=std_value,
                        sample_count=len(values),
                    )
                )

        if "length" in dimensions:
            len_buckets: Dict[str, List[float]] = defaultdict(list)
            for s in scores:
                key = s.length_bucket or "unknown"
                len_buckets[key].append(s.value)
            for bucket, values in len_buckets.items():
                mean_value, std_value = compute_stats(values)
                out.append(
                    MetricBreakdown(
                        metric=metric_name,
                        dimension="length",
                        bucket=bucket,
                        mean=mean_value,
                        std=std_value,
                        sample_count=len(values),
                    )
                )


__all__ = ["EvaluationOrchestrator"]
