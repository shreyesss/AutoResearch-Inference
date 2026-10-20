#!/usr/bin/env bash
# Active-campaign dispatcher retained for compatibility with LAT wrappers.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPERIMENT_ID="${1:?usage: run_experiment.sh EXPERIMENT_ID [options]}"
shift
case "$EXPERIMENT_ID" in
  LAT-00)
    exec "$SCRIPT_DIR/run_import_evidence.sh" "$@"
    ;;
  LAT-PD-SMOKE)
    exec "$SCRIPT_DIR/run_pd_smoke.sh" "$@"
    ;;
  LAT-TP4-BALANCED|LAT-TP4-LOW|LAT-TP4-HYBRID|LAT-PD-BASELINE|LAT-PD-PREFILL16K|LAT-PD-DECODE64)
    exec "$SCRIPT_DIR/run_active_config.sh" "$EXPERIMENT_ID" "$@"
    ;;
  *)
    echo "unknown active latency experiment: $EXPERIMENT_ID" >&2
    echo "legacy LAT-01..LAT-12 live under ops_latency/deferred/legacy" >&2
    exit 2
    ;;
esac
