#!/usr/bin/env bash
# Mandatory stock-PD NIXL transfer/correctness smoke.

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
      echo "Usage: $(basename "$0") [--plan] [--no-sync]"
      exit 0
      ;;
    *) latency_die "unknown argument: $1"; exit 2 ;;
  esac
done

if ((PLAN)); then
  cat <<EOF
experiment: LAT-PD-SMOKE
profile: pd-tp4-baseline
public_url: http://127.0.0.1:8000/v1
prefill: GPUs 0-3, HTTP 8001, NIXL side ports 5600-5603
decode: GPUs 4-7, HTTP 8002, NIXL side ports 5700-5703
router: native vllm-router, HTTP 8000
fallback: one attempt only when LATENCY_PD_FALLBACK_IMAGE and LATENCY_PD_FALLBACK_ROUTER_BIN are set
EOF
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock
RUN_ROOT="$(latency_new_run_root LAT-PD-SMOKE)"
mkdir -p "$RUN_ROOT"
latency_write_status "$RUN_ROOT" running "stock PD smoke started"
latency_write_manifest \
  "$RUN_ROOT" LAT-PD-SMOKE pd-tp4-baseline "" "text-smoke"

FINAL_STATUS=failed
FINAL_MESSAGE="PD smoke failed"
on_exit() {
  local rc=$?
  trap - EXIT INT TERM
  latency_finalize "$RUN_ROOT" "$FINAL_STATUS" "$FINAL_MESSAGE" || rc=1
  exit "$rc"
}
trap on_exit EXIT
trap 'exit 130' INT TERM

validate_pd_log() {
  local log_file="$1"
  "$LATENCY_PYTHON" - "$log_file" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
if text.count("NixlConnector") < 2:
    raise SystemExit("both PD workers did not report NixlConnector")
bad = re.compile(
    r"(kv[_ -]?load failed|nixl.*(?:error|failed)|recomput(?:e|ing).*(?:prompt|kv))",
    re.IGNORECASE,
)
matches = [line for line in text.splitlines() if bad.search(line)]
if matches:
    raise SystemExit("PD log reports transfer failure/recompute: " + matches[-1][:500])
PY
}

attempt_smoke() {
  local label="$1"
  local log_file="$RUN_ROOT/$label-server.log"
  local smoke_file="$RUN_ROOT/$label-smoke.json"
  latency_start_pd_server pd-tp4-baseline "$log_file" || return 1
  latency_scrape_pd_metrics \
    pd-tp4-baseline "$RUN_ROOT/$label-metrics-before.txt" || true
  "$LATENCY_REPO_ROOT/.venv/bin/python" \
    "$LATENCY_REPO_ROOT/testing/common/smoke.py" \
    --base-url http://127.0.0.1:8000/v1 \
    --model "$SERVED_MODEL" \
    --output "$smoke_file" \
    --skip-image || return 1
  sleep "${LATENCY_PD_SMOKE_SETTLE_SECONDS:-30}"
  latency_scrape_pd_metrics \
    pd-tp4-baseline "$RUN_ROOT/$label-metrics-after.txt" || true
  validate_pd_log "$log_file" || return 1
  latency_stop_server
}

if attempt_smoke stock; then
  jq -n \
    '{schema_version:1, pd_available:true, implementation:"stock", fallback_attempted:false}' \
    >"$RUN_ROOT/pd_availability.json"
  FINAL_STATUS=complete
  FINAL_MESSAGE="stock PD NIXL smoke passed"
else
  latency_stop_server
  if [[ -n "${LATENCY_PD_FALLBACK_IMAGE:-}" &&
        -n "${LATENCY_PD_FALLBACK_ROUTER_BIN:-}" ]]; then
    export VLLM_IMAGE="$LATENCY_PD_FALLBACK_IMAGE"
    export VLLM_ROUTER_BIN="$LATENCY_PD_FALLBACK_ROUTER_BIN"
    if attempt_smoke fallback; then
      jq -n \
        --arg fallback_image "$LATENCY_PD_FALLBACK_IMAGE" \
        --arg fallback_router_bin "$LATENCY_PD_FALLBACK_ROUTER_BIN" \
        '{
          schema_version:1,
          pd_available:true,
          implementation:"fallback-open-pr",
          fallback_attempted:true,
          fallback_image:$fallback_image,
          fallback_router_bin:$fallback_router_bin
        }' \
        >"$RUN_ROOT/pd_availability.json"
      FINAL_STATUS=complete
      FINAL_MESSAGE="stock PD failed; one fallback PD smoke passed"
    else
      latency_stop_server
      jq -n \
        '{schema_version:1, pd_available:false, implementation:null, fallback_attempted:true}' \
        >"$RUN_ROOT/pd_availability.json"
      exit 1
    fi
  else
    jq -n \
      '{schema_version:1, pd_available:false, implementation:null, fallback_attempted:false, reason:"stock failed and no prebuilt fallback was configured"}' \
      >"$RUN_ROOT/pd_availability.json"
    exit 1
  fi
fi
