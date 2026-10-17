#!/usr/bin/env bash
# Bounded live Qwen transport checks for the existing production input sources.
set -u -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null || exit 1

run_probe() {
  local workload="$1" count="$2"
  "$ROOT/.venv/bin/python" "$ROOT/infra/run-ops-production-b0.py" \
    --workload "$workload" --cell "probe-prefix-$workload" \
    --count "$count" --duration 120 --timeout 900
}

run_probe mooncake-median 12 || echo 'mooncake-median probe failed' >&2
run_probe mooncake-burst 12 || echo 'mooncake-burst probe failed' >&2
run_probe mooncake-cache-heavy 12 || echo 'mooncake-cache-heavy probe failed' >&2
"$ROOT/.venv/bin/python" "$ROOT/infra/run-ops-production-b0.py" \
  --workload exgentic --cell probe-exgentic \
  --conversations 1 --duration 120 --timeout 900 || echo 'exgentic probe failed' >&2
