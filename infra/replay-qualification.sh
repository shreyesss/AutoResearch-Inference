#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT=.artifacts/dataset-qualification
curl --fail --silent http://127.0.0.1:8000/health >/dev/null
test -f "$OUT/source-audit.json"

COMMON=(--model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions
  --streaming --url 127.0.0.1:8000 --tokenizer .artifacts/models/Qwen3.8-27B
  --apply-chat-template --use-server-token-count --per-chunk-usage
  --export-level raw --export-http-trace
  --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0}')

"$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}" \
  --custom-dataset-type single-turn --input-file "$OUT/specbench-replay.jsonl" \
  --dataset-sampling-strategy sequential --request-count 5 \
  --concurrency 1 --request-rate 1 --request-rate-mode constant \
  --random-seed 42 --output-artifact-dir "$OUT/specbench-replay" \
  > "$OUT/specbench-replay-console.log" 2>&1

"$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}" \
  --custom-dataset-type tracelab --input-file "$OUT/tracelab-replay.jsonl" \
  --fixed-schedule --fixed-schedule-auto-offset --request-count 2 \
  --random-seed 42 --output-artifact-dir "$OUT/tracelab-replay" \
  > "$OUT/tracelab-replay-console.log" 2>&1
