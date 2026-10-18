# B200 benchmark findings (18 October 2026)

## Access and sources

- S3 bucket: `s3://b200-bench-results/`. The full inventory is about 119 GB, so this folder contains the relevant aggregate report, point data, vLLM configs, and AIPerf scores/manifests rather than logs, telemetry, and compiled engine caches.
- The self-contained `deepseek-b200-latency-cost-pareto.html` was generated on `bitlane-n4` at 08:29 UTC on 18 October from the refreshed S3 archive. `pareto-data.json` is its embedded 255-point dataset, extracted without changing values. Every point's `source` maps to an object in the S3 inventory.
- The native campaign CSV is from `/home/ubuntu/Deepseek_serve/ops_latency/report/latency-campaign-points.csv` on `bitlane-n4` (Git revision `724cee8`). The vLLM config snapshot is from its `serving/b200/vllm/` directory.
- AIPerf `score.json` and `manifest.json` files were downloaded from the internal campaign under `deepseek-v4.1-flash/i-01bb8819a01d0999d/results/b200/vllm/aiperf-campaign/` and the public endpoint comparison under `deepseek-v4.1-flash/i-0265a4e096dfa399d/results/aiperf-bitlane/`.
- The Notion project page was not accessible without authentication. The figures below come from S3 and the host configs, not that page.

## Native 8×B200 agent workload Pareto

These are all 11 nondominated **end-to-end p50 versus estimated cost** points among 55 comparable closed-loop `agent-f75` runs (8,192 input and 1,024 output tokens, 75% cacheable prefix target). The cost column assumes **8 GPUs at $4.50 per GPU-hour and 100% utilization**; it is a scenario, not a cloud bill. End-to-end p95 and TTFT/ITL p95 are shown to avoid choosing from p50 alone.

| Run | Concurrency | req/s | E2E p50 / p95 (s) | TTFT p95 (s) | ITL p95 (ms) | $/M req |
|---|---:|---:|---:|---:|---:|---:|
| LAT-Q1-TP4-SEQ256 | 4 | 0.83 | 4.83 / 5.31 | 0.32 | 5.0 | 12,066 |
| LAT-Q1-TP4-SEQ256 | 8 | 1.45 | 5.50 / 5.89 | 0.60 | 5.5 | 6,905 |
| LAT-Q1-TP4-SEQ256 | 16 | 2.41 | 6.60 / 7.08 | 0.52 | 6.7 | 4,150 |
| LAT-Q1-TP4-SEQ256 | 32 | 3.51 | 8.87 / 10.48 | 0.91 | 10.0 | 2,851 |
| LAT-R4-NVFP4-TP4-DSPARK2-S256-G256-C64 | 64 | 6.76 | 9.33 / 11.30 | 0.96 | 10.6 | 1,480 |
| LAT-R4-TP4-DSPARK2 | 64 | 6.76 | 9.40 / 11.20 | 0.78 | 10.6 | 1,479 |
| LAT-R4f-TP4-DSPARK5-S160-B32K-G1024 | 128 | 11.01 | 11.25 / 15.20 | 1.20 | 14.6 | 909 |
| LAT-2XDEP4-R7b | 256 | 21.67 | 11.41 / 15.33 | 0.98 | 14.8 | 461 |
| LAT-2XDEP4-R7b | 384 | 27.69 | 13.44 / 18.30 | 1.33 | 17.7 | 361 |
| LAT-2XDEP4-R7b | 512 | 33.76 | 14.47 / 19.49 | 1.58 | 18.8 | 296 |
| LAT-R10-DEP8-DSPARK2-S160-LP4K-B16K-G512 | 1,024 | 43.55 | 23.84 / 29.61 | 4.43 | 28.6 | 230 |

**Practical choices from these measured points:** `LAT-2XDEP4-R7b` at concurrency 256 has the best latency of the three high-throughput R7b points; at 384 it reaches 27.69 req/s with E2E p95 18.30 s; at 512 it is the fastest comparable point with E2E p95 under 20 s (33.76 req/s, 19.49 s). The R10 point reaches 43.55 req/s at substantially higher latency. For very low load, 2×TP4 without speculative decoding has the lowest latency.

The checked-in `latency-2xdep4-sla.yaml` defines two independent TP1/DP4/EP4 engines on eight GPUs, DSpark k5, prefix caching, and API2 per replica. The R7b run also applies `lat-seqs-128`; the base profile alone does not fully specify that measured run. The NVFP4 point is a different precision variant, so treat it separately until quality equivalence is verified.

The `chat` workload has six comparable points, all from `LAT-Q1-TP4-SEQ256` at a 50% cache target. `code` and `mix` have no comparable points in this report. A frontier is meaningful only within the same workload, cache target, and load mode.

## Mooncake production replay: measured operating points

These AIPerf runs use the same named trace per row group. `1×`, `1.25×`, and `2×` refer to **replay speed**, not GPU count. The internal configurations were measured on the B200 campaign; `bitlane-public` is a public multi-node endpoint. Goodput is the score file's SLO goodput. These are observed points at the tested loads, not measured maximum capacities.

| Workload | Candidate | req/s | SLO goodput | E2E p50 / p95 (s) | TTFT p95 (s) | ITL p95 (ms) | SLO eligible |
|---|---|---:|---:|---:|---:|---:|---|
| Median | r7b-2xdep4-seq128, 1× | 6.65 | 6.63 | 1.36 / 5.54 | 1.35 | 184.0 | yes |
| Median | bitlane-public, 1× | 6.66 | 6.65 | 0.91 / 4.28 | 1.04 | 144.2 | yes |
| Median | r7-1xdep8-1.25x | 8.25 | 8.17 | 1.82 / 9.23 | 1.57 | 225.3 | yes |
| Median | r7-1xdep8-2x | 13.13 | 11.02 | 2.85 / 21.26 | 1.78 | 216.8 | no |
| Median | bitlane-public, 2× | 13.09 | 13.04 | 1.04 / 6.14 | 1.25 | 166.0 | yes |
| Burst | r7b-2xdep4-seq128, 1× | 7.01 | 7.00 | 1.40 / 5.38 | 1.27 | 182.2 | yes |
| Burst | bitlane-public, 1× | 7.01 | 7.01 | 0.97 / 4.19 | 1.08 | 150.0 | yes |
| Burst | r7-1xdep8-1.25x | 8.73 | 8.64 | 2.01 / 9.54 | 1.58 | 212.4 | yes |
| Burst | r7-1xdep8-2x | 13.89 | 11.87 | 3.03 / 19.82 | 1.72 | 216.1 | no |
| Burst | bitlane-public, 2× | 13.89 | 13.86 | 1.12 / 6.06 | 1.20 | 176.9 | yes |
| Cache heavy | r7b-2xdep4-seq128, 1× | 6.76 | 6.74 | 1.29 / 5.35 | 1.19 | 171.4 | yes |
| Cache heavy | bitlane-public, 1× | 6.76 | 6.75 | 0.90 / 4.03 | 0.91 | 134.0 | yes |
| Cache heavy | r7-1xdep8-1.25x | 8.43 | 8.35 | 1.84 / 9.00 | 1.44 | 214.2 | yes |
| Cache heavy | r7-1xdep8-2x | 13.27 | 12.01 | 2.80 / 18.01 | 1.73 | 212.3 | no |
| Cache heavy | bitlane-public, 2× | 13.41 | 13.38 | 1.02 / 5.92 | 1.15 | 144.7 | yes |

At the same 1× replay, the public endpoint has lower p50/p95 latency than the measured internal R7b configuration on all three traces. At 2×, the public endpoint remains SLO eligible; internal R7 DEP8 does not. Its GPU topology and actual endpoint operating cost are not established by these score files. The HTML report applies its generic 8-GPU cost assumption to public endpoint rows, so its cross-endpoint **cost frontier should not be used as a price comparison**.

## How to reproduce or inspect

- Open `deepseek-b200-latency-cost-pareto.html` locally for interactive workload, percentile, cache and configuration filters. The green frontier changes with the selected boundary.
- Use `pareto-data.json` for all 255 points and their exact source paths. For each source under `/opt/dlami/nvme/deepseek-v4.1-flash/results-archive/`, replace that prefix with `s3://b200-bench-results/deepseek-v4.1-flash/` to fetch its original `summary.json` or `score.json`.
- From this Mac, `ssh bitlane-n4` and `ssh bitlane-n5` work through AWS Systems Manager and short-lived EC2 Instance Connect keys. From the CPU controller, `aws s3 ls s3://b200-bench-results/` works; S3 is object storage, not an SSH server.
