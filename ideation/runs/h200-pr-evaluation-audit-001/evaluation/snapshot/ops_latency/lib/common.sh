#!/usr/bin/env bash
# Shared helpers for the isolated B200 latency campaign.

set -Eeuo pipefail

LATENCY_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$LATENCY_REPO_ROOT"

# shellcheck source=../../source.sh
source "$LATENCY_REPO_ROOT/source.sh"

LATENCY_CAMPAIGN_CONFIG="${LATENCY_CAMPAIGN_CONFIG:-$LATENCY_REPO_ROOT/ops_latency/campaign.yaml}"
LATENCY_RESULTS_ROOT="${LATENCY_RESULTS_ROOT:-$RESULTS_ROOT/b200/vllm/latency-campaign}"
LATENCY_REPORT="${LATENCY_REPORT:-$LATENCY_REPO_ROOT/ops_latency/report/latency-b200-campaign-export.html}"
LATENCY_ARCHIVE_ROOT="${LATENCY_ARCHIVE_ROOT:-/data/b200-bench-results/deepseek-v4.1-flash/i-097469ebb78e9333e}"
LATENCY_S3_BUCKET="${S3_BUCKET:-b200-bench-results}"
LATENCY_S3_PREFIX="${S3_PREFIX:-deepseek-v4.1-flash}"
LATENCY_SYNC="${LATENCY_SYNC:-1}"
VLLM_ROUTER_BIN="${VLLM_ROUTER_BIN:-$MODEL_STORAGE_ROOT/tools/vllm-router/bin/vllm-router}"
PYTHONDONTWRITEBYTECODE=1
if [[ -x "$LATENCY_REPO_ROOT/.venv/bin/python" ]]; then
  LATENCY_PYTHON="$LATENCY_REPO_ROOT/.venv/bin/python"
else
  LATENCY_PYTHON="$(command -v python3)"
fi

export LATENCY_CAMPAIGN_CONFIG LATENCY_RESULTS_ROOT LATENCY_REPORT
export LATENCY_ARCHIVE_ROOT LATENCY_S3_BUCKET LATENCY_S3_PREFIX
export LATENCY_PYTHON
export VLLM_ROUTER_BIN
# Bound sticky routing so a Zipf-hot session cannot overload one replica.
# This changes latency-campaign routing only; the shared router default stays
# unchanged.
export DSV41_ROUTER_LOAD_FACTOR="${DSV41_ROUTER_LOAD_FACTOR:-1.1}"
export DSV41_ROUTER_CONNECTION_LIMIT="${DSV41_ROUTER_CONNECTION_LIMIT:-4096}"
export DSV41_ROUTER_RETRY_CONNECTION_ERRORS="${DSV41_ROUTER_RETRY_CONNECTION_ERRORS:-1}"
export PYTHONDONTWRITEBYTECODE

latency_log() {
  printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"
}

latency_die() {
  latency_log "ERROR: $*" >&2
  return 1
}

latency_sha256_or_na() {
  local path="$1"
  if [[ -f "$path" ]]; then
    sha256sum "$path" | awk '{print $1}'
  else
    printf 'not-applicable\n'
  fi
}

latency_require_safe_root() {
  case "/$(realpath -m "$LATENCY_RESULTS_ROOT")/" in
    */latency-campaign/) ;;
    *) latency_die "LATENCY_RESULTS_ROOT must end in latency-campaign" ;;
  esac
}

latency_require_tools() {
  local command
  for command in curl flock jq paste python3; do
    command -v "$command" >/dev/null 2>&1 ||
      latency_die "required command is unavailable: $command"
  done
  [[ -x "$LATENCY_REPO_ROOT/.venv/bin/python" ]] ||
    latency_die "missing project Python: $LATENCY_REPO_ROOT/.venv/bin/python"
}

latency_profile_allowed() {
  case "$1" in
    balanced|low-latency|latency-tp4|latency-dep8|latency-dep8-sla|latency-2xdep4-sla|latency-tp8) return 0 ;;
    *) latency_die "refusing non-latency profile: $1" ;;
  esac
}

latency_pd_profile_allowed() {
  case "$1" in
    pd-tp4-baseline|pd-tp4-prefill16k|pd-tp4-decode64|pd-tp4-decode128) return 0 ;;
    *) latency_die "refusing unknown PD profile: $1" ;;
  esac
}

latency_latest_run() {
  local experiment_id="$1"
  ls -1dt "$LATENCY_RESULTS_ROOT/$experiment_id/"* 2>/dev/null | awk 'NR==1'
}

latency_latest_completed_run() {
  local experiment_id="$1"
  local directory
  for directory in "$LATENCY_RESULTS_ROOT/$experiment_id/"*; do
    [[ -d "$directory" && -f "$directory/status.json" ]] || continue
    if jq -e '.status == "complete"' "$directory/status.json" >/dev/null; then
      printf '%s\n' "$directory"
    fi
  done | sort -r | awk 'NR==1'
}

latency_new_run_root() {
  local experiment_id="$1"
  local stamp
  stamp="$(date -u +%Y%m%d-%H%M%S)"
  printf '%s/%s/%s\n' "$LATENCY_RESULTS_ROOT" "$experiment_id" "$stamp"
}

latency_write_status() {
  local root="$1"
  local status="$2"
  local message="${3:-}"
  mkdir -p "$root"
  jq -n \
    --arg status "$status" \
    --arg message "$message" \
    --arg time "$(date -u +%FT%TZ)" \
    '{schema_version: 1, status: $status, message: $message, updated_at: $time}' \
    >"$root/status.json"
}

latency_write_manifest() {
  local root="$1"
  local experiment_id="$2"
  local profile="$3"
  local experiments="$4"
  local workload="$5"
  local profile_path="$LATENCY_REPO_ROOT/serving/b200/vllm/profiles/$profile.yaml"
  local profile_sha256="not-applicable"
  local git_revision="unknown"
  local git_dirty=false
  local selected_image="${VLLM_IMAGE:-}"
  local router_revision="not-applicable"
  local workload_sha256
  local experiment_definitions_sha256
  local loadgen_sha256
  local loadgen_shards_sha256
  local latency_search_sha256
  local serve_recipe_sha256
  local serve_pd_recipe_sha256
  local local_router_sha256
  local sweep_runner_sha256
  local comparison_analyzer_sha256
  local comparison_runner_sha256
  if [[ -f "$profile_path" ]]; then
    profile_sha256="$(sha256sum "$profile_path" | awk '{print $1}')"
  elif [[ -f "$LATENCY_REPO_ROOT/serving/b200/vllm/pd_profiles/$profile.yaml" ]]; then
    profile_path="$LATENCY_REPO_ROOT/serving/b200/vllm/pd_profiles/$profile.yaml"
    profile_sha256="$(sha256sum "$profile_path" | awk '{print $1}')"
  fi
  git_revision="$(
    git -C "$LATENCY_REPO_ROOT" rev-parse HEAD 2>/dev/null ||
      printf 'unknown'
  )"
  if [[ -n "$(git -C "$LATENCY_REPO_ROOT" status --porcelain 2>/dev/null)" ]]; then
    git_dirty=true
  fi
  if [[ -z "$selected_image" ]]; then
    selected_image="$(
      "$LATENCY_PYTHON" - \
        "$LATENCY_REPO_ROOT/serving/b200/vllm/images.yaml" <<'PY'
import sys
import yaml
print(yaml.safe_load(open(sys.argv[1]))["default"])
PY
    )"
  fi
  if [[ -f "$(dirname "$VLLM_ROUTER_BIN")/../COMMIT" ]]; then
    router_revision="$(<"$(dirname "$VLLM_ROUTER_BIN")/../COMMIT")"
  fi
  workload_sha256="$(latency_sha256_or_na "$workload")"
  experiment_definitions_sha256="$(
    latency_sha256_or_na \
      "$LATENCY_REPO_ROOT/serving/b200/vllm/experiments.yaml"
  )"
  loadgen_sha256="$(
    latency_sha256_or_na "$LATENCY_REPO_ROOT/testing/common/loadgen.py"
  )"
  loadgen_shards_sha256="$(
    latency_sha256_or_na "$LATENCY_REPO_ROOT/testing/common/loadgen_shards.py"
  )"
  latency_search_sha256="$(
    latency_sha256_or_na "$LATENCY_REPO_ROOT/ops_latency/latency_search.py"
  )"
  serve_recipe_sha256="$(
    latency_sha256_or_na "$LATENCY_REPO_ROOT/lib/serve_recipe.py"
  )"
  serve_pd_recipe_sha256="$(
    latency_sha256_or_na "$LATENCY_REPO_ROOT/lib/serve_pd_recipe.py"
  )"
  local_router_sha256="$(
    latency_sha256_or_na "$LATENCY_REPO_ROOT/lib/router.py"
  )"
  sweep_runner_sha256="$(
    latency_sha256_or_na \
      "$LATENCY_REPO_ROOT/ops_latency/run_concurrency_sweep.sh"
  )"
  comparison_analyzer_sha256="$(
    latency_sha256_or_na \
      "$LATENCY_REPO_ROOT/ops_latency/compare_dep8_2xdep4.py"
  )"
  comparison_runner_sha256="$(
    latency_sha256_or_na \
      "$LATENCY_REPO_ROOT/ops_latency/run_dep8_vs_2xdep4.sh"
  )"
  mkdir -p "$root"
  jq -n \
    --arg experiment_id "$experiment_id" \
    --arg profile "$profile" \
    --arg experiments "$experiments" \
    --arg workload "$workload" \
    --arg git_revision "$git_revision" \
    --argjson git_dirty "$git_dirty" \
    --arg profile_sha256 "$profile_sha256" \
    --arg campaign_sha256 "$(sha256sum "$LATENCY_CAMPAIGN_CONFIG" | awk '{print $1}')" \
    --arg workload_sha256 "$workload_sha256" \
    --arg experiment_definitions_sha256 "$experiment_definitions_sha256" \
    --arg loadgen_sha256 "$loadgen_sha256" \
    --arg loadgen_shards_sha256 "$loadgen_shards_sha256" \
    --arg latency_search_sha256 "$latency_search_sha256" \
    --arg serve_recipe_sha256 "$serve_recipe_sha256" \
    --arg serve_pd_recipe_sha256 "$serve_pd_recipe_sha256" \
    --arg local_router_sha256 "$local_router_sha256" \
    --arg sweep_runner_sha256 "$sweep_runner_sha256" \
    --arg comparison_analyzer_sha256 "$comparison_analyzer_sha256" \
    --arg comparison_runner_sha256 "$comparison_runner_sha256" \
    --arg model "$MODEL" \
    --arg model_revision "$MODEL_REVISION" \
    --arg selected_image "$selected_image" \
    --arg router_bin "$VLLM_ROUTER_BIN" \
    --arg router_revision "$router_revision" \
    --arg router_load_factor "$DSV41_ROUTER_LOAD_FACTOR" \
    --argjson router_connection_limit "$DSV41_ROUTER_CONNECTION_LIMIT" \
    --argjson router_retry_connection_errors "$DSV41_ROUTER_RETRY_CONNECTION_ERRORS" \
    --arg created_at "$(date -u +%FT%TZ)" \
    '{
      schema_version: 1,
      evidence_class: "latency_campaign",
      experiment_id: $experiment_id,
      profile: $profile,
      experiments: ($experiments | split(" ") | map(select(length > 0))),
      workload: $workload,
      git_revision: $git_revision,
      git_dirty: $git_dirty,
      profile_sha256: $profile_sha256,
      campaign_sha256: $campaign_sha256,
      workload_sha256: $workload_sha256,
      code_sha256: {
        experiment_definitions: $experiment_definitions_sha256,
        loadgen: $loadgen_sha256,
        loadgen_shards: $loadgen_shards_sha256,
        latency_search: $latency_search_sha256,
        serve_recipe: $serve_recipe_sha256,
        serve_pd_recipe: $serve_pd_recipe_sha256,
        local_router: $local_router_sha256,
        sweep_runner: $sweep_runner_sha256,
        comparison_analyzer: $comparison_analyzer_sha256,
        comparison_runner: $comparison_runner_sha256
      },
      model: $model,
      model_revision: $model_revision,
      selected_image: $selected_image,
      router_bin: $router_bin,
      router_revision: $router_revision,
      aggregated_router_config: {
        load_factor: ($router_load_factor | tonumber),
        connection_limit: $router_connection_limit,
        retry_connection_errors: ($router_retry_connection_errors == 1)
      },
      created_at: $created_at
    }' >"$root/manifest.json"
}

latency_profile_metric_urls() {
  local profile="$1"
  "$LATENCY_PYTHON" - "$profile" "$LATENCY_REPO_ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

profile, root = sys.argv[1], Path(sys.argv[2])
data = yaml.safe_load(
    (root / f"serving/b200/vllm/profiles/{profile}.yaml").read_text()
)
for replica in data.get("replicas", []):
    print(f"http://127.0.0.1:{replica['port']}/metrics")
PY
}

latency_pd_metric_urls() {
  local profile="${1:-pd-tp4-baseline}"
  "$LATENCY_PYTHON" - "$profile" "$LATENCY_REPO_ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

profile, root = sys.argv[1], Path(sys.argv[2])
data = yaml.safe_load(
    (root / f"serving/b200/vllm/pd_profiles/{profile}.yaml").read_text()
)
for role in ("prefill", "decode"):
    print(f"http://127.0.0.1:{data[role]['port']}/metrics")
PY
}

latency_start_server() {
  local profile="$1"
  local experiments="$2"
  local log_file="$3"
  latency_profile_allowed "$profile"
  mkdir -p "$(dirname "$log_file")"
  latency_log "Starting profile=$profile experiments=[$experiments]"
  setsid --wait env PROFILE="$profile" EXPERIMENTS="$experiments" \
    make serve-b200-vllm >"$log_file" 2>&1 &
  ACTIVE_SERVER_PID=$!
  if ! wait_for_server "http://127.0.0.1:8000/v1" "$ACTIVE_SERVER_PID"; then
    latency_log "Server failed; see $log_file"
    return 1
  fi
}

latency_start_pd_server() {
  local profile="$1"
  local log_file="$2"
  latency_pd_profile_allowed "$profile"
  mkdir -p "$(dirname "$log_file")"
  latency_log "Starting PD profile=$profile"
  setsid --wait \
    bash "$LATENCY_REPO_ROOT/serving/b200/vllm/serve_pd.sh" \
      --profile "$profile" >"$log_file" 2>&1 &
  ACTIVE_SERVER_PID=$!
  if ! wait_for_server "http://127.0.0.1:8000/v1" "$ACTIVE_SERVER_PID"; then
    latency_log "PD server failed; see $log_file"
    return 1
  fi
}

latency_stop_server() {
  if [[ -n "${ACTIVE_SERVER_PID:-}" ]]; then
    stop_server "$ACTIVE_SERVER_PID"
    ACTIVE_SERVER_PID=""
  fi
}

LATENCY_TELEMETRY_PID=""

latency_start_telemetry() {
  local profile="$1"
  local output_dir="$2"
  local command=(
    "$LATENCY_REPO_ROOT/.venv/bin/python"
    "$LATENCY_REPO_ROOT/testing/telemetry/collector.py"
    --output-dir "$output_dir"
  )
  local url
  while IFS= read -r url; do
    [[ -n "$url" ]] && command+=(--engine-metrics-url "$url")
  done < <(latency_profile_metric_urls "$profile")
  if [[ -n "${DCGM_METRICS_URL:-}" ]]; then
    command+=(--dcgm-metrics-url "$DCGM_METRICS_URL")
  fi
  "${command[@]}" >"$output_dir.log" 2>&1 &
  LATENCY_TELEMETRY_PID=$!
}

latency_start_pd_telemetry() {
  local profile="$1"
  local output_dir="$2"
  local command=(
    "$LATENCY_REPO_ROOT/.venv/bin/python"
    "$LATENCY_REPO_ROOT/testing/telemetry/collector.py"
    --output-dir "$output_dir"
  )
  local url
  while IFS= read -r url; do
    [[ -n "$url" ]] && command+=(--engine-metrics-url "$url")
  done < <(latency_pd_metric_urls "$profile")
  if [[ -n "${DCGM_METRICS_URL:-}" ]]; then
    command+=(--dcgm-metrics-url "$DCGM_METRICS_URL")
  fi
  "${command[@]}" >"$output_dir.log" 2>&1 &
  LATENCY_TELEMETRY_PID=$!
}

latency_scrape_profile_metrics() {
  local profile="$1"
  local output="$2"
  local url
  : >"$output"
  while IFS= read -r url; do
    [[ -n "$url" ]] || continue
    printf '# source %s\n' "$url" >>"$output"
    curl -fsS "$url" >>"$output"
    printf '\n' >>"$output"
  done < <(latency_profile_metric_urls "$profile")
}

latency_scrape_pd_metrics() {
  local profile="$1"
  local output="$2"
  local url
  : >"$output"
  while IFS= read -r url; do
    [[ -n "$url" ]] || continue
    printf '# source %s\n' "$url" >>"$output"
    curl -fsS "$url" >>"$output"
    printf '\n' >>"$output"
  done < <(latency_pd_metric_urls "$profile")
}

latency_stop_telemetry() {
  if [[ -n "${LATENCY_TELEMETRY_PID:-}" ]]; then
    kill -TERM "$LATENCY_TELEMETRY_PID" 2>/dev/null || true
    wait "$LATENCY_TELEMETRY_PID" 2>/dev/null || true
    LATENCY_TELEMETRY_PID=""
  fi
}

latency_generate_dataset() {
  local workload="$1"
  local case_name="$2"
  local requests="$3"
  local output="$4"
  local seed="${5:-${LATENCY_SEED:-17}}"
  mkdir -p "$(dirname "$output")"
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/testing/common/generate_workload.py" \
    --config "$workload" \
    --case "$case_name" \
    --requests "$requests" \
    --seed "$seed" \
    --output "$output"
}

latency_trial_run_id() {
  local mode="$1"
  local point="$2"
  local repetition="$3"
  "$LATENCY_PYTHON" - "$mode" "$point" "$repetition" <<'PY'
import sys

mode, point, repetition = sys.argv[1:]
if mode == "open":
    label = f"{float(point):.6f}".rstrip("0").rstrip(".").replace(".", "_")
    print(f"open-r{label}-rep{repetition}")
else:
    print(f"closed-c{int(float(point))}-rep{repetition}")
PY
}

latency_trial_dataset_seed() {
  local case_name="$1"
  local namespace="$2"
  "$LATENCY_PYTHON" - "${LATENCY_SEED:-17}" "$case_name" "$namespace" <<'PY'
import hashlib
import sys

base, case_name, namespace = sys.argv[1:]
digest = hashlib.blake2s(
    f"{base}:{case_name}:{namespace}".encode(), digest_size=4
).digest()
print(1 + int.from_bytes(digest, "big") % 2_000_000_000)
PY
}

latency_open_trial_requests() {
  local rate="$1"
  local duration="$2"
  local minimum="$3"
  "$LATENCY_PYTHON" - "$rate" "$duration" "$minimum" <<'PY'
import math
import sys

rate, duration, minimum = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
mean = rate * duration
# Eight standard deviations plus a fixed margin makes accidental exhaustion
# vanishingly unlikely while avoiding oversized long-prompt datasets.
print(max(minimum, math.ceil(mean + 8 * math.sqrt(mean) + 128)))
PY
}

latency_prepare_trial_dataset() {
  local workload="$1"
  local case_name="$2"
  local output="$3"
  local requests="$4"
  local namespace="$5"
  local warmup="${6:-0}"
  [[ -s "$output" ]] && return 0
  local raw="${output%.jsonl}.raw.jsonl"
  local seed
  seed="$(latency_trial_dataset_seed "$case_name" "$namespace")"
  latency_generate_dataset "$workload" "$case_name" "$requests" "$raw" "$seed"
  local -a prepare_args=(
    --input "$raw"
    --output "$output"
  )
  ((warmup)) && prepare_args+=(--warmup)
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/ops_latency/prepare_dataset.py" \
    "${prepare_args[@]}"
  rm -f "$raw"
}

latency_prepare_search_datasets() {
  local workload="$1"
  local case_name="$2"
  local mode="$3"
  local points="$4"
  local duration="$5"
  local repetitions="$6"
  local repetition_start="$7"
  local output_dir="$8"
  local namespace="$9"
  local minimum_requests="${10}"
  mkdir -p "$output_dir"
  local -a point_values=()
  IFS=, read -r -a point_values <<<"$points"
  local point repetition identifier requests
  for point in "${point_values[@]}"; do
    for ((repetition = repetition_start;
         repetition < repetition_start + repetitions;
         repetition++)); do
      identifier="$(latency_trial_run_id "$mode" "$point" "$repetition")"
      if [[ "$mode" == open ]]; then
        requests="$(
          latency_open_trial_requests "$point" "$duration" "$minimum_requests"
        )"
      else
        requests="$minimum_requests"
      fi
      latency_prepare_trial_dataset \
        "$workload" "$case_name" "$output_dir/$identifier.jsonl" "$requests" \
        "$namespace:$identifier"
    done
  done
}

latency_smoke() {
  local output="$1"
  local base_url="${2:-http://127.0.0.1:8000/v1}"
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/testing/common/smoke.py" \
    --base-url "$base_url" \
    --model "$SERVED_MODEL" \
    --output "$output"
}

latency_warmup() {
  local dataset="$1"
  local output="$2"
  local base_url="${3:-http://127.0.0.1:8000/v1}"
  if [[ -f "$output/complete.json" ]]; then
    latency_log "Reusing completed warmup: $output"
    return 0
  fi
  mkdir -p "$output"
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/testing/common/loadgen.py" \
    --dataset "$dataset" \
    --base-url "$base_url" \
    --model "$SERVED_MODEL" \
    --mode closed \
    --concurrency "${LATENCY_WARMUP_CONCURRENCY:-16}" \
    --duration "${LATENCY_WARMUP_DURATION:-120}" \
    --timeout "${LATENCY_TIMEOUT:-1800}" \
    --seed "${LATENCY_SEED:-17}" \
    --output-dir "$output" >"$output/loadgen.log" 2>&1 || {
    # Warmup is not measured. Tolerate the load generator's generic failure
    # exit only when at least 99% of scheduled warmup requests succeeded.
    local rc=$?
    [[ $rc -eq 1 ]] &&
      jq -e \
        '(.failed // 1) <= 0.01 * ((.scheduled // 0) + 1)' \
        "$output/summary.json" >/dev/null 2>&1 ||
      return "$rc"
    latency_log \
      "Warmup had $(jq -r .failed "$output/summary.json") failed request(s); continuing"
  }
  jq -n \
    --arg completed_at "$(date -u +%FT%TZ)" \
    '{schema_version:1, evidence_class:"cache_warmup_not_measured", completed_at:$completed_at}' \
    >"$output/complete.json"
}

latency_search() {
  local dataset="$1"
  local output="$2"
  local mode="$3"
  local points="$4"
  local base_url="${5:-http://127.0.0.1:8000/v1}"
  local phase="${6:-discovery}"
  local repetition_start="${7:-1}"
  local metrics_csv="${8:-}"
  local -a metric_urls=()
  local args=(
    "$LATENCY_REPO_ROOT/.venv/bin/python"
    "$LATENCY_REPO_ROOT/ops_latency/latency_search.py"
    --base-url "$base_url"
    --model "$SERVED_MODEL"
    --results "$output"
    --slo-config "$LATENCY_CAMPAIGN_CONFIG"
    --mode "$mode"
    --duration "${LATENCY_DURATION:-300}"
    --repetitions "${LATENCY_REPETITIONS:-1}"
    --repetition-start "$repetition_start"
    --phase "$phase"
    --timeout "${LATENCY_TIMEOUT:-1800}"
    --open-concurrency "${LATENCY_OPEN_CONCURRENCY:-4096}"
    --max-requests "${LATENCY_MAX_REQUESTS:-0}"
    --seed "${LATENCY_SEED:-17}"
    --resume
  )
  if [[ -d "$dataset" ]]; then
    args+=(--dataset-dir "$dataset")
  else
    args+=(--dataset "$dataset")
  fi
  if [[ "${LATENCY_REQUIRE_UNIQUE_REQUESTS:-0}" == 1 ]]; then
    args+=(--require-unique-requests)
  fi
  if [[ -n "$metrics_csv" ]]; then
    IFS=',' read -r -a metric_urls <<<"$metrics_csv"
    local metric_url
    for metric_url in "${metric_urls[@]}"; do
      [[ -n "$metric_url" ]] && args+=(--metrics-url "$metric_url")
    done
  fi
  if [[ "$mode" == open ]]; then
    args+=(--rates "$points")
  else
    args+=(--concurrencies "$points")
  fi
  "${args[@]}"
}

latency_build_report() {
  local builder="$LATENCY_REPO_ROOT/ops_latency/report/build_report.py"
  [[ -f "$builder" ]] || {
    latency_log "Report builder not present yet; skipping refresh."
    return 0
  }
  "$LATENCY_REPO_ROOT/.venv/bin/python" "$builder" \
    --campaign "$LATENCY_CAMPAIGN_CONFIG" \
    --archive-root "$LATENCY_ARCHIVE_ROOT" \
    --live-root "$LATENCY_RESULTS_ROOT" \
    --output "$LATENCY_REPORT"
}

latency_sync_results() {
  local reason="$1"
  if [[ "$LATENCY_SYNC" != 1 ]]; then
    latency_log "S3 sync disabled for $reason (LATENCY_SYNC=$LATENCY_SYNC)."
    return 0
  fi
  latency_log "S3 sync ($reason)."
  DATA_ROOT="${DATA_ROOT:-$MODEL_STORAGE_ROOT}" \
    bash "$LATENCY_REPO_ROOT/ops/sync_to_s3.sh" \
      --bucket "$LATENCY_S3_BUCKET" \
      --prefix "$LATENCY_S3_PREFIX" \
      --execute \
      --no-campaign
}

latency_write_delivery_status() {
  local root="$1"
  local report_status="$2"
  local sync_status="$3"
  jq -n \
    --arg report_status "$report_status" \
    --arg sync_status "$sync_status" \
    --arg time "$(date -u +%FT%TZ)" \
    '{
      schema_version: 1,
      report_status: $report_status,
      sync_status: $sync_status,
      updated_at: $time
    }' >"$root/delivery_status.json"
}

latency_delivery_complete() {
  local root="$1"
  [[ -f "$root/delivery_status.json" ]] &&
    jq -e \
      '.report_status == "complete" and
       (.sync_status == "complete" or .sync_status == "skipped")' \
      "$root/delivery_status.json" >/dev/null
}

latency_deliver() {
  local root="$1"
  local reason="$2"
  local report_status="complete"
  local sync_status="pending"
  local rc=0
  if ! latency_build_report; then
    latency_log "WARNING: report refresh failed."
    report_status="failed"
    rc=1
  fi
  if [[ "$LATENCY_SYNC" != 1 ]]; then
    sync_status="skipped"
    latency_write_delivery_status "$root" "$report_status" "$sync_status"
    return "$rc"
  fi
  latency_write_delivery_status "$root" "$report_status" "$sync_status"
  if latency_sync_results "$reason"; then
    sync_status="complete"
  else
    latency_log "WARNING: S3 sync failed."
    sync_status="failed"
    rc=1
  fi
  latency_write_delivery_status "$root" "$report_status" "$sync_status"
  return "$rc"
}

latency_finalize() {
  local root="$1"
  local status="$2"
  local message="$3"
  local rc=0
  latency_stop_telemetry
  latency_stop_server
  latency_write_status "$root" "$status" "$message"
  latency_deliver \
    "$root" "$status: $(basename "$(dirname "$root")")" || rc=1
  return "$rc"
}

latency_acquire_lock() {
  mkdir -p "$LATENCY_RESULTS_ROOT"
  exec 9>"$LATENCY_RESULTS_ROOT/.campaign.lock"
  flock -n 9 || latency_die "another latency campaign process is running"
}
