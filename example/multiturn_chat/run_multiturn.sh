#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "[multiturn] ERROR: OPENAI_API_KEY is not set." >&2
  exit 1
fi

DATA_DIR="${ROOT_DIR}/example/multiturn_chat/data"
DATASET_ROOT="${ROOT_DIR}/example/multiturn_chat/dataset"
RUNS_DIR="${ROOT_DIR}/example/multiturn_chat/runs"
REPORTS_DIR="${ROOT_DIR}/example/multiturn_chat/reports"

mkdir -p "${DATASET_ROOT}" "${RUNS_DIR}" "${REPORTS_DIR}"

echo "[multiturn] 1/3: Generating canonical dataset (JSON source)..."
# Note: The generator CLI currently handles csv/jsonl inputs.
# For complex multi-turn JSON, we might need to ensure the generator handles it correctly
# or we just use the generator to pass-through if formatted correctly.
# Here we will use a small python script to convert our custom JSON to JSONL for the generator if needed,
# but let's try using the generator with jsonl input format.

# First convert JSON list to JSONL for the generator input
python3 -c "import json; data=json.load(open('${DATA_DIR}/conversations.json')); [print(json.dumps(d)) for d in data]" > "${DATA_DIR}/conversations.jsonl"

python -m lm_eval_so.generator.cli \
  --input "${DATA_DIR}/conversations.jsonl" \
  --input-format jsonl \
  --output-dir "${DATASET_ROOT}" \
  --dataset-id multiturn_demo \
  --name "Multi-turn Demo" \
  --version v1 \
  --id-col id \
  --tags-col tags \
  --language-col lang

DATASET_DIR="${DATASET_ROOT}/multiturn_demo_v1"

echo "[multiturn] 2/3: Running Runner (OpenAI)..."
python -m lm_eval_so.runner.cli \
  --dataset "${DATASET_DIR}" \
  --backend openai \
  --model gpt-4o-mini \
  --output-dir "${RUNS_DIR}"

echo "[multiturn] 3/3: Evaluating..."
# We use a simple config for now
cat <<EOF > "${ROOT_DIR}/example/multiturn_chat/eval_config.yaml"
metrics:
  - name: length_check
    type: length
    min_tokens: 5
    max_tokens: 1000
EOF

python -m lm_eval_so.evaluator.cli \
  --dataset "${DATASET_DIR}/test.jsonl" \
  --metadata "${DATASET_DIR}/metadata.json" \
  --runs "${RUNS_DIR}/run_results.jsonl" \
  --config "${ROOT_DIR}/example/multiturn_chat/eval_config.yaml" \
  --output "${REPORTS_DIR}"

echo "[multiturn] Done."
