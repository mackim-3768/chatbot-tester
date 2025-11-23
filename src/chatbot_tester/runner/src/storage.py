from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Iterable, List, Optional, Dict, Any, TYPE_CHECKING

from .models import DatasetInfo, RunConfig, RunResult

if TYPE_CHECKING:  # pragma: no cover
    from .runner_core import RunnerOptions


def write_run_results(results: Iterable[RunResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run_results.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for result in results:
            json.dump(result.to_record(), f, ensure_ascii=False)
            f.write("\n")
    return path


def write_run_metadata(
    dataset: DatasetInfo,
    run_config: RunConfig,
    options: "RunnerOptions",
    results: List[RunResult],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "run_metadata.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset.to_dict(),
        "run_config": run_config.to_dict(),
        "options": options.to_metadata_dict(),
        "summary": _build_summary(results),
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def _build_summary(results: List[RunResult]) -> Dict[str, Any]:
    status_counter = Counter(r.status.value for r in results)
    latencies = [r.latency_ms for r in results if r.latency_ms is not None]
    tokens = [
        r.response.usage.total_tokens
        for r in results
        if r.response and r.response.usage and r.response.usage.total_tokens is not None
    ]

    summary: Dict[str, Any] = {
        "total": len(results),
        "status_counts": dict(status_counter),
    }
    if latencies:
        summary["latency_ms"] = {
            "min": min(latencies),
            "max": max(latencies),
            "avg": mean(latencies),
        }
    if tokens:
        summary["total_tokens"] = {
            "min": min(tokens),
            "max": max(tokens),
            "avg": mean(tokens),
        }
    return summary


__all__ = ["write_run_results", "write_run_metadata"]
