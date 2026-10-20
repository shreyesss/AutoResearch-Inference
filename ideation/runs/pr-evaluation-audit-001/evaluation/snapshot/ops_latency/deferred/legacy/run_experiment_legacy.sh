#!/usr/bin/env bash
# Execute one isolated LAT-* experiment. Thin run_lat_XX.sh files call this.

set -Eeuo pipefail

LEGACY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(cd "$LEGACY_DIR/../.." && pwd)"
# shellcheck source=../../lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

EXPERIMENT_ID="${1:?usage: run_experiment.sh LAT-XX [options]}"
shift

PLAN=0
RESUME=0
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --resume) RESUME=1; shift ;;
    --duration)
      export LATENCY_DURATION="${2:?missing duration}"
      shift 2
      ;;
    --repetitions)
      export LATENCY_REPETITIONS="${2:?missing repetitions}"
      shift 2
      ;;
    --rates)
      export LATENCY_RATES="${2:?missing rates}"
      shift 2
      ;;
    --concurrencies)
      export LATENCY_CONCURRENCIES="${2:?missing concurrencies}"
      shift 2
      ;;
    --requests)
      export LATENCY_REQUESTS="${2:?missing requests}"
      shift 2
      ;;
    --no-sync)
      export LATENCY_SYNC=0
      shift
      ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") $EXPERIMENT_ID [options]
  --plan                 print the manifest entry and planned actions
  --resume               reuse the latest experiment directory
  --duration SECONDS     override each load point's duration
  --repetitions N        override repetitions per point
  --rates CSV            override open-loop rate ladder
  --concurrencies CSV    override closed-loop concurrency ladder
  --requests N           override generated dataset records
  --no-sync              skip S3 synchronization (local development only)
EOF
      exit 0
      ;;
    *)
      latency_die "unknown argument: $1"
      exit 2
      ;;
  esac
done

case "$EXPERIMENT_ID" in
  LAT-0[0-9]|LAT-1[0-2]) ;;
  *) latency_die "unknown experiment ID: $EXPERIMENT_ID"; exit 2 ;;
esac

WORKLOAD="$LATENCY_REPO_ROOT/testing/workloads/latency-classes.yaml"
REQUESTS="${LATENCY_REQUESTS:-512}"
CLOSED_POINTS="${LATENCY_CONCURRENCIES:-1,2,4,8}"
OPEN_RATES="${LATENCY_RATES:-0.5,1,2,4,8,12,16,20}"

show_plan() {
  "$LATENCY_PYTHON" - \
    "$LATENCY_CAMPAIGN_CONFIG" "$EXPERIMENT_ID" <<'PY'
import sys
import yaml

config = yaml.safe_load(open(sys.argv[1]))
experiment_id = sys.argv[2]
experiments = config.get("deferred_experiments", config.get("experiments", []))
for experiment in experiments:
    if experiment["id"] == experiment_id:
        print(yaml.safe_dump(experiment, sort_keys=False).rstrip())
        break
else:
    raise SystemExit(f"unknown experiment {experiment_id}")
PY
  cat <<EOF
latency_results_root: $LATENCY_RESULTS_ROOT
duration_s: ${LATENCY_DURATION:-300}
repetitions: ${LATENCY_REPETITIONS:-1}
closed_points: $CLOSED_POINTS
open_rates: $OPEN_RATES
requests: $REQUESTS
s3_destination: s3://$LATENCY_S3_BUCKET/$LATENCY_S3_PREFIX/<instance-id>/
EOF
}

if ((PLAN)); then
  show_plan
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock

if ((RESUME)); then
  RUN_ROOT="$(latency_latest_run "$EXPERIMENT_ID" || true)"
else
  RUN_ROOT=""
fi
if [[ -z "$RUN_ROOT" ]]; then
  RUN_ROOT="$(latency_new_run_root "$EXPERIMENT_ID")"
fi
mkdir -p "$RUN_ROOT"
latency_write_status "$RUN_ROOT" running "experiment started"

FINAL_MESSAGE="experiment failed"
on_exit() {
  local rc=$?
  local final_rc=$rc
  trap - EXIT INT TERM
  if ((rc == 0)); then
    latency_finalize "$RUN_ROOT" complete "$FINAL_MESSAGE" || final_rc=1
  else
    latency_finalize "$RUN_ROOT" failed "$FINAL_MESSAGE (exit $rc)" ||
      final_rc="$rc"
  fi
  exit "$final_rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

repeat_open_boundaries() {
  local dataset="$1"
  local screen_root="$2"
  local boundary_root="$3"
  local base_url="${4:-http://127.0.0.1:8000/v1}"
  local boundary_rates
  boundary_rates="$(
    "$LATENCY_PYTHON" - \
      "$screen_root/latency_search_summary.json" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1]))
rates = {
    value["load_point"]
    for value in summary.get("highest_passing", {}).values()
    if isinstance(value, dict) and value.get("load_point") is not None
}
print(",".join(f"{rate:g}" for rate in sorted(rates)))
PY
  )"
  if [[ -n "$boundary_rates" ]]; then
    LATENCY_REPETITIONS="${LATENCY_BOUNDARY_REPETITIONS:-5}" \
      latency_search \
        "$dataset" "$boundary_root" open "$boundary_rates" "$base_url"
  fi
}

arm_complete() {
  local root="$1"
  [[ -f "$root/status.json" ]] &&
    jq -e '.status == "complete"' "$root/status.json" >/dev/null
}

run_profile_arm() {
  local arm="$1"
  local profile="$2"
  local experiments="$3"
  local workload="$4"
  local cases_csv="$5"
  local closed_points="$6"
  local open_rates="$7"
  local arm_root="$RUN_ROOT/arms/$arm"
  local server_log="$arm_root/server.log"
  local case_name dataset

  if arm_complete "$arm_root"; then
    latency_log "Skipping completed arm $arm."
    return 0
  fi
  latency_profile_allowed "$profile"
  mkdir -p "$arm_root"
  latency_write_manifest \
    "$arm_root" "$EXPERIMENT_ID" "$profile" "$experiments" "$workload"
  latency_start_server "$profile" "$experiments" "$server_log"
  latency_smoke "$arm_root/smoke.json"
  latency_start_telemetry "$profile" "$arm_root/telemetry"

  IFS=',' read -r -a case_names <<<"$cases_csv"
  for case_name in "${case_names[@]}"; do
    dataset="$arm_root/datasets/$case_name.jsonl"
    [[ -s "$dataset" ]] ||
      latency_generate_dataset "$workload" "$case_name" "$REQUESTS" "$dataset"
    if [[ -n "$closed_points" ]]; then
      latency_search \
        "$dataset" "$arm_root/$case_name/closed" closed "$closed_points"
    fi
    if [[ -n "$open_rates" ]]; then
      latency_search \
        "$dataset" "$arm_root/$case_name/open" open "$open_rates"
      if [[ "${LATENCY_REPEAT_BOUNDARY:-0}" == 1 ]]; then
        repeat_open_boundaries \
          "$dataset" \
          "$arm_root/$case_name/open" \
          "$arm_root/$case_name/boundary"
      fi
    fi
  done

  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$arm_root" complete "arm complete"
}

run_router_comparison() {
  local arm_root="$RUN_ROOT/arms/path-comparison"
  local profile="latency-tp4"
  local dataset case_name
  if arm_complete "$arm_root"; then
    latency_log "Skipping completed path-comparison arm."
    return 0
  fi
  mkdir -p "$arm_root"
  latency_write_manifest \
    "$arm_root" "$EXPERIMENT_ID" "$profile" "" "$WORKLOAD"
  latency_start_server "$profile" "" "$arm_root/server.log"
  latency_start_telemetry "$profile" "$arm_root/telemetry"
  dataset="$arm_root/datasets/chat-512-256.jsonl"
  latency_generate_dataset "$WORKLOAD" chat-512-256 "$REQUESTS" "$dataset"
  LATENCY_MAX_REQUESTS=1 LATENCY_DURATION=600 \
    latency_search \
      "$dataset" "$arm_root/chat-512-256/first-request-direct" \
      closed "1" "http://127.0.0.1:8100/v1"
  latency_smoke "$arm_root/smoke.json"
  for case_name in chat-512-256 agent-8k-1k; do
    dataset="$arm_root/datasets/$case_name.jsonl"
    [[ -s "$dataset" ]] ||
      latency_generate_dataset "$WORKLOAD" "$case_name" "$REQUESTS" "$dataset"
    LATENCY_DURATION="${LATENCY_WARMUP_DURATION:-60}" \
      latency_search \
        "$dataset" "$arm_root/$case_name/warmup-direct" closed "1" \
        "http://127.0.0.1:8100/v1"
    latency_search \
      "$dataset" "$arm_root/$case_name/direct" closed "1,2,4" \
      "http://127.0.0.1:8100/v1"
    latency_search \
      "$dataset" "$arm_root/$case_name/router" closed "1,2,4" \
      "http://127.0.0.1:8000/v1"
  done
  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$arm_root" complete "path comparison complete"
}

run_session_arm() {
  local arm="$1"
  local experiments="$2"
  local dp_ranks="$3"
  local arm_root="$RUN_ROOT/arms/$arm"
  local profile="latency-dep8"
  local workload="$LATENCY_REPO_ROOT/testing/workloads/agent-sessions.yaml"
  local dataset="$arm_root/datasets/agent-session.jsonl"
  local output="$arm_root/agent-session/session"

  if arm_complete "$arm_root"; then
    latency_log "Skipping completed arm $arm."
    return 0
  fi
  mkdir -p "$arm_root"
  latency_write_manifest \
    "$arm_root" "$EXPERIMENT_ID" "$profile" "$experiments" "$workload"
  latency_start_server "$profile" "$experiments" "$arm_root/server.log"
  latency_smoke "$arm_root/smoke.json"
  latency_start_telemetry "$profile" "$arm_root/telemetry"
  [[ -s "$dataset" ]] ||
    latency_generate_dataset "$workload" agent-session "$REQUESTS" "$dataset"
  mkdir -p "$output"
  if [[ -s "$output/summary.json" &&
        -s "$output/requests.jsonl" &&
        -s "$output/latency_analysis.json" ]]; then
    latency_log "Reusing completed session load artifacts for $arm."
  else
    "$LATENCY_REPO_ROOT/.venv/bin/python" \
      "$LATENCY_REPO_ROOT/testing/common/session_loadgen.py" \
      --dataset "$dataset" \
      --base-url http://127.0.0.1:8000/v1 \
      --model "$SERVED_MODEL" \
      --concurrency "${LATENCY_SESSION_CONCURRENCY:-128}" \
      --turns 6 \
      --tool-tokens 1500 \
      --duration "${LATENCY_SESSION_DURATION:-900}" \
      --warmup "${LATENCY_SESSION_WARMUP:-300}" \
      --timeout "${LATENCY_TIMEOUT:-1800}" \
      --seed "${LATENCY_SEED:-17}" \
      --dp-ranks "$dp_ranks" \
      --output-dir "$output"
    "$LATENCY_REPO_ROOT/.venv/bin/python" \
      "$LATENCY_REPO_ROOT/ops_latency/analyze_latency.py" \
      --requests "$output/requests.jsonl" \
      --summary "$output/summary.json" \
      --slo-config "$LATENCY_CAMPAIGN_CONFIG" \
      --output "$output/latency_analysis.json"
  fi
  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$arm_root" complete "session arm complete"
}

run_sharded_arm() {
  local arm="$1"
  local profile="$2"
  local experiments="$3"
  local base_urls="$4"
  local mode="$5"
  local points="$6"
  local arm_root="$RUN_ROOT/arms/$arm"
  local dataset="$arm_root/datasets/production-mix-32k.jsonl"
  local point output concurrency
  local -a point_args

  if arm_complete "$arm_root"; then
    latency_log "Skipping completed arm $arm."
    return 0
  fi
  mkdir -p "$arm_root"
  latency_write_manifest \
    "$arm_root" "$EXPERIMENT_ID" "$profile" "$experiments" "$WORKLOAD"
  latency_start_server "$profile" "$experiments" "$arm_root/server.log"
  latency_smoke "$arm_root/smoke.json"
  latency_start_telemetry "$profile" "$arm_root/telemetry"
  [[ -s "$dataset" ]] ||
    latency_generate_dataset \
      "$WORKLOAD" production-mix-32k "$REQUESTS" "$dataset"

  IFS=',' read -r -a load_points <<<"$points"
  for point in "${load_points[@]}"; do
    if [[ "$mode" == open ]]; then
      output="$arm_root/production-mix-32k/open-r${point//./_}"
      point_args=(--request-rate "$point")
      concurrency="${LATENCY_OPEN_CONCURRENCY:-4096}"
    else
      output="$arm_root/production-mix-32k/closed-c$point"
      point_args=()
      concurrency="$point"
    fi
    mkdir -p "$output"
    if [[ -s "$output/summary.json" &&
          -s "$output/requests.jsonl" &&
          -s "$output/latency_analysis.json" ]]; then
      latency_log "Reusing completed sharded load point $point."
    else
      "$LATENCY_REPO_ROOT/.venv/bin/python" \
        "$LATENCY_REPO_ROOT/ops_latency/sharded_latency.py" \
        --dataset "$dataset" \
        --base-urls "$base_urls" \
        --model "$SERVED_MODEL" \
        --mode "$mode" \
        --concurrency "$concurrency" \
        --shards "${LATENCY_CLIENT_SHARDS:-8}" \
        --duration "${LATENCY_DURATION:-300}" \
        --timeout "${LATENCY_TIMEOUT:-1800}" \
        --seed "${LATENCY_SEED:-17}" \
        --output-dir "$output" \
        "${point_args[@]}"
      "$LATENCY_REPO_ROOT/.venv/bin/python" \
        "$LATENCY_REPO_ROOT/ops_latency/analyze_latency.py" \
        --requests "$output/requests.jsonl" \
        --summary "$output/summary.json" \
        --slo-config "$LATENCY_CAMPAIGN_CONFIG" \
        --output "$output/latency_analysis.json"
    fi
  done
  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$arm_root" complete "sharded client arm complete"
}

run_burst_sequence() {
  local arm_root="$RUN_ROOT/arms/burst-recovery"
  local profile="${LATENCY_FINAL_PROFILE:-latency-dep8}"
  local experiments="${LATENCY_FINAL_EXPERIMENTS:-lat-eplb lat-engram-thp}"
  local dataset="$arm_root/datasets/production-mix-32k.jsonl"
  local normal="${LATENCY_NORMAL_RATE:-4}"
  local burst="${LATENCY_BURST_RATE:-8}"

  if arm_complete "$arm_root"; then
    latency_log "Skipping completed burst-recovery arm."
    return 0
  fi
  mkdir -p "$arm_root"
  latency_write_manifest \
    "$arm_root" "$EXPERIMENT_ID" "$profile" "$experiments" "$WORKLOAD"
  latency_start_server "$profile" "$experiments" "$arm_root/server.log"
  latency_smoke "$arm_root/smoke.json"
  latency_start_telemetry "$profile" "$arm_root/telemetry"
  [[ -s "$dataset" ]] ||
    latency_generate_dataset \
      "$WORKLOAD" production-mix-32k "$REQUESTS" "$dataset"
  LATENCY_DURATION="${LATENCY_NORMAL_DURATION:-300}" \
    latency_search "$dataset" "$arm_root/normal-before" open "$normal"
  LATENCY_DURATION="${LATENCY_BURST_DURATION:-120}" \
    latency_search "$dataset" "$arm_root/burst" open "$burst"
  LATENCY_DURATION="${LATENCY_RECOVERY_DURATION:-600}" \
    latency_search "$dataset" "$arm_root/recovery" open "$normal"
  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$arm_root" complete "burst sequence complete"
}

run_soak() {
  local arm_root="$RUN_ROOT/arms/soak"
  local profile="${LATENCY_FINAL_PROFILE:-latency-dep8}"
  local experiments="${LATENCY_FINAL_EXPERIMENTS:-lat-eplb lat-engram-thp}"
  local dataset="$arm_root/datasets/production-mix-32k.jsonl"
  local output="$arm_root/production-mix-32k/open"
  local cancel_root

  if arm_complete "$arm_root"; then
    latency_log "Skipping completed soak arm."
    return 0
  fi
  mkdir -p "$arm_root"
  latency_write_manifest \
    "$arm_root" "$EXPERIMENT_ID" "$profile" "$experiments" "$WORKLOAD"
  latency_start_server "$profile" "$experiments" "$arm_root/server.log"
  latency_smoke "$arm_root/smoke.json"
  latency_start_telemetry "$profile" "$arm_root/telemetry"
  [[ -s "$dataset" ]] ||
    latency_generate_dataset \
      "$WORKLOAD" production-mix-32k "$REQUESTS" "$dataset"
  LATENCY_DURATION="${LATENCY_SOAK_DURATION:-3600}" \
    LATENCY_REPETITIONS=1 \
    latency_search \
      "$dataset" "$output" open "${LATENCY_SOAK_RATE:-4}"

  cancel_root="$arm_root/cancellation"
  mkdir -p "$cancel_root"
  latency_scrape_profile_metrics \
    "$profile" "$cancel_root/metrics-before.txt"
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/ops_latency/cancellation_probe.py" \
    --dataset "$dataset" \
    --base-url http://127.0.0.1:8000/v1 \
    --requests "${LATENCY_CANCEL_REQUESTS:-64}" \
    --concurrency "${LATENCY_CANCEL_CONCURRENCY:-32}" \
    --timeout "${LATENCY_TIMEOUT:-1800}" \
    --output "$cancel_root/summary.json"
  sleep "${LATENCY_CANCEL_RECOVERY_SECONDS:-30}"
  latency_scrape_profile_metrics \
    "$profile" "$cancel_root/metrics-after.txt"

  if [[ "${LATENCY_ALLOW_FAULTS:-0}" == 1 ]]; then
    [[ -n "${LATENCY_FAULT_COMMAND:-}" ]] ||
      latency_die "LATENCY_FAULT_COMMAND is required when faults are enabled"
    bash -lc "$LATENCY_FAULT_COMMAND"
  else
    jq -n \
      '{status:"skipped", reason:"set LATENCY_ALLOW_FAULTS=1 and LATENCY_FAULT_COMMAND to opt in"}' \
      >"$arm_root/fault-arms.json"
  fi
  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$arm_root" complete "soak complete"
}

case "$EXPERIMENT_ID" in
  LAT-00)
    latency_build_report
    ;;
  LAT-01)
    run_router_comparison
    ;;
  LAT-02)
    run_profile_arm \
      tp4 latency-tp4 "" "$WORKLOAD" \
      "chat-512-256,code-2k-1k,agent-8k-1k,document-32k-512,multimodal-512-256" \
      "$CLOSED_POINTS" ""
    run_profile_arm \
      tp4-long latency-tp4 "" "$WORKLOAD" \
      "long-context-128k-128,long-context-512k-32,long-context-1m-16" \
      "1,2" ""
    run_profile_arm \
      dep8 latency-dep8 "" "$WORKLOAD" \
      "chat-512-256,code-2k-1k,agent-8k-1k,document-32k-512,multimodal-512-256" \
      "$CLOSED_POINTS" ""
    run_profile_arm \
      dep8-long latency-dep8 "" "$WORKLOAD" \
      "long-context-128k-128,long-context-512k-32,long-context-1m-16" \
      "1,2" ""
    ;;
  LAT-03)
    for spec in \
      "target-only|" \
      "dspark-k2|lat-dspark-k2" \
      "dspark-k5|lat-dspark-k5"; do
      arm="${spec%%|*}"
      flags="${spec#*|}"
      run_profile_arm \
        "$arm" latency-tp4 "$flags" "$WORKLOAD" \
        "chat-512-256,code-2k-1k,agent-8k-1k" \
        "1,16,32,64" "${LATENCY_DSPARK_RATES:-0.5,1,2,4}"
    done
    ;;
  LAT-04)
    for sequences in 8 16 32 64; do
      run_profile_arm \
        "seqs-$sequences" latency-tp4 "lat-seqs-$sequences" "$WORKLOAD" \
        "production-mix-32k" "8,16,32,64" "$OPEN_RATES"
    done
    ;;
  LAT-05)
    for spec in \
      "batched-2k|lat-batched-2k" \
      "batched-4k|lat-batched-4k" \
      "batched-8k|lat-batched-8k" \
      "long-prefill-4k|lat-batched-4k lat-long-prefill-4k"; do
      arm="${spec%%|*}"
      flags="${spec#*|}"
      run_profile_arm \
        "$arm" latency-tp4 "$flags" "$WORKLOAD" \
        "chat-512-256,agent-8k-1k,document-32k-512,production-mix-32k" \
        "4,8,16,32" "${LATENCY_PREFILL_RATES:-1,2,4,6}"
    done
    ;;
  LAT-06)
    run_profile_arm \
      tp4 latency-tp4 "${LATENCY_TP4_EXPERIMENTS:-lat-dspark-k2}" "$WORKLOAD" \
      "chat-512-256,agent-8k-1k,production-mix-32k" \
      "1,8,16,32,64" "$OPEN_RATES"
    run_profile_arm \
      dep8 latency-dep8 "${LATENCY_DEP8_EXPERIMENTS:-lat-eplb lat-engram-thp}" "$WORKLOAD" \
      "chat-512-256,agent-8k-1k,production-mix-32k" \
      "1,8,16,32,64" "$OPEN_RATES"
    ;;
  LAT-07)
    CACHE_WORKLOAD="$LATENCY_REPO_ROOT/testing/workloads/cache-sweep.yaml"
    run_profile_arm \
      cache-off latency-dep8 "lat-prefix-off lat-eplb" "$CACHE_WORKLOAD" \
      "cache-f50" "16,32,64" "${LATENCY_CACHE_RATES:-1,2,4,8}"
    run_profile_arm \
      cache-on latency-dep8 "lat-prefix-on lat-eplb" "$CACHE_WORKLOAD" \
      "cache-f50" "16,32,64" "${LATENCY_CACHE_RATES:-1,2,4,8}"
    run_session_arm sessions-unpinned "lat-prefix-on lat-eplb" 0
    run_session_arm sessions-sticky "lat-prefix-on lat-eplb" 8
    ;;
  LAT-08)
    cases="chat-512-256,code-2k-1k,agent-8k-1k,document-32k-512,multimodal-512-256"
    LATENCY_REPEAT_BOUNDARY=1 run_profile_arm \
      tp4 latency-tp4 "${LATENCY_TP4_EXPERIMENTS:-lat-dspark-k2}" "$WORKLOAD" \
      "$cases" "" "$OPEN_RATES"
    LATENCY_REPEAT_BOUNDARY=1 run_profile_arm \
      dep8 latency-dep8 "${LATENCY_DEP8_EXPERIMENTS:-lat-eplb lat-engram-thp}" "$WORKLOAD" \
      "$cases" "" "$OPEN_RATES"
    ;;
  LAT-09)
    LATENCY_REPEAT_BOUNDARY=1 run_profile_arm \
      synthetic-mix "${LATENCY_FINAL_PROFILE:-latency-dep8}" \
      "${LATENCY_FINAL_EXPERIMENTS:-lat-eplb lat-engram-thp}" "$WORKLOAD" \
      "production-mix-32k" "" "$OPEN_RATES"
    if [[ -n "${LATENCY_TRACE_DATASET:-}" ]]; then
      profile="${LATENCY_FINAL_PROFILE:-latency-dep8}"
      flags="${LATENCY_FINAL_EXPERIMENTS:-lat-eplb lat-engram-thp}"
      arm_root="$RUN_ROOT/arms/production-trace"
      if arm_complete "$arm_root"; then
        latency_log "Skipping completed production-trace arm."
      else
        mkdir -p "$arm_root"
        latency_write_manifest \
          "$arm_root" "$EXPERIMENT_ID" "$profile" "$flags" \
          "$LATENCY_TRACE_DATASET"
        latency_start_server "$profile" "$flags" "$arm_root/server.log"
        latency_smoke "$arm_root/smoke.json"
        latency_start_telemetry "$profile" "$arm_root/telemetry"
        latency_search \
          "$LATENCY_TRACE_DATASET" "$arm_root/trace/open" open "$OPEN_RATES"
        repeat_open_boundaries \
          "$LATENCY_TRACE_DATASET" \
          "$arm_root/trace/open" \
          "$arm_root/trace/boundary"
        latency_stop_telemetry
        latency_stop_server
        latency_write_status \
          "$arm_root" complete "production trace arm complete"
      fi
    else
      jq -n \
        '{status:"planned", reason:"set LATENCY_TRACE_DATASET to enable trace replay"}' \
        >"$RUN_ROOT/production-trace.json"
    fi
    ;;
  LAT-10)
    run_burst_sequence
    ;;
  LAT-11)
    run_soak
    ;;
  LAT-12)
    run_sharded_arm \
      local-multiprocess "${LATENCY_FINAL_PROFILE:-latency-dep8}" \
      "${LATENCY_FINAL_EXPERIMENTS:-lat-eplb lat-engram-thp}" \
      "http://127.0.0.1:8000/v1" closed "64,128,256"
    jq -n \
      --arg runner "ops_latency/run_remote_client.sh" \
      --arg parent_run "$RUN_ROOT" \
      '{
        status:"planned",
        runner:$runner,
        parent_run:$parent_run,
        reason:"execute from the intended remote load-generator host and set LATENCY_REMOTE_RUN_ROOT to parent_run"
      }' \
      >"$RUN_ROOT/remote-gateway.json"
    ;;
esac

FINAL_MESSAGE="experiment completed"
