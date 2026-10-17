#!/usr/bin/env bash
# Two real B0 load points per qualified synthetic ops_aiperf family.
# These are calibration cells; finalist schedules are frozen from their raw exports.
set -u -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1
curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null || exit 1

run_cell() {
  local name="$1" label="$2" rate="$3" count="$4" entries="$5" cap="$6"
  "$ROOT/.venv/bin/python" "$ROOT/infra/run-ops-b0.py" \
    --workload "$name" --rate "$rate" --count "$count" \
    --dataset-entries "$entries" --duration "$cap" --timeout 900 \
    --cell "curve-$name-$label"
}

run_cell chat low 2.56 307 1228 240 || echo 'chat low failed' >&2
run_cell chat high 3.2 384 1536 240 || echo 'chat high failed' >&2
run_cell agent low 0.15 27 108 360 || echo 'agent low failed' >&2
run_cell agent high 0.3 54 216 360 || echo 'agent high failed' >&2
run_cell code low 0.2 36 144 360 || echo 'code low failed' >&2
run_cell code high 0.4 72 288 360 || echo 'code high failed' >&2
run_cell document low 0.1 18 72 360 || echo 'document low failed' >&2
run_cell document high 0.2 36 144 360 || echo 'document high failed' >&2
run_cell mixed low 0.2 36 144 360 || echo 'mixed low failed' >&2
run_cell mixed high 0.4 72 288 360 || echo 'mixed high failed' >&2
run_cell mixed-bursty low 0.2 36 144 360 || echo 'mixed-bursty low failed' >&2
run_cell mixed-bursty high 0.4 72 288 360 || echo 'mixed-bursty high failed' >&2
