#!/usr/bin/env bash
# Closed-loop concurrency sweep for one aggregated or PD configuration.
#
# Usage:
#   run_concurrency_sweep.sh EXPERIMENT_ID PROFILE "FLAGS" [--no-sync]
#
# Fixed search uses SWEEP_CONCURRENCIES in order. Adaptive search raises or
# lowers concurrency and inserts geometric midpoints around TTFT/per-user-speed
# boundaries. FLAGS must be empty for a pd-* profile.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

EXPERIMENT_ID="${1:?usage: run_concurrency_sweep.sh EXPERIMENT_ID PROFILE FLAGS}"
PROFILE="${2:?missing profile}"
EXPERIMENTS="${3:-}"
shift 3 || true
[[ "${1:-}" == --no-sync ]] && export LATENCY_SYNC=0

CASES="${SWEEP_CASES:-chat-f50 code-f50 agent-f50 mix-f50}"
CONCURRENCIES="${SWEEP_CONCURRENCIES:-8 16 32 64 128 192 256 384 512}"
DURATION="${SWEEP_DURATION_S:-180}"
WARMUP_SECONDS="${SWEEP_WARMUP_S:-120}"
STOP_TTFT_P50_MS="${SWEEP_STOP_TTFT_P50_MS:-10000}"
STOP_ERROR_RATE="${SWEEP_STOP_ERROR_RATE:-0.01}"
SEARCH="${SWEEP_SEARCH:-fixed}"
REPETITIONS="${SWEEP_REPETITIONS:-1}"
REPETITION_START="${SWEEP_REPETITION_START:-1}"
PHASE="${SWEEP_PHASE:-discovery}"
DATASET_NAMESPACE="${SWEEP_DATASET_SEED_NAMESPACE:-sweep}"
DISABLE_EARLY_STOP="${SWEEP_DISABLE_EARLY_STOP:-0}"
MIN_CONCURRENCY="${SWEEP_MIN:-8}"
TARGETS_MS="${SWEEP_TARGETS_MS:-500,1000,5000}"
MAX_POINTS="${SWEEP_MAX_POINTS:-5}"
PER_USER_TARGETS="${SWEEP_PER_USER_TARGETS:-68,100}"
START="${SWEEP_START:-32}"
MAX_CONCURRENCY="${SWEEP_MAX:-2048}"
WORKLOAD="${SWEEP_WORKLOAD:-$LATENCY_REPO_ROOT/testing/workloads/latency-active-matrix.yaml}"
[[ "$REPETITIONS" =~ ^[1-9][0-9]*$ ]] ||
  latency_die "SWEEP_REPETITIONS must be a positive integer"
[[ "$REPETITION_START" =~ ^[1-9][0-9]*$ ]] ||
  latency_die "SWEEP_REPETITION_START must be a positive integer"
case "$PHASE" in
  discovery|confirm) ;;
  *) latency_die "SWEEP_PHASE must be discovery or confirm" ;;
esac
[[ "$DISABLE_EARLY_STOP" == 0 || "$DISABLE_EARLY_STOP" == 1 ]] ||
  latency_die "SWEEP_DISABLE_EARLY_STOP must be 0 or 1"

latency_require_safe_root
latency_require_tools
latency_acquire_lock

RUN_ROOT="$(latency_new_run_root "$EXPERIMENT_ID")"
mkdir -p "$RUN_ROOT"
jq -n '{schema_version:1, policy:"unique-per-trial-v1"}' \
  >"$RUN_ROOT/dataset_policy.json"
latency_write_status "$RUN_ROOT" running "concurrency sweep started"
latency_write_manifest \
  "$RUN_ROOT" "$EXPERIMENT_ID" "$PROFILE" "$EXPERIMENTS" "$WORKLOAD"
jq -n \
  --arg cases "$CASES" \
  --arg points "$CONCURRENCIES" \
  --argjson duration "$DURATION" \
  --argjson warmup_s "$WARMUP_SECONDS" \
  --argjson stop_ttft "$STOP_TTFT_P50_MS" \
  --arg flags "$EXPERIMENTS" \
  --arg profile "$PROFILE" \
  --arg search "$SEARCH" \
  --arg phase "$PHASE" \
  --arg dataset_namespace "$DATASET_NAMESPACE" \
  --arg workload "$WORKLOAD" \
  --argjson shards "${LATENCY_LOADGEN_SHARDS:-1}" \
  --argjson repetitions "$REPETITIONS" \
  --argjson repetition_start "$REPETITION_START" \
  --argjson stop_error "$STOP_ERROR_RATE" \
  --argjson disable_early_stop "$DISABLE_EARLY_STOP" \
  '{
    schema_version:1,
    kind:"closed_loop_concurrency_sweep",
    profile:$profile,
    experiment_flags:$flags,
    cases:$cases,
    concurrencies:$points,
    search:$search,
    phase:$phase,
    repetitions:$repetitions,
    repetition_start:$repetition_start,
    dataset_seed_namespace:$dataset_namespace,
    workload:$workload,
    loadgen_shards:$shards,
    duration_s:$duration,
    warmup_s:$warmup_s,
    stop_ttft_p50_ms:$stop_ttft,
    stop_error_rate:$stop_error,
    disable_early_stop:$disable_early_stop
  }' >"$RUN_ROOT/configuration.json"

FINAL_STATUS=failed
FINAL_MESSAGE="concurrency sweep failed"
on_exit() {
  local rc=$?
  trap - EXIT INT TERM
  latency_finalize "$RUN_ROOT" "$FINAL_STATUS" "$FINAL_MESSAGE" || rc=1
  exit "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

export LATENCY_REQUIRE_UNIQUE_REQUESTS=1
if [[ "$PROFILE" == pd-* ]]; then
  [[ -z "$EXPERIMENTS" ]] ||
    latency_die "PD profiles do not take experiment flags"
  latency_start_pd_server "$PROFILE" "$RUN_ROOT/server.log"
  latency_start_pd_telemetry "$PROFILE" "$RUN_ROOT/telemetry"
  METRICS_CSV="$(latency_pd_metric_urls "$PROFILE" | paste -sd, -)"
else
  latency_start_server "$PROFILE" "$EXPERIMENTS" "$RUN_ROOT/server.log"
  latency_start_telemetry "$PROFILE" "$RUN_ROOT/telemetry"
  METRICS_CSV="$(latency_profile_metric_urls "$PROFILE" | paste -sd, -)"
  if [[ "$PROFILE" == latency-2xdep4-sla ]]; then
    METRICS_CSV+=",http://127.0.0.1:8000/metrics"
  fi
fi
"$LATENCY_REPO_ROOT/.venv/bin/python" \
  "$LATENCY_REPO_ROOT/testing/common/smoke.py" \
  --base-url http://127.0.0.1:8000/v1 \
  --model "$SERVED_MODEL" \
  --output "$RUN_ROOT/smoke.json" \
  --skip-image

sweep_requests() {
  "$LATENCY_PYTHON" - "$WORKLOAD" "$1" "$2" "$DURATION" <<'PY'
import math
import sys
from pathlib import Path

import yaml

workload_path, case_name = Path(sys.argv[1]), sys.argv[2]
concurrency, duration = int(sys.argv[3]), float(sys.argv[4])
workload = yaml.safe_load(workload_path.read_text())
case = next(
    (item for item in workload.get("cases", []) if item.get("name") == case_name),
    None,
)
if case is None:
    raise SystemExit(f"unknown workload case {case_name!r} in {workload_path}")
variants = case.get("variants")
if variants:
    total_weight = sum(float(item.get("weight", 0)) for item in variants)
    if total_weight <= 0:
        raise SystemExit(f"workload case {case_name!r} has no positive weights")
    mean_output = sum(
        float(item["max_tokens"]) * float(item.get("weight", 0))
        for item in variants
    ) / total_weight
else:
    mean_output = float(case["max_tokens"])
tpot_lower_bound_s = (3.8 + 0.02 * concurrency / 2) / 1000
e2e_lower_bound_s = mean_output * tpot_lower_bound_s
print(
    max(
        256,
        math.ceil(concurrency * duration / e2e_lower_bound_s) + concurrency,
    )
)
PY
}

POINT_EXCEEDS_STOP=0
run_point() {
  local case_value="$1" concurrency="$2"
  local cell_root="$RUN_ROOT/cells/$case_value"
  local point_datasets="$RUN_ROOT/trial-datasets/cells/$case_value/c$concurrency"
  local requests summary
  POINT_EXCEEDS_STOP=0
  requests="$(sweep_requests "$case_value" "$concurrency")"
  latency_prepare_search_datasets \
    "$WORKLOAD" "$case_value" closed "$concurrency" "$DURATION" \
    "$REPETITIONS" "$REPETITION_START" "$point_datasets" \
    "$DATASET_NAMESPACE:$case_value:c$concurrency" "$requests"
  (
    cd "$point_datasets"
    sha256sum -- *.jsonl | sort -k2
  ) >"$point_datasets/dataset-sha256.txt"
  LATENCY_DURATION="$DURATION" \
    LATENCY_REPETITIONS="$REPETITIONS" \
    LATENCY_MAX_REQUESTS="$requests" \
    latency_search \
      "$point_datasets" "$cell_root/c$concurrency" closed "$concurrency" \
      http://127.0.0.1:8000/v1 "$PHASE" "$REPETITION_START" "$METRICS_CSV"
  summary="$(
    find "$cell_root/c$concurrency/runs" -mindepth 2 -maxdepth 2 \
      -name summary.json -print -quit
  )"
  [[ -n "$summary" ]] || latency_die "missing summary for $case_value c$concurrency"
  if jq -e \
    --argjson ttft "$STOP_TTFT_P50_MS" \
    --argjson err "$STOP_ERROR_RATE" \
    '(.ttft_ms.p50 // 1e18) > $ttft or (.error_rate // 1) > $err' \
    "$summary" >/dev/null; then
    latency_log \
      "$case_value: stopping at c$concurrency (TTFT p50 or error limit)"
    POINT_EXCEEDS_STOP=1
  fi
}

next_point() {
  "$LATENCY_PYTHON" - \
    "$1" "$START" "$MAX_CONCURRENCY" "$MIN_CONCURRENCY" \
    "$STOP_TTFT_P50_MS" "$TARGETS_MS" "$MAX_POINTS" \
    "$STOP_ERROR_RATE" "$PER_USER_TARGETS" <<'PY'
import json
import math
import sys
from pathlib import Path

cell, start, high, low, stop, targets, max_points, max_error, speeds = sys.argv[1:]
speed_targets = sorted(float(item) for item in speeds.split(",") if item)
start, high, low, max_points = map(int, (start, high, low, max_points))
stop, max_error = float(stop), float(max_error)
targets = sorted(float(item) for item in targets.split(","))
ttft, speed = {}, {}
for path in Path(cell).glob("c*/runs/*/summary.json"):
    data = json.loads(path.read_text())
    bad = (
        (data.get("error_rate") or 0) > max_error
        or data["ttft_ms"]["p50"] is None
    )
    concurrency = int(path.parts[-4][1:])
    ttft[concurrency] = math.inf if bad else data["ttft_ms"]["p50"]
    tpot = (data.get("tpot_ms") or {}).get("p50")
    speed[concurrency] = 0.0 if bad or not tpot else 1000.0 / tpot


def emit(value: int) -> None:
    print(value)
    raise SystemExit(0)


if len(ttft) >= max_points:
    raise SystemExit(0)
if not ttft:
    emit(start)
top = max(ttft)
if ttft[top] <= stop and top * 2 <= high:
    emit(top * 2)
bottom = min(ttft)
too_slow = bool(speed_targets) and speed[bottom] < speed_targets[-1]
if (ttft[bottom] > targets[0] or too_slow) and bottom // 4 >= low:
    emit(bottom // 4)
points = sorted(ttft)
for target in targets:
    for left, right in zip(points, points[1:]):
        if (
            ttft[left] <= target < ttft[right]
            and right >= left * 2
            and ttft[right] > 2 * ttft[left]
        ):
            middle = int(round(math.sqrt(left * right) / 8) * 8)
            middle = middle or int(round(math.sqrt(left * right)))
            if middle not in ttft and left < middle < right:
                emit(middle)
for target in reversed(speed_targets):
    for left, right in zip(points, points[1:]):
        if speed[left] >= target > speed[right] and right >= left * 2:
            middle = int(round(math.sqrt(left * right) / 8) * 8)
            middle = middle or int(round(math.sqrt(left * right)))
            if middle not in ttft and left < middle < right:
                emit(middle)
PY
}

for case_value in $CASES; do
  cell_root="$RUN_ROOT/cells/$case_value"
  trial_datasets="$RUN_ROOT/trial-datasets/cells/$case_value"
  if [[ "$case_value" != *-f0 ]]; then
    latency_prepare_trial_dataset \
      "$WORKLOAD" "$case_value" "$trial_datasets/warmup.jsonl" 512 \
      "$DATASET_NAMESPACE:$case_value:warmup" 1
    sha256sum "$trial_datasets/warmup.jsonl" \
      >"$trial_datasets/warmup-sha256.txt"
    LATENCY_WARMUP_DURATION="$WARMUP_SECONDS" \
      latency_warmup \
        "$trial_datasets/warmup.jsonl" "$cell_root/warmup" \
        http://127.0.0.1:8000/v1
  fi
  if [[ "$SEARCH" == adaptive ]]; then
    while true; do
      if ! concurrency="$(next_point "$cell_root")"; then
        latency_die "adaptive search failed for $case_value"
      fi
      [[ -n "$concurrency" ]] || break
      run_point "$case_value" "$concurrency"
    done
  else
    for concurrency in $CONCURRENCIES; do
      run_point "$case_value" "$concurrency"
      if ((POINT_EXCEEDS_STOP)) && [[ "$DISABLE_EARLY_STOP" != 1 ]]; then
        break
      fi
    done
  fi
  latency_write_status "$cell_root" complete "sweep cell complete"
done

latency_stop_telemetry
latency_stop_server
FINAL_STATUS=complete
FINAL_MESSAGE="concurrency sweep complete"
