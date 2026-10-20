# H200 overnight continuation: interim evidence

The first native C25 allocation passed all eight baseline native checks but failed container identity recording before traffic or candidate execution. A CPU-proven narrow infrastructure repair passed independent review and fresh A/B002 is running. Completed results below are scoped; no new service speedup is established. Original C03 and C24 verdicts remain unchanged.

| Family | Completed evidence | Decision |
| --- | --- | --- |
| C24 coupled verification/draft cost | Actual joint-DP source reconstruction; preserved 647 historical chronology flags; two bounded synthetic probes are clean but do not reproduce or repair the old instrument failure. | Park full AV timing work. Remote budget/confidence state and accepted-progress effects remain unresolved. |
| C25 unsharded sampler fusion | Installed RNG adapted, real BF16 Markov weights, 108 correctness fixtures, 2,560 graph replays, six rejected negative controls; positive sampler-component timing at all eight fixed shapes. | Advance to independently designed native integration pilot, before considering service testing. |
| C26 FP32-weight router port | All 43 learned-router checkpoint headers and actual allocation/load/dispatch inspected; weights remain BF16. | Proposed FP32-weight mechanism is inapplicable to this frozen baseline. No weight cast or GPU experiment. |

## C25 component result

The qualified port preserves the installed Gumbel seed/position/draft-salt semantics, all five Markov bias GEMMs, BF16 cache rounding, tokens and next embeddings. Actual engine watermark configuration is absent; retaining the request watermark flag does not create a draft watermarker. No existing sampler/config behavior was disabled to make this port eligible.

| Executed rows | Baseline µs | Candidate µs | Saved µs | Gain |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 181.480 | 136.135 | 45.346 | 24.99% |
| 2 | 206.086 | 138.961 | 67.125 | 32.57% |
| 4 | 215.749 | 145.294 | 70.455 | 32.66% |
| 5 | 226.090 | 149.538 | 76.553 | 33.86% |
| 7 | 239.984 | 156.740 | 83.244 | 34.69% |
| 16 | 309.809 | 186.735 | 123.074 | 39.73% |
| 32 | 331.703 | 227.966 | 103.736 | 31.27% |
| 64 | 484.137 | 330.474 | 153.662 | 31.74% |

Thirty alternating paired blocks with 100 graph replays per arm measured each shape, without CUPTI. Intervals measure within-session variation, not independent startup or service uncertainty. Native historical capacities 1/2/4/7 cover 92.79% of submitted events in a warmup/profiling-inclusive histogram; this is not a latency weighting. The sampler uses actual model weights and controlled base logits, so this remains a component result.

[Independent result review](evaluator/C25_COMPONENT_RESULT_REVIEW.md), [raw result](executions/sampler-component-002/component/result.json), [execution receipt](executions/sampler-component-002/execution.json), [source audit](developer/APPLICABILITY.md), [qualified port](developer/candidate/fused_sampler.py).

The first component allocation failed before loading weights because checkpoint symlinks escaped the snapshot mount. Its receipt remains retained. A CPU-only regular-file mount preflight and [independent repair review](evaluator/C25_MOUNT_REPAIR_REVIEW.md) preceded the separately named successful allocation. No correctness or timing gate was changed in response to measured outputs.

## C24 and C26

C24's [saved trace audit](tooling-evidence/C24_TRACE_AUDIT.md) does not find a duplicate-correlation parser repair. Clean GPU0 long-operation and implicated-GPU6 short-operation probes are limited instrument evidence, not repaired historical timing or AV benefit. [First probe review](evaluator/C24_FINAL_OFFLINE_REVIEW.md), [short probe review](evaluator/C24_SHORT_PROBE_RESULT_REVIEW.md). The [joint dispatch reconstruction](developer/C24_JOINT_DISPATCH.md) shows why independent local budgets cannot predict synchronized target/draft capacities without additional remote state. A post-sync capacity-fill idea is a separate prospective revision and remains unimplemented.

C26's [source audit](developer/APPLICABILITY.md) and [independent review](evaluator/APPLICABILITY_REVIEW.md) close applicability for this baseline. FP32 output does not imply FP32 router weights. This is not a measured kernel-performance failure.

## Course correction and next allocation

The requested [meta-critic](meta-critic/CONTRACT_REVIEW_003.md) supports a separately declared C25 native-model pilot. C03's 2% service confirmation rule remains unchanged; it is not a universal veto on a valid smaller component/native observation. The [prospective native contract](evaluator/C25_NATIVE_PILOT_CONTRACT.md) specifies original FULL graph replay, captured-activation reference comparison, real request lifecycle fixtures, all-cell reporting and 90 minutes / 12 GPU-hours including cold startup and cleanup. Padded dummy timing excludes ordinary expert routing/accepted-token progress; it cannot establish production service gain.

Completed small allocations consumed 0.0243944 visible GPU-hours (0.195155 eight-GPU-node equivalent hours under the whole-node idle policy), including the failed mount attempt. Two full service attempts remain. Native allocation001 additionally consumed 2.558871 GPU-hours (19.1915 minutes), including its infrastructure failure and cleanup. Its closed receipts record all GPUs/containers idle despite transient Docker zombie-init removal errors. A fresh002 must remain inside001’s original 00:19:00.993689 UTC work deadline and 00:24:00.993689 UTC hard deadline on October21, with no baseline pooling. [Failure review](evaluator/C25_NATIVE_001_INFRA_REVIEW.md), [CPU reproduction](native-root/identity-cpu-reproduction.json), [meta-critic repair recommendation](meta-critic/INFRASTRUCTURE_REPAIR_005.md). Native comparison and final publication are pending; [status](status.json) and [journal](journal.jsonl) are the progress pointers.
