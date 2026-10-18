#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
bash infra/direct_optuna/launch.sh search
python3 infra/direct_optuna/select_confirmation.py > .artifacts/optuna-direct-v1/confirmation-selection.log
bash infra/direct_optuna/launch.sh confirmation
MPLCONFIGDIR=/tmp/iar-direct-optuna-mpl .venv/bin/python infra/direct_optuna/report.py
