#!/usr/bin/env bash
# Root executes only after independent controlled-A acceptance.
source /home/ubuntu/Deepseek_serve/lib/env.sh
cd /home/ubuntu/Deepseek_serve-c03
export SKIP_PREFLIGHT=1
export PYTHONDONTWRITEBYTECODE=1
exec /home/ubuntu/Deepseek_serve/.venv/bin/python \
  /home/ubuntu/Deepseek_serve-c03/lib/serve_recipe.py \
  --hardware h200 --engine vllm --profile latency-2xdep4-sla \
  --backends-only \
  --c03-source-manifest /home/ubuntu/Deepseek_serve-c03/c03/diagnostic-candidate-manifest.json
