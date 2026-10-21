# C24 baseline timing diagnostic — AV off, k5

**Decision: `instrumentation_inconclusive`; adaptive verification remains unqualified.** Traffic, runtime identity and cleanup passed, but the timing evidence failed its predeclared adequacy checks. This is a limitation of our measurement, not an AV performance failure. Adaptive verification was never enabled, and no service speedup or full hypothesis A/B result is claimed. The user's two remaining full attempts are unchanged.

## Mechanism being qualified

The current server drafts five tokens, then runs the large target model to verify the proposed continuation. Adaptive verification keeps that five-token proposal but uses confidence and cost estimates to choose how many proposed tokens are worth verifying. Its potential benefit is fewer target-model token rows. Its costs include the controller itself, fewer accepted tokens per iteration, different graph shapes and extra draft padding. It needs a net improvement in time per accepted output token, not merely fewer target rows.

This differs from C03's occasional reduction of draft padding. C03 proved that its graph-selection mechanism activated, but never established a sufficiently expensive time contribution; its valid service screen failed promotion. Here the prerequisite is a direct, bounded observation of baseline target and draft work before selecting an AV experiment.

A concrete source-derived warning remains: with five real requests per rank, one valid adaptive dispatch changes target capacity **36→16 rows**, while draft capacity changes **35→80 rows**. These are reachable source-level capacities, not observed AV choices or predicted latency. The installed code already contains an AV controller and the checkpoint index contains its confidence-head weight; metadata presence is not proof of the head's runtime use. See [source feasibility and exact code chain](IMPLEMENTATION_FEASIBILITY.md).

## What ran

| Setting | Exact diagnostic |
| --- | --- |
| Node | `jl-vm-541077`, eight H200s; this node only |
| Baseline profile | Original `latency-2xdep4-sla.yaml`, SHA256 `edb4c68cb4ee72415abe65c077683a8f88942bfcc8fff5833270ba05cdddcab8` |
| Runtime | Original pinned vLLM image, nominal revision `ac9126e58aa7bbab1856ba6593ba4d5003fea516`; installed file identities are authoritative |
| Model | DeepSeek-V4.1-Flash, revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027` |
| Parallel layout | Two replicas, each TP1/DP4/EP4; two API processes per replica |
| Speculation | DSpark k5, probabilistic drafting, block rejection; **AV off** |
| Other baseline behavior | FP8 KV, prefix cache, Engram host offload and DP embedding; original graph capacities and request logging |
| Workload | First986 exact rows of the median Mooncake trace, ordinary runner at 0.5×; 299.232 s arrival span |
| Client | Original `.venv-aiperf`, seed 42, maximum 256 workers, 120 s warmup |
| Captures | Phase +90 s and +210 s; all eight workers; CPU+CUDA, warmup 1 / active 20 / max 20; no stack/shape/memory/FLOP recording |
| Observation | Three CPU `record_function` labels in two read-only source copies; removing labels reproduces original AST; no new synchronization or computation |
| Evaluator separation | Independent designer `c03_evaluator`; tooling builder `c03_evaluator_builder_review`; source/launch developer `c03_dev_review`; root owns runtime and publication |

The986-row prefix is a short sample, not the full 4,004-request workload. Its service score cannot be compared directly with C03's full-trace score. [Subset receipt](subset-receipt.json), [contract](EVALUATION_CONTRACT.md), [actual runtime identity](runtime-identity.json) and [capture inventory](startup-capture-inventory.json) bind the settings and sources.

## Workload and control validity

| Check | Observed result |
| --- | --- |
| Warmup | 55 completed, 0 errors |
| Profiling requests | 986/986 completed, 0 errors, 0 cancellations; unique IDs and workload keys |
| Completion ratio | 100% |
| Replay p99 / degraded | 4.6538368 ms / false |
| NOTICE versus exact phase start |NOTICE is 46,323 ns earlier; within the prospective 1 s bound |
| Four capture dispatch errors |+2.894ms,+4.844ms,+0.326ms,+0.713ms relative to exact phase+offset |
| Saved traces | 16 files, all eight workers in both episodes; no silent selection of favorable ranks |
| Final drain |Router and all eight running/waiting pairs zero for three consecutive 1 s samples |
| Original files and environments |All 30 pinned file checks and both package inventories unchanged |
| Cleanup |All eight GPU allocations released; ports 8000/8100/8101 closed; monitoring 9400 preserved |

The console's 107,615 ms replay warning exactly matches the **separate warmup** aggregate, not profiling. Both phase exports are retained. A server-metrics completion RPC timed out after the workload ended; its Parquet export later completed 3,105,464 rows and the client reported all results received. This is an observability delay, not a request failure or proof that every telemetry scrape succeeded. The runner exited 1 because the completed prefix missed service SLOs; service eligibility is not this diagnostic's fidelity gate. See [phase reconciliation](phase-final.json), [fidelity receipts](fidelity-builder.json), [cleanup](cleanup.json) and [integrity](final-integrity.json).

## Timing interpretation

The frozen criteria require at least ten complete decode-only cycles per rank/window, actual CPU-launch-to-CUDA correlations, both target and draft graph coverage, and at least 95% categorized device-busy union. The conditional materiality heuristic is target-attributed occupied time at least 20% of complete-cycle span on every rank in both windows. The adequacy gate failed before that heuristic could authorize any next experiment.

The decisive shortfall is replica 1, DP 2, phase +90 s: the trace contains 26 target ranges but only 8 native execute ranges, and only **4 complete eligible decode cycles** survive the required joins. Nineteen target candidates lack an unambiguous native/draft join, two are mixed prefill/no-generation, and one lacks its following boundary. Other rank/window cells retain 15–19 eligible cycles. A configuration requesting 20 active profiler steps did not guarantee20 readable decode cycles.

Five cells also contain GPU activities whose recorded end precedes the start of their supposedly correlated CPU launch:53,406,43,91 and54 events respectively. The reader retains them as unattributed and flags graph-coverage uncertainty. These observations do not distinguish a timestamp calibration problem from a correlation/trace-format problem; no invented correction or timestamp tolerance was applied. Their exact cause remains unresolved.

Readable cycle subsets show target-attributed occupied fractions of roughly 39.6–97.1% of cycle span. These are **descriptive values from an inadequately qualified capture**, not a validated AV opportunity or expected percentage saving. Some target-owned kernels are NCCL collectives, with individual long activities around 40–52 ms in replica 0's second episode. Execution or waiting inside a collective is not necessarily reducible by verifying fewer tokens. Uneven profiling/export across cooperating ranks is a plausible perturbation, not a measured causal explanation.

The predeclared inactive bracket at phase 110–130 s overlaps the first episode's replica 1 stop/export response until phase 113.651 s. It remains marked contaminated and is not shifted to a more favorable interval. The other three brackets have no control/export overlap. These brackets are descriptive context under different traffic, not an unbiased profiler-overhead estimate.

See the complete [reader output](trace-summary-v2.json), [trace inventory](trace-inventory-builder.json), [independent review](EVALUATOR_REVIEW.md), and per-cell timing table below. A cell passing local reader checks does not repair the required all 16-cell coverage.

| Phase offset | Replica / DP rank | Eligible cycles | Target occupied | Draft proposal occupied | No observed GPU activity | Local adequacy |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| +90 s | 0 / 0 | 19 | 86.77% | 6.99% | 4.27% | Pass local checks |
| +90 s | 0 / 1 | 19 | 86.74% | 7.01% | 4.29% | Pass local checks |
| +90 s | 0 / 2 | 19 | 86.83% | 6.82% | 4.30% | Pass local checks |
| +90 s | 0 / 3 | 19 | 86.64% | 6.97% | 4.40% | Pass local checks |
| +90 s | 1 / 0 | 16 | 96.05% | 2.05% | 1.46% | Association uncertainty |
| +90 s | 1 / 1 | 19 | 80.19% | 8.17% | 8.90% | Pass local checks |
| +90 s | 1 / 2 | 4 | 39.56% | 0.43% | 59.98% | Only 4 cycles; association uncertainty |
| +90 s | 1 / 3 | 19 | 80.09% | 8.13% | 9.03% | Association uncertainty |
| +210 s | 0 / 0 | 17 | 97.07% | 1.83% | 0.83% | Pass local checks |
| +210 s | 0 / 1 | 15 | 90.53% | 5.92% | 2.38% | Pass local checks |
| +210 s | 0 / 2 | 15 | 90.27% | 5.78% | 2.62% | Pass local checks |
| +210 s | 0 / 3 | 18 | 97.13% | 1.81% | 0.81% | Pass local checks |
| +210 s | 1 / 0 | 19 | 87.58% | 6.46% | 4.15% | Association uncertainty |
| +210 s | 1 / 1 | 19 | 87.60% | 6.49% | 4.18% | Pass local checks |
| +210 s | 1 / 2 | 19 | 87.60% | 6.46% | 4.23% | Pass local checks |
| +210 s | 1 / 3 | 19 | 88.00% | 6.41% | 3.83% | Association uncertainty |

Percentages use summed same-device complete-cycle span within each cell. Absence of observed GPU activity does not establish physical idleness, especially in flagged cells. Other/unattributed work and any overlap are retained in the [full table](timing-table.json) and [CSV](timing-table.csv); these columns are not an exhaustive additive partition. The required all-cell gate fails despite 11 cells passing local reader checks.

This heuristic does not establish a service critical path, reducible computation, an AV budget or expected speedup. Target ranges include graph-contained communication. Draft execution is a composite graph containing context preparation, model and sampling; draft execution is contained in draft proposal and must not be added to it again. Same-device unions and overlaps are required; summing ranks is not wall time.

## Consequence for the remaining attempts

Do not select AV as the highest-ROI experiment from this evidence and do not launch an AV-ON campaign. The source mechanism is still plausible, but we have not measured its removable cost. There is no automatic replacement run. Any further timing diagnostic needs a prospective instrumentation addendum addressing actual trace categories, timestamp associations, native decode-cycle coverage and rank-dependent profiling perturbation before consuming more GPU time. A later AV qualification must also measure its controller overhead, draft-padding tradeoff, accepted progress and correctness. No C03 patch is silently combined with it.

## Measurement issue preserved

Torch emitted CPU `user_annotation` and mirrored `gpu_user_annotation` events with identical names. The original reader selected by name alone and mixed CPU worker identities with the GPU namespace. The corrected, separately retained reader selects CPU annotation parents explicitly, then uses the same actual CUDA correlations. Independent review approved its two-line schema fix and ten CPU tests before the full 16-trace pass. The original reader/source and first-actual-trace reproduction are retained. No runtime rerun, different threshold or weaker attribution rule was used. [Offline schema addendum](READER_SCHEMA_ADDENDUM.md).

## Cost and preservation

Cold startup took about 26 minutes on this node, including about 20 minutes of model loading. The measured cause of that slow load is unknown. Task-owned containers occupied the node from 20:51:10 to approximately21:29:48 UTC: about 38.6 minutes, or 5.15 allocated GPU-hours across eight GPUs. This includes startup, warmup, replay, export and cleanup; it is not all active inference time. The arrival trace itself spans about 5 minutes. Future pilot budgets must include startup and evidence-processing costs.

All raw traces, backend/client/router logs, request exports and evaluator/source versions are preserved in the [checksummed evidence archive](../../evidence/av-k5-timing-001/README.md). Readable records are organized through [execution](../../records/EXECUTION.md), [analysis](../../records/ANALYSIS.md), [meta-learning](../../records/META_LEARNING.md) and the [C24 hypothesis card](../../hypotheses/C24.md). The original C03 execution artifacts and verdict remain unchanged.
