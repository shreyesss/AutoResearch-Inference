#!/usr/bin/env bash
# One-factor-at-a-time tuning sweep around the measured 2xDEP4 R7 baseline.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

run_variant() {
  local experiment_id="$1"
  local flags="$2"

  printf '%s starting %s flags=[%s]\n' \
    "$(date -u +%FT%TZ)" "$experiment_id" "$flags"

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
      "$experiment_id" latency-2xdep4-sla "$flags"

  printf '%s completed %s\n' "$(date -u +%FT%TZ)" "$experiment_id"
}

# Baseline: seq64, DSpark k5, batch16K, graph512, API2 per replica.
run_variant LAT-2XDEP4-R7a "lat-seqs-80"
run_variant LAT-2XDEP4-R7b "lat-seqs-128"
run_variant LAT-2XDEP4-R7c "lat-dspark-k2"
run_variant LAT-2XDEP4-R7d "lat-batched-8k"
run_variant LAT-2XDEP4-R7e "batched-32k"
