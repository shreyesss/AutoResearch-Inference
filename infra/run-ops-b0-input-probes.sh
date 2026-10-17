#!/usr/bin/env bash
# First live transport/realization probes for the six pinned ops synthetic loads.
set -u -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
for attempt in $(seq 1 90); do
  if curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 5
done
curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null || {
  echo 'B0 server did not become ready' >&2
  exit 1
}

"$ROOT/infra/first-baseline.sh" smoke || exit 1

run_probe() {
  local workload="$1" rate="$2" count="$3" entries="$4" duration="$5"
  "$ROOT/.venv/bin/python" "$ROOT/infra/run-ops-b0.py" \
    --workload "$workload" --rate "$rate" --count "$count" \
    --dataset-entries "$entries" --duration "$duration" \
    --cell "probe-$workload"
}

run_probe chat 0.5 20 80 80 || echo 'chat probe failed' >&2
run_probe agent 0.2 12 48 80 || echo 'agent probe failed' >&2
run_probe code 0.3 18 72 80 || echo 'code probe failed' >&2
run_probe document 0.1 8 32 100 || echo 'document probe failed' >&2
run_probe mixed 0.2 12 48 80 || echo 'mixed probe failed' >&2
run_probe mixed-bursty 0.2 12 48 80 || echo 'mixed-bursty probe failed' >&2
