#!/usr/bin/env bash
set -euo pipefail

# A two-iteration AIPerf adaptive-load integration check on a running B0 server.
# It is too small to estimate capacity, tail latency, or an SLA boundary.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-${ROOT}/.artifacts/aiperf-adaptive-ops4-spike}"
curl --fail --silent --max-time 3 http://127.0.0.1:8000/health >/dev/null
mkdir -p "${OUTPUT_DIR}"

"${ROOT}/.venv/bin/aiperf" profile \
  --model Qwen/Qwen3.8-27B \
  --endpoint-type chat --endpoint /v1/chat/completions \
  --streaming --url 127.0.0.1:8000 \
  --tokenizer "${ROOT}/.artifacts/models/Qwen3.8-27B" \
  --apply-chat-template --use-server-token-count --per-chunk-usage \
  --isl 512 --isl-stddev 0 --osl 256 --osl-stddev 0 \
  --extra-inputs '{"chat_template_kwargs":{"enable_thinking":false},"temperature":0,"ignore_eos":true,"min_tokens":256}' \
  --request-rate 2.2 --request-rate-mode constant \
  --concurrency 8 --request-count 12 --num-profile-runs 1 \
  --search-space 'rate:1.8,2.6:real' \
  --search-metric output_token_throughput \
  --search-direction maximize \
  --search-max-iterations 2 --search-initial-points 1 \
  --search-planner bayesian \
  --search-random-seed 42 --random-seed 42 \
  --export-level raw \
  --output-artifact-dir "${OUTPUT_DIR}"
