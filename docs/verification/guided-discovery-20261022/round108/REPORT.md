# Round108 — historical Mooncake cache-exposure readback

## Decision

The locally retained21 endpoint score summaries provide cache-hit reporting but do not establish the eviction/preemption/recomputation premise needed by round105. Keep its restoration-budget policy parked. No new hypothesis, benchmark or GPU operation.

## What was inspected

Read all score.json files under the declared b200-bench-analysis/aiperf-scores directory: seven each for Mooncake median, cache-heavy and burst. Their21 associated manifests and scores are copied/hash-pinned. These are historical October18 results, not fresh measurements of the planned c455/Flash1017 deployment. Two additional manifests without score files are outside the scored inventory; no completed result is inferred for them.

The manifests identify load-generator code/revision, workload/tokenizer, endpoint and configured command. Their benchmark git revision is not a vLLM server source pin; a selected image, when supplied, still needs digest/source correspondence before a current-runtime comparison. A public endpoint's reported model name does not attest serving hardware, cache policy or backend. readback.json retains these distinctions rather than silently projecting old results onto d464.

## Why cache-hit share is insufficient

Reported cache-hit share divides cached prompt tokens by prompt tokens. A miss can be a genuinely unique suffix, cold first access, changed routing, policy eviction, window boundary or unsupported reusable state. It is not automatically an avoidable recomputation event. The retained summaries do not provide per-prefix/group eviction, failed-allocation, preemption or restored-row attribution. Absence of those fields is unknown, not zero events.

The cache-heavy workload name and nonzero hit share show that some reuse was exposed. They do not show that protecting more cached state improves net ITL or throughput. A reservation can trade reuse against active capacity, batching and victim costs. Aggregating unmatched runs or comparing their hit-share extrema would not estimate that intervention's benefit.

For example, the retained public production cache-heavy run20261018-080958 reports4053 requests,10,142,720 cached prompt tokens out of33,375,484 prompt tokens (share about.3039), with full cache-reporting coverage. That is an endpoint accounting observation, not evidence that the other69.6% was evicted or recoverable. Its selected_image is null and its benchmark checkout is marked dirty. It cannot qualify an exact current server experiment.

## Evaluation consequence

Existing Mooncake/agent-p75 endpoint benchmarks can remain the later service comparator. To qualify round105, first recover already-recorded server metrics/traces with exact run pins and identify an actual costly eviction/preemption decision, surviving cache on requeue, recomputed rows and associated output stalls. If those records are unavailable, a future explicitly authorized diagnostic would add attribution to the same workload; a tenant benchmark is not automatically required. Nothing was launched now.

## Yield and limits

21 existing score files inspected,42 exact source copies,zero new runtime tests or measurements. The bounded search found no mechanism-counter keys in the score metrics. It did not scan arbitrary home directories, fetch missing S3 artifacts, contact servers or establish that no richer evidence exists elsewhere. This narrows the evidence gap; it is not a new negative performance result.
