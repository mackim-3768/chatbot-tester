from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import logging

from chatbot_tester.runner import RunnerOptions, backend_registry, load_dataset, run_job
from chatbot_tester.runner.models import RunConfig
from chatbot_tester.runner.storage import write_run_metadata, write_run_results


# 기본 경로 설정 (필요하면 파일 상단에서 수정)
EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = EXAMPLE_ROOT / "output"
DATASET_DIR = OUTPUT_ROOT / "datasets" / "ces_llm_v1"
RUN_OUTPUT_DIR = OUTPUT_ROOT / "runs" / "adb_cli"

BACKEND_NAME = "adb-cli-llama-freeform"
MODEL_NAME = "LLama-1B"  # 디바이스 상에서 사용 중인 모델 식별자

# llama-1b
BACKEND_OPTIONS: Dict[str, Any] = {
    "adb_path": "adb",
    "device_id": "000008f62f8747d3",
    "binary": "export LD_LIBRARY_PATH=/data/local/tmp/CPU_GPU_LLAMA && /data/local/tmp/CPU_GPU_LLAMA/llama-cli",
    "binary_args": "-m /data/local/tmp/CPU_GPU_LLAMA/llama-1b.gguf -ngl 99 --output-buffer-size 10",
}

# llama-3b
# BACKEND_OPTIONS: Dict[str, Any] = {
#     "adb_path": "adb",
#     "device_id": "000008f62f8747d3",
#     "binary": "export LD_LIBRARY_PATH=/data/local/tmp/CPU_GPU_LLAMA && /data/local/tmp/CPU_GPU_LLAMA/llama-cli",
#     "binary_args": "-m /data/local/tmp/CPU_GPU_LLAMA/llama-1b.gguf -ngl 99 --output-buffer-size 10",
# }

# Mamba
# BACKEND_OPTIONS: Dict[str, Any] = {
#     "adb_path": "adb",
#     "device_id": "000008f62f8747d3",
#     "binary": "export LD_LIBRARY_PATH=/data/local/tmp/CPU_GPU_LLAMA && /data/local/tmp/CPU_GPU_LLAMA/llama-cli",
#     "binary_args": "-m /data/local/tmp/CPU_GPU_LLAMA/llama-1b.gguf -ngl 99 --output-buffer-size 10",
# }

# Llama-8b
# BACKEND_OPTIONS: Dict[str, Any] = {
#     "adb_path": "adb",
#     "device_id": "000008f62f8747d3",
#     "binary": "export LD_LIBRARY_PATH=/data/local/tmp/CPU_GPU_LLAMA && /data/local/tmp/CPU_GPU_LLAMA/llama-cli",
#     "binary_args": "-m /data/local/tmp/CPU_GPU_LLAMA/llama-1b.gguf -ngl 99 --output-buffer-size 10",
# }


# RunConfig.parameters: 러너에게 전달할 추가 파라미터(온도, 토큰 길이 등)
RUN_PARAMETERS: Dict[str, Any] = {}


def main() -> None:
    dataset_path = DATASET_DIR / "test.jsonl"
    metadata_path = DATASET_DIR / "metadata.json"

    if not dataset_path.exists():
        raise SystemExit(f"Dataset not found: {dataset_path}")
    if not metadata_path.exists():
        raise SystemExit(f"Metadata not found: {metadata_path}")

    dataset_info, samples = load_dataset(dataset_path, metadata_path)

    run_config = RunConfig(
        backend=BACKEND_NAME,
        model=MODEL_NAME,
        parameters=RUN_PARAMETERS,
        backend_options=BACKEND_OPTIONS,
    )

    options = RunnerOptions(
        max_concurrency=1,
        timeout_seconds=120.0,
        max_retries=1,
        rate_limit_per_second=None,
        trace_prefix="ces_adb",
        output_dir=RUN_OUTPUT_DIR,
    )

    if BACKEND_NAME not in backend_registry.names():
        available = ", ".join(sorted(backend_registry.names()))
        raise SystemExit(f"Unknown backend '{BACKEND_NAME}'. Available: {available}")

    RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("chatbot_tester.runner")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger.setLevel(logging.INFO)

    results = run_job(
        dataset=dataset_info,
        samples=samples,
        backend_name=BACKEND_NAME,
        run_config=run_config,
        options=options,
        logger=logger,
    )

    results_path = write_run_results(results, RUN_OUTPUT_DIR)
    metadata_out_path = write_run_metadata(dataset_info, run_config, options, results, RUN_OUTPUT_DIR)

    print(str(RUN_OUTPUT_DIR))
    print(str(results_path))
    print(str(metadata_out_path))


if __name__ == "__main__":  # pragma: no cover
    main()
