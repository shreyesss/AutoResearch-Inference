# Checkpoint14 — reviewed interfaces, conditional graph gains, rejected shortcuts

**CPU/source-only discovery continues. No GPU experiment, serving change or measured inference improvement.** This checkpoint records actual review effects and distinguishes useful implementation leads from qualified service gains.

## Current technical priorities

| Lead | What became more concrete | What still prevents qualification |
|---|---|---|
| **PJ01: remove discarded draft-context Q columns** | The two pinned FlashInfer Python backends accept current KV-only weight/scale views through their existing kernel object; a second registered module is unnecessary | Actual prepared tensors, numerical behavior, graph/refit lifetime and exposed projection time |
| **WP38: paired FP4 weight packets** | Target geometry fits; the donor packing component has an explicit loader/EPLB ownership design problem to resolve | Correct ownership adapter and mapped native execution; donor's bundled gain is not a target forecast |
| **OP36: quantized projection handoff** | The removable BF16 round trip and compatible-output primitive are identified | Quantization policy and scale/layout ABI differ; needs the planned aligned three-arm comparison |
| **Graph-size configuration lead** | Exact extracted dispatch methods show smaller descriptors at concrete K5 shapes; independent review found the adaptive branch changes more cases than the original uniform fixture | Actual graph settings, common DP-selected shapes, frequency, memory cost and exposed duration |

This is an investigation ordering, not a ranking by invented percentage gains. The graph lead extends the existing graph-coverage work without adding another hypothesis identity. PJ01's immutable original baseline remains unchanged; c455 applicability evidence does not silently rebaseline it.

### PJ01: genuine simplification, bounded proof

[Round40](round40/REPORT.md) executes the unchanged Python backend bodies with metadata/native-call stubs. Twelve wrapper cases and six context-control cases show the intended512-column call, retained quantizer/norm/cache-control path and current-owner views. Six negative eligibility controls use the original call. [Independent review](round40/INDEPENDENT_REVIEW.md) reproduced the observations and notes that a smaller GEMM can still choose different native workspace/tactics. No numerical tensors, actual graph or device execution was tested. PJ01 stays deferred.

### Graph padding: the critic changed the conclusion

[Round41](round41/REPORT.md) combined recent online paper search, retained CoRun/Herschel fulltexts, dated local PR searches, PR62173's actual diff and pinned target source. The first uniform fixture changed only five-request selection. [Independent review](round41/INDEPENDENT_REVIEW.md) followed the adaptive runner call site and tested the varlen branch: constructed request counts3,5,6,7 select smaller token capacities. Neither probe establishes those shapes occur after DP synchronization on the deployment.

The Gemma padding PR's central unrouting mechanism is already conditionally present in our MegaMoE preparation. That result therefore cannot be presented as an absent feature or borrowed ROI. Existing Mooncake and agent75 workloads remain suitable for a later service comparison; graph/shape telemetry is a mechanism measurement, not a replacement benchmark.

[Further source review](round41/COST_MODEL_ADDENDUM.md) shows captured sizes also feed adaptive verification's startup cost curves and budget selection. Keep the policy/profiling procedure fixed, rebuild valid curves for each graph configuration, and report admitted budgets and committed progress. A service result can combine direct padding effects and scheduling feedback; isolate them only with a separately labelled diagnostic.

### Sampling: two plausible transfers stopped before implementation

[Round39](round39/REPORT.md) retained a useful fused LM-head statistics component, but the actual donor's FP32-accumulator sampling is not automatically equivalent to the target's BF16 boundary. Block verification still requires draft statistics and residual work. Target head geometry and dtype also differ. The component is parked, with no new card.

[Round42](round42/REPORT.md) examined a narrower residual-scan shortcut at saturated acceptance ratio. A stdlib float32 counterexample and [independent exact-rational check](round42/INDEPENDENT_REVIEW.md) invalidate the unconditional source-algebra equivalence argument. Actual Triton lowering, achievable residuals and RNG trajectories remain unverified; this is neither a demonstrated target bug nor proof that every possible guarded shortcut is impossible. No new card was generated from unresolved algebra.

[Source-locator correction](corrections/round39-42-locators/ADDENDUM.md): the retained c455 target files belong to `callgideon/vllm`; earlier round39/42 URLs used the upstream namespace. The exact bytes remain unchanged, and the correction preserves the original records.

## Tool and skill changes

Commit `d3e94fd2ed39712b232f4fabc2c82956ee6fda7a` is verified on Git main. Explicit pinned-code/repository investigation now works without a paper seed. Failed/blank-only reads cannot enter model reasoning or typed hypothesis retention. Existing cache and HTTP budgets remain in force. [Before/after real CLI receipts and independent review](code-only-investigate/INDEPENDENT_REVIEW.md) document the repair; the retained-cache replay returns one pinned source with zero HTTP budget/misses.

The full research suite passed **319 tests plus29 subtests**, bootstrap dry-run and diffcheck passed. Independent review additionally ran52 tests plus15 subtests and eight CLI controls. These overlap the full suite and must not be summed as independent coverage. They test infrastructure behavior, not hypothesis quality or serving performance.

The critic skill gained a narrow instruction to trace mode selection and distributed agreement before generalizing a shape fixture. The observed review motivated this change; syntax validation passed using the existing isolated validator environment after the repository environment lacked PyYAML. There is no claim that a new blind trial proved improved skill quality. No dependency or GPU package was installed for it.

## Yield and durable state at this checkpoint

- Canonical memory contains141 total historical hypotheses. Within this guided campaign, **37 cards are retained:2 accepted bounded CPU investigations,27 deferred,7 rejected,1 duplicate**. Accepted CPU work is not implementation permission or a service qualification.
- NQ33 and OP36 were canonically retained with their evidence and diagnostic plans. WP38 remains pending: its reviewed import is waiting for the background publisher's writer lock. Including WP38 gives38 reviewed cards/28 deferred, but that is explicitly not the canonical count yet.
- Rounds39–42 create **zero new cards and zero service qualifications**. Round40 refines PJ01; round41 preserves a concrete configuration lead; rounds39/42 preserve scoped non-transfer results. No idea quota is used.
- Current reviewed retention packets for39 and40/42 passed isolated default-snapshot/relocation checks. They are not claimed applied canonically or published to S3 at this checkpoint.

The earlier3334/353637 merge wrapper had a latent revision-metadata encoding defect. Independent and root audits show the actual completed packets added no malformed revisions: the older-source branch inserted no new malformed row in3334 and was not exercised in353637. The future v3 path uses Store encoding and retains source-derived edge invariants. Original v2 receipts remain historical; they are not relabelled as v3 executions.

One operational-history failure is disclosed explicitly: retention39 development reused validation filenames. Six exact older files were recovered; four previous operational receipt/script-note versions are unavailable. [The limitation](round39/SUPERSEDED_RECEIPTS.json) does not change the original frozen science/packet or current independently verified v5 result. Do not claim complete immutable history for those superseded operational receipts. Future versions use separate final directories.

S3 publication `5069c38cb001bfc79baf25dd6f9c2cb82fa090fd149a98e2427b32f8ccdaff74` now has a successful background-publisher receipt. Its local manifest covers all463 earlier retained artifact references checked by root. This is publisher/local-manifest verification, not a new remote GET or VM restore. The new NQ33/OP36 imports and pending packets are not represented as covered by that publication.

GitHub opening-record backfill remains active and incomplete for vLLM and SGLang; the last completed batch before the present publication wait reached863 successful pages. This does not include full comments, reviews or diffs. No completion ETA is inferred while publication holds the writer lock.

The next discovery direction is recent work on exact expert-intermediate sparsity, distinguishing useful software components from trained/pruned-model or custom-hardware requirements. All existing no-GPU restrictions remain in effect.
