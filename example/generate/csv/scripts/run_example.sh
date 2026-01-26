#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)/../.."
EXAMPLE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)/.."
OUTPUT_DIR="$EXAMPLE_DIR/outputs"
DATA_FILE="$EXAMPLE_DIR/data/sample.csv"

if ! command -v gen-dataset >/dev/null 2>&1; then
  echo "gen-dataset command not found. Install generator package first: pip install -e src/lm_eval_so/generator" >&2
  exit 1
fi

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

cd "$ROOT_DIR"

gen-dataset \
  --input "$DATA_FILE" \
  --input-format csv \
  --output-dir "$OUTPUT_DIR" \
  --dataset-id support_qa \
  --name "Support QA" \
  --version v1 \
  --source '{"origin": "example_csv"}' \
  --csv-user-col user \
  --csv-expected-col expected \
  --csv-system-col system \
  --csv-tags-col tags \
  --csv-language-col lang

cd "$EXAMPLE_DIR"

echo "Generated dataset under $OUTPUT_DIR/support_qa_v1"
