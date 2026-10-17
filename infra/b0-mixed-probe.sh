#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/.artifacts/b0-load-curve"
mkdir -p "$OUT"
curl --fail --silent http://127.0.0.1:8000/health >/dev/null
export HF_HUB_CACHE="$("$ROOT/infra/prepare-aiperf-tokenizer-cache.sh")"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

CELL=mixed-probe
ARTIFACT="$OUT/$CELL"
test ! -e "$ARTIFACT" || { echo "Cell already exists: $ARTIFACT" >&2; exit 1; }
SEQ_DIST="$("$ROOT/.venv/bin/python" -c 'import json; print(json.load(open("infra/mixed-prefill-control.json"))["aiperf_sequence_distribution"])')"
CMD=("$ROOT/.venv/bin/aiperf" profile
  --model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions
  --streaming --url 127.0.0.1:8000
  --tokenizer Qwen/Qwen3.8-27B --tokenizer-revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
  --apply-chat-template --use-server-token-count --per-chunk-usage
  --sequence-distribution "$SEQ_DIST" --num-dataset-entries 64
  --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true}'
  --request-rate 0.5 --request-rate-mode constant --concurrency 256
  --request-count 30 --benchmark-duration 70 --benchmark-grace-period 60
  --random-seed 51 --export-level raw --export-http-trace
  --output-artifact-dir "$ARTIFACT")
printf '%q ' "${CMD[@]}" > "$OUT/$CELL-command.sh"
printf '\n' >> "$OUT/$CELL-command.sh"
printf '{"cell":"%s","offered_rps":0.5,"request_count":30,"duration_s":70,"grace_period_s":60,"seed":51,"client_concurrency_cap":256,"output_mode":"forced_varied","arrival":"constant","cache_protocol":"shared warmed server; disjoint seed; no reset","config":"infra/mixed-prefill-control.json"}\n' "$CELL" > "$OUT/$CELL-plan.json"
"${CMD[@]}" > "$OUT/$CELL-console.log" 2>&1
