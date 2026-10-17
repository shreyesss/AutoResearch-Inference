#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
OUT="$ROOT/.artifacts/b0-load-curve"
mkdir -p "$OUT"
curl --fail --silent http://127.0.0.1:8000/health >/dev/null
export HF_HUB_CACHE="$("$ROOT/infra/prepare-aiperf-tokenizer-cache.sh")"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

CELL="${1:?Usage: b0-load-curve.sh CELL (warmup|r02|r04|r08|r16|r256|r32|r48|r64|r32b)}"
case "$CELL" in
  warmup) RATE=0.2; COUNT=3; SEED=41; DURATION=20; CAP=256 ;;
  r02) RATE=0.2; COUNT=12; SEED=42; DURATION=70; CAP=256 ;;
  r04) RATE=0.4; COUNT=24; SEED=43; DURATION=70; CAP=256 ;;
  r08) RATE=0.8; COUNT=48; SEED=44; DURATION=70; CAP=256 ;;
  r16) RATE=1.6; COUNT=96; SEED=45; DURATION=70; CAP=256 ;;
  r256) RATE=2.56; COUNT=154; SEED=50; DURATION=70; CAP=256 ;;
  r32) RATE=3.2; COUNT=192; SEED=46; DURATION=70; CAP=256 ;;
  r48) RATE=4.8; COUNT=288; SEED=48; DURATION=70; CAP=512 ;;
  r64) RATE=6.4; COUNT=384; SEED=47; DURATION=70; CAP=512 ;;
  r32b) RATE=3.2; COUNT=192; SEED=49; DURATION=70; CAP=256 ;;
  *) echo "Unknown cell: $CELL" >&2; exit 2 ;;
esac

ARTIFACT="$OUT/$CELL"
test ! -e "$ARTIFACT" || { echo "Cell already exists: $ARTIFACT" >&2; exit 1; }
CMD=("$ROOT/.venv/bin/aiperf" profile
  --model Qwen/Qwen3.8-27B --endpoint-type chat --endpoint /v1/chat/completions
  --streaming --url 127.0.0.1:8000
  --tokenizer Qwen/Qwen3.8-27B --tokenizer-revision 1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0
  --apply-chat-template --use-server-token-count --per-chunk-usage
  --prompt-input-tokens-mean 552 --prompt-input-tokens-stddev 0
  --prompt-output-tokens-mean 256 --prompt-output-tokens-stddev 0
  --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":256}'
  --request-rate "$RATE" --request-rate-mode constant --concurrency "$CAP"
  --request-count "$COUNT" --benchmark-duration "$DURATION" --benchmark-grace-period 60
  --random-seed "$SEED" --export-level raw --export-http-trace
  --output-artifact-dir "$ARTIFACT")
printf '%q ' "${CMD[@]}" > "$OUT/$CELL-command.sh"
printf '\n' >> "$OUT/$CELL-command.sh"
printf '{"cell":"%s","offered_rps":%s,"request_count":%s,"duration_s":%s,"grace_period_s":60,"seed":%s,"client_concurrency_cap":%s,"output_mode":"forced_256","input_target":552,"target_server_tokens":512,"arrival":"constant","cache_protocol":"shared warmed server; disjoint synthetic seeds per cell; no reset"}\n' "$CELL" "$RATE" "$COUNT" "$DURATION" "$SEED" "$CAP" > "$OUT/$CELL-plan.json"
"${CMD[@]}" > "$OUT/$CELL-console.log" 2>&1
