# DeepSeek / B200 reference analysis

The original 73 files are imported verbatim under `b200-bench-analysis/`, separate from the local Qwen/RTX PRO study. [SOURCE_MANIFEST](B200_SOURCE_MANIFEST.json) records every original file's size and SHA-256. Navigation and import metadata live here so the supplied source folder stays unchanged.

## Read in this order

1. [Findings and interpretation](../b200-bench-analysis/PARETO_FINDINGS.md).
2. [Interactive latency/cost report](../b200-bench-analysis/deepseek-b200-latency-cost-pareto.html).
3. [255 report points](../b200-bench-analysis/pareto-data.json), each with its original source path.
4. [Native campaign CSV](../b200-bench-analysis/latency-campaign-points.csv) and [selected run summary](../b200-bench-analysis/r7b-c512-summary.json).
5. [Serving configuration snapshot](../b200-bench-analysis/configs/vllm/README.md).
6. [AIPerf score/manifest folders](../b200-bench-analysis/aiperf-scores/): 23 manifests, 21 scores. Manifest-only attempts are retained and must not count as scored successes.

## Provenance and limits

The supplied findings document records `s3://b200-bench-results/` as its source, a report generated on `bitlane-n4` on 18 October 2026, and a native campaign/config snapshot from Deepseek_serve revision `724cee8`. These are retained provenance statements; this organization did not re-fetch S3 or inspect the hosts.

The reference includes synthetic closed-loop agent/chat workloads and separate Mooncake replay comparisons. The comparable agent slice uses 8,192 input / 1,024 output tokens with a 75% cacheable-prefix target. It is not the same workload or hardware as our four-class Qwen mix. The 255 points are not 255 independent launches or repetitions: the CSV has workload/tier/category views of source measurements.

Cost estimates assume eight GPUs at $4.50/GPU-hour and 100% utilization. They are scenarios, not bills. Public endpoint hardware/cost is not established by these scores; the cross-endpoint cost frontier is not a valid price comparison.

The original inventory is described as approximately 119 GB. This imported 1.7 MB subset contains aggregate reports, scores/manifests and serving configs, not full per-request logs, telemetry or caches. Source paths identify the original evidence; access depends on the original storage. Copied launchers refer to their original repository layout and are reference material, not locally qualified deployment commands.

## What we can reuse

Workload-scoped frontiers, multiple operating points per launch, explicit prefix-cache treatment, diagnostic metrics and complete configuration provenance. We cannot transfer measured throughput/latency/cost or a winning B200 configuration directly to the single-GPU Qwen setting.

[Research index](RESEARCH.md) · [local results](../results/2026-10-18-direct-optuna/README.md)
