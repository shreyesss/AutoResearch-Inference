# Independent round96 review

No blocker to retaining this as an optional arm of round92, still parked and unqualified. Seventeen frozen author files, eleven exact source quotes and seven pinned archive/copy equalities pass. This is a downstream projection addition to an already fused producer, not a rediscovery of the state-save/compress/norm fusion or a new counted identity.

## Source and implementation contract

The two _store_latent calls cover different cases: the request's first emitted boundary can depend on the prior ring row, and the pair program skips that first token. The request branch must still execute its ring-tail stores after projection; an invalid index-cache slot cannot justify early-returning unrelated ring/main-cache work. The producer uses state_slots whereas the later K writer uses its own cache slot mapping. A full-shape k_pre buffer avoids a new compaction/index map, but does not itself prove valid output coverage.

One concrete remaining admission check is the set relation: every row read by the unchanged index-K writer must have been emitted by the producer in the same invocation, including first-token boundaries, padding, invalid state slots and short-context/replay paths. Keeping a full-shape output with unwritten rows is sound only with that predicate coverage. The baseline already relies on masking garbage latent rows, so this is a bounded source/interface proof, not evidence of an observed race or need to zero every row. It should precede or accompany the tile/resource design, rather than be hidden by a pointer/shape check. Source ownership/reload and the existing profile/no-metadata fallback must also stay coherent.

The latent BF16 cast and projected-output BF16 boundary are real. The scalar cancellation negative correctly proves a missing cast can matter; it does not prove the synthetic vector occurs after target normalization, or that keeping both casts reproduces a backend GEMM. Here the projection feeds target index-key selection, so changed accumulation can change target support. A future target-preservation test must check the admitted backend/cache semantics; drafter-only numerical freedom does not excuse an altered target sparse indexer.

## Schedule and cost

The source really has two joins: Q/SWA with compression, then index preparation with main-cache insertion. CUDA event1 is recorded after the compressor callable's enqueued work. Moving K into that callable can delay main-cache insertion even if Kf=K. The report's harmful example is valid under its idealized two-stage graph; the beneficial example is equally conditional. A value stored early inside one kernel is not available to the other stream through the existing end-of-call event. Additional intra-kernel readiness would be a different protocol, not implied by fusion.

The helper disables auxiliary overlap during active breakable capture, not universally during every graph replay; the report appropriately leaves actual topology open. Main latent materialization remains necessary. The arm can eliminate the separate wk call and that consumer read, but not all latent stores or K norm/RoPE/cache insertion. Per-row128KiB weights are logical operands, not wire/HBM traffic. A rowwise projection loses some potential batched reuse, while small-shape launch/tile cost may favor fusion; neither direction is established.

The two arms must be compared against the same baseline and real shape strata, not added together. Three source-owning ratio2 layers do not establish executed-call counts or material long-output exposure. The model's scheduling examples and65,536 MAC calculation are design controls only. No runtime graph, numerical, throughput or SLA qualification follows.

## Next useful action

Retain the report's concrete tile/register/weight-reuse plan as the next implementation-design gate, with the emitted-row versus consumer-predicate relation above made explicit. Native compilation and whole-preparation measurements remain later authorized work. Further generic fusion papers or scalar schedule examples would not close those gaps. No new tests or runtime work were run for this review.
