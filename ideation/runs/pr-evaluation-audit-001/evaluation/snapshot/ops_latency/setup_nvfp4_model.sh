#!/usr/bin/env bash
# Install the pinned NVIDIA NVFP4 checkpoint and build the matching vLLM fork.
# This setup never exposes GPUs to Docker and refuses to run beside a benchmark.

set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../lib/env.sh
source "$ROOT/lib/env.sh"

NVFP4_MODEL="${NVFP4_MODEL:-nvidia/DeepSeek-V4.1-Flash-NVFP4}"
NVFP4_MODEL_REVISION="${NVFP4_MODEL_REVISION:-c48dca0146b56d64c8116dbb6fcace8b7cc835f8}"
NVFP4_VLLM_REPOSITORY="${NVFP4_VLLM_REPOSITORY:-https://github.com/Zhehao-Hu/vllm.git}"
NVFP4_VLLM_COMMIT="${NVFP4_VLLM_COMMIT:-1800929afdd3728860f794bcf69ae7beda95649d}"
NVFP4_VLLM_BASE_IMAGE="${NVFP4_VLLM_BASE_IMAGE:-dsv41/vllm-openai:nvfp4-engram-1800929}"
NVFP4_VLLM_IMAGE="${NVFP4_VLLM_IMAGE:-dsv41/vllm-openai:nvfp4-engram-moeep-1800929}"
NVFP4_VLLM_SOURCE_ROOT="${NVFP4_VLLM_SOURCE_ROOT:-$MODEL_STORAGE_ROOT/src/vllm-nvfp4-engram}"
NVFP4_BUILD_JOBS="${NVFP4_BUILD_JOBS:-4}"
NVFP4_NVCC_THREADS="${NVFP4_NVCC_THREADS:-4}"
NVFP4_RUN_WHEEL_CHECK="${NVFP4_RUN_WHEEL_CHECK:-false}"
NVFP4_SKIP_DOWNLOAD="${NVFP4_SKIP_DOWNLOAD:-0}"
NVFP4_SKIP_IMAGE_BUILD="${NVFP4_SKIP_IMAGE_BUILD:-0}"
NVFP4_ALLOW_BUSY_SETUP="${NVFP4_ALLOW_BUSY_SETUP:-0}"
DRY_RUN="${DRY_RUN:-0}"
HF_CLI="${HF_CLI:-$ROOT/.venv/bin/hf}"
SETUP_ROOT="$MODEL_STORAGE_ROOT/nvfp4"
STATE_FILE="$SETUP_ROOT/setup.env"
SNAPSHOT_ROOT="$HF_HOME/hub/models--nvidia--DeepSeek-V4.1-Flash-NVFP4/snapshots/$NVFP4_MODEL_REVISION"

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

print_command() {
  printf '%q ' "$@"
  printf '\n'
}

require_command() {
  command -v "$1" >/dev/null 2>&1 ||
    die "required command is unavailable: $1"
}

verify_snapshot() {
  "$ROOT/.venv/bin/python" - "$SNAPSHOT_ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
config_path = root / "config.json"
index_path = root / "model.safetensors.index.json"
if not config_path.is_file():
    raise SystemExit(f"missing {config_path}")
if not index_path.is_file():
    raise SystemExit(f"missing {index_path}")

config = json.loads(config_path.read_text())
quantization = config.get("quantization_config") or {}
text = config.get("text_config") or {}
checks = {
    "architecture": "DeepseekV41ForCausalLM"
    in (config.get("architectures") or []),
    "model_type": config.get("model_type") == "deepseek_v41",
    "expert_quantization": (
        quantization.get("moe_quant_algo") == "NVFP4"
        and quantization.get("expert_dtype") == "fp4"
    ),
    "packed_engram": quantization.get("engram_embed_quant") == "mxfp4",
    "mtp_for_dspark": int(text.get("num_nextn_predict_layers", 0)) > 0,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("checkpoint validation failed: " + ", ".join(failed))
shards = list(root.glob("model-*-of-00048.safetensors"))
if len(shards) != 48:
    raise SystemExit(f"expected 48 safetensor shards, found {len(shards)}")
print(
    json.dumps(
        {
            "snapshot": str(root),
            "shards": len(shards),
            "expert_quantization": "NVFP4",
            "engram_quantization": "MXFP4",
            "mtp_layers": text["num_nextn_predict_layers"],
        },
        indent=2,
    )
)
PY
}

if [[ "$DRY_RUN" != 1 && "$NVFP4_ALLOW_BUSY_SETUP" != 1 ]] &&
  pgrep -f \
    'ops_latency/(run_concurrency_sweep|run_active_config|latency_search)\.(sh|py)' \
    >/dev/null; then
  die "a latency benchmark is active; wait or set NVFP4_ALLOW_BUSY_SETUP=1"
fi

require_command git
require_command docker

if [[ "$DRY_RUN" == 1 ]]; then
  if [[ "$NVFP4_SKIP_DOWNLOAD" != 1 ]]; then
    print_command env "HF_HOME=$HF_HOME" "$HF_CLI" download \
      "$NVFP4_MODEL" --revision "$NVFP4_MODEL_REVISION"
  fi
  if [[ "$NVFP4_SKIP_IMAGE_BUILD" != 1 ]]; then
    print_command git init "$NVFP4_VLLM_SOURCE_ROOT"
    print_command git -C "$NVFP4_VLLM_SOURCE_ROOT" fetch --depth 1 \
      "$NVFP4_VLLM_REPOSITORY" "$NVFP4_VLLM_COMMIT"
    print_command git -C "$NVFP4_VLLM_SOURCE_ROOT" checkout --detach FETCH_HEAD
    print_command env DOCKER_BUILDKIT=1 docker build \
      --file "$NVFP4_VLLM_SOURCE_ROOT/docker/Dockerfile" \
      --target vllm-openai \
      --tag "$NVFP4_VLLM_BASE_IMAGE" \
      --build-arg torch_cuda_arch_list=10.0 \
      --build-arg "max_jobs=$NVFP4_BUILD_JOBS" \
      --build-arg "nvcc_threads=$NVFP4_NVCC_THREADS" \
      --build-arg "RUN_WHEEL_CHECK=$NVFP4_RUN_WHEEL_CHECK" \
      "$NVFP4_VLLM_SOURCE_ROOT"
    print_command docker build \
      --file "$ROOT/ops_latency/Dockerfile.nvfp4-moeep" \
      --build-arg "BASE_IMAGE=$NVFP4_VLLM_BASE_IMAGE" \
      --tag "$NVFP4_VLLM_IMAGE" \
      "$ROOT"
  fi
  exit 0
fi

[[ -x "$ROOT/.venv/bin/python" ]] ||
  die "missing project Python: $ROOT/.venv/bin/python"

ensure_storage_dirs
mkdir -p "$SETUP_ROOT"

if [[ "$NVFP4_SKIP_DOWNLOAD" != 1 ]]; then
  [[ -x "$HF_CLI" ]] || die "missing Hugging Face CLI: $HF_CLI"
  HF_HOME="$HF_HOME" "$HF_CLI" download \
    "$NVFP4_MODEL" --revision "$NVFP4_MODEL_REVISION"
fi
verify_snapshot

if [[ "$NVFP4_SKIP_IMAGE_BUILD" != 1 ]] &&
  docker image inspect "$NVFP4_VLLM_IMAGE" >/dev/null 2>&1; then
  existing_commit="$(
    docker image inspect "$NVFP4_VLLM_IMAGE" \
      --format '{{ index .Config.Labels "ai.vllm.source.revision" }}'
  )"
  existing_model_revision="$(
    docker image inspect "$NVFP4_VLLM_IMAGE" \
      --format '{{ index .Config.Labels "ai.deepseek.model.revision" }}'
  )"
  if [[ "$existing_commit" == "$NVFP4_VLLM_COMMIT" &&
        "$existing_model_revision" == "$NVFP4_MODEL_REVISION" ]]; then
    printf 'Reusing verified NVFP4 image: %s\n' "$NVFP4_VLLM_IMAGE"
    NVFP4_SKIP_IMAGE_BUILD=1
  fi
fi

if [[ "$NVFP4_SKIP_IMAGE_BUILD" != 1 ]]; then
  if [[ ! -d "$NVFP4_VLLM_SOURCE_ROOT/.git" ]]; then
    mkdir -p "$NVFP4_VLLM_SOURCE_ROOT"
    git -C "$NVFP4_VLLM_SOURCE_ROOT" init
  fi
  if git -C "$NVFP4_VLLM_SOURCE_ROOT" remote get-url origin \
    >/dev/null 2>&1; then
    git -C "$NVFP4_VLLM_SOURCE_ROOT" remote set-url \
      origin "$NVFP4_VLLM_REPOSITORY"
  else
    git -C "$NVFP4_VLLM_SOURCE_ROOT" remote add \
      origin "$NVFP4_VLLM_REPOSITORY"
  fi
  git -C "$NVFP4_VLLM_SOURCE_ROOT" fetch --depth 1 \
    origin "$NVFP4_VLLM_COMMIT"
  git -C "$NVFP4_VLLM_SOURCE_ROOT" checkout --detach FETCH_HEAD
  actual_commit="$(git -C "$NVFP4_VLLM_SOURCE_ROOT" rev-parse HEAD)"
  [[ "$actual_commit" == "$NVFP4_VLLM_COMMIT" ]] ||
    die "vLLM checkout is $actual_commit, expected $NVFP4_VLLM_COMMIT"

  DOCKER_BUILDKIT=1 docker build \
    --file "$NVFP4_VLLM_SOURCE_ROOT/docker/Dockerfile" \
    --target vllm-openai \
    --tag "$NVFP4_VLLM_BASE_IMAGE" \
    --label "ai.vllm.source.revision=$NVFP4_VLLM_COMMIT" \
    --label "ai.deepseek.model.revision=$NVFP4_MODEL_REVISION" \
    --build-arg torch_cuda_arch_list=10.0 \
    --build-arg "max_jobs=$NVFP4_BUILD_JOBS" \
    --build-arg "nvcc_threads=$NVFP4_NVCC_THREADS" \
    --build-arg "RUN_WHEEL_CHECK=$NVFP4_RUN_WHEEL_CHECK" \
    "$NVFP4_VLLM_SOURCE_ROOT"
  docker build \
    --file "$ROOT/ops_latency/Dockerfile.nvfp4-moeep" \
    --build-arg "BASE_IMAGE=$NVFP4_VLLM_BASE_IMAGE" \
    --tag "$NVFP4_VLLM_IMAGE" \
    "$ROOT"
fi

image_commit="$(
  docker image inspect "$NVFP4_VLLM_IMAGE" \
    --format '{{ index .Config.Labels "ai.vllm.source.revision" }}'
)"
[[ "$image_commit" == "$NVFP4_VLLM_COMMIT" ]] ||
  die "image $NVFP4_VLLM_IMAGE is not the pinned MXFP4-Engram build"
runtime="$(
  docker image inspect "$NVFP4_VLLM_IMAGE" \
    --format '{{ index .Config.Labels "ai.deepseek.nvfp4.moe_ep_runtime" }}'
)"
[[ "$runtime" == "nvshmem4py-cu13-0.4.0" ]] ||
  die "image $NVFP4_VLLM_IMAGE lacks the pinned MoE-EP runtime"

{
  printf 'NVFP4_MODEL=%q\n' "$NVFP4_MODEL"
  printf 'NVFP4_MODEL_REVISION=%q\n' "$NVFP4_MODEL_REVISION"
  printf 'NVFP4_VLLM_BASE_IMAGE=%q\n' "$NVFP4_VLLM_BASE_IMAGE"
  printf 'NVFP4_VLLM_IMAGE=%q\n' "$NVFP4_VLLM_IMAGE"
  printf 'NVFP4_ECR_IMAGE=%q\n' "${NVFP4_ECR_IMAGE:-}"
  printf 'NVFP4_VLLM_COMMIT=%q\n' "$NVFP4_VLLM_COMMIT"
  printf 'NVFP4_SNAPSHOT_ROOT=%q\n' "$SNAPSHOT_ROOT"
} >"$STATE_FILE"
chmod 0600 "$STATE_FILE"

printf 'NVFP4 setup complete. State: %s\n' "$STATE_FILE"
printf 'No Docker command in this script receives --gpus.\n'
