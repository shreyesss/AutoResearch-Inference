#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

PLAN=0
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --no-sync) export LATENCY_SYNC=0; shift ;;
    *) latency_die "unknown argument: $1"; exit 2 ;;
  esac
done
if ((PLAN)); then
  "$LATENCY_PYTHON" "$SCRIPT_DIR/campaign_query.py" \
    --campaign "$LATENCY_CAMPAIGN_CONFIG" --id LAT-00
  exit 0
fi

latency_require_safe_root
latency_require_tools
latency_acquire_lock
RUN_ROOT="$(latency_new_run_root LAT-00)"
mkdir -p "$RUN_ROOT"
latency_write_status "$RUN_ROOT" running "evidence import started"
latency_write_manifest \
  "$RUN_ROOT" LAT-00 evidence-import "" "$LATENCY_ARCHIVE_ROOT"
latency_write_status "$RUN_ROOT" complete "evidence import complete"
latency_deliver "$RUN_ROOT" "LAT-00 evidence import"
