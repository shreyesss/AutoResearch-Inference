# Checkpoint 25 — selective PR reuse and a corrected falsifier

The guided CPU-only discovery loop continues. No GPU, native model, CUDA build, serving modification or inference performance test ran in these rounds. The findings below are decisions about future experiments, not measured improvements.

## One small new candidate: unchanged sampling metadata

HM65 adapts only one component of vLLM#62748: avoid refreshing five SamplingStates arrays on steps with no changes. The exact pinned target currently publishes temperature, top-p, top-k, min-p and effective seeds on every flush. Keep every outer sampler/processor callback running; the donor's broader admission-only sampler gate changes that contract.

On the UVA path these are CPU-to-CPU copies into mapped pinned storage, totaling `24 * max_num_reqs` logical bytes per refresh. They are not five DMA launches. The relevant unknown is exposed host time and the fraction of steps without admissions. Neither the donor's different-model timing nor the byte count supports a target ITL percentage.

| Question | Current evidence | Next decisive check |
|---|---|---|
| Are these values static between admissions? | Exact constructor/admission writer audit; no other direct writer found in the inspected tree | Confirm all actual writers/plugins and invalidate on admission/reused slots |
| Can we preserve callbacks? | Put the gate inside SamplingStates; leave outer callbacks unchanged | Native callback, seed and slot-reuse differential checks |
| Can the existing published slot be reused? | Immutable contents make clean reuse plausible under the existing reader-retirement contract | Actual queue depth and graph pointer binding |
| Does retry remain safe after a partial copy? | A two-slot counterexample shows immediate retry can overwrite an outstanding reader | Preserve existing exception/abort behavior; add recovery only as a separately justified change |
| Does less copying improve our objective? | Unknown | Measure clean-step frequency and exposed cost, then paired agent-p75/Mooncake with long-output ITL and tail guards |

Independent review retains the narrow arm for a bounded future experiment. The author packet remains deferred; no typed canonical creation is claimed here. The two separately parked AV copy eliminations and donor buffer-pool changes are not included in its gain. [Full mechanism and controls](round65/REPORT.md), [independent review](round65/INDEPENDENT_REVIEW.md).

## Recent-paper synthesis: preserve the consumer's required information

Round66 read the recent Pruned CTC paper's selected-class/normalization component. Its surrounding training system does not prevent examining that separable component. However, our native DSpark verifier needs per-token positive residuals and correction-token support. Selected target probabilities plus one aggregate complement are insufficient for that consumer.

**The first proposed counterexample was mis-scoped.** It varied draft probabilities while claiming to refute target-only compression with the full draft vector retained. Root caught this; the author preserved the original and supplied a matched-input correction. Fix full draft probabilities `[.4,.3,.3]`, cumulative factor `.8`, selected target probability `.4` and target complement mass `.6`. Changing only omitted target probabilities yields different residual support and masses `.1`, `.1`, `.06`. The same retained inputs therefore cannot determine the required result.

Root reran the exact-rational fixture and an independent reviewer recomputed it. This is a mathematical falsifier, not native floating-point execution or an observed model trace. Richer streamed residual/sampling designs and recomputation remain possible. The existing LS39 component is not renamed into a new hypothesis. [Correction](round66/TARGET_SUMMARY_CORRECTION.md), [review](round66/INDEPENDENT_REVIEW.md), [original preserved report](round66/ORIGINAL_REPORT.md).

The critic skill now explicitly requires holding every retained input fixed in this kind of argument and naming the exact representation refuted. Skill validation and independent instruction review passed. This is a repair prompted by an observed reasoning error, not a demonstrated increase in research quality or a new runtime validator. [Lesson](matched-counterexamples/REPORT.md).

## PJ01: use existing warmup and capture

Round67 revisits the existing KV-columns-only DSpark context projection. Source inspection finds that the DFlash graph manager's existing callback runs context preparation both during warmup and graph capture. The initial adapter should be enabled consistently before that lifecycle; a separate warmup framework is not justified.

PAD slot mappings and None/profiling inputs must retain their existing projection/norm behavior. Fresh Python views do not repair addresses already captured in a graph; owner/layout replacement requires the existing invalidation/recapture lifecycle. Eight static AST observations support these source-control statements. No tensor operation, backend allocation, graph or numerical check was executed. External FlashInfer allocation, processed runtime tensors and numerical equivalence remain open. This refines the same PJ01 handoff without changing its scientific priority or qualification. [Minimal handoff](round67/REPORT.md), [independent review](round67/INDEPENDENT_REVIEW.md).

## Yield and tool usefulness

Rounds 65/66 made two dated online paper queries, returned 18 paper records and selected one fulltext. This is a sum of returned records, not a cross-provider distinct-paper denominator. Round65's useful implementation evidence came from the exact PR diff and three pinned donor files. One new deferred author direction resulted; zero implementations or service improvements were qualified. Round67 used existing source because another paper would not settle the capture question.

Round66 also exposed a process error: prior hypothesis recall ran, but standalone report search happened after the first online query. The reports were already indexed. The search tool worked when used; this is not evidence that ranking was broken or needed a new implementation. Selected-import replay distinguished isolated-state coverage from canonical coverage.

The active follow-ups inspect the separate AV overwritten-copy arm and recent-paper mechanisms outside the established projection/layout work. No acceptance quota is imposed.

## Retention status

At the saved 06:23:35 UTC observation, the GitHub backfill job recorded 937 successful pages and a last completed batch at 06:10:58 UTC with no batch errors. Its local snapshot was `b57a565991adf4b30ebef05e660799bba01b25b8868f529405aa59191f842752`; the last completed published lineage remained `f82df0e3c9dc0b01534b03f6915f2b1f1e000e888e1ee4de0b4d0b2d63da356d`. Local snapshot and successful S3 publication are separate facts. The 65/66 isolated retention rehearsal preserved 151 artifact references and 77 source revisions through default snapshot/restore; root verified the exact deferred HM65 card and state. The round66 findings remain report/source-only because no typed LS39 identity was found. This is an isolated durability check, not canonical completion. [Readback](retention-25/isolated-6566-checks.json). The queued canonical retention sequence remains subject to the normal writer lock. This checkpoint does not claim cloud or VM coverage of the new packets. [Observation](retention-25/publication-observation.json), [delivery hashes](source-copy-manifest-25.json).
