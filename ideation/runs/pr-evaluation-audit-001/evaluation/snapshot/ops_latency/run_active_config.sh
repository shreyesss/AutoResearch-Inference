#!/usr/bin/env bash
# Run one loaded TP4 or PD configuration across the active cache/workload matrix.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

EXPERIMENT_ID="${1:?usage: run_active_config.sh EXPERIMENT_ID [options]}"
shift
PLAN=0
RESUME=0
MIN_REQUESTS="${LATENCY_REQUESTS:-512}"
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --resume) RESUME=1; shift ;;
    --requests) MIN_REQUESTS="${2:?missing requests}"; shift 2 ;;
    --no-sync) export LATENCY_SYNC=0; shift ;;
    -h|--help)
      echo "Usage: $(basename "$0") EXPERIMENT_ID [--plan] [--resume] [--requests N] [--no-sync]"
      exit 0
      ;;
    *) latency_die "unknown argument: $1"; exit 2 ;;
  esac
done

CONFIG_JSON="$(
  "$LATENCY_PYTHON" "$SCRIPT_DIR/campaign_query.py" \
    --campaign "$LATENCY_CAMPAIGN_CONFIG" --id "$EXPERIMENT_ID"
)"
KIND="$(jq -r '.kind' <<<"$CONFIG_JSON")"
[[ "$KIND" == configuration ]] ||
  latency_die "$EXPERIMENT_ID is not a configuration experiment"
SERVER_KIND="$(jq -r '.server_kind' <<<"$CONFIG_JSON")"
PROFILE="$(jq -r '.profile' <<<"$CONFIG_JSON")"
EXPERIMENTS="$(jq -r '(.experiment_flags // []) | join(" ")' <<<"$CONFIG_JSON")"
CALIBRATE="$(jq -r '.calibrate' <<<"$CONFIG_JSON")"
CALIBRATION_SOURCE="$(jq -r '.calibration_source // empty' <<<"$CONFIG_JSON")"
INCLUDE_UNCACHED="$(jq -r '.include_uncached' <<<"$CONFIG_JSON")"
WORKLOAD="$LATENCY_REPO_ROOT/testing/workloads/latency-active-matrix.yaml"
WARMUP_SECONDS="$(jq -r '.protocol.warmup.duration_s' <<<"$CONFIG_JSON")"
FLOOR_SECONDS="$(jq -r '.protocol.floor.duration_s' <<<"$CONFIG_JSON")"
KNEE_SECONDS="$(jq -r '.protocol.knee.duration_s' <<<"$CONFIG_JSON")"
CALIBRATION_SECONDS="$(jq -r '.protocol.calibration.duration_s' <<<"$CONFIG_JSON")"
DISCOVERY_REPETITIONS="$(jq -r '.protocol.discovery_repetitions' <<<"$CONFIG_JSON")"
MAX_ADJUSTMENTS="$(jq -r '.protocol.knee.maximum_adjustments' <<<"$CONFIG_JSON")"
CACHE_TIERS="$(jq -r '.protocol.cache_tiers | join(" ")' <<<"$CONFIG_JSON")"

if ((PLAN)); then
  jq . <<<"$CONFIG_JSON"
  cat <<EOF
minimum_requests_per_trial: $MIN_REQUESTS
dataset_policy: unique-per-trial-v1
warmup_seconds: $WARMUP_SECONDS
floor_seconds: $FLOOR_SECONDS
knee_seconds: $KNEE_SECONDS
cache_order: $CACHE_TIERS
uncached_control: $INCLUDE_UNCACHED
results_root: $LATENCY_RESULTS_ROOT/$EXPERIMENT_ID/<timestamp>
EOF
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock

if ((RESUME)); then
  RUN_ROOT="$(latency_latest_run "$EXPERIMENT_ID" || true)"
  if [[ -n "$RUN_ROOT" && -f "$RUN_ROOT/status.json" ]] &&
     jq -e '.status == "complete"' "$RUN_ROOT/status.json" >/dev/null; then
    if ! latency_delivery_complete "$RUN_ROOT"; then
      latency_log "Retrying report/S3 delivery for $RUN_ROOT"
      latency_deliver "$RUN_ROOT" "delivery retry: $EXPERIMENT_ID"
    fi
    latency_log "Latest $EXPERIMENT_ID run is already complete: $RUN_ROOT"
    exit 0
  fi
else
  RUN_ROOT=""
fi
[[ -n "$RUN_ROOT" ]] || RUN_ROOT="$(latency_new_run_root "$EXPERIMENT_ID")"
mkdir -p "$RUN_ROOT"
DATASET_POLICY="unique-per-trial-v1"
if ((RESUME)) && [[ -f "$RUN_ROOT/status.json" ]]; then
  recorded_policy="$(
    jq -r '.policy // empty' "$RUN_ROOT/dataset_policy.json" 2>/dev/null || true
  )"
  [[ "$recorded_policy" == "$DATASET_POLICY" ]] ||
    latency_die \
      "cannot resume pre-fix cache datasets in $RUN_ROOT; start a new run"
fi
jq -n --arg policy "$DATASET_POLICY" \
  '{schema_version:1, policy:$policy}' >"$RUN_ROOT/dataset_policy.json"
latency_write_status "$RUN_ROOT" running "active configuration started"
latency_write_manifest \
  "$RUN_ROOT" "$EXPERIMENT_ID" "$PROFILE" "$EXPERIMENTS" "$WORKLOAD"
(jq . <<<"$CONFIG_JSON") >"$RUN_ROOT/configuration.json"

FINAL_STATUS=failed
FINAL_MESSAGE="active configuration failed"
on_exit() {
  local rc=$?
  trap - EXIT INT TERM
  latency_finalize "$RUN_ROOT" "$FINAL_STATUS" "$FINAL_MESSAGE" || rc=1
  exit "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

case_name() {
  local workload_name="$1"
  local cache_tier="$2"
  printf '%s-f%s' "$workload_name" "$cache_tier"
}

export LATENCY_REQUIRE_UNIQUE_REQUESTS=1

if [[ "$SERVER_KIND" == aggregated ]]; then
  latency_start_server "$PROFILE" "$EXPERIMENTS" "$RUN_ROOT/server.log"
  latency_start_telemetry "$PROFILE" "$RUN_ROOT/telemetry"
  METRICS_CSV="$(
    latency_profile_metric_urls "$PROFILE" | paste -sd, -
  )"
elif [[ "$SERVER_KIND" == pd ]]; then
  smoke_root="$(latency_latest_completed_run LAT-PD-SMOKE || true)"
  if [[ -z "$smoke_root" || ! -f "$smoke_root/pd_availability.json" ]] ||
     ! jq -e '.pd_available == true' "$smoke_root/pd_availability.json" >/dev/null; then
    latency_write_status "$RUN_ROOT" unavailable "PD smoke did not establish availability"
    FINAL_STATUS=unavailable
    FINAL_MESSAGE="PD configuration skipped because PD smoke did not pass"
    exit 0
  fi
  implementation="$(jq -r '.implementation' "$smoke_root/pd_availability.json")"
  if [[ "$implementation" == fallback-open-pr ]]; then
    LATENCY_PD_FALLBACK_IMAGE="${LATENCY_PD_FALLBACK_IMAGE:-$(jq -r '.fallback_image // empty' "$smoke_root/pd_availability.json")}"
    LATENCY_PD_FALLBACK_ROUTER_BIN="${LATENCY_PD_FALLBACK_ROUTER_BIN:-$(jq -r '.fallback_router_bin // empty' "$smoke_root/pd_availability.json")}"
    : "${LATENCY_PD_FALLBACK_IMAGE:?missing fallback image recorded by smoke}"
    : "${LATENCY_PD_FALLBACK_ROUTER_BIN:?missing fallback router recorded by smoke}"
    export VLLM_IMAGE="$LATENCY_PD_FALLBACK_IMAGE"
    export VLLM_ROUTER_BIN="$LATENCY_PD_FALLBACK_ROUTER_BIN"
  fi
  latency_start_pd_server "$PROFILE" "$RUN_ROOT/server.log"
  latency_start_pd_telemetry "$PROFILE" "$RUN_ROOT/telemetry"
  METRICS_CSV="$(latency_pd_metric_urls "$PROFILE" | paste -sd, -)"
else
  latency_die "unsupported server_kind: $SERVER_KIND"
fi

"$LATENCY_REPO_ROOT/.venv/bin/python" \
  "$LATENCY_REPO_ROOT/testing/common/smoke.py" \
  --base-url http://127.0.0.1:8000/v1 \
  --model "$SERVED_MODEL" \
  --output "$RUN_ROOT/smoke.json" \
  --skip-image

calibration_file="$RUN_ROOT/calibration_rates.json"
if [[ "$CALIBRATE" == true ]]; then
  [[ -s "$calibration_file" ]] || jq -n '{}' >"$calibration_file"
  for workload_name in chat code agent mix; do
    if jq -e --arg workload "$workload_name" \
      'has($workload)' "$calibration_file" >/dev/null; then
      latency_log "Reusing calibration rate for $workload_name."
      continue
    fi
    rates="$(jq -r --arg workload "$workload_name" '.calibration_rates[$workload] | join(",")' <<<"$CONFIG_JSON")"
    case_value="$(case_name "$workload_name" 50)"
    output="$RUN_ROOT/calibration/$workload_name"
    trial_datasets="$RUN_ROOT/trial-datasets/calibration/$workload_name"
    warmup_dataset="$trial_datasets/warmup.jsonl"
    search_datasets="$trial_datasets/search"
    latency_prepare_trial_dataset \
      "$WORKLOAD" "$case_value" "$warmup_dataset" "$MIN_REQUESTS" \
      "calibration:$workload_name:warmup" 1
    latency_prepare_search_datasets \
      "$WORKLOAD" "$case_value" open "$rates" "$CALIBRATION_SECONDS" 1 1 \
      "$search_datasets" "calibration:$workload_name" "$MIN_REQUESTS"
    LATENCY_WARMUP_DURATION="$WARMUP_SECONDS" \
      latency_warmup \
        "$warmup_dataset" "$output/warmup" \
        http://127.0.0.1:8000/v1
    LATENCY_DURATION="$CALIBRATION_SECONDS" LATENCY_REPETITIONS=1 \
      latency_search \
        "$search_datasets" "$output" open "$rates" \
        http://127.0.0.1:8000/v1 calibration 1 "$METRICS_CSV"
    selected_rate="$(
      "$LATENCY_PYTHON" - "$output/latency_search_summary.json" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1]))
balanced = summary.get("highest_passing", {}).get("balanced")
if isinstance(balanced, dict):
    print(f"{balanced['load_point']:g}")
else:
    refs = summary.get("run_references", [])
    rates = [r["configured_rate"] for r in refs if r.get("configured_rate")]
    print(f"{min(rates):g}" if rates else "")
PY
    )"
    [[ -n "$selected_rate" ]] ||
      latency_die "calibration produced no rate for $workload_name"
    tmp="$calibration_file.tmp"
    jq --arg workload "$workload_name" --argjson rate "$selected_rate" \
      '. + {($workload): $rate}' "$calibration_file" >"$tmp"
    mv "$tmp" "$calibration_file"
  done
else
  baseline_root="$(latency_latest_completed_run "$CALIBRATION_SOURCE" || true)"
  [[ -n "$baseline_root" && -s "$baseline_root/calibration_rates.json" ]] ||
    latency_die "run calibration source $CALIBRATION_SOURCE first"
  cp "$baseline_root/calibration_rates.json" "$calibration_file"
  jq -n --arg source "$baseline_root/calibration_rates.json" \
    '{schema_version:1, source:$source}' >"$RUN_ROOT/calibration_source.json"
fi

read -r -a cache_tiers <<<"$CACHE_TIERS"
if [[ "$INCLUDE_UNCACHED" == true ]]; then
  cache_tiers=(0 25 50 75)
fi
for cache_tier in "${cache_tiers[@]}"; do
  for workload_name in chat code agent mix; do
    case_value="$(case_name "$workload_name" "$cache_tier")"
    cell_root="$RUN_ROOT/cells/$case_value"
    trial_datasets="$RUN_ROOT/trial-datasets/cells/$case_value"
    warmup_dataset="$trial_datasets/warmup.jsonl"
    if [[ "$cache_tier" != 0 ]]; then
      latency_prepare_trial_dataset \
        "$WORKLOAD" "$case_value" "$warmup_dataset" "$MIN_REQUESTS" \
        "cell:$case_value:warmup" 1
      LATENCY_WARMUP_DURATION="$WARMUP_SECONDS" \
        latency_warmup \
          "$warmup_dataset" "$cell_root/warmup" \
          http://127.0.0.1:8000/v1
    fi
    floor_datasets="$trial_datasets/floor"
    latency_prepare_search_datasets \
      "$WORKLOAD" "$case_value" closed "1" "$FLOOR_SECONDS" 1 1 \
      "$floor_datasets" "cell:$case_value:floor" "$MIN_REQUESTS"
    LATENCY_DURATION="$FLOOR_SECONDS" LATENCY_REPETITIONS=1 \
      latency_search \
        "$floor_datasets" "$cell_root/floor" closed "1" \
        http://127.0.0.1:8000/v1 floor 1 "$METRICS_CSV"
    knee_rate="$(jq -r --arg workload "$workload_name" '.[$workload]' "$calibration_file")"
    knee_datasets="$trial_datasets/knee"
    latency_prepare_search_datasets \
      "$WORKLOAD" "$case_value" open "$knee_rate" "$KNEE_SECONDS" \
      "$DISCOVERY_REPETITIONS" 1 "$knee_datasets" "cell:$case_value:knee" \
      "$MIN_REQUESTS"
    LATENCY_DURATION="$KNEE_SECONDS" LATENCY_REPETITIONS="$DISCOVERY_REPETITIONS" \
      latency_search \
        "$knee_datasets" "$cell_root/knee" open "$knee_rate" \
        http://127.0.0.1:8000/v1 discovery 1 "$METRICS_CSV"
    current_rate="$knee_rate"
    current_search_root="$cell_root/knee"
    for ((adjustment = 1; adjustment <= MAX_ADJUSTMENTS; adjustment++)); do
      relative_analysis="$(
        jq -r --argjson rate "$current_rate" \
          '.run_references[]
           | select(.configured_rate == $rate and .repetition == 1)
           | .analysis' \
          "$current_search_root/latency_search_summary.json" | awk 'NR==1'
      )"
      [[ -n "$relative_analysis" ]] ||
        latency_die \
          "cannot locate analysis for $case_value at $current_rate"
      analysis_path="$current_search_root/$relative_analysis"
      decision_path="$cell_root/knee_adjustment-$adjustment.json"
      "$LATENCY_REPO_ROOT/.venv/bin/python" \
        "$LATENCY_REPO_ROOT/ops_latency/select_knee_adjustment.py" \
        --analysis "$analysis_path" \
        --campaign "$LATENCY_CAMPAIGN_CONFIG" \
        --rate "$current_rate" \
        --output "$decision_path"
      adjusted_rate="$(jq -r '.adjusted_rate // empty' "$decision_path")"
      [[ -n "$adjusted_rate" ]] || break
      adjusted_root="$cell_root/adjustment-$adjustment"
      adjusted_datasets="$trial_datasets/adjustment-$adjustment"
      latency_prepare_search_datasets \
        "$WORKLOAD" "$case_value" open "$adjusted_rate" "$KNEE_SECONDS" \
        "$DISCOVERY_REPETITIONS" 1 "$adjusted_datasets" \
        "cell:$case_value:adjustment-$adjustment" "$MIN_REQUESTS"
      LATENCY_DURATION="$KNEE_SECONDS" LATENCY_REPETITIONS="$DISCOVERY_REPETITIONS" \
        latency_search \
          "$adjusted_datasets" "$adjusted_root" open "$adjusted_rate" \
          http://127.0.0.1:8000/v1 discovery 1 "$METRICS_CSV"
      current_rate="$adjusted_rate"
      current_search_root="$adjusted_root"
    done
    latency_write_status "$cell_root" complete "first-pass cell complete"
  done
done

latency_stop_telemetry
latency_stop_server
FINAL_STATUS=complete
FINAL_MESSAGE="active configuration matrix complete"
