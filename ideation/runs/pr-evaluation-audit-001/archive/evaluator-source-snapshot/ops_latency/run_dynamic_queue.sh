#!/usr/bin/env bash
# Run editable concurrency-sweep queue entries one at a time until a deadline.
#
# Entry format:
#   EXPERIMENT_ID|PROFILE|FLAGS|NAME=VALUE;NAME=VALUE
#
# The queue is reread and atomically popped before every run. Completed entries
# are appended to QUEUE_FILE.done, so pending entries may be safely reordered.
#
# Usage: run_dynamic_queue.sh QUEUE_FILE DEADLINE_UTC [ESTIMATE_MINUTES]

set -Euo pipefail

QUEUE_FILE="${1:?usage: run_dynamic_queue.sh QUEUE_FILE DEADLINE_UTC [ESTIMATE_MINUTES]}"
DEADLINE="${2:?missing deadline (UTC)}"
ESTIMATE_MINUTES="${3:-45}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
deadline_epoch="$(date -u -d "$DEADLINE" +%s)"
PYTHON="$SCRIPT_DIR/../.venv/bin/python"

log() {
  printf '%s queue: %s\n' "$(date -u +%FT%TZ)" "$*"
}

pop_entry() {
  "$PYTHON" - "$QUEUE_FILE" <<'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    lines = path.read_text().splitlines()
except FileNotFoundError:
    raise SystemExit(0)
for index, line in enumerate(lines):
    if line.strip() and not line.lstrip().startswith("#"):
        remaining = lines[:index] + lines[index + 1 :]
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(
            "\n".join(remaining) + ("\n" if remaining else "")
        )
        os.replace(temporary, path)
        print(line)
        break
PY
}

while true; do
  while pgrep -f "ops_latency/run_concurrency_sweep.sh" >/dev/null; do
    sleep 30
  done
  if (( $(date -u +%s) + ESTIMATE_MINUTES * 60 > deadline_epoch )); then
    log "deadline $DEADLINE reached for new sweeps; stopping"
    break
  fi
  entry="$(pop_entry)"
  if [[ -z "$entry" ]]; then
    sleep 60
    continue
  fi
  IFS='|' read -r experiment_id profile flags settings <<<"$entry"
  log \
    "starting $experiment_id profile=$profile flags=[$flags] settings=[$settings]"
  started="$(date -u +%FT%TZ)"
  (
    IFS=';' read -r -a pairs <<<"${settings:-}"
    for pair in "${pairs[@]}"; do
      [[ -n "$pair" ]] && export "${pair%%=*}=${pair#*=}"
    done
    exec bash "$SCRIPT_DIR/run_concurrency_sweep.sh" \
      "$experiment_id" "$profile" "$flags" </dev/null
  )
  status=$?
  printf '%s|%s|exit=%s\n' "$started" "$entry" "$status" \
    >>"$QUEUE_FILE.done"
  log "finished $experiment_id exit=$status"
done
log "queue complete"
