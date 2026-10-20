#!/usr/bin/env bash
# Compare NVIDIA's NVFP4 checkpoint using the R4d TP4 configuration.
#
# First run setup_nvfp4_model.sh, then this script. The checkpoint, image, and
# vLLM source revisions are pinned; no throughput profile is modified.

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../lib/env.sh
source "$ROOT/lib/env.sh"

NVFP4_MODEL="${NVFP4_MODEL:-nvidia/DeepSeek-V4.1-Flash-NVFP4}"
NVFP4_MODEL_REVISION="${NVFP4_MODEL_REVISION:-c48dca0146b56d64c8116dbb6fcace8b7cc835f8}"
NVFP4_VLLM_COMMIT="${NVFP4_VLLM_COMMIT:-1800929afdd3728860f794bcf69ae7beda95649d}"
NVFP4_VLLM_IMAGE="${NVFP4_VLLM_IMAGE:-dsv41/vllm-openai:nvfp4-engram-1800929}"
NVFP4_EXPERIMENT_ID="${NVFP4_EXPERIMENT_ID:-LAT-R4d-NVFP4-TP4-DSPARK2-B16K-G512}"
NVFP4_SERVED_MODEL="${NVFP4_SERVED_MODEL:-deepseek-v4.1-flash-nvfp4}"
DRY_RUN="${DRY_RUN:-0}"
SNAPSHOT_ROOT="$HF_HOME/hub/models--nvidia--DeepSeek-V4.1-Flash-NVFP4/snapshots/$NVFP4_MODEL_REVISION"
FLAGS="lat-dspark-k2 lat-seqs-256 lat-graph-512 lat-batched-16k"
FORWARD=()

while (($#)); do
  case "$1" in
    --no-sync)
      FORWARD+=(--no-sync)
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h | --help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      printf 'ERROR: unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

print_command() {
  printf '%q ' "$@"
  printf '\n'
}

if [[ "$DRY_RUN" != 1 ]]; then
  [[ -f "$SNAPSHOT_ROOT/config.json" ]] || {
    printf 'ERROR: checkpoint is not installed at %s\n' "$SNAPSHOT_ROOT" >&2
    printf 'Run: bash ops_latency/setup_nvfp4_model.sh\n' >&2
    exit 1
  }
  image_commit="$(
    docker image inspect "$NVFP4_VLLM_IMAGE" \
      --format '{{ index .Config.Labels "ai.vllm.source.revision" }}' \
      2>/dev/null || true
  )"
  [[ "$image_commit" == "$NVFP4_VLLM_COMMIT" ]] || {
    printf 'ERROR: image %s is missing or not built from %s\n' \
      "$NVFP4_VLLM_IMAGE" "$NVFP4_VLLM_COMMIT" >&2
    printf 'Run: bash ops_latency/setup_nvfp4_model.sh\n' >&2
    exit 1
  }
fi

export MODEL="$NVFP4_MODEL"
export MODEL_REVISION="$NVFP4_MODEL_REVISION"
export SERVED_MODEL="$NVFP4_SERVED_MODEL"
export VLLM_IMAGE="$NVFP4_VLLM_IMAGE"
export DSV41_ROUTER_LOAD_FACTOR="${DSV41_ROUTER_LOAD_FACTOR:-1.1}"
export SWEEP_CASES="agent-f75 chat-f50"
export SWEEP_SEARCH=fixed
export SWEEP_CONCURRENCIES="128 192 256"
export SWEEP_DURATION_S="${SWEEP_DURATION_S:-150}"
export SWEEP_WARMUP_S="${SWEEP_WARMUP_S:-120}"
export SWEEP_STOP_TTFT_P50_MS="${SWEEP_STOP_TTFT_P50_MS:-5000}"
export SWEEP_STOP_ERROR_RATE="${SWEEP_STOP_ERROR_RATE:-0.01}"
export LATENCY_LOADGEN_SHARDS="${LATENCY_LOADGEN_SHARDS:-8}"

command=(
  bash "$ROOT/ops_latency/run_concurrency_sweep.sh"
  "$NVFP4_EXPERIMENT_ID"
  balanced
  "$FLAGS"
  "${FORWARD[@]}"
)

if [[ "$DRY_RUN" == 1 ]]; then
  printf 'MODEL=%q MODEL_REVISION=%q SERVED_MODEL=%q VLLM_IMAGE=%q \\\n' \
    "$MODEL" "$MODEL_REVISION" "$SERVED_MODEL" "$VLLM_IMAGE"
  printf 'SWEEP_CASES=%q SWEEP_CONCURRENCIES=%q LATENCY_LOADGEN_SHARDS=%q \\\n' \
    "$SWEEP_CASES" "$SWEEP_CONCURRENCIES" "$LATENCY_LOADGEN_SHARDS"
  print_command "${command[@]}"
  exit 0
fi

exec "${command[@]}"
