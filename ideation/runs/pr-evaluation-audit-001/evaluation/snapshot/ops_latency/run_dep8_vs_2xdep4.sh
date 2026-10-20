#!/usr/bin/env bash
# Resumable paired R7 DEP8 versus real 2xDEP4 latency comparison.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

PLAN=0
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --no-sync) export LATENCY_SYNC=0; shift ;;
    -h|--help)
      printf 'Usage: %s [--plan] [--no-sync]\n' "$(basename "$0")"
      exit 0
      ;;
    *) latency_die "unknown argument: $1"; exit 2 ;;
  esac
done

COMPARISON_ROOT="$LATENCY_RESULTS_ROOT/_dep8-vs-2xdep4"
SELECTION_JSON="$COMPARISON_ROOT/comparison.json"
WORKLOAD="$LATENCY_REPO_ROOT/testing/workloads/latency-active-matrix.yaml"
COMMON_NAMESPACE="dep8-vs-2xdep4-v1"
COMMON_CONCURRENCIES="256 384 512"

if ((PLAN)); then
  cat <<'EOF'
DEP8 versus 2xDEP4 execution order:
  1. Mandatory 2xDEP4 backend/router smoke.
  2. DEP8 R7 control: agent-f75 at c=256,384,512.
  3. 2xDEP4 API2/seq64 baseline at the same points.
  4. Correction 1: 2xDEP4 API4/seq64.
  5. Select API2 or API4 using the campaign qualification contract.
  6. Correction 2: selected API count with seq80.
  7. Select each topology's qualifying operating point.
  8. Add repetitions 2-3 for those two selected points.
All measured runs use 8 shards, 120 s warmup, 150 s measurement, and
topology-independent deterministic datasets. Existing complete steps resume.
EOF
  printf '\n2xDEP4 smoke plan:\n'
  bash "$SCRIPT_DIR/run_2xdep4_smoke.sh" --plan
  exit 0
fi

latency_require_safe_root
latency_require_tools
mkdir -p "$COMPARISON_ROOT"

has_complete_run() {
  local experiment_id="$1" profile="$2" flags="$3" phase="$4"
  local repetitions="$5" repetition_start="$6" concurrencies="$7"
  local namespace="$COMMON_NAMESPACE-${phase}"
  local profile_path="$LATENCY_REPO_ROOT/serving/b200/vllm/profiles/$profile.yaml"
  local campaign_sha profile_sha workload_sha experiments_sha loadgen_sha
  local shards_sha search_sha serve_sha pd_sha router_sha sweep_sha
  local analyzer_sha runner_sha
  campaign_sha="$(sha256sum "$LATENCY_CAMPAIGN_CONFIG" | awk '{print $1}')"
  profile_sha="$(sha256sum "$profile_path" | awk '{print $1}')"
  workload_sha="$(sha256sum "$WORKLOAD" | awk '{print $1}')"
  experiments_sha="$(
    sha256sum "$LATENCY_REPO_ROOT/serving/b200/vllm/experiments.yaml" |
      awk '{print $1}'
  )"
  loadgen_sha="$(
    sha256sum "$LATENCY_REPO_ROOT/testing/common/loadgen.py" | awk '{print $1}'
  )"
  shards_sha="$(
    sha256sum "$LATENCY_REPO_ROOT/testing/common/loadgen_shards.py" |
      awk '{print $1}'
  )"
  search_sha="$(
    sha256sum "$LATENCY_REPO_ROOT/ops_latency/latency_search.py" |
      awk '{print $1}'
  )"
  serve_sha="$(sha256sum "$LATENCY_REPO_ROOT/lib/serve_recipe.py" | awk '{print $1}')"
  pd_sha="$(sha256sum "$LATENCY_REPO_ROOT/lib/serve_pd_recipe.py" | awk '{print $1}')"
  router_sha="$(sha256sum "$LATENCY_REPO_ROOT/lib/router.py" | awk '{print $1}')"
  sweep_sha="$(
    sha256sum "$LATENCY_REPO_ROOT/ops_latency/run_concurrency_sweep.sh" |
      awk '{print $1}'
  )"
  analyzer_sha="$(
    sha256sum "$LATENCY_REPO_ROOT/ops_latency/compare_dep8_2xdep4.py" |
      awk '{print $1}'
  )"
  runner_sha="$(sha256sum "$0" | awk '{print $1}')"
  local root
  for root in "$LATENCY_RESULTS_ROOT/$experiment_id"/*; do
    [[ -f "$root/status.json" && -f "$root/configuration.json" &&
       -f "$root/manifest.json" ]] || continue
    jq -e \
      --arg phase "$phase" \
      --argjson repetitions "$repetitions" \
      --argjson repetition_start "$repetition_start" \
      '.status == "complete"' "$root/status.json" >/dev/null || continue
    jq -e \
      --arg phase "$phase" \
      --arg profile "$profile" \
      --arg flags "$flags" \
      --arg concurrencies "$concurrencies" \
      --arg workload "$WORKLOAD" \
      --arg namespace "$namespace" \
      --argjson repetitions "$repetitions" \
      --argjson repetition_start "$repetition_start" \
      '.kind == "closed_loop_concurrency_sweep"
       and .profile == $profile
       and .experiment_flags == $flags
       and .cases == "agent-f75"
       and (.phase // "discovery") == $phase
       and .concurrencies == $concurrencies
       and (.repetitions // 1) == $repetitions
       and (.repetition_start // 1) == $repetition_start
       and .search == "fixed"
       and .workload == $workload
       and .loadgen_shards == 8
       and .duration_s == 150
       and .warmup_s == 120
       and .dataset_seed_namespace == $namespace
       and .disable_early_stop == 1' \
      "$root/configuration.json" >/dev/null || continue
    jq -e \
      --arg profile "$profile" \
      --arg flags "$flags" \
      --arg workload "$WORKLOAD" \
      --arg model "$MODEL" \
      --arg model_revision "$MODEL_REVISION" \
      --arg campaign_sha "$campaign_sha" \
      --arg profile_sha "$profile_sha" \
      --arg workload_sha "$workload_sha" \
      --arg experiments_sha "$experiments_sha" \
      --arg loadgen_sha "$loadgen_sha" \
      --arg shards_sha "$shards_sha" \
      --arg search_sha "$search_sha" \
      --arg serve_sha "$serve_sha" \
      --arg pd_sha "$pd_sha" \
      --arg router_sha "$router_sha" \
      --arg sweep_sha "$sweep_sha" \
      --arg analyzer_sha "$analyzer_sha" \
      --arg runner_sha "$runner_sha" \
      --argjson router_connections "$DSV41_ROUTER_CONNECTION_LIMIT" \
      --argjson router_retries "$DSV41_ROUTER_RETRY_CONNECTION_ERRORS" \
      --arg router_load "$DSV41_ROUTER_LOAD_FACTOR" \
      '.profile == $profile
       and .experiments == ($flags | split(" ") | map(select(length > 0)))
       and .workload == $workload
       and .model == $model
       and .model_revision == $model_revision
       and .campaign_sha256 == $campaign_sha
       and .profile_sha256 == $profile_sha
       and .workload_sha256 == $workload_sha
       and .code_sha256.experiment_definitions == $experiments_sha
       and .code_sha256.loadgen == $loadgen_sha
       and .code_sha256.loadgen_shards == $shards_sha
       and .code_sha256.latency_search == $search_sha
       and .code_sha256.serve_recipe == $serve_sha
       and .code_sha256.serve_pd_recipe == $pd_sha
       and .code_sha256.local_router == $router_sha
       and .code_sha256.sweep_runner == $sweep_sha
       and .code_sha256.comparison_analyzer == $analyzer_sha
       and .code_sha256.comparison_runner == $runner_sha
       and .aggregated_router_config.load_factor == ($router_load | tonumber)
       and .aggregated_router_config.connection_limit == $router_connections
       and .aggregated_router_config.retry_connection_errors
         == ($router_retries == 1)' \
      "$root/manifest.json" >/dev/null || continue
    return 0
  done
  return 1
}

run_sweep() {
  local experiment_id="$1" profile="$2" flags="$3"
  local phase="${4:-discovery}" repetitions="${5:-1}"
  local repetition_start="${6:-1}" concurrencies="${7:-$COMMON_CONCURRENCIES}"
  if has_complete_run \
    "$experiment_id" "$profile" "$flags" "$phase" \
    "$repetitions" "$repetition_start" \
    "$concurrencies"; then
    latency_log "Reusing completed $phase sweep: $experiment_id"
    return 0
  fi
  local -a sync_arg=()
  [[ "$LATENCY_SYNC" == 1 ]] || sync_arg+=(--no-sync)
  LATENCY_LOADGEN_SHARDS=8 \
    SWEEP_CASES=agent-f75 \
    SWEEP_CONCURRENCIES="$concurrencies" \
    SWEEP_DURATION_S=150 \
    SWEEP_WARMUP_S=120 \
    SWEEP_SEARCH=fixed \
    SWEEP_WORKLOAD="$WORKLOAD" \
    SWEEP_DATASET_SEED_NAMESPACE="$COMMON_NAMESPACE-${phase}" \
    SWEEP_REPETITIONS="$repetitions" \
    SWEEP_REPETITION_START="$repetition_start" \
    SWEEP_PHASE="$phase" \
    SWEEP_DISABLE_EARLY_STOP=1 \
    bash "$SCRIPT_DIR/run_concurrency_sweep.sh" \
      "$experiment_id" "$profile" "$flags" "${sync_arg[@]}"
}

current_smoke_root() {
  local root
  root="$(latency_latest_completed_run LAT-CMP-2XDEP4-SMOKE || true)"
  [[ -n "$root" && -f "$root/configuration.json" &&
     -f "$root/manifest.json" ]] || return 1
  jq -e '
    .kind == "two_dep4_launch_smoke"
    and .profile == "latency-2xdep4-sla"
  ' "$root/configuration.json" >/dev/null || return 1
  jq -e \
    --arg campaign_sha \
      "$(sha256sum "$LATENCY_CAMPAIGN_CONFIG" | awk '{print $1}')" \
    --arg profile_sha \
      "$(sha256sum "$LATENCY_REPO_ROOT/serving/b200/vllm/profiles/latency-2xdep4-sla.yaml" | awk '{print $1}')" \
    --arg workload_sha "$(sha256sum "$WORKLOAD" | awk '{print $1}')" \
    --arg serve_sha \
      "$(sha256sum "$LATENCY_REPO_ROOT/lib/serve_recipe.py" | awk '{print $1}')" \
    --arg router_sha \
      "$(sha256sum "$LATENCY_REPO_ROOT/lib/router.py" | awk '{print $1}')" \
    --arg analyzer_sha \
      "$(sha256sum "$LATENCY_REPO_ROOT/ops_latency/compare_dep8_2xdep4.py" | awk '{print $1}')" \
    --arg runner_sha "$(sha256sum "$0" | awk '{print $1}')" \
    '.profile == "latency-2xdep4-sla"
     and .experiments == []
     and .campaign_sha256 == $campaign_sha
     and .profile_sha256 == $profile_sha
     and .workload_sha256 == $workload_sha
     and .code_sha256.serve_recipe == $serve_sha
     and .code_sha256.local_router == $router_sha
     and .code_sha256.comparison_analyzer == $analyzer_sha
     and .code_sha256.comparison_runner == $runner_sha' \
    "$root/manifest.json" >/dev/null || return 1
  printf '%s\n' "$root"
}

analyze_comparison() {
  local required_stage="$1"
  "$LATENCY_PYTHON" "$SCRIPT_DIR/compare_dep8_2xdep4.py" \
    --campaign "$LATENCY_CAMPAIGN_CONFIG" \
    --results-root "$LATENCY_RESULTS_ROOT" \
    --output "$SELECTION_JSON" \
    --require-stage "$required_stage" \
    >"$COMPARISON_ROOT/analyzer-$required_stage.log"
}

if smoke_root="$(current_smoke_root || true)" &&
   [[ -n "$smoke_root" ]]; then
  latency_log "Reusing completed 2xDEP4 smoke: $smoke_root"
else
  smoke_args=()
  [[ "$LATENCY_SYNC" == 1 ]] || smoke_args+=(--no-sync)
  bash "$SCRIPT_DIR/run_2xdep4_smoke.sh" "${smoke_args[@]}"
fi

run_sweep LAT-CMP-DEP8-R7 latency-dep8-sla ""
run_sweep LAT-CMP-2XDEP4-API2-S64 latency-2xdep4-sla ""
run_sweep \
  LAT-CMP-2XDEP4-API4-S64 latency-2xdep4-sla "lat-api-4"

analyze_comparison api
jq -e '
  .dataset_pairing.discovery_by_arm.dep4_api2.complete_and_match == true
  and .dataset_pairing.discovery_by_arm.dep4_api4.complete_and_match == true
' \
  "$SELECTION_JSON" >/dev/null ||
  latency_die "paired discovery datasets do not have matching SHA-256 hashes"

SEQ80_ID="$(jq -r '.selected_seq80_definition.experiment_id' "$SELECTION_JSON")"
SEQ80_PROFILE="$(jq -r '.selected_seq80_definition.profile' "$SELECTION_JSON")"
SEQ80_FLAGS="$(
  jq -r '.selected_seq80_definition.experiment_flags | join(" ")' \
    "$SELECTION_JSON"
)"
[[ -n "$SEQ80_ID" && "$SEQ80_ID" != null ]] ||
  latency_die "API correction produced no seq80 arm"
run_sweep "$SEQ80_ID" "$SEQ80_PROFILE" "$SEQ80_FLAGS"

analyze_comparison final
DEP8_ARM="$(jq -r '.selected_dep8_point.arm' "$SELECTION_JSON")"
DEP8_C="$(jq -r '.selected_dep8_point.concurrency' "$SELECTION_JSON")"
DEP4_ARM="$(jq -r '.selected_dep4_point.arm' "$SELECTION_JSON")"
DEP4_C="$(jq -r '.selected_dep4_point.concurrency' "$SELECTION_JSON")"
for value in "$DEP8_ARM" "$DEP8_C" "$DEP4_ARM" "$DEP4_C"; do
  [[ -n "$value" && "$value" != null ]] ||
    latency_die "final discovery selection is incomplete"
done

arm_value() {
  local arm="$1" field="$2"
  jq -r --arg arm "$arm" --arg field "$field" \
    '.arm_definitions[$arm][$field]
     | if type == "array" then join(" ") else . end' \
    "$SELECTION_JSON"
}

DEP8_ID="$(arm_value "$DEP8_ARM" experiment_id)"
DEP8_PROFILE="$(arm_value "$DEP8_ARM" profile)"
DEP8_FLAGS="$(arm_value "$DEP8_ARM" experiment_flags)"
DEP4_ID="$(arm_value "$DEP4_ARM" experiment_id)"
DEP4_PROFILE="$(arm_value "$DEP4_ARM" profile)"
DEP4_FLAGS="$(arm_value "$DEP4_ARM" experiment_flags)"

run_sweep "$DEP8_ID" "$DEP8_PROFILE" "$DEP8_FLAGS" confirm 2 2 "$DEP8_C"
run_sweep "$DEP4_ID" "$DEP4_PROFILE" "$DEP4_FLAGS" confirm 2 2 "$DEP4_C"

analyze_comparison final
jq -n \
  --arg completed_at "$(date -u +%FT%TZ)" \
  --argjson dep8_confirmed \
    "$(jq '.selected_dep8_point.confirmed' "$SELECTION_JSON")" \
  --argjson dep4_confirmed \
    "$(jq '.selected_dep4_point.confirmed' "$SELECTION_JSON")" \
  --argjson pairing_complete \
    "$(jq '.selected_dataset_pairing.complete_and_match' "$SELECTION_JSON")" \
  --argjson confirmation_pairs_match \
    "$(jq '.dataset_pairing.all_available_confirmation_pairs_match' "$SELECTION_JSON")" \
  --argjson confirmation_warmup_paired \
    "$(jq '.selected_confirmation_warmup_pairing.complete_and_match' "$SELECTION_JSON")" \
  '{
    schema_version: 1,
    status: "complete",
    completed_at: $completed_at,
    dep8_confirmed: $dep8_confirmed,
    dep4_confirmed: $dep4_confirmed,
    selected_discovery_datasets_paired: $pairing_complete,
    available_same_concurrency_confirmation_datasets_paired:
      $confirmation_pairs_match,
    confirmation_warmup_datasets_paired: $confirmation_warmup_paired,
    decision_grade:
      ($dep8_confirmed and $dep4_confirmed and $pairing_complete
       and $confirmation_pairs_match and $confirmation_warmup_paired)
  }' >"$COMPARISON_ROOT/status.json"

latency_build_report
latency_sync_results "DEP8 versus 2xDEP4 comparison complete"
latency_log \
  "Comparison complete: $SELECTION_JSON (decision-grade=$(jq -r .decision_grade "$COMPARISON_ROOT/status.json"))"
