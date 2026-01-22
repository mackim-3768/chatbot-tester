from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

from chatbot_tester.core.backends import backend_registry
from . import RunnerConfig, load_dataset, run_job
from .models import RunConfig
from .storage import write_run_metadata, write_run_results


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="chatbot-runner", description="Chatbot Test Runner")

    # dataset
    p.add_argument("--dataset", required=True, help="Dataset JSONL path or dataset directory")
    p.add_argument("--metadata", default=None, help="Optional metadata.json path (if not in dataset dir)")

    # backend selection
    p.add_argument("--backend", required=True, help="Backend name (e.g. openai, adb-cli)")
    p.add_argument("--model", default=None, help="Model id/name for the backend")

    # run config parameters / backend options
    p.add_argument("--param", action="append", default=[], help="Run parameter key=value (can repeat)")
    p.add_argument("--backend-opt", action="append", default=[], help="Backend option key=value (can repeat)")

    # runner options
    p.add_argument("--engine", choices=["sync"], default="sync", help="Execution engine (currently only sync exposed)")
    p.add_argument("--max-concurrency", type=int, default=2)
    p.add_argument("--timeout", type=float, default=60.0, help="Per-sample timeout in seconds")
    p.add_argument("--max-retries", type=int, default=2, help="Number of retries on retryable errors")
    p.add_argument("--rate-limit", type=float, default=None, help="Max requests per second (float)")
    p.add_argument("--trace-prefix", default="run", help="Prefix for trace_id values")

    # output
    p.add_argument("--output-dir", required=True, help="Directory to store run_results.jsonl and run_metadata.json")

    # misc
    p.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    p.add_argument("--version", action="store_true", help="Show version and exit")

    return p


def _parse_kv_list(items: list[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        try:
            out[key] = json.loads(value)
        except json.JSONDecodeError:
            out[key] = value
    return out


def main(argv: list[str] | None = None) -> None:
    from . import __version__

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"chatbot_tester.runner {__version__}")
        return

    logging.basicConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO))
    logger = logging.getLogger("chatbot_tester.runner")

    dataset_path = Path(args.dataset).resolve()
    metadata_path = Path(args.metadata).resolve() if args.metadata else None
    output_dir = Path(args.output_dir).resolve()

    dataset_info, samples = load_dataset(dataset_path, metadata_path)

    params = _parse_kv_list(list(args.param or []))
    backend_opts = _parse_kv_list(list(args.backend_opt or []))

    run_config = RunConfig(
        backend=args.backend,
        model=args.model,
        parameters=params,
        backend_options=backend_opts,
    )

    options = RunnerConfig(
        max_concurrency=int(args.max_concurrency or 1),
        timeout_seconds=float(args.timeout or 60.0),
        max_retries=int(args.max_retries or 0),
        rate_limit_per_second=float(args.rate_limit) if args.rate_limit is not None else None,
        trace_prefix=str(args.trace_prefix or "run"),
        output_dir=output_dir,
    )

    if args.backend not in backend_registry.names():
        available = ", ".join(backend_registry.names())
        raise SystemExit(f"Unknown backend '{args.backend}'. Available: {available}")

    logger.info(
        "Starting run: dataset=%s backend=%s model=%s samples=%d",
        dataset_info.dataset_id or dataset_path,
        args.backend,
        args.model,
        len(samples),
    )

    from chatbot_tester.core.storage import LocalFileSystemStorage
    
    # ... (skipping logs)

    results = run_job(
        dataset=dataset_info,
        samples=samples,
        backend_name=args.backend,
        run_config=run_config,
        options=options,
        logger=logger,
    )

    storage = LocalFileSystemStorage(output_dir)
    results_path = write_run_results(results, storage)
    metadata_path = write_run_metadata(dataset_info, run_config, options, results, storage)

    logger.info("Run completed. results=%s metadata=%s", results_path, metadata_path)


if __name__ == "__main__":  # pragma: no cover
    main()
