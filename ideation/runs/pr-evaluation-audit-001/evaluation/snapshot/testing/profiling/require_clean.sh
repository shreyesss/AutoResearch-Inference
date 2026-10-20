#!/usr/bin/env bash
set -euo pipefail

BASELINE_DIR="${BASELINE_DIR:?set BASELINE_DIR to a completed clean run}"
MARKER="$BASELINE_DIR/clean_complete.json"
MANIFEST="$BASELINE_DIR/manifest.json"

if [[ ! -r "$MARKER" || ! -r "$MANIFEST" ]]; then
  echo "Profiling requires clean_complete.json and manifest.json." >&2
  exit 2
fi

python3 - "$MARKER" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text())
if payload.get("clean_run_complete") is not True:
    raise SystemExit("baseline marker is not a successful clean run")
if not payload.get("completed_cases"):
    raise SystemExit("baseline contains no completed workload cases")
PY

export BASELINE_DIR MARKER MANIFEST
