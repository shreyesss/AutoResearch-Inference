#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PHASE="${1:?Usage: run-sequence-cap-pilot.sh b0a|cap32a|b0b|cap32b}"
case "$PHASE" in
  b0a|b0b) CAP=512 ;;
  cap32a|cap32b) CAP=32 ;;
  *) echo "Unknown phase: $PHASE" >&2; exit 2 ;;
esac
OUT="$ROOT/.artifacts/sequence-cap-pilot/$PHASE"
test ! -e "$OUT" || { echo "Phase already exists: $OUT" >&2; exit 1; }
mkdir -p "$OUT"
test "$(find "$ROOT/.artifacts/models/Qwen3.8-27B" -maxdepth 1 -name '*.safetensors' | wc -l)" -eq 18
test "$(docker ps --format '{{.Names}}' | wc -l)" -eq 0 || {
  echo 'Another Docker container is running; inspect GPU lease first.' >&2; exit 1;
}
MODEL='Qwen/Qwen3.8-27B'
IMAGE='vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14'
CONTAINER="iar-seq-pilot-$PHASE"
SERVER=(/models/Qwen3.8-27B --served-model-name "$MODEL"
  --tensor-parallel-size 1 --dtype bfloat16 --max-model-len 40960
  --max-num-seqs "$CAP" --reasoning-parser qwen3 --host 0.0.0.0 --port 8000)
printf '%q ' "${SERVER[@]}" > "$OUT/server-command.sh"
printf '\n' >> "$OUT/server-command.sh"
docker run --pull never -d --name "$CONTAINER" --gpus all --ipc=host \
  -p 127.0.0.1:8000:8000 \
  -v "$ROOT/.artifacts/models/Qwen3.8-27B:/models/Qwen3.8-27B:ro" \
  "$IMAGE" "${SERVER[@]}" > "$OUT/container-id.txt"
cleanup() {
  docker inspect "$CONTAINER" --format '{{json .Config.Cmd}}' > "$OUT/server-argv.json" 2>/dev/null || true
  docker inspect "$CONTAINER" --format '{{json .State}}' > "$OUT/server-state-before-stop.json" 2>/dev/null || true
  docker logs "$CONTAINER" > "$OUT/server.log" 2>&1 || true
  docker stop "$CONTAINER" > /dev/null 2>&1 || true
  docker rm "$CONTAINER" > /dev/null 2>&1 || true
}
trap cleanup EXIT
READY=0
for _ in $(seq 1 120); do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null; then READY=1; break; fi
  if [[ "$(docker inspect "$CONTAINER" --format '{{.State.Running}}')" != true ]]; then break; fi
  sleep 5
done
test "$READY" -eq 1 || { echo 'Server failed readiness; see server.log' >&2; exit 1; }
"$ROOT/infra/prepare-aiperf-tokenizer-cache.sh" > "$OUT/tokenizer-cache-path.txt"
unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
COMMON=(--model "$MODEL" --endpoint-type chat --endpoint /v1/chat/completions
  --streaming --url 127.0.0.1:8000
  --tokenizer "$ROOT/.artifacts/models/Qwen3.8-27B"
  --apply-chat-template --use-server-token-count --per-chunk-usage
  --export-level raw --export-http-trace --benchmark-duration 70
  --benchmark-grace-period 60)
for CELL in warmup r256 r32; do
  ARTIFACT="$OUT/$CELL"
  CMD=("$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}" --output-artifact-dir "$ARTIFACT")
  if [[ "$CELL" == warmup ]]; then
    CMD+=(--prompt-input-tokens-mean 552 --prompt-input-tokens-stddev 0
      --prompt-output-tokens-mean 256 --prompt-output-tokens-stddev 0
      --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":256}'
      --request-rate 0.2 --request-rate-mode constant --concurrency 256
      --request-count 3 --random-seed 41)
  else
    COUNT=154
    [[ "$CELL" == r32 ]] && COUNT=192
    CMD+=(--custom-dataset-type single-turn
      --input-file "$ROOT/infra/workloads/b0-chat-$CELL.jsonl"
      --fixed-schedule --fixed-schedule-auto-offset
      --request-count "$COUNT" --random-seed 42)
  fi
  printf '%q ' "${CMD[@]}" > "$OUT/$CELL-command.sh"
  printf '\n' >> "$OUT/$CELL-command.sh"
  echo "Running $PHASE/$CELL"
  "${CMD[@]}" > "$OUT/$CELL-console.log" 2>&1
done
echo "Completed $PHASE"
