#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root (two levels up from this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "[quickstart] ERROR: OPENAI_API_KEY is not set. Please export it before running this script." >&2
  exit 1
fi

# Allow overriding the model via QUICKSTART_MODEL; default to gpt-4o-mini.
: "${QUICKSTART_MODEL:=gpt-4o-mini}"

DATASET_ROOT="${ROOT_DIR}/example/quickstart/dataset"
RUNS_DIR="${ROOT_DIR}/example/quickstart/runs/openai_${QUICKSTART_MODEL}"
REPORTS_DIR="${ROOT_DIR}/example/quickstart/reports"

mkdir -p "${DATASET_ROOT}" "${RUNS_DIR}" "${REPORTS_DIR}"

echo "[quickstart] 1/3: Generating canonical dataset..."
python -m lm_eval_so.generator.cli \
  --input "${ROOT_DIR}/example/quickstart/data/toy_support_qa.csv" \
  --input-format csv \
  --output-dir "${DATASET_ROOT}" \
  --dataset-id toy_support_qa \
  --name "Toy Support QA" \
  --version v1 \
  --csv-user-col user \
  --csv-expected-col expected \
  --csv-system-col system \
  --csv-tags-col tags \
  --csv-language-col lang \
  --sample-size 3 \
  --sample-random

DATASET_DIR="${DATASET_ROOT}/toy_support_qa_v1"

echo "[quickstart] 2/3: Running Runner against OpenAI backend..."
python -m lm_eval_so.runner.cli \
  --dataset "${DATASET_DIR}" \
  --backend openai \
  --model "${QUICKSTART_MODEL}" \
  --param temperature=0 \
  --output-dir "${RUNS_DIR}"

echo "[quickstart] 3/3: Evaluating run results..."
python -m lm_eval_so.evaluator.cli \
  --dataset "${DATASET_DIR}/test.jsonl" \
  --metadata "${DATASET_DIR}/metadata.json" \
  --runs "${RUNS_DIR}/run_results.jsonl" \
  --config "${ROOT_DIR}/example/quickstart/config/eval_toy.yaml" \
  --output "${REPORTS_DIR}"

echo "[quickstart] Done. Reports written under example/quickstart/reports"
