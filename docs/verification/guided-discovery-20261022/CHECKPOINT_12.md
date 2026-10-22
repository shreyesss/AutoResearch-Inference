# Checkpoint12 — prioritize exposed work; preserve negative results

**Canonical guided portfolio:35 reviewed cards,2 accepted bounded CPU investigations,25 deferred,7 rejected,1 duplicate; zero implementation/service qualifications.** NQ33-01 has passed independent source/address review but remains pending canonical retention. Including it gives36 reviewed proposals/26 deferred. Accepted historical CPU investigations remain parked where their useful next step requires missing exposure evidence.

## What to investigate next

[Independent direct-decode priority audit](priority/DIRECT_DECODE_PRIORITY.md): **PJ01 → MF19 → A01 → TR01**, ordered by the clarity and cost of the next investigation, not predicted speedup.

- **PJ01:** three context projections compute Q1280+KV512 and immediately discard Q. The native checkpoint's FP8 spelling routes through ModelOpt MXFP8; the proposed512×5120 shape passes the relevant source guard. This clears a necessary source objection. Actual processed backend/layout and exposed context-operation time remain unknown. The71.43% nominal projection-MAC reduction is not an ITL estimate.
- **MF19:** producer-emitted packed activation may avoid a reread, but preserves both BF16 boundaries and changes the overlap schedule. Extra work can delay the coefficient stream.
- **A01:** earlier Engram WKV could hide existing work only if the true lookup/stream/resource timeline has slack; two projections, not40layers.
- **TR01:** bounded context-row trimming mainly targets eligible prefill. Ordinary small decode is unchanged. Combining it with PJ01 multiplies retained rows by retained columns; savings cannot be added.

The52-file local metadata inventory does not provide the needed exact-baseline trace. A separate bounded read-only S3 inventory is underway; no GPU/device queries or new traces are being generated.

## New candidate: packed-scale padding scheduling

[NQ33-01](round33/REPORT.md) separates live Q/KV work from padding-only scale initialization inside the existing fused launch. At the target Q1280 width, the illustrative small-shape grid changes256CTAs to2n+10 while retaining one kernel launch and every allocated scale byte. This is fewer workgroups, not fewer launches, a memory-bandwidth claim or a speedup forecast.

The128-case integer layout diagnostic covers all bytes and catches88 failures of naive contiguous-prefix zeroing. [Independent review](round33/INDEPENDENT_REVIEW.md) checks the source offset/inverse at six boundaries. Neither executes live RMSNorm/FP8 conversion, Triton, PDL or a device kernel. Original empty CTAs may be cheap; grouping padding writes may not improve the critical path.

The [append-only clarification](round33/REVIEW_ADDENDUM.md) limits the two-consumer claim to index-source layers. Other layers have the main projection only. Matching producer PDL intrinsics is insufficient: the external FlashInfer consumer visibility contract still needs validation. Keep NQ33 deferred and below more substantial work-elimination candidates pending exposure.

## Supplementary literature result

[Round34](round34/REPORT.md) revisited temporal exact Top-K through the older Guess-Verify-Refine paper. It produced **zero new hypothesis cards**. The target already has cooperative/persistent selectors and sampled threshold/refinement machinery; M02 already records a failed direct-port case. A temporal predictor is a potentially different component, but needs exact fallback, tie handling, speculative/request-state ownership and target row-cost evidence. Search rediscovery does not reopen M02 or prove novelty. The report records partial paper-read depth and supplementary web-tool scope.

## Pipeline robustness and verification

`paper-search` previously returned shell exit0 even when its structured receipt said `failed`. Commit `5004540` now returns1 for that outcome while preserving the complete JSON receipt. A successful empty search still returns0; partial useful results remain explicit and return0. Provider requests, caching, persistence and in-process/MCP receipt semantics are unchanged. **305 tests +25 subtests passed**, bootstrap dry-run and diffcheck passed.

## Canonical retention and backup boundary

Four queued operations completed: earlier21/23/24/25 recovery,26/27 refinements,29/attention30/32 screenings, and HS30. Root independently resolved and hash-verified all **463 artifact references** in their completion receipts. Canonical total is139 hypotheses including historical campaigns; HS30 is deferred on exact planned baseline `d4640b…`. See [readback](canonical-through-host30.json). This is current local-state verification, not remote restore proof.

Published lineage advanced to `743ef260ed43b945f9b0680d6e36dbd09f41cdbc2f3634910c78c5088d9f2628` at03:23:43UTC. The03:26:09 pending marker correctly says the latest imports need a new snapshot/publication. Their successful local import does not mean that existing remote snapshot contains them. Read-only remote-manifest verification and newer publication status will be reported separately.

The loop remains active: recent output-projection research, independent scrutiny, and recovery of existing exposure evidence. No GPU experiments, model launches, serving changes or training.
