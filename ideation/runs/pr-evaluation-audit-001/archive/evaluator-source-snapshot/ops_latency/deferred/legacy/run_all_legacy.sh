#!/usr/bin/env bash
# Resumable sequential driver for LAT-00 through LAT-12.

set -Eeuo pipefail

LEGACY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LATENCY_DIR="$(cd "$LEGACY_DIR/../.." && pwd)"
# shellcheck source=../../lib/common.sh
source "$LATENCY_DIR/lib/common.sh"

PLAN=0
RERUN=0
FROM=""
ONLY=""
FORWARD=()
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --rerun) RERUN=1; shift ;;
    --from) FROM="${2:?missing experiment ID}"; shift 2 ;;
    --only) ONLY="${2:?missing comma-separated IDs}"; shift 2 ;;
    --no-sync)
      export LATENCY_SYNC=0
      FORWARD+=(--no-sync)
      shift
      ;;
    --duration|--repetitions|--rates|--concurrencies|--requests)
      FORWARD+=("$1" "${2:?missing value for $1}")
      shift 2
      ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") [options]
  --plan             print every selected experiment without running it
  --from LAT-XX      begin at this experiment
  --only CSV         run only the listed experiment IDs
  --rerun            do not skip experiments whose latest status is complete
  --no-sync          pass through to each experiment
  --duration N       pass through to each experiment
  --repetitions N    pass through to each experiment
  --rates CSV        pass through to each experiment
  --concurrencies CSV
  --requests N
EOF
      exit 0
      ;;
    *) latency_die "unknown argument: $1"; exit 2 ;;
  esac
done

EXPERIMENTS=(
  LAT-00 LAT-01 LAT-02 LAT-03 LAT-04 LAT-05 LAT-06
  LAT-07 LAT-08 LAT-09 LAT-10 LAT-11 LAT-12
)

selected() {
  local id="$1"
  if [[ -n "$FROM" ]]; then
    if [[ "$id" == "$FROM" ]]; then
      FROM=""
    else
      return 1
    fi
  fi
  if [[ -n "$ONLY" ]]; then
    case ",$ONLY," in
      *",$id,"*) ;;
      *) return 1 ;;
    esac
  fi
}

latest_completed_root() {
  local latest
  latest="$(latency_latest_run "$1" || true)"
  [[ -n "$latest" && -f "$latest/status.json" ]] || return 1
  jq -e '.status == "complete"' "$latest/status.json" >/dev/null ||
    return 1
  printf '%s\n' "$latest"
}

delivery_complete() {
  local root="$1"
  [[ -f "$root/delivery_status.json" ]] &&
    jq -e \
      '.report_status == "complete" and
       (.sync_status == "complete" or .sync_status == "skipped")' \
      "$root/delivery_status.json" >/dev/null
}

retry_delivery() {
  local root="$1"
  local experiment_id="$2"
  mkdir -p "$LATENCY_RESULTS_ROOT"
  exec 8>"$LATENCY_RESULTS_ROOT/.campaign.lock"
  flock -n 8 || latency_die "another latency campaign process is running"
  latency_deliver "$root" "delivery retry: $experiment_id"
  flock -u 8
  exec 8>&-
}

SELECTED_COUNT=0
for experiment_id in "${EXPERIMENTS[@]}"; do
  selected "$experiment_id" || continue
  SELECTED_COUNT=$((SELECTED_COUNT + 1))
  if [[ "$experiment_id" == LAT-00 ]]; then
    script="$LATENCY_DIR/run_lat_00.sh"
  else
    script="$LEGACY_DIR/run_lat_${experiment_id#LAT-}.sh"
  fi
  if ((PLAN)); then
    "$script" --plan "${FORWARD[@]}"
    continue
  fi
  if ((RERUN == 0)); then
    completed_root="$(latest_completed_root "$experiment_id" || true)"
    if [[ -n "$completed_root" ]]; then
      if ! delivery_complete "$completed_root"; then
        latency_log "Retrying report/S3 delivery for completed $experiment_id."
        retry_delivery "$completed_root" "$experiment_id"
      fi
      latency_log "Skipping completed $experiment_id."
      continue
    fi
  fi
  latency_log "Starting $experiment_id."
  if ((RERUN)); then
    "$script" "${FORWARD[@]}"
  else
    "$script" --resume "${FORWARD[@]}"
  fi
  latency_log "Completed $experiment_id."
done

((SELECTED_COUNT > 0)) || {
  latency_log "ERROR: no experiments matched --from/--only" >&2
  exit 2
}
