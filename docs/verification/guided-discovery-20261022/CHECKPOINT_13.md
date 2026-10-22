# Checkpoint13 — two concrete candidates, rejected transfers, reusable evidence

The active loop remains CPU/source-only. **No GPU experiment, serving change or measured performance win.** Newly reviewed candidates are deferred while their integration and exposure questions remain open.

## What is worth investigating

| Candidate | Concrete target delta | Strongest objection | Next useful work |
|---|---|---|---|
| **WP38: paired FP4 weight packets** | Keep cooperating CTA weights/scales adjacent; port the actual DeepGEMM394 packet/TMA component | Target loader already transforms weights; donor flattened views fail EPLB ownership, and small-row result bundles three changes | Bounded packing/ownership adapter, followed later by correct mapped-kernel and matched service comparisons |
| **OP36: output-projection handoff** | Emit packed FP8 from grouped WO-A directly into compatible WO-B | Scale floors and activation/weight layouts differ; advertised PR integration is absent from its inspected diff | Establish exact numerical policy and compatible loader, then align three-arm comparison |

Read [WP38 mechanism and four-arm design](round38/REPORT.md), its [independent review](round38/INDEPENDENT_REVIEW.md), [OP36 mechanism and three-arm design](round36/REPORT.md), and its [independent review](round36/INDEPENDENT_REVIEW.md).

WP38 is the more concrete new integration lead: static H5120/I2304 geometry fits, and intended values/routing remain unchanged. This is investigation priority, not a serving-gain ranking. The donor's9.51% component result is not our forecast. Keep PJ01's existing source/exposure work active; no additive ROI arithmetic across these candidates.

## What did not survive transfer

[Round37](round37/REPORT.md) produced no new card. SPIN skips potentially relevant blocks under an approximation/quality contract; AVSG removes host-to-device transfers absent from the resident Mega reader; the inline528B KV format is already present. Useful subcomponents and explicit reopening conditions are retained. These source checks did not run target experiments or invalidate the papers' own reported settings.

Round38's persistent-execution query rediscovered MonoMoE and MegaFlux. Their downloaded texts match round19 byte-for-byte, so they are **revisited sources**, not new discoveries. Pinned MegaMoE already performs SwapAB. The new packet proposal came from a subsequent concrete PR/source inspection.

An earlier MonoMoE note incorrectly described its DeepSeek TP8 results as spanning a regression. [Append-only correction](corrections/round19-monomoe/ADDENDUM.md): all four reported TP8 points improve; EP collective-fusion parity is a separate comparison. Original artifacts and hypothesis decisions are preserved, with the false negative explicitly corrected.

## Actual tool improvement

Commit `d017759` adds `import-corpus --source-id ID` and MCP `import_sources` to reuse selected retained SQLite documents, their revisions and incident provenance edges. They preserve newer destination records and exclude unrelated collection cursors. Missing IDs fail before corpus writes. Selection for JSONL is explicitly unsupported; whole-file import behavior remains available.

[Real isolated replay](source-reuse/replay-receipt.json) reused two fulltexts/four revisions without creating an HTTP cache or calling the instrumented socket connection function. This preserves old evidence; it does **not** claim current arXiv freshness. `investigate` retrieval behavior is unchanged. The workflow is lookup → selected import → exact retained revision read, with a deliberate refresh only when needed.

[Independent review](source-reuse/INDEPENDENT_REVIEW.md) found an obsolete-link resurrection case involving an unselected evidence document. The fix and regression check preserve the newer document's current derived links. **311 tests +25 subtests passed**, bootstrap dry-run, skill validation and diffcheck passed. Reviewer also ran six focused tests. These gates test research infrastructure, not inference kernels.

## Yield and durability boundary

At this checkpoint, canonical guided memory still contains **35 reviewed cards:2 accepted bounded CPU investigations,25 deferred,7 rejected,1 duplicate**. Existing accepted investigations remain parked where the next useful step needs missing exposure. Three new independently reviewed cards—NQ33, OP36, WP38—remain pending canonical retention. Including those pending cards gives38 reviewed/28 deferred; **zero implementation/service qualifications**.

The typed claim→proposal→screen→evaluation-plan→decision pipeline ran in isolated state for NQ33 and OP36, with unknown gain and execution permission kept false. WP38's typed retention is being prepared. A review-ready CPU diagnostic plan is not implementation approval. Source-formula and geometry checks are retrospectively labelled and inconclusive for target performance.

[Bounded S3 inventory](round35/REPORT.md) recovered no exact-baseline projection trace. Remote published manifest `743ef260…` matched the local manifest; this verifies a manifest, not a restored running deployment. The sampled external manifest used a different tokenizer/model alias. Untouched prefixes and incomplete pages remain explicit.

The background publisher holds the canonical writer lock. Its last verified published lineage remains `743ef260ed43b945f9b0680d6e36dbd09f41cdbc2f3634910c78c5088d9f2628`; a newer local snapshot `5069c38c…` is not yet claimed remotely published. Root cancelled the waiting NQ33 import before mutation after finding the same derived-edge issue in the manual retention wrapper. Revised wrappers are being verified before retry. Earlier463 artifact references were verified locally; pending bundles are not represented as uploaded or restored on a VM.

The loop continues with exact logits/sampling-boundary research and reviewed persistence. No candidate is promoted to meet a yield quota.
