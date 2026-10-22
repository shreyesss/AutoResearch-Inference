# Checkpoint 30 — three refinements and a sharper admission rule

The CPU-only guided discovery loop continues. Start with the [current candidate map](CANDIDATE_MAP_30.md) for the concrete source changes, strongest objections and next informative comparisons. Its order reflects bounded implementation scope, not predicted gains. No serving speedup or GPU experiment has been established in this campaign.

## What changed scientifically

### CF59: a narrower, better-supported overlap arm

The source audit found no common external MXFP8-GEMM/workspace caller between the admitted native block-rejection path and context projection. A shared allocator alone does not establish a scratch race. The first arm can fork after the target head and join immediately **after the original AsyncOutput enqueue**, before postprocessing. This narrows the concurrent surface while preserving the proposed early token-release ordering.

Inputs, projected outputs, capture buffers and subsequent reuse still need valid ownership. An existing graph must actually consume the new staging once; moving eager work beside an unchanged graph can duplicate it. The source audit does not prove native scheduling safety or useful overlap. [Mechanism and ownership](round81/REPORT.md), [independent review](round81/INDEPENDENT_REVIEW.md).

The benchmark's thinking effort75 is a separate concept from `thinking_token_budget`. The saved request builder and pinned protocol distinguish them. Consequently the label alone neither disables nor establishes the guarded logits-processing path. We retain effective per-request admission and preserve requested thinking behavior. The native budget helper itself has no shared-GEMM caller, but other active processors still need inspection before widening the arm. [Source clarification](round81/THINKING_ELIGIBILITY.md), [review](round81/THINKING_REVIEW.md).

### EC79: measure the actual changed return value

A recent mixed-precision paper, NatScale, sharpened EC79's future quality experiment. Its full weight-allocation objective cannot be copied: its unchanged-weight structural factor could assign zero cost while the return codec changes activations.

Retain the useful measurement distinctions: residual at the actual already-weighted BF16 return boundary, complete token-combine error with native accumulation order, real event counts, then downstream distributions and generated task outputs. Do not apply routing weights twice or equate local error with task quality. This refines the existing experiment; it supplies no transport tolerance or speedup estimate. [Selective synthesis](round80/REPORT.md), [independent review](round80/INDEPENDENT_REVIEW.md).

### AT02: dense prefix code is not a sparse-attention adapter

Two adaptive queries found GraniKV. The provider's newer v2 fulltext was unavailable; the report explicitly reads v1 and content-hashed anonymous code, without claiming a Git pin or latest-revision coverage.

The donor groups physical prefix owners and reads a dense contiguous prefix. Our reader uses per-query physical TopK, separate SWA/compressed regions, an attention sink and fused quantization/RoPE. A direct transplant would change selected support. Physical-owner grouping with exact masks remains a refinement of existing AT02; storage-only slabs remain unqualified. Different queries keep their own scores and normalization, with the sink accounted for once.

The next useful evidence is an actual executed selected-slot trace, not a synthetic shared-prefix workload constructed to guarantee reuse. Existing Mooncake and agent-p75 remain the service evaluators. [Source comparison](round82/REPORT.md), [independent review](round82/INDEPENDENT_REVIEW.md).

## Rubric and skill correction

Independent review of the candidate map exposed a possible overly strict filter. **Changed draft activations are not automatically a target-distribution failure.** For PJ01, comparing old/new KV numerics diagnoses the changed proposal; losslessness depends on consistent actual proposal probabilities, acceptance/residual handling and the target-facing contract. Confidence, AV and accepted progress can change and need accounting. An explicit task requiring draft equality still governs that task.

This relaxation does not apply to EC79's altered target arithmetic. Eight lines were added to the existing synthesis reference; no orchestration component was added. Existing scalar probability controls support the distinction within their stated scope, not native DSpark correctness. Skill validation, 385 research tests plus 29 subtests, bootstrap dry-run and whitespace checks passed. Independent review passed. There is no claimed before/after behavioral quality score. [Change and evidence](skill-draft-target/REPORT.md), [review](skill-draft-target/INDEPENDENT_REVIEW.md).

## Yield and command usefulness

Rounds80–82 produced **two provider searches, 20 returned paper identities, two selected fulltext reads, three existing-hypothesis refinements, and zero new hypothesis identities or implementation promotions**. Round80 followed a known result; round81 was source-only. These are bounded campaign observations, not independent trials or an exhaustive literature census. [Counts](yield-8082/counts.json).

The useful changes were specific: rejecting an incompatible objective, narrowing a lifetime hazard, separating thinking configuration fields, and preventing a dense reader from replacing sparse support. A failed v2 fetch remained a failure; the older version was explicit. Invalid setup/plan attempts were retained, and failed empty recalls were not treated as prior-coverage evidence. The existing error surfaces resolved those mistakes; no new retrieval feature was justified by them.

## Memory and publication

Root independently reread canonical retention6566/6768: 259 artifact references and 106 source revisions, exact deferred HM65/AV68 state, and preserved PJ01 state plus its reviewed background links. Three existing paper revisions differed only in retrieval timestamps/query fields, with matching scientific hashes; the review records that distinction. [Readback](retention-30/canonical-readback.json).

The reviewed EC79 packet and its round80 background-only refinement are approved for the existing serialized import chain; this is not a claim those successors have completed. Original cards, decisions and baselines remain immutable. [EC79 retention review](retention-30/7879_REVIEW.md), [refinement review](retention-30/80_REVIEW.md).

At07:53 UTC, local receipts still recorded the last research publication at07:32 (`1dd2460…966f`), while a newer local snapshot (`80abdf2…f3e9`) existed. The backfill receipt recorded969 successful pages and its last completed batch at07:38. These observations do not establish current process liveness, newer S3 coverage or VM synchronization. [Exact observation](retention-30/publication-observation.json), [delivery hashes](source-copy-manifest-30.json).

The next active investigations inspect a recent low-bit attention-state paper against the native mixed-format cache path and search recent PRs for a genuinely missing, separable optimization. All GPU and serving execution remain outside this session's authorization.
