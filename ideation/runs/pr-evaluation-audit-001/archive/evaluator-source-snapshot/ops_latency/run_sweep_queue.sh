#!/usr/bin/env bash
# Run a fixed queue of concurrency sweeps back to back until a deadline.
#
# Queue entries are EXPERIMENT_ID|PROFILE|FLAGS. Lines beginning with
# "@env NAME=VALUE" change SWEEP_* settings for following entries.
#
# Usage: run_sweep_queue.sh QUEUE_FILE DEADLINE_UTC [ESTIMATE_MINUTES]

set -Euo pipefail

QUEUE_FILE="${1:?usage: run_sweep_queue.sh QUEUE_FILE DEADLINE_UTC [ESTIMATE_MINUTES]}"
DEADLINE="${2:?missing deadline (UTC, e.g. 2026-10-15T11:30:00Z)}"
ESTIMATE_MINUTES="${3:-70}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
deadline_epoch="$(date -u -d "$DEADLINE" +%s)"

log() {
  printf '%s queue: %s\n' "$(date -u +%FT%TZ)" "$*"
}

while pgrep -f "ops_latency/run_concurrency_sweep.sh" >/dev/null; do
  sleep 30
done

while IFS='|' read -r experiment_id profile flags; do
  [[ -z "${experiment_id// }" || "$experiment_id" == \#* ]] && continue
  if [[ "$experiment_id" == "@env "* ]]; then
    setting="${experiment_id#@env }"
    export "${setting%%=*}=${setting#*=}"
    log "setting ${setting%%=*}=${setting#*=}"
    continue
  fi
  if (( $(date -u +%s) + ESTIMATE_MINUTES * 60 > deadline_epoch )); then
    log "skipping $experiment_id: would end after $DEADLINE"
    continue
  fi
  log "starting $experiment_id profile=$profile flags=[$flags]"
  if bash "$SCRIPT_DIR/run_concurrency_sweep.sh" \
    "$experiment_id" "$profile" "$flags" </dev/null; then
    log "finished $experiment_id"
  else
    log "FAILED $experiment_id (exit $?); continuing with the next sweep"
  fi
done <"$QUEUE_FILE"
log "queue complete"
