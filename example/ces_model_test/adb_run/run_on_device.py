from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import logging

from chatbot_tester.runner import RunnerOptions, backend_registry, load_dataset, run_job
from chatbot_tester.runner.models import RunConfig
from chatbot_tester.runner.storage import write_run_metadata, write_run_results


# 기본 경로 설정 (필요하면 파일 상단에서 수정)
EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = EXAMPLE_ROOT / "datasets" / "ces_llm_v1"
RUN_OUTPUT_DIR = EXAMPLE_ROOT / "runs" / "adb_cli"

BACKEND_NAME = "adb-cli-llama-1b-freeform"
MODEL_NAME = "LLama-1B"  # 디바이스 상에서 사용 중인 모델 식별자

# ADB backend 옵션: 실제 환경에 맞게 수정 필요
BACKEND_OPTIONS: Dict[str, Any] = {
    # adb 바이너리 경로가 다르면 수정 (예: "adb.exe")
    "adb_path": "adb",
    # 대상 디바이스가 여러 대일 때 특정 디바이스를 지정하고 싶다면 설정
    "device_id": "00000a750d8747d3",
    # 디바이스 안에서 실행할 커맨드 (stdin으로 JSON, stdout으로 JSON 응답을 기대하지만, 현재는 순수 CLI 실행)
    # adb_cli_backend 는 [adb, shell, binary] 형태로 커맨드를 구성하므로,
    # binary 에 전체 셸 커맨드를 넣으면 실제로는 다음과 같은 형태가 된다:
    #   adb shell "cd /data/local/tmp/llama_1124 && LD_LIBRARY_PATH=/data/local/tmp/llama_1124:$LD_LIBRARY_PATH ./llama-cli ..."
    "binary": "export LD_LIBRARY_PATH=/data/local/tmp/CPU_GPU_LLAMA && /data/local/tmp/CPU_GPU_LLAMA/llama-cli",
    # 추가 인자가 필요하면 문자열 또는 리스트로 지정 (현재는 사용하지 않음)
    "binary_args": "-m /data/local/tmp/CPU_GPU_LLAMA/llama-1b.gguf -ngl 99 --output-buffer-size 10",
}

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
