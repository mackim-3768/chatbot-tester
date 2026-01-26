from __future__ import annotations

import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP, Context

# Core imports
from chatbot_tester.config import TesterConfig, RunnerConfig
from chatbot_tester.core.backends import backend_registry
from chatbot_tester.core.models import RunResult

# Runner imports
from chatbot_tester.runner import run_job, load_dataset
from chatbot_tester.runner.models import RunConfig
from chatbot_tester.runner.storage import write_run_results, write_run_metadata
from chatbot_tester.core.storage import LocalFileSystemStorage

# Generator imports
from chatbot_tester.generator.pipeline import run_pipeline, PipelineOptions

# Evaluator imports
from chatbot_tester.evaluator.config import load_config as load_eval_config
from chatbot_tester.evaluator.domain import (
    dataset_metadata_from_dict,
    run_record_from_dict,
    test_sample_from_dict,
)
from chatbot_tester.evaluator.metrics import register_default_metrics
from chatbot_tester.evaluator.registry import metric_registry
from chatbot_tester.evaluator.orchestrator import EvaluationOrchestrator
from chatbot_tester.evaluator.report.json_reporter import JsonReporter
from chatbot_tester.evaluator.report.markdown_reporter import MarkdownReporter

# Create MCP server
mcp = FastMCP("chatbot-tester")

# Logger setup
logger = logging.getLogger("chatbot_tester.mcp")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

@mcp.tool()
def list_available_backends() -> List[str]:
    """
    List all available backends registered in the chatbot-tester library.
    Use this to verify which backends (e.g., 'openai', 'adb-cli') can be used for running tests.
    """
    return backend_registry.names()

@mcp.tool()
def load_tester_config(path: str) -> Dict[str, Any]:
    """
    Load and parse a full TesterConfig from a YAML or JSON file.
    
    Args:
        path: Absolute path to the configuration file (e.g., /path/to/config.yaml).
        
    Returns:
        A dictionary representation of the loaded configuration.
    """
    try:
        config = TesterConfig.load(path)
        return config.model_dump()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def generate_dataset(
    input_path: str,
    output_dir: str,
    dataset_id: str,
    input_format: Optional[str] = None,
    sample_size: int = 0,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> str:
    """
    Generate a standardized dataset from raw input files (CSV, JSONL).
    
    Args:
        input_path: Path to the input file (e.g., raw_data.csv).
        output_dir: Directory where the generated dataset will be saved.
        dataset_id: Unique identifier for the dataset (e.g., 'customer-support-v1').
        input_format: Format of input file ('csv' or 'jsonl'). If None, inferred from extension.
        sample_size: If > 0, randomly sample this many items.
        min_len: Filter items shorter than this length.
        max_len: Filter items longer than this length.
        
    Returns:
        The path to the generated dataset directory.
    """
    opts = PipelineOptions(
        input_path=Path(input_path).resolve(),
        input_format=input_format,
        output_dir=Path(output_dir).resolve(),
        dataset_id=dataset_id,
        name=dataset_id,
        version="v1",
        source=str(input_path),
        id_col=None, # Use defaults or auto-detection
        user_col=None,
        expected_col=None,
        system_col=None,
        tags_col=None,
        tags_sep=",",
        language_col=None,
        min_len=min_len,
        max_len=max_len,
        sample_size=sample_size,
        sample_random=True,
    )
    
    try:
        result_path = run_pipeline(opts)
        return str(result_path)
    except Exception as e:
        return f"Error generating dataset: {str(e)}"

@mcp.tool()
def run_test_job(
    dataset_path: str,
    backend_name: str,
    output_dir: str,
    model_name: Optional[str] = None,
    metadata_path: Optional[str] = None,
    max_concurrency: int = 2,
    timeout_seconds: float = 60.0,
    retries: int = 2,
    trace_prefix: str = "mcp-run",
    backend_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run a chatbot testing job against a specified backend.
    
    Args:
        dataset_path: Path to the dataset JSONL file or directory.
        backend_name: Name of the backend to use (e.g., 'openai').
        output_dir: Directory to store results.
        model_name: Optional model identifier (e.g., 'gpt-4o').
        metadata_path: Path to metadata.json if not in dataset directory.
        max_concurrency: Maximum number of concurrent requests.
        timeout_seconds: Timeout per request in seconds.
        retries: Number of retries for failed requests.
        trace_prefix: Prefix for trace IDs.
        backend_options: Additional options to pass to the backend (e.g., api_key mappings).
    
    Returns:
        Summary of the run including output paths and basic stats.
    """
    d_path = Path(dataset_path).resolve()
    m_path = Path(metadata_path).resolve() if metadata_path else None
    out_dir = Path(output_dir).resolve()
    
    try:
        # Load dataset
        dataset_info, samples = load_dataset(d_path, m_path)
        
        # Configure run
        run_config = RunConfig(
            backend=backend_name,
            model=model_name,
            parameters={},
            backend_options=backend_options or {},
        )
        
        runner_opts = RunnerConfig(
            max_concurrency=max_concurrency,
            timeout_seconds=timeout_seconds,
            max_retries=retries,
            trace_prefix=trace_prefix,
            output_dir=out_dir,
        )
        
        # Run job (Synchronous for now to simplify tool interface)
        results = run_job(
            dataset=dataset_info,
            samples=samples,
            backend_name=backend_name,
            run_config=run_config,
            options=runner_opts,
            logger=logger,
        )
        
        # Save results using internal storage mechanism
        storage = LocalFileSystemStorage(out_dir)
        results_file = write_run_results(results, storage)
        metadata_file = write_run_metadata(dataset_info, run_config, runner_opts, results, storage)
        
        # Calculate basic stats
        total = len(results)
        ok = sum(1 for r in results if r.status == "ok")
        errors = total - ok
        
        return {
            "status": "success",
            "total_samples": total,
            "successful": ok,
            "errors": errors,
            "results_file": str(results_file),
            "metadata_file": str(metadata_file),
            "output_directory": str(out_dir)
        }
    except Exception as e:
        logger.exception("Run job failed")
        return {"status": "error", "message": str(e)}

@mcp.tool()
def evaluate_run(
    dataset_path: str,
    metadata_path: str,
    runs_path: str,
    config_path: str,
    output_dir: str,
) -> Dict[str, Any]:
    """
    Evaluate the results of a test run using configured metrics.
    
    Args:
        dataset_path: Path to the original dataset JSONL file.
        metadata_path: Path to the dataset metadata.json.
        runs_path: Path to the run_results.jsonl file produced by run_test_job.
        config_path: Path to the evaluator configuration (yaml/json).
        output_dir: Directory to save evaluation reports.
        
    Returns:
        A dictionary containing paths to generated reports and summary scores.
    """
    d_path = Path(dataset_path).resolve()
    m_path = Path(metadata_path).resolve()
    r_path = Path(runs_path).resolve()
    c_path = Path(config_path).resolve()
    out_dir = Path(output_dir).resolve()
    
    try:
        # Load configuration
        config = load_eval_config(path=c_path)
        register_default_metrics(metric_registry)
        
        # Load data
        with m_path.open("r", encoding="utf-8") as f:
            metadata_raw = json.load(f)
        dataset_meta = dataset_metadata_from_dict(metadata_raw)
        
        samples = []
        with d_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    samples.append(test_sample_from_dict(json.loads(line)))
                    
        runs = []
        with r_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    runs.append(run_record_from_dict(json.loads(line)))
                    
        # Orchestrate evaluation
        orchestrator = EvaluationOrchestrator(config=config)
        result = orchestrator.evaluate(samples=samples, runs=runs, dataset=dataset_meta)
        
        # Generate Reports
        files = []
        files.extend(JsonReporter().write(result, out_dir))
        files.extend(MarkdownReporter().write(result, out_dir))
        
        # Extract summary scores
        summaries = [s.model_dump() for s in result.report.summaries]
        
        return {
            "status": "success",
            "report_files": [str(p) for p in files],
            "metrics_summary": summaries
        }
        
    except Exception as e:
        logger.exception("Evaluation failed")
        return {"status": "error", "message": str(e)}

def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
