# Baseline audit for the next B200 experiments

Source: the existing `b200-bench-analysis/` artifacts, not newly executed benchmarks. Exact values, paths and SHA-256 hashes are in [baseline-audit.json](baseline-audit.json).

## What is measured

| Anchor | Completed req/s | E2E p95 | TTFT p95 | TPOT p95 |
|---|---:|---:|---:|---:|
| R7b 2×DEP4, c256 | 21.66994 | 15.332 s | 0.981 s | 14.776 ms |
| R7b 2×DEP4, c384 | 27.68820 | 18.299 s | 1.335 s | 17.678 ms |
| R7b 2×DEP4, c512 | 33.76224 | 19.491 s | 1.578 s | 18.771 ms |

These are closed-loop synthetic agent-f75 observations, 8192 input /1024 output tokens. They are not open-loop capacity estimates. The inspected CSV R7b rows are repetition 1, discovery phase, `decision_grade=False`. Tier-specific goodput differs from raw throughput: c512 balanced-tier goodput is 20.1493 req/s, not 33.7622. Do not infer statistical significance from these single observations.

The refreshed dataset has 255 points. The original case-based native comparison has 55 points and 11 p50/cost frontier points. Adding **exact observed token-length equality** leaves 51 points and 10 p50/cost frontier points. Four NVFP4 records have different observed input lengths; the original report's workload label alone does not make them exactly matched. Precision/quality equivalence also needs a separate check. The original report is retained unchanged.

For eight GPUs at the report's assumed $4.50/GPU-hour, node cost is $36/hour. Thus `$ / million completed requests = 10000 / completed_req_s`; for useful throughput use **goodput** in that denominator. At a fixed GPU count and price, cost and throughput are mathematically coupled. The meaningful tradeoff is latency/quality-constrained goodput versus cost, with separate workload frontiers. This price is a scenario, not a measured bill. Do not reuse it to compare the public multi-node endpoint.

## Runtime configuration is not completely established

The refreshed `latency-2xdep4-sla.yaml` declares two TP1/DP4/EP4 engines, DSpark k5, adaptive verification false, prefix cache on, API2 per replica, graph512, token budget16384. Its default seq64 must be combined with R7b's **lat-seqs-128 overlay**. The CSV's derived `dspark_config=off` disagrees with that refreshed profile. Neither a label nor a later config snapshot proves the historical launch arguments.

`images.yaml` pins source `ac9126e58aa7bbab1856ba6593ba4d5003fea516` and an image digest. This is the configuration's intended pin. The inspected AIPerf manifest has empty `selected_image`, `git_dirty=true`, and serving-repository revision `7562145d309205bcfd4f7d55ecc0304f099b31f1`; the findings also mention a later config snapshot at `724cee8`. These references must not be collapsed into one clean, reproduced baseline.

Before implementation, record actual image digest, vLLM and serving SHAs plus dirty patch, loaded model/weight/tokenizer hashes, resolved backend, complete process arguments and environment, rank/replica mapping, all experiment overlays and graph mode. The experiment manifest must contain the resolved values. If code already contains the proposed behavior, skip it or define a smaller concrete delta.

## Goodput and streaming measurements need separate names

| R7b replay 1× | Completed req/s | Campaign length-aware goodput | AIPerf goodput | Whole-trace ITL p95 | Long-output ITL p95 |
|---|---:|---:|---:|---:|---:|
| Median | 6.64871 | 6.62879 | 4.67270 | 184.001 ms | 14.919 ms |
| Burst | 7.00893 | 6.99897 | 5.11884 | 182.183 ms | 14.663 ms |
| Cache heavy | 6.75661 | 6.73661 | 5.02286 | 171.392 ms | 14.657 ms |

The score files expose both definitions. The campaign's output-speed policy uses a >=50-token long-output cohort, >=30 tokens/s and 95% minimum attainment. AIPerf was invoked with TTFT4000ms, ITL33.333ms and request_latency75000ms limits. Recover and hash the historical custom scorer before using its formula for a new acceptance decision; aggregate fields do not completely specify implementation.

Observed replay cache-hit shares are about 27.6–29.4%, unlike synthetic agent-f75's approximately75% target. Separate workloads and controlled cache preparation are essential. One cannot claim a routing win simply by comparing these two datasets.

At fixed1× arrival rate, R7b's campaign goodput is already near completed/offered throughput; a5% goodput improvement is impossible without changing the offered load or metric. Test latency at fixed load, and use a separate offered-rate sweep to find sustainable SLO capacity.

vLLM documents streaming-event intervals separately from per-request time per output token; speculative batching makes that distinction especially important. Preserve token/chunk timestamps, not just averages. [vLLM metric definitions](https://github.com/vllm-project/vllm/blob/main/docs/design/metrics.md). AIPerf's goodput depends on configured request-quality criteria and benchmark duration; pin its implementation version as well. [AIPerf metric definitions](https://github.com/ai-dynamo/aiperf/blob/main/docs/metrics-reference.md).

## Evidence limits

This audit reads the downloaded aggregate reports, scores, manifests and config snapshots. It does not inspect the entire119GB S3 inventory, all per-token records, GPU traces or current serving processes. Aggregate symptoms motivate experiments; they do not establish that kernel time, cache misses, queueing or speculative verification is the actual bottleneck.

## Live access check during this exploration

Read-only `ssh bitlane-n4` and `ssh bitlane-n5` attempts both failed before running any remote command: AWS EC2 Instance Connect returned `EC2InstanceStateInvalidException` and reported the instance terminated. No instance was started or modified. Therefore this session cannot claim to have verified either host's current serving backend; archived evidence and runtime identity remain separate.
