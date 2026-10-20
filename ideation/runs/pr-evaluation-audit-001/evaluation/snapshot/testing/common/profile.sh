#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"

MODE="${1:-nsys}"
shift || true
BASELINE_DIR="${BASELINE_DIR:?set BASELINE_DIR to the completed clean suite}"
DATASET="${DATASET:?set DATASET to a generated workload JSONL from that suite}"
BASE_URL="${BASE_URL:-http://127.0.0.1:$PORT/v1}"
CONCURRENCY="${CONCURRENCY:-16}"
DURATION="${DURATION:-20}"
MAX_REQUESTS="${MAX_REQUESTS:-0}"
export BASELINE_DIR BASE_URL DURATION

load_command=(
  "$ROOT/.venv/bin/python"
  "$ROOT/testing/common/loadgen.py"
  --dataset "$DATASET"
  --base-url "$BASE_URL"
  --model "$SERVED_MODEL"
  --mode closed
  --concurrency "$CONCURRENCY"
  --duration "$DURATION"
  --max-requests "$MAX_REQUESTS"
  --output-dir "$BASELINE_DIR/profiling/load-$MODE-$(date +%Y%m%d-%H%M%S)"
)

case "$MODE" in
  nsys)
    exec "$ROOT/testing/profiling/nsys_capture.sh" -- "${load_command[@]}"
    ;;
  torch)
    exec "$ROOT/testing/profiling/torch_profile.sh" -- "${load_command[@]}"
    ;;
  ncu)
    if (($# == 0)); then
      echo "For ncu, pass an isolated microbenchmark command after ncu." >&2
      exit 2
    fi
    exec "$ROOT/testing/profiling/ncu_capture.sh" -- "$@"
    ;;
  *)
    echo "Usage: profile.sh nsys|torch|ncu [ncu microbenchmark command]" >&2
    exit 2
    ;;
esac
