from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


def _coerce_tags(value: Optional[Iterable[str]]) -> List[str]:
    return [str(v) for v in value] if value else []


def _estimate_length(messages: Sequence[Dict[str, Any]]) -> int:
    return sum(len(str(m.get("content", ""))) for m in messages)


def infer_length_bucket(messages: Sequence[Dict[str, Any]]) -> str:
    length = _estimate_length(messages)
    if length < 200:
        return "short"
    if length < 600:
        return "medium"
    return "long"


@dataclass(slots=True)
class DatasetMetadata:
    dataset_id: str
    version: str
    name: Optional[str] = None
    source: Optional[Any] = None
    created_at: Optional[str] = None
    generator_commit: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None
    counts: Optional[Dict[str, Any]] = None
    languages: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TestSampleRecord:
    id: str
    messages: List[Dict[str, Any]]
    expected: Optional[Any] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def language(self) -> Optional[str]:
        return self.metadata.get("language")

    @property
    def length_bucket(self) -> str:
        return infer_length_bucket(self.messages)


@dataclass(slots=True)
class RunRecord:
    sample_id: str
    dataset_id: Optional[str]
    backend: str
    run_config: Dict[str, Any]
    response_text: Optional[str]
    status: str
    latency_ms: Optional[float]
    trace_id: str
    attempts: int
    error: Optional[Dict[str, Any]] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvalScore:
    sample_id: str
    metric: str
    value: float
    tags: List[str]
    language: Optional[str]
    length_bucket: Optional[str]
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MetricSummary:
    metric: str
    mean: float
    std: float
    sample_count: int


@dataclass(slots=True)
class MetricBreakdown:
    metric: str
    dimension: str
    bucket: str
    mean: float
    std: float
    sample_count: int


@dataclass(slots=True)
class ErrorCase:
    sample_id: str
    status: str
    trace_id: str
    message: Optional[str]
    latency_ms: Optional[float]
    backend: Optional[str] = None


@dataclass(slots=True)
class LLMJudgeDetail:
    metric: str
    prompt_id: str
    prompt_version: str
    language: Optional[str]
    criteria: List[str]
    sample_count: int
    sample_ids: List[str]


@dataclass(slots=True)
class ExperimentMetadata:
    dataset: DatasetMetadata
    run_config: Dict[str, Any]
    evaluator_config: Dict[str, Any]


@dataclass(slots=True)
class EvaluationReport:
    experiment: ExperimentMetadata
    summaries: List[MetricSummary]
    breakdowns: List[MetricBreakdown]
    error_cases: List[ErrorCase]
    llm_judge_details: List[LLMJudgeDetail]


@dataclass(slots=True)
class EvaluationResult:
    scores: List[EvalScore]
    report: EvaluationReport


def compute_stats(values: Sequence[float]) -> Tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(mean(values)), float(pstdev(values))


__all__ = [
    "DatasetMetadata",
    "EvalScore",
    "EvaluationReport",
    "ExperimentMetadata",
    "LLMJudgeDetail",
    "MetricBreakdown",
    "MetricSummary",
    "RunRecord",
    "TestSampleRecord",
    "ErrorCase",
    "EvaluationResult",
    "compute_stats",
    "infer_length_bucket",
    "dataset_metadata_from_dict",
    "test_sample_from_dict",
    "run_record_from_dict",
]


def dataset_metadata_from_dict(data: Mapping[str, Any]) -> DatasetMetadata:
    dataset_id = str(data.get("dataset_id")) if data.get("dataset_id") else None
    version = str(data.get("version")) if data.get("version") else None
    if not dataset_id or not version:
        raise ValueError("dataset metadata must include dataset_id and version")

    return DatasetMetadata(
        dataset_id=dataset_id,
        version=version,
        name=data.get("name"),
        source=data.get("source"),
        created_at=data.get("created_at"),
        generator_commit=data.get("generator_commit"),
        filters=data.get("filters"),
        sampling=data.get("sampling"),
        counts=data.get("counts"),
        languages=data.get("languages"),
        tags=data.get("tags"),
        extra={k: v for k, v in data.items() if k not in {
            "dataset_id",
            "version",
            "name",
            "source",
            "created_at",
            "generator_commit",
            "filters",
            "sampling",
            "counts",
            "languages",
            "tags",
        }},
    )


def test_sample_from_dict(data: Mapping[str, Any]) -> TestSampleRecord:
    tags = _coerce_tags(data.get("tags"))
    metadata = dict(data.get("metadata", {}))
    messages = [dict(m) for m in data.get("messages", [])]
    return TestSampleRecord(
        id=str(data["id"]),
        messages=messages,
        expected=data.get("expected"),
        tags=tags,
        metadata=metadata,
    )


def run_record_from_dict(data: Mapping[str, Any]) -> RunRecord:
    response = data.get("response") or {}
    response_text = response.get("text") if isinstance(response, Mapping) else None
    error = data.get("error") if isinstance(data.get("error"), Mapping) else None
    return RunRecord(
        sample_id=str(data.get("sample_id")),
        dataset_id=data.get("dataset_id"),
        backend=str(data.get("backend")),
        run_config=dict(data.get("run_config", {})),
        response_text=str(response_text) if response_text is not None else None,
        status=str(data.get("status")),
        latency_ms=float(data.get("latency_ms")) if data.get("latency_ms") is not None else None,
        trace_id=str(data.get("trace_id")),
        attempts=int(data.get("attempts", 1)),
        error=error,
        raw=dict(data),
    )
