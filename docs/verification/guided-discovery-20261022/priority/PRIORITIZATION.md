# Adversarial review of accepted investigation priority

No memory transition, frozen packet edit, GPU action, runtime probing or new package test. This is a prioritization proposal for root review, not a new selection decision.

## What accepted currently means

Read-only latest-review inventory contains four accepted identities. Two belong to the current guided run: S01 and M01. Historical R1 (`7edff722...896d7`) and TreeSpark transfer diagnostic (`766121e3...94bfc`) were accepted for experiment design only under distinct baselines. Counting all four as implementation-ready would be incorrect. Preserve their original records; expose investigation phase and implementation/service readiness alongside selection status.

## S01: finish the version bridge, then park unless exposure changes

Identity: `hypothesis:a5d530ce5da737fb780bdd0aed42e9126ba955b1375307b0fe3592bbf63ad4ed`.
Baseline: `baseline:3b223afd8c30209a2c71d6f8cdd36e4da640b4bc67cdf331f108d2d2496131ca`.

The historical acceptance was reasonable for a bounded exact-tokenizer feasibility question. Much of that investigation is now complete: native CPU suffix encoding in Python repair, actual whole-input alternative, default lower-bound loader semantics, runtime-option counterexample, and conditional local CPU timing. These findings made the idea more concrete but did not supply the missing link to the frozen long-output ITL objective.

Input tokenization ordinarily occurs before generation. Reducing that work has a direct potential TTFT effect; a long-output ITL effect requires shared CPU contention, delayed streaming/scheduling, or another demonstrated coupling. The direct coupling has not been established here. Repeated GPU KV prefixes do not establish reusable tokenizer sessions. The stateless segmentation refinement removes the session prerequisite but still requires actual input-path exposure and whole-input benefit. Local short marker-heavy regressions also rule out an unconditional fast route.

**Recommended queue state:** preserve the historical accepted-for-CPU selection; describe the completed compatibility phase as complete, implementation as deferred/low-priority, service as unqualified. Round27's already-started version bridge is a finite remaining compatibility check. Its pass closes a specified mismatch; it must not automatically trigger more fixtures, serving integration or another native tuning study. Its failure should stop the affected adapter and record the minimal mismatch, not expand scope into a new tokenizer project.

**One bounded next evidence check after27:** inspect existing saved launch/request/host artifacts only for the actual tokenizer version/options, ordinary text route, renderer markers, and whether frontend encoding shares a saturated resource with token streaming. For prefix repair, additionally require actual previous-rendered-text/session continuity; for stateless segmentation do not impose that irrelevant prerequisite. Limit to the already-named artifacts. If those artifacts do not establish exposure or contention, park this branch without generating more random inputs or synthetic timing sweeps.

**Stop conditions:** no exact live loader identity; token-ID/offset contract mismatch for the intended API; processing is off the ITL dependency path with no evidence of contention; no retained evidence to estimate even exposure; or realistic whole-input mixture dominated by regressions. Absence of timing is a reason to stop further CPU optimization effort for now, not proof the optimization can never help.

**Reopen conditions:** retained production/benchmark CPU traces or logs identify tokenization/renderer work delaying the relevant service metric; or the task explicitly changes to TTFT/frontend goodput; and the proposed adapter covers the actual input/options and improves a representative CPU workload. Later service comparison must preserve the frozen workload and long-output ITL/tail guards. No arbitrary accepted quota or paper novelty threshold applies.

## M01: more direct decode mechanism, but source feasibility work is mostly done

Identity: `hypothesis:7deeaba77bd1290ce3850134faa175d3b7b38a877efb126357a4feab8364baf0`.
Baseline: the same `3b223afd...131ca` planned Flash1017/c455 profile.

M01 targets decode MoE work and therefore has a more direct path to ITL than input-tokenizer work. That does not establish benefit. The completed parameter-flow audit already found shared buffer capacity over legal tiles, getter/kernel shared-scale coupling and limits on candidate configurations. Repeating those arithmetic checks or inventing more routing histograms would not decide whether a profitable target tactic exists.

The smallest remaining nonGPU check is **artifact eligibility, not another tactic simulator**: inspect an already-retained per-layer/per-rank physical receive-count artifact and its pin/shape/EPLB provenance. The current `capture_fn(topk_ids)` occurs before EPLB physical remap; it cannot simply be relabeled physical receive data. DeepGEMM has an optional cumulative receive counter, but cumulative totals alone do not reconstruct per-step within-bucket variation. No instrumentation should be enabled under this CPU-only review.

If a valid artifact exists, check whether equal captured token buckets actually contain materially different physical distributions, using complete request/rank/padding metadata. Evaluate only currently legal layout-compatible candidates and report padding/tile proxies as proxies. The source audit found global capacity entries8/96 are not automatically legal ordinary MXFP8FP4 tactics. A proxy ordering is not a latency ordering and cannot choose a faster tactic without calibrated component timings.

If no such retained artifact exists, mark the source/CPU feasibility investigation complete and park implementation/quantitative ROI until evidence or GPU authorization changes. If distributions do not change a plausible tactic tradeoff, stop the adaptive extension and keep the existing heuristic/best fixed comparator. If a static per-layer/bucket table suffices, prefer that; per-round dynamic selection is not inherently required and its overhead must be charged.

Reopen only with attested loaded dependency/quantization/graph path and physical distribution evidence, followed later by matched complete-MoE and service measurements against the best fixed tactic. Historical R1 backend switching and M01 within-backend tile choice should remain explicitly linked, not counted as two independently qualified improvements.

## Practical ordering now

1. Finish the finite already-started27 bridge as a closure artifact; no further S01 fixture expansion without exposure evidence.
2. One bounded existing-artifact inventory for M01 physical receive data. If absent, park rather than fabricate a surrogate workload.
3. Spend subsequent discovery effort on candidates with a specific absent component and a demonstrable path to the frozen metric. Acceptance history is retained; active work priority follows current evidence.

There is no recommended implementation promotion among these items from this audit. No global scientific rejection or canonical status rewrite is requested.
