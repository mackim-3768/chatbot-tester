from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from lm_eval_so.evaluator.config import EvaluatorConfig, load_config
from lm_eval_so.evaluator.domain import (
    DatasetMetadata,
    RunRecord,
    TestSampleRecord,
    dataset_metadata_from_dict,
    run_record_from_dict,
    test_sample_from_dict,
)
from lm_eval_so.evaluator.metrics import register_default_metrics
from lm_eval_so.evaluator.orchestrator import EvaluationOrchestrator
from lm_eval_so.evaluator.registry import metric_registry
from lm_eval_so.evaluator.report.json_reporter import JsonReporter
from lm_eval_so.evaluator.report.markdown_reporter import MarkdownReporter


EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = EXAMPLE_ROOT / "output"
DATASET_DIR = OUTPUT_ROOT / "datasets" / "ces_llm_v1"
RUN_OUTPUT_DIR = OUTPUT_ROOT / "runs" / "adb_cli"
EVAL_CONFIG_PATH = EXAMPLE_ROOT / "evaluate" / "eval_config.json"
REPORT_DIR = OUTPUT_ROOT / "reports" / "adb_cli"


def _load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def main() -> None:
    dataset_path = DATASET_DIR / "test.jsonl"
    metadata_path = DATASET_DIR / "metadata.json"
    runs_path = RUN_OUTPUT_DIR / "run_results.jsonl"

    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")
    if not metadata_path.exists():
        raise SystemExit(f"Metadata not found: {metadata_path}")
    if not runs_path.exists():
        raise SystemExit(f"Run results not found: {runs_path}")

    config: EvaluatorConfig = load_config(path=EVAL_CONFIG_PATH)
    register_default_metrics(metric_registry)

    with metadata_path.open("r", encoding="utf-8") as f:
        metadata_raw = json.load(f)
    dataset_meta: DatasetMetadata = dataset_metadata_from_dict(metadata_raw)

    samples: List[TestSampleRecord] = [
        test_sample_from_dict(obj) for obj in _load_jsonl(dataset_path)
    ]
    runs: List[RunRecord] = [run_record_from_dict(obj) for obj in _load_jsonl(runs_path)]

    orchestrator = EvaluationOrchestrator(config=config)
    result = orchestrator.evaluate(samples=samples, runs=runs, dataset=dataset_meta)

    created_paths: List[Path] = []
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    created_paths.extend(JsonReporter().write(result, REPORT_DIR))
    created_paths.extend(MarkdownReporter().write(result, REPORT_DIR))

    for p in created_paths:
        print(str(p))


if __name__ == "__main__":  # pragma: no cover
    main()
