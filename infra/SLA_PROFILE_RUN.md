# Class-aware SLA rate profiler

This command is gated by `configs/sla-study-v3.template.json`. It refuses to
start a GPU unless the approved policy hash, validated 240-request development
manifest and class sidecar, and a complete matched B0 evaluator CellResult
with raw request evidence are present. Input replay validation alone does not
meet that gate. It
reads the development manifest directly from the study, since the v2 workload
registry contains only the 36-request screen.

```bash
PYTHONPATH=src .venv/bin/python -m inference_autoresearch.cli sla-profile \
  --backend real --campaign configs/campaign-v2.json \
  --study configs/sla-study-v3.template.json \
  --initial-rate-rps 0.2 --min-rate-rps 0.1 \
  --max-rate-rps 1.6 --max-points 6
```

One fresh pinned vLLM server is started and warmed once. At each proposed rate,
AIPerf sends the frozen 36-request screen with Poisson arrivals as a transport
check. If that is valid, it sends all 240 frozen development requests once,
also with Poisson arrivals. The request bodies and class labels stay fixed;
arrival seeds and offered rates are recorded. AIPerf exports raw requests,
per-request metrics, HTTP traces, server metrics and summary. The evaluator
joins native requests to exact frozen bodies and class sidecar IDs, checks
completion and dispatch, then applies the approved class TTFT/TPOT/error policy.

The outer rate planner doubles upward until it sees an observed SLA failure,
then bisects. It can also halve down to the declared 0.1 requests/s floor if
the initial rate fails. Invalid native trials stop the planner for inspection;
they never become a boundary. The 36-request screen does not make an SLA
decision. The floor, ceiling and six-point budget bound runtime, though a
single 0.1 requests/s 240-request Poisson trial may still take about 40 minutes
plus drain. AIPerf's own throughput/Bayesian planner cannot enforce the four
class-specific SLA rules, so the class-aware planner is outside AIPerf.

Every point is appended to `sla-profile-points.json` as soon as it completes,
under `.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/sla-profile/<run-id>/aiperf/`.
It includes invalid points, configured and realized rates, arrival seed,
per-class p50/p90/p95/p99 and confidence checks, validity reasons, and paths
plus SHA256 hashes for native exports. A flat per-class CSV is written to the
run's `report/` directory. The claim is **observed development points only**.
An independently confirmed SLA capacity still needs new matched windows and
sealed test evidence.
