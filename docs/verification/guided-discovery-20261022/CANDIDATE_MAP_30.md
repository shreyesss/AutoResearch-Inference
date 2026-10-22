# Current candidates: what is missing, and what would decide it

This is a navigation and experiment-selection aid, not a measured-gain leaderboard or a new selection event. All candidates below remain conditional/deferred; no GPU experiment or service improvement has been established in this discovery campaign. The common source discussion is Flash1017/c455 and its pinned dependencies on planned B200 TP1/DP4/EP4 groups. It is not a fresh live-node attestation. Historical identities/baselines, including PJ01's older baseline identity, remain unchanged.

## Narrow changes to inspect first when execution is authorized

Order reflects bounded implementation scope and ability to isolate the changed work, **not expected speedup**. An inactive backend/feature can immediately remove an item from this list for a particular deployment.

| Candidate | Source-supported missing operation | Strongest objection / cheapest decisive observation |
|---|---|---|
| PJ01: context-only KV projection | Native DSpark context calls compute Q1280+KV512, then discard Q. Two inspected FlashInfer backend wrappers can consume the current KV weight/scale views; no separate registered weight module is required. | Confirm actual prepared layout/backend and compare the smaller GEMM's KV results through norm/cache. Changed GEMM width can change tactic/rounding; logical MAC reduction is not saved ITL. [Details](round40/REPORT.md), [capture contract](round67/REPORT.md). |
| AV68: two overwritten metadata copies | Active AV with scheduled drafts replaces the general cumulative-logit reference and overwrites the full persistent query-start array before their consumers. | First establish effective AV activation. The source defaults/recipe do not attest the runtime. Check full-capacity padding and final InputBatch equality; then determine whether removed host submissions were exposed. [Details](round68/REPORT.md), [activation audit](round74/REPORT.md). |
| CR64: compressed-KV cache hint | Mega decode assigns FIRST to both per-layer SWA and shared compressed KV. The compressed role can independently test NORMAL/LAST without changing attention support or format. | Hints do not reserve L2; other useful data can lose residency. A warm source20 consumer sequence with intervening weights is the relevant comparison, not only an isolated cold-cache launch. [Details and controls](round64/REPORT.md). |
| ER73 / EM75: Engram hash work | ER73 replaces fixed-divisor remainder with exact prepared reciprocal arithmetic; EM75 can reuse the current invocation's request map instead of searching boundaries. | The compiler may already make remainder efficient; an extra map load can lose. ER73 belongs to NgramHashState. EM75 requires matching row/padding semantics and excludes unattested paths. Measure each and their interaction, not summed savings in the same kernel. [Remainder arithmetic](round73/REPORT.md), [request-map reuse](round75/REPORT.md). |
| HM65: static sampler metadata | Five sampling-state arrays can avoid unchanged publication while preserving per-step processor callbacks. | Requires complete writer invalidation and safe copy/lifetime handling while preserving existing exception/abort behavior; no new automatic recovery protocol is presumed. Long output does not prove clean-step frequency or exposed host time. Do not skip the whole sampler update. [Details](round65/REPORT.md). |

## Larger or semantically different experiments

| Candidate | Why retain it | Why it does not yet outrank the narrow options on evidence |
|---|---|---|
| CF59: overlap context preparation with sampling | Target feature combination and context projection/norm can be separated from sampling-dependent positions and KV insertion. | Preserve original early token release, padded row partitions, paired eager/graph modes and output/scratch ownership. The legal window and contention are unmeasured. [Round81](round81/REPORT.md) refines workspace reasoning; it does not supply a timeline. |
| PC76: scalar proposal-temperature calibration | Borrow the acceptance-overlap objective without neural retraining; change the draft distribution while preserving actual proposal probabilities in acceptance and residual correction. | No universal direction for temperature. Old/teacher-forced traces can rank policies incorrectly; the exact CPU counterexample demonstrates that possibility. Preserve support, AV comparator and real output/EOS accounting. No target-weight change is proposed. [Details and controls](round76/REPORT.md). |
| EC79: FP8 expert-return representation | A donor implements an independently selectable compressed return; its FP4 activation change is not required. Current return payload is BF16. | This changes target arithmetic and needs an explicit numerical/task contract. Keep the current scheduler/readiness protocol. Donor timings do not isolate this component; local/shared codec cost and actual remote exposure matter. [Round80](round80/REPORT.md) improves quality diagnostics, not benefit evidence; [EC79 mechanism](round79/REPORT.md). |
| RM61 / LP63: request ownership / prefill interference | Retain serving-policy alternatives whose benefit depends on actual request placement, progress and interference. | Integration, movement/queueing cost and workload operating region dominate. They cannot be promoted from aggregate token counts or a paper's fleet result. [Request ownership](round61/REPORT.md), [prefill interference](round63/REPORT.md). |

## Draft arithmetic and target arithmetic have different contracts

For PJ01, comparing retained KV outputs against the original projection is a diagnostic of the changed draft computation, not a universal demand for bit-identical draft activations. A different draft proposal can still preserve the target distribution if the engine consistently uses its actual proposal law and preserves acceptance/residual, support, RNG and lifetime semantics. Record confidence, adaptive verification and accepted-progress changes; do not attribute those effects solely to cheaper GEMM work. This distinction does **not** relax EC79, which changes target activations themselves.

## Interactions that prohibit adding percentages

- PJ01 and its round48 shared-input-quantization arm reduce context work; CF59 overlaps that work with sampling. C025 reduces sampling work. Changing either side can shrink the overlap available to CF59. Use the same strong comparator and measure the combined interval.
- ER73 and EM75 touch the same Engram hashing path. Removing arithmetic and replacing indexing can interact through memory/instruction scheduling.
- PC76 changes proposals and potentially acceptance/AV behavior. A fixed-context surrogate, higher accepted length or a nominal five-token block cannot supply its serving benefit denominator.
- EC79's local residual, complete token combine error, common-prefix logits and generated task outputs answer different questions. Standard Mooncake/agent75 load runs measure service benefit, but do not alone qualify altered target numerics.

## What the continued search is doing

The useful output is a better-supported decision, not one card per source. Round78 retained a selectively reusable rejected-state feature component but found no supported direct native trie/cache adapter. Round80 rejected direct reuse of a weight-allocation objective while sharpening EC79's quality experiment. Round82 rejected a direct dense-prefix port and retained exact support-preserving physical-owner grouping within AT02 after independent review. It did not create a new candidate.

No finite CPU test here proves native CUDA correctness, installed feature activation, exact stochastic decoding in the engine, or positive latency/throughput. Conversely, absence of current timing does not erase a concrete source-supported opportunity: it specifies the next informative comparison. Remaining unknowns must not be filled with donor percentages or self-assigned confidence scores.
