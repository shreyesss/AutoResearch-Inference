#!/usr/bin/env bash
# Run an isolated AIPerf synthetic or production workload suite.

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../lib/env.sh
source "$ROOT/lib/env.sh"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

exec "$PYTHON" -m ops_aiperf.runner "$@"
