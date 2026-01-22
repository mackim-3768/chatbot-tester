from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from typing import Iterable, List, Optional, Dict, Any, TYPE_CHECKING

from .models import DatasetInfo, RunConfig, RunResult

if TYPE_CHECKING:  # pragma: no cover
    from ..config import RunnerConfig

# ... (StorageBackend import remains)

def write_run_results(results: Iterable[RunResult], storage: StorageBackend, key: str = "run_results.jsonl") -> str:
    path = storage.save_jsonl(key, [r.to_record() for r in results])
    return path


def write_run_metadata(
    dataset: DatasetInfo,
    run_config: RunConfig,
    options: "RunnerConfig",
    results: List[RunResult],
    storage: StorageBackend,
    key: str = "run_metadata.json",
) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset.to_dict(),
        "run_config": run_config.to_dict(),
        "options": options.to_metadata_dict(),
        "summary": _build_summary(results),
    }
    path = storage.save_json(key, payload, indent=2)
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
