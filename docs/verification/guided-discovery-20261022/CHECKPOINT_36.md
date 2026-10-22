# Checkpoint36 — selective transfers that survive source review

The CPU-only loop continues. This batch retains two distinct research
directions, corrects their optimistic premises, and rejects two additions
already implemented in the target. **No native implementation, GPU execution,
service qualification or measured improvement.** The reference remains the
pinned Flash1017/c455 source plan, not an attestation of a running node.

## 1. SL97: change the Sinkhorn lane layout, keep the computation

FlashInfer PR6202 supplies a separable two-row register layout for the4×4
coefficient matrix. The pinned DeepGEMM helper still assigns one scalar to each
of16 Comb lanes. We can investigate that layout within the current backend,
retaining20 iterations, target epsilon/primitives, Pre/Post/Comb outputs,
synchronization and the original Pre return value. The donor's complete CAKE
backend and timings are not required or transferable evidence.

The independent critic corrected the initial cost premise: both layouts have
four source shuffle operations per normalization stage. The donor adds entry
gathers and replicated per-lane work; returning values to the old output owners
also costs communication. Any benefit must come from dependency scheduling or
instruction-level parallelism, with register pressure as a serious countercase.
The FULL-graph overlap branch for1–16 token rows uses another coefficient path
and is outside this initial patch. Request concurrency does not establish exposure.

**Disposition:** deferred. The actual claim/propose/screen/eval-plan/decide flow
recorded nine exact source claims and null ROI. A retrospective source diagnostic
became ready for review after two links were narrowed to supporting the layout
mechanism; they do not support a speedup. The initial blocked plan is preserved.
The next useful design artifact is an explicit output-transport/store-ownership
and live-register plan, followed later by native differential/resource checks.

[Author report](round97/REPORT.md) · [Required correction](round97/REVIEW_ADDENDUM.md) ·
[Independent review](round97/INDEPENDENT_REVIEW.md) · [Actual tool flow](round97/TYPED_FLOW.md)

## 2. SN98: a different verifier law, with a progress penalty to overcome

The recent paper *Watermarkable Multi-Draft Speculative Sampling via Poisson
Processes* (`2609.21858v1`) contains a single-sample shared-noise component.
The proposed chain verifier samples the target at proposed prefixes with the
same position noise as the draft, commits matches, then commits the first target
correction or final bonus. Full target logits remain. This could replace native
normalization/ratio/residual work, while adding per-row target Gumbel sampling.
Its multi-draft tree, watermarking and top-k target truncation are excluded.

Independent review supports a sufficient position-tape argument under explicit
target-prefix and state assumptions. The finite CPU oracle matched192 cases
across64 tapes and three admission policies. Neither result proves native
PRNG behavior, processors, cache commits, batching or latency. The native code
also ties cache presence to probabilistic proposal mode and seed mixing; simply
deleting the draft cache or removing a salt would be wrong.

The critic found a concrete fallback hazard: after inspecting noise-dependent
invalid drafts or AV conditions, switching to fresh independent sampling can
reintroduce bias. Use same-tape target-only correction, or establish a separately
valid conditional law. A static supported-mode decision made before lookahead
is different. Round99's exact coin counterexample documents the hazard without
claiming that current DSpark is biased.

Shared-noise matching can lose acceptance. In one hypothetical one-proposal
example, expected progress falls from8/5 to53/35 tokens per round. Complete-round
time must fall by more than5.36% merely to break even there. **That is not a
five-token deployment forecast.** Compare against the strongest compatible
native baseline, including C025/FV86 where applicable, rather than adding their
savings to work this alternative removes.

**Disposition:** deferred research direction. The existing Mooncake/agent-p75
workloads remain the serving comparison. An additional scoped target-only oracle
differential is justified for the changed law and state lifecycle; serving
timing alone cannot certify them. No new load harness or assumed gain threshold.

The actual isolated production flow recorded13 exact claims, proposal, null-ROI
screen, retrospective finite-oracle evaluation plan and deferred decision.
Diagnostic readiness means ready for review, not permission to execute or a
passed native correctness gate. Its next useful task is the concrete
seed/position/row-map/fallback adapter table.

[Author report](round98/REPORT.md) · [Root review](round98/ROOT_REVIEW.md) ·
[Independent critic](round98/INDEPENDENT_REVIEW.md) ·
[Actual tool flow](round98/TYPED_FLOW.md) ·
[Position-tape argument and break-even](round98/POSITION_TAPE_ARGUMENT.md) ·
[Discarded-randomness counterexample](round99/REPORT.md)

## 3. New prefetch research: two useful rejections

Round100 adaptively changed its query from expert prefetch to producer/consumer
scheduling and read the October FlashMask-3 paper's forward component. Exact
target source already has independent activation and weight TMA producers plus
a dedicated scheduler with a two-stage metadata queue. Those two generic
additions are redundant. This does not declare current prefetch optimal; a
different reuse/stage/order policy must identify its own missing operation and
safe buffer lifecycle. No GPU diagnostic was needed to settle these premises.

[Report](round100/REPORT.md) · [Independent source review](round100/INDEPENDENT_REVIEW.md) ·
[All12 paper dispositions](round100/paper-dispositions.json)

## Yield, tool failures and retention

| Work | New provider calls / returned records | Outcome |
|---|---|---|
|97 prior lead deep read|0 paper searches;7 PR/code requests|One distinct layout component, corrected cost premise|
|98 exact sampling|2 paper searches /22 returned records;1 new fulltext|One alternative verifier direction; acceptance/fallback risks explicit|
|99 mathematical adversary|0 network calls|24 exact finite outcomes; method evidence, no new optimization|
|100 prefetch|2 paper searches /12 identities;1 new fulltext|Two proposed additions already implemented|

These are scoped discovery counts, not recall, success probabilities or measured
performance yield. Recent literature is preferred, while prior papers/PRs are
reused when they answer a specific unresolved component question. Follow-up
reading is now checking shared-noise implementations and weight reuse across
expert tasks rather than restarting broad keyword searches.

Two new formal identities were created in isolated production-tool flows:
SL97 `c9c3ae4e…e11a43` and SN98 `68e3668d…4df697`. Both are deferred with null ROI.
Their combined canonical retention is being prepared; their creation does not
mean canonical application or cloud publication has completed.

The SL97 author's frozen export retained code records that its mutable staging
database had not committed. The typed-flow recovery reconstructed the exact
export in isolated state and verified fingerprints/quotes before normal import;
the failed attempt remains. Round98's manually exported command history used a
snapshot mirror; an additive follow-up is preserving its active journal. Query
results and frozen sources remain available. These are recorded workflow
mistakes, not concealed successful persistence claims. Production tool/skill
code was not changed in this checkpoint.

Queued canonical retention has resumed through81,82/83 and84/85;86 was still
active at the latest observation. This is not a blanket S3-sync receipt. Selected
reports/controls are delivered in Git; full source and command packets retain
separate local/canonical/publication status. The null critic-guidance experiment
from Checkpoint35 remains a null result, with no production skill edit.

[Exact delivery hashes](source-copy-manifest-36.json) ·
[Null critic-test retention review](retention-36/CRITIC_NULL_REVIEW.md)
