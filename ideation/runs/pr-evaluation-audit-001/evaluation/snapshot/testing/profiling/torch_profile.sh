#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"
# shellcheck disable=SC1091
source "$ROOT/testing/profiling/require_clean.sh"

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
CONTROL_BASE="${BASE_URL%/v1}"
CAPTURE_NAME="${CAPTURE_NAME:-torch-$(date +%Y%m%d-%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-$BASELINE_DIR/profiling/$CAPTURE_NAME}"
PROFILE_STEPS="${PROFILE_STEPS:-20}"

if (($# == 0)); then
  echo "Pass the focused load command after --." >&2
  exit 2
fi
if [[ "${1:-}" == -- ]]; then
  shift
fi

mkdir -p "$OUTPUT_DIR"
cp "$MANIFEST" "$OUTPUT_DIR/baseline-manifest.json"

payload="$(python3 -c 'import json,sys; print(json.dumps({"output_dir":"/profiles/torch","num_steps":int(sys.argv[1]),"activities":["CPU","GPU"]}))' "$PROFILE_STEPS")"
curl -fsS -X POST "$CONTROL_BASE/start_profile" \
  -H 'Content-Type: application/json' \
  -d "$payload" >"$OUTPUT_DIR/start-response.json"

"$@"

curl -fsS -X POST "$CONTROL_BASE/stop_profile" \
  -H 'Content-Type: application/json' \
  -d '{}' >"$OUTPUT_DIR/stop-response.json"

cat >"$OUTPUT_DIR/profiling.json" <<EOF
{
  "instrumentation": "pytorch-profiler",
  "capacity_publishable": false,
  "profile_steps": $PROFILE_STEPS,
  "note": "Do not run concurrently with Nsight; both use CUPTI."
}
EOF

echo "PyTorch profiler control artifacts: $OUTPUT_DIR"
