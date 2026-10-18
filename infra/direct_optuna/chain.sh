#!/usr/bin/env bash
set -euo pipefail
main() {
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
OUT="$ROOT/.artifacts/optuna-direct-v1"
trap 'rc=$?; if [ "$rc" -ne 0 ]; then printf "Chain failed: exit %s at %s\n" "$rc" "$(date -u +%FT%TZ)" >> "$OUT/chain-error.log"; fi' EXIT
if [ ! -f "$OUT/search-finished.json" ]; then
  bash infra/direct_optuna/launch.sh search
fi
if [ ! -f "$OUT/confirmation-selection.json" ]; then
  python3 infra/direct_optuna/select_confirmation.py > "$OUT/confirmation-selection.log"
fi
if [ ! -f "$OUT/confirmation-finished.json" ]; then
  bash infra/direct_optuna/launch.sh confirmation
fi
MPLCONFIGDIR=/tmp/iar-direct-optuna-mpl .venv/bin/python infra/direct_optuna/report.py
}
main "$@"
