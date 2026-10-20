#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/lib/env.sh"
ensure_storage_dirs

HARDWARE="${HARDWARE:?set HARDWARE}"
ENGINE="${ENGINE:?set ENGINE}"
PROFILE="${PROFILE:-balanced}"
WORKLOAD="${WORKLOAD:-$ROOT/testing/workloads/default-mix.yaml}"

args=(
  --hardware "$HARDWARE"
  --engine "$ENGINE"
  --profile "$PROFILE"
  --workload "$WORKLOAD"
  --base-url "${BASE_URL:-http://127.0.0.1:$PORT/v1}"
  --requests "${REQUESTS:-128}"
  --screen-duration "${SCREEN_DURATION:-30}"
  --boundary-duration "${BOUNDARY_DURATION:-30}"
  --repetitions "${REPETITIONS:-3}"
  --request-timeout "${REQUEST_TIMEOUT:-600}"
  --search-mode "${SEARCH_MODE:-slo-capacity}"
)

if [[ -n "${CLOSED_DURATION:-}" ]]; then
  args+=(--closed-duration "$CLOSED_DURATION")
fi
if [[ -n "${OPEN_DURATION:-}" ]]; then
  args+=(--open-duration "$OPEN_DURATION")
fi

if [[ -n "${CASES:-}" ]]; then
  IFS=',' read -r -a cases <<<"$CASES"
  for case_name in "${cases[@]}"; do
    args+=(--case "$case_name")
  done
fi
if [[ "${SKIP_SMOKE:-0}" == 1 ]]; then
  args+=(--skip-smoke)
fi
if [[ "${AIPERF_CROSSCHECK:-0}" == 1 ]]; then
  args+=(--aiperf-crosscheck)
fi

exec "$ROOT/.venv/bin/python" "$ROOT/testing/common/run_suite.py" "${args[@]}"
