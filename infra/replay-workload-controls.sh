#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT=.artifacts/workload-controls
curl --fail --silent http://127.0.0.1:8000/health >/dev/null
test -f "$OUT/manifest.json"
case "${1:-all}" in all|tracelab|mooncake) ;; *) echo 'Usage: replay-workload-controls.sh [all|tracelab|mooncake]' >&2; exit 2 ;; esac
export HF_HUB_CACHE="$("$ROOT/infra/prepare-aiperf-tokenizer-cache.sh")"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

COMMON=(--model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions
  --streaming --url 127.0.0.1:8000 --tokenizer Qwen/Qwen3.8-27B
  --tokenizer-revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
  --apply-chat-template --use-server-token-count --per-chunk-usage
  --export-level raw --export-http-trace
  --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0}')

if [[ "${1:-all}" == all || "${1:-all}" == tracelab ]]; then
"$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}" \
  --custom-dataset-type tracelab --input-file "$OUT/tracelab-four-turn.jsonl" \
  --fixed-schedule --fixed-schedule-auto-offset --request-count 4 \
  --random-seed 42 --output-artifact-dir "$OUT/tracelab-four-turn" \
  > "$OUT/tracelab-four-turn-console.log" 2>&1
fi

if [[ "${1:-all}" == all || "${1:-all}" == mooncake ]]; then
"$ROOT/.venv/bin/aiperf" profile "${COMMON[@]}" \
  --custom-dataset-type mooncake-trace --input-file "$OUT/mooncake-six-sessions.jsonl" \
  --isl-block-size 64 --fixed-schedule --fixed-schedule-auto-offset \
  --request-count 18 --random-seed 42 \
  --output-artifact-dir "$OUT/mooncake-six-sessions" \
  > "$OUT/mooncake-six-sessions-console.log" 2>&1
fi
