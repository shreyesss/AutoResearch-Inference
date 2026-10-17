#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

run_dir="$project_root/.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real"
mkdir -p "$run_dir"
started_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\n' "$started_utc" > "$run_dir/overnight-started-utc.txt"
printf '%s\n' "$$" > "$run_dir/overnight-pid.txt"

finish() {
  status=$?
  printf '%s\n' "$status" > "$run_dir/overnight-exit-code.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/overnight-finished-utc.txt"
}
trap finish EXIT

search_status=0
PYTHONUNBUFFERED=1 "$project_root/.venv/bin/iar" search \
  --campaign "$project_root/configs/campaign-v2.json" \
  --backend real \
  --proposer optuna \
  --resume \
  --output-dir "$project_root/.artifacts/autoresearch-codebase" \
  > "$run_dir/overnight-console.log" 2>&1 || search_status=$?
printf '%s\n' "$search_status" > "$run_dir/search-exit-code.txt"
if (( search_status != 0 )); then
  exit "$search_status"
fi

# The exploratory load pilot starts only after outer search releases the GPU.
# Its output and exit code remain separate from the serving search.
adaptive_status=0
PYTHONUNBUFFERED=1 "$project_root/.venv/bin/iar" adaptive \
  --campaign "$project_root/configs/campaign-v2.json" \
  --backend real \
  --output-dir "$project_root/.artifacts/autoresearch-codebase" \
  > "$run_dir/adaptive-pilot-console.log" 2>&1 || adaptive_status=$?
printf '%s\n' "$adaptive_status" > "$run_dir/adaptive-exit-code.txt"
exit "$adaptive_status"
