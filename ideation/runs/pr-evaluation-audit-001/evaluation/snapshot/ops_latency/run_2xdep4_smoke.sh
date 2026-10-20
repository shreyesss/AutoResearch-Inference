#!/usr/bin/env bash
# Mandatory launch/route smoke for the real same-node 2xDEP4 profile.

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

EXPERIMENT_ID="LAT-CMP-2XDEP4-SMOKE"
PROFILE="latency-2xdep4-sla"
WORKLOAD="$LATENCY_REPO_ROOT/testing/workloads/latency-active-matrix.yaml"

if ((PLAN)); then
  cat <<EOF
experiment_id: $EXPERIMENT_ID
profile: $PROFILE
public_endpoint: http://127.0.0.1:8000/v1
backend_endpoints:
  - http://127.0.0.1:8100/v1
  - http://127.0.0.1:8101/v1
checks: backend smoke, public smoke, both router counters positive
EOF
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock

RUN_ROOT="$(latency_new_run_root "$EXPERIMENT_ID")"
mkdir -p "$RUN_ROOT"
latency_write_status "$RUN_ROOT" running "2xDEP4 launch smoke started"
latency_write_manifest \
  "$RUN_ROOT" "$EXPERIMENT_ID" "$PROFILE" "" "$WORKLOAD"
jq -n \
  --arg profile "$PROFILE" \
  '{
    schema_version: 1,
    kind: "two_dep4_launch_smoke",
    profile: $profile,
    public_endpoint: "http://127.0.0.1:8000/v1",
    backend_endpoints: [
      "http://127.0.0.1:8100/v1",
      "http://127.0.0.1:8101/v1"
    ]
  }' >"$RUN_ROOT/configuration.json"

FINAL_STATUS=failed
FINAL_MESSAGE="2xDEP4 launch smoke failed"
on_exit() {
  local rc=$?
  trap - EXIT INT TERM
  latency_finalize "$RUN_ROOT" "$FINAL_STATUS" "$FINAL_MESSAGE" || rc=1
  exit "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

latency_start_server "$PROFILE" "" "$RUN_ROOT/server.log"
latency_start_telemetry "$PROFILE" "$RUN_ROOT/telemetry"

for port in 8100 8101; do
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/testing/common/smoke.py" \
    --base-url "http://127.0.0.1:$port/v1" \
    --model "$SERVED_MODEL" \
    --output "$RUN_ROOT/backend-$port-smoke.json" \
    --skip-image
done

"$LATENCY_REPO_ROOT/.venv/bin/python" \
  "$LATENCY_REPO_ROOT/testing/common/smoke.py" \
  --base-url http://127.0.0.1:8000/v1 \
  --model "$SERVED_MODEL" \
  --output "$RUN_ROOT/router-smoke.json" \
  --skip-image

curl -fsS http://127.0.0.1:8000/health >"$RUN_ROOT/router-health.json"
curl -fsS http://127.0.0.1:8000/metrics >"$RUN_ROOT/router-metrics.txt"
"$LATENCY_PYTHON" - "$RUN_ROOT/router-metrics.txt" \
  >"$RUN_ROOT/router-balance.json" <<'PY'
import json
import re
import sys
from pathlib import Path

pattern = re.compile(
    r'dsv41_router_requests_total\{kind="requests_backend_([01])"\}\s+([0-9.]+)'
)
counts = {int(index): float(value) for index, value in pattern.findall(
    Path(sys.argv[1]).read_text(encoding="utf-8")
)}
if counts.get(0, 0) <= 0 or counts.get(1, 0) <= 0:
    raise SystemExit(f"router did not reach both DEP4 backends: {counts}")
print(json.dumps({"backend_request_counts": counts, "both_reached": True}, indent=2))
PY

latency_stop_telemetry
latency_stop_server
FINAL_STATUS=complete
FINAL_MESSAGE="2xDEP4 launch smoke complete; both backends routed"
