#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "[custom_metric] ERROR: OPENAI_API_KEY is not set." >&2
  exit 1
fi

DATA_DIR="${ROOT_DIR}/example/custom_metric/data"
DATASET_ROOT="${ROOT_DIR}/example/custom_metric/dataset"
RUNS_DIR="${ROOT_DIR}/example/custom_metric/runs"
REPORTS_DIR="${ROOT_DIR}/example/custom_metric/reports"
PLUGIN_PATH="${ROOT_DIR}/example/custom_metric/plugins/keyword_metric.py"

mkdir -p "${DATASET_ROOT}" "${RUNS_DIR}" "${REPORTS_DIR}"

echo "[custom_metric] 1/3: Generating canonical dataset..."
python -m lm_eval_so.generator.cli \
  --input "${DATA_DIR}/toy_dataset.jsonl" \
  --input-format jsonl \
  --output-dir "${DATASET_ROOT}" \
  --dataset-id custom_metric_demo \
  --name "Custom Metric Demo" \
  --version v1 \
  --id-col id \
  --tags-col tags \
  --language-col lang

DATASET_DIR="${DATASET_ROOT}/custom_metric_demo_v1"

echo "[custom_metric] 2/3: Running Runner..."
python -m lm_eval_so.runner.cli \
  --dataset "${DATASET_DIR}" \
  --backend openai \
  --model gpt-4o-mini \
  --output-dir "${RUNS_DIR}"

echo "[custom_metric] 3/3: Evaluating with Custom Metric Plugin..."
python -m lm_eval_so.evaluator.cli \
  --dataset "${DATASET_DIR}/test.jsonl" \
  --metadata "${DATASET_DIR}/metadata.json" \
  --runs "${RUNS_DIR}/run_results.jsonl" \
  --config "${ROOT_DIR}/example/custom_metric/config/eval_config.yaml" \
  --plugin "${PLUGIN_PATH}" \
  --output "${REPORTS_DIR}"

echo "[custom_metric] Done. Check reports in example/custom_metric/reports"
