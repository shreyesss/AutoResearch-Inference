#!/usr/bin/env bash
set -Eeuo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/run_active_config.sh" \
  LAT-TP4-HYBRID "$@"
