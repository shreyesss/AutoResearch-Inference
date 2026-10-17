#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/.artifacts/b0-frozen-replay"
mkdir -p "$OUT"
curl --fail --silent http://127.0.0.1:8000/health >/dev/null
export HF_HUB_CACHE="$("$ROOT/infra/prepare-aiperf-tokenizer-cache.sh")"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

CELL="${1:?Usage: replay-frozen-b0.sh warmup|r256|r32}"
ARTIFACT="$OUT/$CELL"
test ! -e "$ARTIFACT" || { echo "Cell already exists: $ARTIFACT" >&2; exit 1; }
COMMON=(--model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions
  --streaming --url 127.0.0.1:8000
  --tokenizer Qwen/Qwen3.8-27B --tokenizer-revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
  --apply-chat-template --use-server-token-count --per-chunk-usage
  --export-level raw --export-http-trace --benchmark-duration 70
  --benchmark-grace-period 60 --output-artifact-dir "$ARTIFACT")
case "$CELL" in
  warmup)
    CMD=("$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}"
      --prompt-input-tokens-mean 552 --prompt-input-tokens-stddev 0
      --prompt-output-tokens-mean 256 --prompt-output-tokens-stddev 0
      --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":256}'
      --request-rate 0.2 --request-rate-mode constant --concurrency 256
      --request-count 3 --random-seed 41)
    ;;
  r256|r32)
    COUNT=154
    [[ "$CELL" == r32 ]] && COUNT=192
    CMD=("$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}"
      --custom-dataset-type single-turn --input-file "$ROOT/infra/workloads/b0-chat-$CELL.jsonl"
      --fixed-schedule --fixed-schedule-auto-offset
      --request-count "$COUNT" --random-seed 42)
    ;;
  *) echo "Unknown cell: $CELL" >&2; exit 2 ;;
esac
printf '%q ' "${CMD[@]}" > "$OUT/$CELL-command.sh"
printf '\n' >> "$OUT/$CELL-command.sh"
"${CMD[@]}" > "$OUT/$CELL-console.log" 2>&1
