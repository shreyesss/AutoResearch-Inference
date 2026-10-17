#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
run_root="$project_root/.artifacts/v3-independent-capture"
scenario_id="qwen-ops-mixed-development-1042-v1"
mkdir -p "$run_root"

finish() {
  status=$?
  printf '%s\n' "$status" > "$run_root/${scenario_id}.capture-exit-code.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_root/${scenario_id}.capture-finished-utc.txt"
  bash "$project_root/infra/first-baseline.sh" down \
    > "$run_root/${scenario_id}.server-stop.log" 2>&1 || true
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for _ in $(seq 1 300); do
  if curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 2
done
curl --fail --silent --max-time 5 http://127.0.0.1:8000/health >/dev/null
date -u +%Y-%m-%dT%H:%M:%SZ > "$run_root/${scenario_id}.capture-started-utc.txt"

"$project_root/.venv/bin/python" "$project_root/infra/run-ops-b0.py" \
  --workload mixed --rate 0.1 --count 240 --duration 4800 --timeout 5400 \
  --dataset-entries 960 --random-seed 1042 \
  --root "$run_root" --cell "$scenario_id" \
  > "$run_root/${scenario_id}.capture-console.log" 2>&1

"$project_root/.venv/bin/python" "$project_root/infra/freeze-ops-synthetic-cell.py" \
  --cell "$run_root/$scenario_id" --scenario-id "$scenario_id" \
  --split development \
  > "$run_root/${scenario_id}.freeze.json"
