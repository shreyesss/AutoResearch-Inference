# Checkpoint38 — recent papers, actual target mechanisms and historical workload evidence

## Result

Three literature branches produced **zero new formal hypotheses**. They preserved two conditional components, rejected direct ports with concrete source reasons, and connected useful attention work to an existing hypothesis. No GPU work, implementation qualification or measured serving improvement.

| Branch | What remains useful | Why it is not ready for implementation |
|---|---|---|
| FairInference: restoration-budget cache reservation | Account for restoration cost when choosing what state to retain | Need an actual costly eviction/preemption decision and its alternative victim/headroom cost |
| T-CCL: TMA bulk reduction | A real copy-and-add primitive with a pinned donor implementation | Target uses ordered FP32 combine; representation, initialization, ordering and extra passes remain unresolved |
| Tessera: logical support versus physical tiles | Exact membership and execution mapping for cross-query reuse | Direct port mismatches the reader; useful residual is existing AT02/QUILT work |

## 1. FairInference: preserve the component, do not transplant the guarantee

[Round105](round105/REPORT.md), with [independent source review](round105/INDEPENDENT_REVIEW.md), read the recent paper's restoration-budget policy separately from its deadline scheduler. It can inform single-tenant retention too; missing tenant identity is not a blanket rejection.

Pinned vLLM reuses zero-reference blocks and separately preempts active requests under allocation failure. A free-queue change alone cannot provide the paper's active-request guarantee. Protecting inactive cache can also reduce admission/batching headroom or move eviction costs elsewhere. The donor's SGLang0.3.0/Llama8B timing model and reported scheduler overhead do not estimate our serving cost.

The paper search genuinely adapted: the first query's10 results were application metadata; the second query's10 results concerned serving. One fulltext and three retained PR bodies were inspected. This is evidence of a useful within-branch correction, not a measured improvement in general research recall.

## 2. T-CCL: distinguish dispatch from combine

[Round106](round106/REPORT.md) and its [independent review](round106/INDEPENDENT_REVIEW.md) separate five components from T-CCL/RailWave and inspect an exact FlashInfer2529 donor head.

- Native scaled-FP8 H5120 **dispatch has one pull chunk**. A deeper pipeline within that row cannot hide repeated waits that are absent at this geometry.
- Native **combine has two chunks** and already alternates two load slots. It sums the shared contribution and selected expert contributions in a defined FP32 order, then casts to BF16.
- The donor bulk-reduction option replaces an atomic finalizer. A direct BF16 reduction introduces intermediate rounding; an FP32 variant needs compatible storage, initialization, ordering, completion and final conversion. Those costs are not free.
- RailWave's inter-node rail schedule does not fit planned single-node EP4. TP1 also makes a generic dense TP-collective backend swap a poor default intervention.

Two scalar arithmetic witnesses disprove assumed equivalence only. They do **not** demonstrate target quality loss or forbid a separately quality-gated arithmetic experiment. Current ROI is unknown; these components do not outrank narrower operation-removal candidates on the evidence available.

## 3. Tessera: useful synthesis without another duplicate

[Round107](round107/REPORT.md), with [independent review](round107/INDEPENDENT_REVIEW.md), read a previously abstract-only paper. The paper separates logical attention support from physical tile size, preserving membership while changing execution.

The target already groups selected token slots into physical B_TOPK blocks. Cross-query reuse requires a typed union and per-query membership; otherwise it changes support. That useful remainder is the existing AT02/QUILT direction. It does not automatically remove the wrapper's BF16 KV gather or the fused reader's RoPE, sink and quantized output handoff. A different paper is additional evidence, not another intervention to count.

The fulltext came from an unversioned HTML locator; its observed content hash/time is retained without inventing an arXiv version. OpenAlex publication dates are also kept distinct from submission dates.

## 4. Existing Mooncake results narrow the cache-policy evidence gap

[Round108](round108/REPORT.md), its [required corrections](round108/CORRECTIONS.md) and [independent review](round108/INDEPENDENT_REVIEW.md) inspect all21 locally retained score summaries and paired manifests in the declared analysis directory.

These runs span October17–18. Eighteen scores report cache-hit share;17 have full reporting coverage and one reports4003/4004 requests. **None of the21 manifests supplies a nonempty selected image.** Their benchmark checkout revision is not a server-source pin.

The public cache-heavy example reports10,142,720 cached prompt tokens out of33,375,484 (~30.39%). It does not establish that the remaining tokens were evicted or avoidably recomputed: cold/unique suffixes, routing, cache support and window boundaries are alternatives. The summaries contain no eviction/preemption/recomputation attribution. Missing counters remain unknown, not zero.

Existing endpoint benchmarks can remain service comparators. A future diagnostic would add the missing attribution to the same workload if already-recorded traces cannot supply it; no tenant workload or new GPU run was created here.

## 5. Skill verification did not manufacture a win

The [date-guidance forward check](date-guidance-forward-check/REPORT.md) gave two independent agents the same offline planning request. Both old and revised skills produced correct date bounds, observation dates, compiled recipes and prior-query linkage: **5/5 versus5/5**. No search was executed. The control agent disclosed incidental historical text from an overly broad source search, weakening isolation.

Keep the focused instruction as clarification of the observed round105 mismatch, supported by compiler replay. Do not claim this single-case, post-output-scored comparison proves better research judgment or yield. Production Python is unchanged; the earlier skill edit passed408 research tests plus29 subtests and bootstrap dry-run.

## Yield and next work

Across105–107: five online query invocations,50 returned references before cross-round deduplication, four selected fulltexts, source/PR triangulation, zero new formal cards. Round108 adds historical evidence inspection, not a benchmark result. All rejection/overlap/conditional dispositions are retained.

The next source task is FV86's existing-launch eligibility flag and its freshness/consumer contract under AV. The next literature task checks frozen-weight representation changes against the actual task policy, distinguishing numerical-tolerance arms from lossless sampling requirements. No GPU execution is authorized.

Git delivery is separate from canonical and S3 retention. Independent local restore reviews verified133 artifacts/71 revisions for101–104 and46 artifacts/44 revisions for105; approved canonical successors remain sequentially gated behind earlier work. This checkpoint does not claim that queued state is already published remotely.
