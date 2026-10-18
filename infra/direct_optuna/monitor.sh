#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
while true; do
  python3 infra/direct_optuna/health.py
  MPLCONFIGDIR=/tmp/iar-direct-optuna-mpl .venv/bin/python infra/direct_optuna/report.py
  nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,power.draw --format=csv,noheader >> .artifacts/optuna-direct-v1/gpu-monitor.csv
  if [ -f .artifacts/optuna-direct-v1/confirmation-finished.json ] || [ -f .artifacts/optuna-direct-v1/fatal.json ]; then
    break
  fi
  sleep 30
done
