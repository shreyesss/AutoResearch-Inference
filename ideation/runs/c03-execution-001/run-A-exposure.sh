#!/bin/bash
set -uo pipefail
source /home/ubuntu/Deepseek_serve/lib/env.sh
cd /home/ubuntu/Deepseek_serve-c03
export PYTHONDONTWRITEBYTECODE=1
/home/ubuntu/Deepseek_serve/.venv-aiperf/bin/python -m ops_aiperf.runner --campaign /home/ubuntu/Deepseek_serve-c03/ops_aiperf/campaign.yaml --aiperf-bin /home/ubuntu/Deepseek_serve/.venv-aiperf/bin/aiperf --suite production --workload mooncake-median --candidate c03-A-exposure-median-0p5x --profile-label latency-2xdep4-sla --profile-path /home/ubuntu/Deepseek_serve/serving/h200/vllm/profiles/latency-2xdep4-sla.yaml --base-url http://127.0.0.1:8000 --model deepseek-v4.1-flash --tokenizer /home/jl_fs/models/DeepSeek-V4.1-Flash --tokenizer-revision 2cba9e42aa026125f3ed06c6d98c1db82f7ca027 --data-root /home/jl_fs/datasets/aiperf --results-root /home/ubuntu/Deepseek_serve-c03/results/h200/vllm/c03 --phase discovery --trace-speedup 0.5 --workers-max 256 --warmup-duration 120 --random-seed 42 --server-metrics-url http://127.0.0.1:8100/metrics --server-metrics-url http://127.0.0.1:8101/metrics --server-metrics-url http://127.0.0.1:8000/metrics --gpu-telemetry-url pynvml --telemetry-interval 1 --dcgm-metrics-url http://127.0.0.1:9400/metrics --no-sync
c03_result=$?
printf '%s\n' "$c03_result" > /home/ubuntu/AutoResearch-Inference-c03/ideation/runs/c03-execution-001/client-A-exposure.exit
exit "$c03_result"
