#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"
# shellcheck disable=SC1091
source "$ROOT/testing/profiling/require_clean.sh"

HARDWARE="${HARDWARE:?set by the hardware/engine profiling wrapper}"
ENGINE="${ENGINE:?set by the hardware/engine profiling wrapper}"
PROFILE="${PROFILE:-balanced}"
CAPTURE_NAME="${CAPTURE_NAME:-nsys-$(date +%Y%m%d-%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-$BASELINE_DIR/profiling/$CAPTURE_NAME}"
READY_TIMEOUT="${READY_TIMEOUT:-7200}"

if (($# == 0)); then
  echo "Pass the focused load command after --." >&2
  exit 2
fi
if [[ "${1:-}" == -- ]]; then
  shift
fi

serve_script="$ROOT/serving/$HARDWARE/$ENGINE/serve.sh"
if [[ ! -x "$serve_script" && ! -r "$serve_script" ]]; then
  echo "No serving script for $HARDWARE/$ENGINE" >&2
  exit 2
fi

mkdir -p "$OUTPUT_DIR"
cp "$MANIFEST" "$OUTPUT_DIR/baseline-manifest.json"
printf '%q ' "$@" >"$OUTPUT_DIR/load-command.txt"
printf '\n' >>"$OUTPUT_DIR/load-command.txt"

echo "Starting an isolated server with Nsight launch sessions."
serve_args=(--profile "$PROFILE" --nsys-output "$CAPTURE_NAME")
if [[ "$ENGINE" == tensorrt ]]; then
  serve_args+=(--stage "${TRTLLM_STAGE:-optimized}")
fi
bash "$serve_script" "${serve_args[@]}" \
  >"$OUTPUT_DIR/server.log" 2>&1 &
serve_pid=$!

cleanup() {
  if kill -0 "$serve_pid" 2>/dev/null; then
    kill "$serve_pid" 2>/dev/null || true
    wait "$serve_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

deadline=$((SECONDS + READY_TIMEOUT))
health_base="${BASE_URL:-http://127.0.0.1:$PORT}"
if [[ "$health_base" == */v1 ]]; then
  health_url="$health_base/models"
else
  health_url="${health_base%/}/v1/models"
fi
until curl -fsS "$health_url" >/dev/null 2>&1; do
  if ! kill -0 "$serve_pid" 2>/dev/null; then
    echo "Profiled server exited before readiness; see $OUTPUT_DIR/server.log" >&2
    exit 1
  fi
  if ((SECONDS >= deadline)); then
    echo "Profiled server readiness timeout" >&2
    exit 1
  fi
  sleep 5
done

if [[ "$ENGINE" == tensorrt ]]; then
  mapfile -t containers < <(
    docker ps --format '{{.Names}}' |
      awk -v name="dsv41-b200-tensorrt-$PROFILE" '$0==name'
  )
else
  mapfile -t containers < <(
    docker ps --format '{{.Names}}' |
      awk -v prefix="dsv41-$HARDWARE-$ENGINE-$PROFILE-" 'index($0,prefix)==1'
  )
fi
if ((${#containers[@]} == 0)); then
  echo "No profiled serving containers found." >&2
  exit 1
fi

for container in "${containers[@]}"; do
  session="$CAPTURE_NAME-$container"
  docker exec "$container" nsys start \
    --session "$session" \
    --sample none \
    --cpuctxsw none \
    --output "/profiles/$session" \
    --force-overwrite true
done

echo "Nsight collection active; capacity metrics from this run are diagnostic only."
"$@"

for container in "${containers[@]}"; do
  session="$CAPTURE_NAME-$container"
  docker exec "$container" nsys stop --session "$session"
done

cleanup
trap - EXIT INT TERM

report_pattern="$PROFILER_CACHE_ROOT/$CAPTURE_NAME-*.nsys-rep"
for _ in {1..60}; do
  if compgen -G "$report_pattern" >/dev/null; then
    break
  fi
  sleep 1
done

for report in "$PROFILER_CACHE_ROOT"/"$CAPTURE_NAME"-*.nsys-rep; do
  [[ -e "$report" ]] || continue
  basename="${report%.nsys-rep}"
  nsys stats \
    --report cuda_gpu_kern_sum,cuda_gpu_trace,nvtx_sum \
    --format csv \
    --output "$OUTPUT_DIR/$(basename "$basename")-stats" \
    "$report"
  cp "$report" "$OUTPUT_DIR/"
done

cat >"$OUTPUT_DIR/profiling.json" <<EOF
{
  "instrumentation": "nsight-systems",
  "capacity_publishable": false,
  "hardware": "$HARDWARE",
  "engine": "$ENGINE",
  "profile": "$PROFILE",
  "baseline_manifest": "baseline-manifest.json"
}
EOF

echo "Nsight Systems artifacts: $OUTPUT_DIR"
