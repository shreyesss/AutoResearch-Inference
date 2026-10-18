#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PHASE="${1:?usage: launch.sh calibration|search|confirmation}"
case "$PHASE" in calibration|search|confirmation) ;; *) exit 2 ;; esac
RUN_NAME="iar-optuna-direct-${PHASE}-$(date -u +%Y%m%d-%H%M%S)"
OUT="$ROOT/.artifacts/optuna-direct-v1"
if [ -e "$OUT/$PHASE.sqlite3" ]; then
  echo "Existing $PHASE study database; refusing to overwrite run metadata." >&2
  exit 2
fi
mkdir -p "$ROOT/.artifacts/gpu-locks" /opt/dlami/nvme/iar-optuna-v1/compile-cache
printf '%s\n' "$RUN_NAME" > "$OUT/$PHASE-container-name.txt"
cleanup() { docker stop --time 30 "$RUN_NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
timeout --signal=TERM --kill-after=45s 8h docker run --init --name "$RUN_NAME" \
  --label inference-autoresearch=direct-optuna --gpus all --ipc=host \
  --workdir /study --entrypoint /opt/tune-env/bin/python \
  -e PATH=/usr/local/bin:/usr/bin:/bin:/opt/tune-env/bin \
  -e TOKENIZERS_PARALLELISM=false -e HF_HUB_OFFLINE=1 \
  -v /opt/dlami/nvme/iar-optuna-v1/models/Qwen3.8-27B:/models/Qwen3.8-27B:ro \
  -v /opt/dlami/nvme/iar-optuna-v1/compile-cache:/root/.cache/vllm \
  -v /opt/dlami/nvme/iar-optuna-v1/environment/tune-env:/opt/tune-env:ro \
  -v "$ROOT/.artifacts/vendor/auto-tuning-vllm":/opt/auto-tuning-vllm:ro \
  -v "$OUT":/study \
  -v "$ROOT/infra/direct_optuna":/code:ro \
  -v "$ROOT/configs/direct-optuna-study.json":/config/study.json:ro \
  -v "$ROOT/.artifacts/gpu-locks":/locks \
  vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14 \
  /code/run.py "$PHASE" > "$OUT/$PHASE-console.log" 2>&1
