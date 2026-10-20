#!/usr/bin/env bash
set -Eeuo pipefail
exec "$(cd "$(dirname "$0")" && pwd)/run_experiment_legacy.sh" "$@"
