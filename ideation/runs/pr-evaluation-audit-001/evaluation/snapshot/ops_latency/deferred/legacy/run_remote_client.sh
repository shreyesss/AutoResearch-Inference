#!/usr/bin/env bash
# Run the LAT-12 remote ingress arm from the intended load-generator host.

set -Eeuo pipefail

LEGACY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LATENCY_DIR="$(cd "$LEGACY_DIR/../.." && pwd)"
# shellcheck source=../../lib/common.sh
source "$LATENCY_DIR/lib/common.sh"

: "${LATENCY_REMOTE_BASE_URL:?set LATENCY_REMOTE_BASE_URL}"
: "${LATENCY_REMOTE_DATASET:?set LATENCY_REMOTE_DATASET to request JSONL}"

PLAN=0
[[ "${1:-}" == "--plan" ]] && PLAN=1
if ((PLAN)); then
  cat <<EOF
experiment: LAT-12
arm: remote-gateway
base_url: $LATENCY_REMOTE_BASE_URL
dataset: $LATENCY_REMOTE_DATASET
rates: ${LATENCY_RATES:-0.5,1,2,4,8,12,16,20}
results_root: $LATENCY_RESULTS_ROOT
EOF
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock
if [[ -n "${LATENCY_REMOTE_RUN_ROOT:-}" ]]; then
  [[ -d "$LATENCY_REMOTE_RUN_ROOT" ]] ||
    latency_die "LATENCY_REMOTE_RUN_ROOT does not exist"
  case "/$(realpath -m "$LATENCY_REMOTE_RUN_ROOT")/" in
    "$LATENCY_RESULTS_ROOT"/LAT-12/*/) ;;
    *) latency_die "LATENCY_REMOTE_RUN_ROOT must be an existing LAT-12 run" ;;
  esac
  RUN_ROOT="$LATENCY_REMOTE_RUN_ROOT/arms/remote-gateway"
else
  RUN_ROOT="$(latency_new_run_root LAT-12)/arms/remote-gateway"
fi
mkdir -p "$RUN_ROOT"
latency_write_manifest \
  "$RUN_ROOT" LAT-12 remote-client "" "$LATENCY_REMOTE_DATASET"
latency_write_status "$RUN_ROOT" running "remote client started"

finalize_remote() {
  local rc=$?
  local final_rc=$rc
  trap - EXIT INT TERM
  if ((rc == 0)); then
    latency_finalize "$RUN_ROOT" complete "remote client complete" ||
      final_rc=1
  else
    latency_finalize \
      "$RUN_ROOT" failed "remote client failed (exit $rc)" ||
      final_rc="$rc"
  fi
  exit "$final_rc"
}
trap finalize_remote EXIT
trap 'exit 130' INT TERM

SCREEN="$RUN_ROOT/production-mix-32k/open"
latency_search \
  "$LATENCY_REMOTE_DATASET" \
  "$SCREEN" \
  open \
  "${LATENCY_RATES:-0.5,1,2,4,8,12,16,20}" \
  "$LATENCY_REMOTE_BASE_URL"

BOUNDARY_RATES="$(
  "$LATENCY_PYTHON" - "$SCREEN/latency_search_summary.json" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1]))
rates = {
    item["load_point"]
    for item in summary.get("highest_passing", {}).values()
    if isinstance(item, dict) and item.get("load_point") is not None
}
print(",".join(f"{rate:g}" for rate in sorted(rates)))
PY
)"
if [[ -n "$BOUNDARY_RATES" ]]; then
  LATENCY_REPETITIONS="${LATENCY_BOUNDARY_REPETITIONS:-5}" \
    latency_search \
      "$LATENCY_REMOTE_DATASET" \
      "$RUN_ROOT/production-mix-32k/boundary" \
      open \
      "$BOUNDARY_RATES" \
      "$LATENCY_REMOTE_BASE_URL"
fi
