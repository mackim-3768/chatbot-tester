from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

from lm_eval_so.core.logging import configure_logging

from .config import EvaluatorConfig, load_config
from .domain import (
    DatasetMetadata,
    RunRecord,
    TestSampleRecord,
    dataset_metadata_from_dict,
    run_record_from_dict,
    test_sample_from_dict,
)
from .metrics import register_default_metrics
from .orchestrator import EvaluationOrchestrator
from .registry import metric_registry
from .plugin import PluginLoader
from .report.html_reporter import HtmlReporter
from .report.json_reporter import JsonReporter
from .report.markdown_reporter import MarkdownReporter
from . import __version__


def _load_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lm-eval-evaluator", description="Chatbot Evaluator")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--dataset", required=True, help="Path to dataset JSONL (canonical TestSample records)")
    p.add_argument("--metadata", required=True, help="Path to dataset metadata.json")
    p.add_argument("--runs", required=True, help="Path to RunResult records JSONL")
    p.add_argument("--config", required=True, help="Path to evaluator config (JSON/YAML)")
    p.add_argument("--output", required=True, help="Directory to write reports into")
    p.add_argument("--plugin", action="append", default=[], help="Path to python file or module name containing custom metrics")
    p.add_argument("--no-markdown", action="store_true", help="Skip Markdown report generation")
    p.add_argument("--no-json", action="store_true", help="Skip JSON summary/scores generation")
    p.add_argument("--html", action="store_true", help="Generate HTML report")
    return p


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    configure_logging(level=logging.INFO)

    dataset_path = Path(args.dataset)
    metadata_path = Path(args.metadata)
    runs_path = Path(args.runs)
    config_path = Path(args.config)
    output_dir = Path(args.output)

    # Load config and register built-in metrics.
    config: EvaluatorConfig = load_config(path=config_path)
    register_default_metrics(metric_registry)

    # Load plugins if any.
    if args.plugin:
        loader = PluginLoader(registry=metric_registry)
        loader.load_plugins(args.plugin)

    # Load dataset and metadata.
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
    if not args.no_json:
        created_paths.extend(JsonReporter().write(result, output_dir))
    if not args.no_markdown:
        created_paths.extend(MarkdownReporter().write(result, output_dir))
    if args.html:
        created_paths.extend(HtmlReporter().write(result, output_dir))

    for p in created_paths:
        print(p)


if __name__ == "__main__":  # pragma: no cover
    main()
