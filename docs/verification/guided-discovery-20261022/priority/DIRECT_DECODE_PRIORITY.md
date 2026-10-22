# Direct-decode investigation priorities

## Decision

Investigate **PJ01 first, MF19 second, A01 third, TR01 fourth** under the frozen long-output ITL objective and separate tail guards. This orders the clarity and cost of the next investigation, **not expected service speedup**. None has measured improvement on the attested target baseline. Preserve all four existing identities, cards, baselines and deferred status. No GPU, network, serving or canonical-memory actions were performed.

PJ01 contains the cleanest missing work elimination: three draft-context projections compute output columns immediately discarded. MF19 avoids a reread by moving quantization into a producer, with a harder rounding/resource/overlap contract. A01 schedules an unchanged projection earlier and may merely move contention. TR01 mostly targets prefill and does not remove ordinary small-decode work; its direct donor has weak service results despite large component improvement.

## Immutable identities

| Label | Hypothesis | Baseline |
|---|---|---|
| PJ01 | `hypothesis:f5836985004cdae101771b82988058329daca79464a067c9d33eac05925869c7` | `baseline:3b223afd8c30209a2c71d6f8cdd36e4da640b4bc67cdf331f108d2d2496131ca` |
| TR01 | `hypothesis:5fb7c35d3e8bd0d3bed75a465702712c06389e7dfd3c7ba3da9f8c16461d3286` | same baseline as PJ01 |
| MF19 | `hypothesis:ad1fb886045bbfd8c17b1fbc2746dbf3a79089b61e4977a50825c8e75482000e` | `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279` |
| A01 | `hypothesis:36794075a7034c3f1ff100e73c1d8436a4606397c8e07766ed5388ef64b16646` | `baseline:80ba6154b79544d9d3c2e657ac363fb6e9aef12047e66f73d2b91d7d0caa0c88` |

A01's historical baseline is not silently replaced by the planned Flash1017 profile. Comparisons below are source feasibility for c455/Flash1017, not evidence these different baseline identities are operationally interchangeable.

## 1. PJ01: remove discarded context-Q columns

Pinned `nvidia/dspark.py:165–195` loops three layers, calls `fused_wqa_wkv(main_x)`, and keeps only `qr_kv[..., attn.q_lora_rank:]`. With the retained config, each linear maps5120→1792, comprising Q1280+KV512. Three smaller KV-only projections retain their own KV normalization, RoPE and cache insertion; actual query forward still uses the complete original projection. This is not a claim of identical weights across layers.

The source caller is reachable during native drafting. V2 DFlash `_precompute_context_kv` passes the **current target hidden span**. FULL capture precomputes a fixed prefix; an eager tail covers extra current rows. These partition work. It is incorrect to multiply by historical context length or by five draft steps. Padded captured rows still incur projection work, while invalid mappings prevent cache stores.

### A source concern resolved in this audit

The checkpoint declares `quant_method=fp8`, block32×32 and E8M0 scales. That spelling does not imply the generic block-FP8 backend: `deepseek_v41/quant_config.py:221–243` maps this native linear layout to `ModelOptLinearMethod(QuantSpec(weight=kMxfp8Static, activation=kMxfp8Dynamic), ...)`, subject to skipped-layer configuration. The retained config contains no ignored-layer list. CUDA MXFP8 selection prefers CuTe then CUTLASS (`kernels/linear/__init__.py:560–564`), but explicit backend filtering, disabled kernels and availability can change selection.

An extracted, unchanged `_check_mm_mxfp8_shape` ran under the repository Python: both full(1792,5120) and proposed(512,5120) shapes pass. N64 and non-32-aligned K5136 controls fail. This closes only a necessary shape-rule objection; it neither selects an installed kernel nor validates real processed tensors. The previous processed-layout audit already establishes aligned output/scale slicing for these two backends. Repeating more integer scale-coordinate fixtures would not establish latency or numerical parity.

### Bound and decisive next check

Nominal MACs per current context row:27,525,120→7,864,320, a71.43% decrease **within these projections only**. Input quantization, three calls, normalization, cache writes, query work, target verification and communication remain. Smaller output width can lose efficiency or change reduction/tactic rounding, affecting draft proposals and acceptance.

**Next action: recover one already-generated, immutable target context-projection exposure record, not a new synthetic GEMM or GPU run.** It must bind:

1. Image/commit and exact checkpoint revision, actual selected linear class and processed weight/scale shapes/strides, plus override/disabled-kernel settings.
2. The three context-projection calls identified separately from query projections, per rank and steady decode round; current target rows, FULL/eager mode, graph prefix/padding and eager tail.
3. Critical-path/exposed timing of projection and remaining quant/norm/insert work, round wall time and committed progress, under the same request and cache settings as the ITL objective.

An existing loader/kernel-selection log can first falsify the initial two-backend adapter cheaply. A trace supplies exposure only if its call identity and baseline can be established. If total relevant kernel duration is at most X per critical rank/round, eliminating all that work is an optimistic bound of X; overlapping rank times cannot be summed. Dividing by actual committed tokens estimates an average round-amortized ceiling, not p95/p99 streamed ITL.

**The bounded local search is exhausted:** reread the52 previously enumerated local metadata files; all hashes unchanged, zero mention of c455, exact Flash1017 revision, either selected kernel class or named context operation. The earlier inventory's16 profiler references have no expected local raw counterparts. This establishes absence in this inspected metadata set, not absence across S3 or the former VM. Source defaults cannot fill this missing record.

**Stop/reopen:** park further CPU address/shape fixtures now. Reopen on compatible attested layout and recoverable exposure; reject the initial adapter if the actual layout differs, without rejecting the general dead-column idea. Only later, with GPU authorization, compare full-projection KV against smaller projection through norm/cache/proposals/confidence and paired serving. If optimistic exposed-time bound is below the predeclared materiality threshold, stop even if the isolated kernel could speed up substantially.

## 2. MF19: preserve BF16 producer semantics, emit packed activation

Original donor57977 emits packed FP8 on the MegaMHC path, but its overlap path returns no packed result. Pinned `nvidia/model.py:506–513` selects overlap on eligible FULL-capture local rows1–16; eager warmup uses another path. Therefore an eager-only timing cannot establish small-decode coverage.

Round29's selective arm adds optional quantized outputs to the existing TileLang input epilogue. It must preserve both BF16 rounding boundaries, output BF16 for the router, group32 amax/E8M0 rules and routed/shared scale mapping. Supplied `layer_input` bypasses the producer, so cannot advertise packed output without writes. Buffers must remain valid through consuming MoE and captures/lanes.

Removing a logical10240-byte BF16 reread per row is not a memory-time bound: cache traffic is unmeasured. Quantization arithmetic and FP8/scalewrites remain, the BF16 store remains, and routing staging still launches. Rows1–8 add work before the coefficient stream is released; rows9–16 can contend with overlapping coefficient work. Resource pressure can exceed the removed reread.

**Next decision-changing record:** a retained capture/dispatch manifest binding actual row buckets and graph mode to the overlap branch, plus separated input/coeff/router/staging timings. Reuse the same existing trace as PJ01 where possible. Source-level numeric constraints are substantially documented; another generic scalar counterexample is not the bottleneck. If the shape branch is never used, the round29 arm is dormant; evaluate the separate original MegaMHC arm only under its own exposure.

**Stop/reopen:** preserve deferred status until branch exposure and a legal compiled epilogue/scale-lane contract are established. Do not promote from nominal bytes or number of MoE layers. External donor GPU-busy improvement versus much smaller TPOT change is a warning about service attribution, not our performance forecast.

## 3. A01: earlier Engram WKV scheduling

Only target Engram layers1 and14 contain the two6144→25600 projections. No multiplier by40 target layers or speculative depth. WKV depends on lookup output/frozen weights; later gates depend on current hidden state, so part can conceptually be scheduled early.

Pinned shared-host prefetch queues lookup1/event1 then lookup14/event14 before decoder execution. Appending WKV1 afterward to that same stream puts it behind lookup14. Inserting it before lookup14 delays that lookup. A separate projection stream avoids FIFO delay only with correct event, output and scratch ownership; it can compete with attention, copies or persistent MegaMoE. No GEMM arithmetic is eliminated.

**Next check:** a retained event/stream timeline and exact selected WKV backend/scratch contract. Look specifically for a legal interval between lookup1 readiness and gate1 need, and corresponding layer14 interval, with fences before persistent MoE. Aggregate idle percentage or WKV kernel duration alone does not demonstrate usable overlap. The current source DAG and dimensionless schedule simulations already identify the FIFO trap; more invented durations add no evidence.

**Bound:** at most the exposed duration of two WKV operations can be hidden, less prefetch delay, contention and scheduling overhead. Use actual per-round committed progress. A large standalone GEMM does not imply a large legal overlap window.

**Stop/reopen:** park until a baseline-linked timeline and scratch/lifetime ownership are available. Retain a potentially useful subset if one layer has legal slack, rather than requiring both. Do not overwrite the historical baseline or infer the shared-host route from a DP-sharded donor.

## 4. TR01: bounded eager context-row trim

This is an adaptation of upstream60320, not a novelty claim. Native three-layer SW128 permits some earlier current-prefill rows to become unnecessary, but rejection/max-model-length clamp needs the query margin and future prefix reuse/KV transfer can require those states. Initial arm preserves full hidden combination and FULL captured prefix, gathering only eligible eager tails.

Ordinary small decode is unchanged. Frozen workload refinement shows one warm2048 span below donor's2048-saved-row threshold; batching two such spans can cross it. These are conditional examples, not observed scheduler exposure. Compact retained rows must be projected in a batched call, not one GEMM per request; gather and scatter costs remain.

The direct donor's GB200 context path drops2.57→~0.2ms, yet reported TTFT changes have95% intervals including zero, and use outputlength1/synthetic acceptance. Our initial arm preserves main_proj that the donor also saved. This is strong contrary evidence to a large long-output ITL forecast. An indirect benefit through prefill interference remains possible but unmeasured.

**Next check:** an existing scheduler trace with eligible prefill spans/cache-group policy, FULL prefix and actual retained-row threshold hits during the frozen mixed workload. If ordinary decode dominates and qualifying prefill does not overlap it, park for this objective. Reopen for measured mixed-prefill interference or a changed explicit TTFT objective. Do not design a new service benchmark merely to manufacture exposure.

## Interactions and denominators

| Pair | Shared work or interference | Required interpretation |
|---|---|---|
| PJ01 + TR01 | Same context GEMMs: columns versus rows | Nominal joint projection work is retained-row fraction×512/1792. Gains are not additive; future baseline/row-only/column-only/both comparison. |
| MF19 + A01 | Can compete for compute, bandwidth, stream execution and scratch during target work | Savings under one schedule do not carry unchanged to another. End-to-end critical path, not sum of standalone durations. |
| PJ01 + other drafting changes | All affect round time and potentially accepted/committed progress | Hold correct target output and inspect draft cache/proposal/confidence changes; correct target-only outputs alone can conceal acceptance degradation. |
| All four | Same target service objective and guards | Never add percent-GEMM, percent-bytes, TTFT and GPU-busy percentages. Tail/ITL and throughput require their own paired measurements. |

For a fixed critical-path decomposition and unchanged progress, potential round-time reduction is exposed component fraction×realized component reduction minus introduced overhead. None of those quantities is established here. Queueing and tail changes need serving evidence; arithmetic and trace ceilings do not predict their sign.

## Audit quality / limits

Source and metadata hashes are in source_exposure_audit.json; frozen science reports are referenced rather than rewritten. The shape check initially failed under system Python because that interpreter could not evaluate `str | None` annotations; rerun with repository Python succeeded. No serving imports occurred. Four extracted shape checks are necessary-condition diagnostics, not target execution. The52-file scan is deliberately bounded and cannot prove remote artifact absence. No new hypothesis or acceptance, no change to any immutable baseline, no service qualification.
