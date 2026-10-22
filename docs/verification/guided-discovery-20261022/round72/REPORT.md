# Round72 — actual role admission and one complete MegaMoE phase transition

**Decision: retain a source-blocked N03 refinement; zero new hypotheses, zero implementation/service promotions.** The follow-up found real ready-chunk claiming in the released donor, but it does not supply the paper's adaptive controller. In the inspected current GEMM+AllReduce body, completed compute/communication CTAs call the reduction helper and then are excluded by every applicable branch. The target already has a complete epilogue-to-combine transition. A different worker joining combine needs a new ownership/resource protocol; simply copying the donor helper does not establish one.

No GPU, native imports/builds, model tensors, serving changes, canonical writes or cloud mutations. This is a bounded source/control-flow audit, not a performance test.

## Question, pins and prior relationship

Round69's paper [mKernel v1](https://arxiv.org/html/2609.13585v1) explicitly describes checking a shared target allocation between tasks. Its existing source audit found fixed MoE role splits. This round follows that specific implementation gap rather than searching for another paper stating the same principle.

- Donor: `uccl-project/mKernel@ef6225fdde493f4119f519c99bfa4ad9234e323b`.
- Target: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; dependency `vllm-project/DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`.
- Planned applicability: exact Flash-1017, TP1/DP4/EP4 B200 layout, baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`. No live runtime attestation.
- Existing N03 identity: `hypothesis:8357ac76a236b1a020bb729b91f0f774a779b5740d334b313f299fd54a86d30f`, immutable original baseline `1267ac65dc4f2f8fd4af62851edd567cf10ad58e206487c21ab8caa495d5387c`. That older Flash profile is not silently rewritten into Flash-1017. No typed identity, baseline or status was changed.

## What was actually investigated

The retained recursive donor tree has 162 entries and `truncated:false`. No filename explicitly names an adaptive controller. This alone proves little: the controller could be embedded. Three exact files were therefore fetched through `researchctl investigate`: `src/gemm_ar.cu`, its `include/operators/gemm_ar/gemm_ar.cuh` header, and `src/dispatch_gemm_warp_specialization.cu`. GEMM+AllReduce is a paper-evaluated operator, and the alternate MoE file tests whether a different specialization body contains the missing mechanism.

All three requests succeeded: three logical HTTP cache misses, no dossier errors. This is not an exact physical-request count; transient transport retries are outside that receipt's logical count. No new paper search or fulltext fetch was needed. One inherited paper fulltext and README were reused locally. The first selected import mistakenly pointed at a JSON export and returned `DatabaseError`; the successful retry used the retained SQLite corpus. The failed command is preserved in `command-journal.json`, and the empty failed-output file is retained.

Read depth: branch functions, kernel dispatcher, host split builder and relevant header fields read directly; selected alternate warp-specialized role/loop bodies read; remaining body text is retained and lexically screened. This is not a claim that every donor operator or linked artifact has been exhaustively audited.

## Decisive donor control flow

See `sources/src__gemm_ar.cu`, lines 1197–1377, and the named reducer bodies earlier in the file.

`fused_kernel` calls `shared_reduce_my_slice` after compute, intra-node reduction and inter-node send. A completed primary worker has `red_id < 0`. Since that invocation has primary workers, `consumer_only` is false.

| Selected branch | Predicate / actual admission | Recycled primary CTA |
|---|---|---|
| Receive-ready queue | Queue enabled and receive-progress CTAs exist; body rejects negative `red_id` | Excluded |
| Work-stealing reduction | `total_chunks >= 512`; body rejects negative `red_id` | Excluded |
| Static reduction | `total_chunks <= 64`; body rejects `!consumer_only && red_id < 0` | Excluded |
| Remaining scan | Consequently `65 <= total_chunks <= 511`; recycled admission requires `total_chunks <= 8` | Excluded |

Thus the apparent tiny-chunk recycling condition is unreachable for a recycled primary CTA through this dispatcher. The header's “all CTAs” comment and the presence of the handoff call are not sufficient evidence that role reuse is enabled. This is a source result for this revision, not a claim that the paper never implemented an adaptive variant or that every repository branch is identical.

`branch_audit.py` checks the exact named source guards and their order, then illustrates the boundary cases with a hand-transcribed model. The interval contradiction supplies the general argument. Twelve boundary rows are not twelve runtime tests. Its negative control shows the header-comment interpretation incorrectly predicts recycling for eight chunks; actual control selects the excluding static branch.

### What is reusable, and what is absent

The donor does have a useful concrete task protocol for **admitted dedicated reducers**:

1. Acquire-read remote-arrival and local-completion flags.
2. Claim a ready chunk by CAS `local_done_flag: 1 -> 2`.
3. Broadcast that claimed chunk within the CTA and reduce it.
4. Order completed writes before incrementing the published count.
5. Keep receive-queue progress and end-of-iteration reset/barrier ownership explicit.

This is task ownership, not the adaptive role controller. Current work-stealing comments explicitly say admitting 132 competing CTAs caused cache/atomic contention; this is an author explanation, not our measurement. The host `gemm_ar_compute_role_split` uses launch arguments/environment and shape bounds to set fixed counts. The alternate dispatch/GEMM file uses fixed `wg == 0` communication and `wg == 1` epilogue roles, with fixed task strides. None of these inspected bodies provides the paper's shared desired-role count with safe task-boundary reassignment.

The donor's final barrier is also selective: only dedicated reduce CTAs are guaranteed to finish final publication before resetting arrival flags. Its own comment warns that allowing the whole grid to reset early caused a race. A transplanted role policy cannot ignore that lifecycle.

## One complete existing target transition: epilogue to combine

All locations below refer to retained `target__deep_gemm__include__deep_gemm__impls__sm100_fp8_fp4_mega_moe.cuh` at the pinned dependency.

| Phase | Actual contract |
|---|---|
| Finish expert L2 outputs, 1335–1373 | Store each routed contribution in its selected destination slot; fixed epilogue barrier protects shared-memory reuse. |
| Release tensor-memory ownership, 1376–1379 | Logical epilogue warp 0 frees TMEM, with a same-logical-warp requirement across the two CTAs. |
| Allocate combine interpretation, 1381–1419 | Reuse SMEM through two load stages plus one store stage per **epilogue warp**. Static chunk count and resource bounds depend on epilogue warp count; separate per-warp barrier addresses are calculated. |
| Publish completed producer phase, 1421–1435 | Epilogue grid synchronization establishes all local L2 writes complete. Publish the corresponding generation's combine readiness to remote ranks with release semantics. |
| Release cleanup, 1437 | Fixed-count dispatch+epilogue barrier permits dispatch workers to clean the workspace. It does not assign them combine tasks. |
| Own combine tasks, 1441+ | Static disjoint `(epilogue_warp_idx, sm_idx)` token/chunk stripes. There is no late-worker CAS queue here. |
| Consume and reduce, 1450–1514 | Acquire-wait on selected expert ranks' readiness for this generation. Load shared expert first, then routed slots in top-k order; wait load barriers and accumulate BF16 contributions into FP32. |
| Commit output, 1517–1541 | Round to BF16; wait previous TMA store before overwriting its store buffer; issue the next output store with existing warp/TMA ordering. |

This is already a useful phase transition. Rebranding it as missing would be a duplicate. Task reallocation across chunks might preserve each chunk's arithmetic if it preserves that exact order, but that does not establish safe resources, completed stores or captured runtime behavior.

## Attempted new transition: dispatch cleanup to combine

Dispatch currently waits at the fixed dispatch/epilogue barrier, clears expert send/receive counts, task counters and ring-generation state, then participates in the all-rank cleanup barrier (625–693). This cleanup is deliberately overlapped with combine.

A dispatch worker cannot simply call the epilogue combine loop after “finishing its useful work”:

- Skipping or shortening cleanup removes required arrivals and can corrupt the next invocation.
- Combine ownership is already statically distributed. A new worker needs an exactly-once claim or an explicit redistribution; reusing an epilogue index duplicates work, inventing another index violates the current stride/resource allocation.
- Combine scratch/barriers are provisioned for epilogue warps. Register allocations and roles differ; available dispatch registers do not imply a valid extra combine scratch slot.
- Readiness is generation-specific and depends on remote ranks. Local idleness does not certify a whole task ready.
- Before moving any activation producer, its outstanding L1/L2 generation and stage-consumer obligations must be completed. The scheduler waits for stage release **before** claiming/publishing a task; it is not a free global job queue available to every idle warp.

These are source-visible missing contracts, not a measured deadlock or a proof no future design can work. The dedicated-donor CAS primitive is a possible ingredient, but a target-compatible transition has not been established. We therefore do not propose a speculative simulator that assumes compatible workers and barriers.

## Benefit, evaluation and stop decision

No compatible trace establishes unused workers overlapping enough remaining combine work. Even an otherwise valid transfer can only save exposed remaining work within the admitted worker's legal late window, minus claim, synchronization, resource and contention overhead. Neither duration nor the critical-path fraction is measured here. No H100 headline, large-token result, SM count or logical idle branch is converted into B200 ITL.

**Fastest falsifier completed:** inspect actual role-admission guards and target ownership. It falsifies treating the selected donor as an available adaptive controller and falsifies a missing target epilogue-to-combine reuse premise. It does not falsify every adaptive role policy.

**Reopen only with a concrete protocol:** locate an executable adaptive controller artifact or specify one named target transfer with exactly-once tasks, cleanup/barrier completion, scratch/register ownership, generations and preserved reduction order. First source-check that protocol. Subsequent GPU evidence would need to prove numerical/termination behavior and exposed phase time, then compare long-output client ITL with standard tail guards. Those experiments are not authorized or run in this CPU-only task.

Yield: three targeted new source reads, one inherited fulltext, zero new papers, zero new mechanisms admitted as hypotheses, zero implementations or service improvements. The decision-changing result is a narrower and better-supported blocker for the existing N03 family.
