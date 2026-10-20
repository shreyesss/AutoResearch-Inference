#!/usr/bin/env bash
set -u

speedup="${MOONCAKE_TRACE_SPEEDUP:-1}"
candidate="${MOONCAKE_CANDIDATE:-r7-1xdep8}"
workloads=("$@")
if ((${#workloads[@]} == 0)); then
  workloads=(mooncake-median mooncake-burst mooncake-cache-heavy)
fi

for workload in "${workloads[@]}"; do
  bash ops_aiperf/run_suite.sh \
    --suite production \
    --workload "$workload" \
    --candidate "$candidate" \
    --profile-label latency-dep8-sla \
    --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
    --base-url http://127.0.0.1:8000 \
    --phase discovery \
    --trace-speedup "$speedup" \
    --server-metrics-url http://127.0.0.1:8000/metrics \
    --gpu-telemetry-url pynvml
done