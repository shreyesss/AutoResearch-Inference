#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"

DATASET="${DATASET:?set DATASET to generated request JSONL}"
OUTPUT_DIR="${OUTPUT_DIR:?set OUTPUT_DIR}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
MODEL_NAME="${MODEL_NAME:-$SERVED_MODEL}"
MODE="${MODE:-closed}"
CONCURRENCY="${CONCURRENCY:-64}"
DURATION="${DURATION:-600}"
WARMUP_DURATION="${WARMUP_DURATION:-300}"
REQUEST_RATE="${REQUEST_RATE:-}"
AIPERF="${AIPERF:-$ROOT/.venv/bin/aiperf}"

mkdir -p "$OUTPUT_DIR"
AIPERF_DATASET="$OUTPUT_DIR/aiperf-single-turn.jsonl"
"$ROOT/.venv/bin/python" "$ROOT/testing/common/to_aiperf.py" \
  --input "$DATASET" --output "$AIPERF_DATASET"
command=(
  "$AIPERF" profile
  --model "$MODEL_NAME"
  --tokenizer "$MODEL"
  --tokenizer-revision "$MODEL_REVISION"
  --tokenizer-trust-remote-code
  --url "$BASE_URL"
  --endpoint-type chat
  --streaming
  --input-file "$AIPERF_DATASET"
  --custom-dataset-type single_turn
  --concurrency "$CONCURRENCY"
  --warmup-duration "$WARMUP_DURATION"
  --benchmark-duration "$DURATION"
  --benchmark-grace-period 300
  --export-level records
  --artifact-dir "$OUTPUT_DIR"
)

if [[ "$MODE" == open ]]; then
  command+=(--arrival-pattern poisson --request-rate "${REQUEST_RATE:?set REQUEST_RATE}")
elif [[ "$MODE" != closed ]]; then
  echo "MODE must be closed or open" >&2
  exit 2
fi

if [[ "${DRY_RUN:-0}" == 1 ]]; then
  printf '%q ' "${command[@]}"
  printf '\n'
else
  "${command[@]}"
fi
