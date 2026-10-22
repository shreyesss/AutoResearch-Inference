# Checkpoint 24 — a narrow cache-policy experiment and corrected adjudication

The CPU-only guided discovery loop continues. No GPU call, CUDA compilation, model/native execution, serving change or measured inference improvement occurred. Independent source review selects CR64 for future consideration; execution remains deferred.

## CR64: shared compressed KV should have its own cache-hint comparison

The pinned SM100 Mega attention reader uses FIRST eviction priority for both per-layer sliding-window KV and the physically shared compressed-cache tensor. Later layers reference the same source allocation, although their selected positions can differ. The proposed intervention changes only compressed-cache payload gathers to NORMAL or LAST; SWA remains FIRST. It changes neither attention support nor precision, token scheduling, gather addresses or barrier accounting.

This is a plausible opportunity to preserve useful L2 lines across layers and verification queries. It does not prove those lines survive intervening weights/indexer work, that misses fall, or that a local reduction improves the group critical path. This is specific to the inspected B200/SM100 source route; H200 applicability is not established.

| Arm | SWA payload hint | Compressed payload hint | Question |
|---|---|---|---|
| A: pinned control | FIRST | FIRST | Current behavior |
| B | FIRST | NORMAL | Does the default policy preserve useful reuse without excessive retention? |
| C | FIRST | LAST | Does stronger retention improve the objective relative to A and B? |

**A subtle adapter requirement:** a non-mixed block can contain entirely compressed-cache rows. `MIXED_BLOCK=false` does not mean SWA. Policy routing must preserve all-original, all-extra and mixed blocks, along with separate two-CTA scale staging. The role fixture is symbolic; no C++ adapter was compiled or tested.

The source also documents a compiler issue with selected tensor-map pointers and a tight instruction-cache footprint in the h128 variant. Neither proves integer hint selection fails on the planned 64-head target. Preserve the existing pointer-offset workaround and burst structure; inspect actual emitted operands and resource use before an authorized native test. [Report](round64/REPORT.md), [independent review](round64/INDEPENDENT_REVIEW.md), [code-generation constraints](round64/CODEGEN_ADDENDUM.md).

## What would actually test it

First confirm the selected backend/build and cache-owner mapping. Then compare A/B/C with identical inputs and attention arithmetic, including mixed, all-extra, invalid-row and two-CTA cases. The performance probe must include a real consumer sequence with intervening model work. Flushing L2 before every isolated launch cannot answer the cross-layer reuse question.

Measure dependency-visible attention time, relevant cache traffic, complete decode-round time and the cross-rank maximum. Lower cache misses alone do not qualify the change. Keep agent-p75 and Mooncake as standard service evaluators, with long-output ITL primary and separate TTFT/tail/goodput/failure guards. No new service workload is justified at this stage.

This option is narrower than RM61 migration or LP63 partial-depth continuation. Its expected gain is unknown; there is no evidence-based percentage ranking against PJ01 or CF59. Source-grounded plausibility and a cheap comparison justify keeping it, while performance qualification remains pending.

## A real review error changed the skill

The original report proposed NORMAL or LAST over FIRST, but its rejection sentence included “NORMAL wins.” That would wrongly reject a successful NORMAL arm. The original remains frozen; an [additive correction](round64/DECISION_ADDENDUM.md) supplies the proper arm-specific interpretation.

NORMAL improving over FIRST supports the proposal even when LAST loses. NORMAL beating LAST alone does not establish improvement over FIRST. If the data are noisy or underpowered, retain an inconclusive outcome; lack of promotion evidence is not proof of equivalence or a measured regression.

The critic skill now explicitly checks arm-versus-baseline and family-level decisions, ties, uncertainty and guards. The focused instruction passed skill validation and independent review. This is an observed instruction repair, not a new semantic validator or demonstrated increase in research quality. [Lesson](multi-arm-decisions/REPORT.md). No runtime code changed; the preceding code test gate is not presented as a new run.

## Measured research yield and a targeted follow-up

The independently recomputed rounds 58–63 inventory contains 13 queries, 133 returned hit references, 122 declared paper identities and 14 selected distinct fulltexts. Those lanes produced three deferred directions, zero implementation/service qualifications and no native/service attempts. Adaptive overlapping searches are not independent trials: do not report a paper-to-win rate. [Yield audit](yield-5863/REPORT.md).

The audit chose a concrete CF59 uncertainty instead of another broad query. Five source-extracted CPU guard cases narrow which steps can exclude extra sampler processors and optional prompt-head calls. Root reran the same fixture and obtained identical results; this is five distinct cases, not ten independent observations. External FlashInfer scratch/stream behavior, graph ownership and actual eligibility frequency remain unproved. No new hypothesis or speed estimate follows. [Checks](yield-5863/source-guard-checks.json), [root review](yield-5863/ROOT_REVIEW.md).

Round64 separately used three dated paper searches, 16 paper hits and one selected fulltext. That paper concerns a CPU/cache architecture and is background only; exact target source and PR counterevidence established the intervention. The zero-result exact policy search is retained. Five PR bodies were read, not claimed as full donor code audits.

## Canonical state and publication are separate

The 58/59/60 package, CF59 prompt-logprob refinement and 61/62 package completed their normal canonical commands. Root independently resolved 255+14+208 artifact references and checked 171+6+119 revision references across these packages; these sums include possible shared sources and are not distinct-source counts. CF59 remains deferred with its original five claims plus three additive background links. RM61 remains deferred with six claims. The read-only canonical inventory contained 145 cards at 06:12:52 UTC. [Readback](retention-24/6162-cf59-root-checks.json).

LP63's isolated typed replay/restore passed and its exact canonical application is queued through the same writer sequence. CR64 and the yield companion have separate retention work. Completion is claimed only where a receipt exists.

The last observed published lineage was `f82df0e3c9dc0b01534b03f6915f2b1f1e000e888e1ee4de0b4d0b2d63da356d`, published at 06:05:49 UTC, before these imports. It does not certify their S3 coverage. GitHub backfill had reached 923 successful pages at the saved 06:07:09 observation; that is progress, not full-repository completion or a wall-clock ETA. [Publication observation](retention-24/publication-observation.json).

A separate pass is auditing sampling-state metadata copies and another is testing vocabulary-output invariants against native stochastic verification. Neither is presented here as a completed candidate. [Delivery hashes](source-copy-manifest-24.json) preserve the copied artifacts; original evidence remains outside Git.
