from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

import yaml
from pydantic import BaseModel, Field, field_validator


class MetricConfig(BaseModel):
    type: str
    name: str | None = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    sample_rate: float = 1.0

    @field_validator("sample_rate")
    @classmethod
    def _validate_sample_rate(cls, value: float) -> float:
        if not 0 < float(value) <= 1:
            raise ValueError("sample_rate must be within (0, 1]")
        return float(value)

    @property
    def resolved_name(self) -> str:
        return self.name or self.type


class BreakdownConfig(BaseModel):
    dimensions: list[str] = Field(default_factory=lambda: ["tag", "language", "length"])


class ReportConfig(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["json", "markdown"])


class EvaluatorConfig(BaseModel):
    run_config: Dict[str, Any] = Field(default_factory=dict)
    metrics: list[MetricConfig] = Field(min_length=1)
    breakdown: BreakdownConfig = Field(default_factory=BreakdownConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)
    min_samples: int = 1

    @field_validator("min_samples")
    @classmethod
    def _validate_min_samples(cls, value: int) -> int:
        if value < 1:
            raise ValueError("min_samples must be >= 1")
        return value

    @field_validator("report")
    @classmethod
    def _normalize_formats(cls, value: ReportConfig) -> ReportConfig:
        value.formats = [fmt.lower() for fmt in value.formats]
        return value


def _load_mapping_from_path(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yml", ".yaml"}:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def load_config(*, path: str | Path | None = None, data: Mapping[str, Any] | None = None) -> EvaluatorConfig:
    if path is None and data is None:
        raise ValueError("Either path or data must be provided")

    payload: Mapping[str, Any]
    if path is not None:
        payload = _load_mapping_from_path(Path(path))
    else:
        payload = data or {}

    return EvaluatorConfig(**payload)


__all__ = [
    "BreakdownConfig",
    "EvaluatorConfig",
    "MetricConfig",
    "ReportConfig",
    "load_config",
]
