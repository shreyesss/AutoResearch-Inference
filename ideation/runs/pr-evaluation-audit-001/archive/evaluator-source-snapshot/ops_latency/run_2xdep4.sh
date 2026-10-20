#!/usr/bin/env bash
# Run only the real 2xDEP4 endpoint at the existing R7 load points.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PLAN=0
NO_SYNC=0
while (($#)); do
  case "$1" in
    --plan) PLAN=1; shift ;;
    --no-sync) NO_SYNC=1; shift ;;
    -h|--help)
      cat <<EOF
Usage: $(basename "$0") [--plan] [--no-sync]

Runs latency-2xdep4-sla on agent-f75 at node-wide c=256,384,512.
EOF
      exit 0
      ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if ((PLAN)); then
  cat <<'EOF'
profile: latency-2xdep4-sla
topology: two TP1 x DP4 x EP4 engines behind the fixed local router
workload: agent-f75 (8192 input / 1024 output, target 75% cacheability)
node-wide concurrency: 256 384 512
approximate balanced load per DEP4: 128 192 256
client shards: 8
warmup: 120 seconds
measurement: 150 seconds per concurrency
repetitions: 1
settings: DSpark k5, seq64/rank, graph512, batch16K, API2/replica
EOF
  exit 0
fi

sync_arg=()
((NO_SYNC)) && sync_arg+=(--no-sync)

LATENCY_LOADGEN_SHARDS=8 \
SWEEP_CASES=agent-f75 \
SWEEP_CONCURRENCIES="256 384 512" \
SWEEP_DURATION_S=150 \
SWEEP_WARMUP_S=120 \
SWEEP_SEARCH=fixed \
SWEEP_DATASET_SEED_NAMESPACE=sweep \
SWEEP_REPETITIONS=1 \
SWEEP_REPETITION_START=1 \
SWEEP_PHASE=discovery \
SWEEP_DISABLE_EARLY_STOP=1 \
bash "$SCRIPT_DIR/run_concurrency_sweep.sh" \
  LAT-2XDEP4-R7-VALUES latency-2xdep4-sla "" "${sync_arg[@]}"
