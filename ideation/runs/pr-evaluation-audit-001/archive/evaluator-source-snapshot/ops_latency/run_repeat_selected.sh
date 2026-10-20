#!/usr/bin/env bash
# Add repetitions 2-3 for user-selected points from one completed config run.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

RUN_ROOT=""
PLAN=0
POINTS=()
while (($#)); do
  case "$1" in
    --run-root) RUN_ROOT="${2:?missing run root}"; shift 2 ;;
    --point) POINTS+=("${2:?expected workload:cache:rate}"); shift 2 ;;
    --plan) PLAN=1; shift ;;
    --no-sync) export LATENCY_SYNC=0; shift ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") --run-root PATH --point WORKLOAD:CACHE:RATE [--point ...]
Example: --point chat:50:8 --point mix:75:6
EOF
      exit 0
      ;;
    *) latency_die "unknown argument: $1"; exit 2 ;;
  esac
done
[[ -n "$RUN_ROOT" && ${#POINTS[@]} -gt 0 ]] ||
  latency_die "--run-root and at least one --point are required"
RUN_ROOT="$(realpath -m "$RUN_ROOT")"
case "/$RUN_ROOT/" in
  "$LATENCY_RESULTS_ROOT"/*/) ;;
  *) latency_die "run root must be below LATENCY_RESULTS_ROOT" ;;
esac
[[ -f "$RUN_ROOT/configuration.json" ]] ||
  latency_die "missing configuration.json in $RUN_ROOT"

CONFIG_JSON="$(cat "$RUN_ROOT/configuration.json")"
EXPERIMENT_ID="$(jq -r '.id' <<<"$CONFIG_JSON")"
SERVER_KIND="$(jq -r '.server_kind' <<<"$CONFIG_JSON")"
PROFILE="$(jq -r '.profile' <<<"$CONFIG_JSON")"
EXPERIMENTS="$(jq -r '(.experiment_flags // []) | join(" ")' <<<"$CONFIG_JSON")"
WARMUP_SECONDS="$(jq -r '.protocol.warmup.duration_s' <<<"$CONFIG_JSON")"
KNEE_SECONDS="$(jq -r '.protocol.knee.duration_s' <<<"$CONFIG_JSON")"
CONFIRM_REPETITIONS="$(jq -r '.protocol.confirmation_repetitions' <<<"$CONFIG_JSON")"
WORKLOAD="$LATENCY_REPO_ROOT/testing/workloads/latency-active-matrix.yaml"
MIN_REQUESTS="${LATENCY_REQUESTS:-512}"
if ((PLAN)); then
  printf 'experiment: %s\nprofile: %s\nrun_root: %s\n' \
    "$EXPERIMENT_ID" "$PROFILE" "$RUN_ROOT"
  printf 'points:\n'
  printf '  - %s\n' "${POINTS[@]}"
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock
CONFIRM_ROOT="$RUN_ROOT/confirmations/$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$CONFIRM_ROOT"
latency_write_status "$CONFIRM_ROOT" running "selected repeats started"

on_exit() {
  local rc=$?
  trap - EXIT INT TERM
  latency_stop_telemetry
  latency_stop_server
  if ((rc == 0)); then
    latency_write_status "$CONFIRM_ROOT" complete "selected repeats complete"
  else
    latency_write_status "$CONFIRM_ROOT" failed "selected repeats failed (exit $rc)"
  fi
  latency_deliver "$CONFIRM_ROOT" "selected repeats: $EXPERIMENT_ID" || rc=1
  exit "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM
export LATENCY_REQUIRE_UNIQUE_REQUESTS=1

if [[ "$SERVER_KIND" == aggregated ]]; then
  latency_start_server "$PROFILE" "$EXPERIMENTS" "$CONFIRM_ROOT/server.log"
  latency_start_telemetry "$PROFILE" "$CONFIRM_ROOT/telemetry"
  METRICS_CSV="$(latency_profile_metric_urls "$PROFILE" | paste -sd, -)"
else
  smoke_root="$(latency_latest_completed_run LAT-PD-SMOKE || true)"
  if [[ -z "$smoke_root" || ! -f "$smoke_root/pd_availability.json" ]] ||
     ! jq -e '.pd_available == true' "$smoke_root/pd_availability.json" >/dev/null; then
    latency_die "PD repeats require a completed successful LAT-PD-SMOKE"
  fi
  if [[ -n "$smoke_root" &&
        -f "$smoke_root/pd_availability.json" &&
        "$(jq -r '.implementation' "$smoke_root/pd_availability.json")" == fallback-open-pr ]]; then
    LATENCY_PD_FALLBACK_IMAGE="${LATENCY_PD_FALLBACK_IMAGE:-$(jq -r '.fallback_image // empty' "$smoke_root/pd_availability.json")}"
    LATENCY_PD_FALLBACK_ROUTER_BIN="${LATENCY_PD_FALLBACK_ROUTER_BIN:-$(jq -r '.fallback_router_bin // empty' "$smoke_root/pd_availability.json")}"
    : "${LATENCY_PD_FALLBACK_IMAGE:?missing fallback image recorded by smoke}"
    : "${LATENCY_PD_FALLBACK_ROUTER_BIN:?missing fallback router recorded by smoke}"
    export VLLM_IMAGE="$LATENCY_PD_FALLBACK_IMAGE"
    export VLLM_ROUTER_BIN="$LATENCY_PD_FALLBACK_ROUTER_BIN"
  fi
  latency_start_pd_server "$PROFILE" "$CONFIRM_ROOT/server.log"
  latency_start_pd_telemetry "$PROFILE" "$CONFIRM_ROOT/telemetry"
  METRICS_CSV="$(latency_pd_metric_urls "$PROFILE" | paste -sd, -)"
fi

for point in "${POINTS[@]}"; do
  IFS=: read -r workload_name cache_tier rate extra <<<"$point"
  [[ -n "$workload_name" && -n "$cache_tier" && -n "$rate" && -z "${extra:-}" ]] ||
    latency_die "invalid point $point; expected workload:cache:rate"
  case_name="${workload_name}-f${cache_tier}"
  point_root="$CONFIRM_ROOT/$case_name/r${rate//./_}"
  trial_datasets="$point_root/trial-datasets"
  warmup_dataset="$trial_datasets/warmup.jsonl"
  if [[ "$cache_tier" != 0 ]]; then
    latency_prepare_trial_dataset \
      "$WORKLOAD" "$case_name" "$warmup_dataset" "$MIN_REQUESTS" \
      "confirm:$case_name:$rate:warmup" 1
    LATENCY_WARMUP_DURATION="$WARMUP_SECONDS" \
      latency_warmup \
        "$warmup_dataset" "$point_root/warmup" \
        http://127.0.0.1:8000/v1
  fi
  search_datasets="$trial_datasets/search"
  latency_prepare_search_datasets \
    "$WORKLOAD" "$case_name" open "$rate" "$KNEE_SECONDS" \
    "$CONFIRM_REPETITIONS" 2 "$search_datasets" \
    "confirm:$case_name:$rate" "$MIN_REQUESTS"
  LATENCY_DURATION="$KNEE_SECONDS" LATENCY_REPETITIONS="$CONFIRM_REPETITIONS" \
    latency_search \
      "$search_datasets" "$point_root/confirm" open "$rate" \
      http://127.0.0.1:8000/v1 confirm 2 "$METRICS_CSV"
done
