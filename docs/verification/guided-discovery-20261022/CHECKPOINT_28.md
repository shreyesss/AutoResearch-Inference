# Checkpoint 28 — selective calibration, request-map reuse and two falsifiers

The discovery loop remains active. Three further investigations produced two deferred interventions and one screened-out transfer. **No GPU experiment, native decoder execution, implementation qualification or serving gain is claimed.** All target conclusions refer to pinned source and the planned baseline, not a newly attested deployment.

## PC76: borrow the fitting objective, preserve the actual sampler

A September paper, *Acceptance-Aware Draft Model Training*, supplies an acceptance-overlap objective. Its neural training and reported gains are not required ingredients for a separate experiment fitting one positive draft-temperature scalar with frozen weights. An open SGLang PR, #43052 at `d618466…`, independently supplies a concrete draft/target-temperature separation to inspect. Its body says validation is pending; it is not performance evidence.

The proposed intervention fits **draft temperature only**, retaining target sampling, effective support and the existing scheduler. Compare with the unchanged T=1 arm. The paper's objective motivates the experiment; it does not establish a good scalar or target throughput.

The pinned vLLM implementation makes this substantially more than a sampling flag:

- Cached draft logits are pre-temperature. Scale the actual parent-conditioned proposal consistently through normalizers, chosen-token probabilities, block residual calculations and resampling.
- Target temperature also selects greedy behavior; globally replacing its pointer would change unrelated semantics.
- If drafting is actually argmax, a positive scalar does nothing. Target temperature 1 does not prove probabilistic drafting is enabled.
- Existing top-k/reduced-vocabulary and confidence/AV paths must be admitted explicitly. Turning on probabilistic drafting, changing support, or disabling AV are separate interventions.
- Changed parents can change confidence and selected verification budgets. Five is the maximum draft depth, not proof that every round verifies five tokens.

**Decision: deferred for an exact probability-contract implementation and an on-policy progress study when execution is authorized.** Neither a scalar fitted to old traces nor greater accepted length qualifies service performance. Preserve the benchmark's EOS/length policy, actual completed outputs and tail guards. [Detailed design](round76/REPORT.md), [independent review](round76/INDEPENDENT_REVIEW.md), [output-policy clarification](round76/OUTPUT_POLICY_ADDENDUM.md).

### Two CPU controls prevent false qualification

1. **Output-law control:** exact single-token rejection arithmetic recovers the target distribution when proposal sampling, acceptance and residual recovery agree. Changing the proposal but retaining the old residual can still bias outputs after acceptance is repaired. [Control and limitations](round76/PROBABILITY_CONTROL.md).
2. **Progress-surrogate control:** in an exact two-token example with one true T=1→2 scalar change, a teacher-forced overlap-window score rises **1.70860→1.73660**, while expected actually accepted draft tokens fall **1.77216→1.73593**. Reaching an accepted parent is weighted by `min(p,q)`, not by the unconditioned target-prefix distribution. Exact path enumeration and an independent arithmetic review agree. [Derivation and runnable control](round76/SURROGATE_CONTROL.md), [review](round76/SURROGATE_INDEPENDENT_REVIEW.md).

These deliberately constructed controls show invalid inferences. They are not native DSpark block-verifier tests, a rejection of PC76, or an estimate of how often calibration helps. Request-disjoint validation prevents leakage but does not repair a structurally wrong progress estimator. Native verifier semantics and actual states remain necessary.

## EM75: reuse an existing request map inside Engram hashing

The attention metadata builder already produces a token-to-request map after AV redistribution. The Engram hash kernel separately searches query boundaries to recover that mapping. Reusing the existing map could remove that search inside the existing hash invocation.

The tempting direct replacement is incorrect on padded tokens: the metadata map can return row 0 where the original hash selects the last request row. The proposed bounded adapter uses the existing map only within its covered live-token extent and preserves the original final-boundary rule. It must preserve request-slot interpretation, chunk/history/position semantics, masked loads, dtype/stride and current-invocation ownership. Unknown or incompatible map extents fall back to the original search. `expanded_idx_mapping` is a different mapping and cannot be substituted.

**Decision: retain as a separately tracked deferred intervention.** The search is short at small batch sizes, and added map loads may erase its benefit. It removes no hash launch or embedding lookup. ER73 changes arithmetic in the same kernel, so their savings cannot be added without a controlled comparison. [Source argument, falsifier and experiment](round75/REPORT.md), [independent review](round75/INDEPENDENT_REVIEW.md).

## Round77: a relevant paper does not imply a missing optimization

The September *Taming Dynamism on GPUs* paper retains row partitions on chip during cross-SM reduction. Full text and released code changed the initial assessment:

- The inspected release's ordinary RMSNorm example is not its cross-SM algorithm and lacks the target's numerical/interface contract.
- Pinned Q1280/KV512 normalization already retains its input through reduction; the eligible Q quantization path also preserves the required rounding boundary.
- The inspected mHC collapse path already keeps its intermediate in shared memory. Its coefficient/statistics calculation is distinct from normalization, and BF16 rounding differs by branch.

Direct substitution is rejected; the broader cross-SM component remains low-priority conditional research. A preceding GEMM→norm buffer still exists, but this paper does not supply a compatible target epilogue. **Zero new hypothesis identities from this round.** [Report](round77/REPORT.md), [review](round77/INDEPENDENT_REVIEW.md).

## Yield and system change

Rounds75–77 added three successful dated provider queries, 28 returned records and 26 identities after matching declared arXiv URLs. This is not independent DOI/title entity resolution. Two selected papers were read in full; round75 used source inspection without an online query. Two interventions were proposed, both deferred; the original author packets created no formal memory cards. Typed retention is being prepared separately. There are zero implementation/service promotions. [Receipts and counts](yield-7577/counts.json).

The synthesis skill now explains the limited transfer from a training objective to inference-only calibration, proposal/residual consistency, policy-dependent state coverage and output accounting. Its frontmatter validator passed in an isolated Python environment; the repository Python lacked PyYAML. Independent source/scope/link review found no blocker. **This is a documented skill correction, not measured improvement in agent quality.** [Review](skill-calibration/INDEPENDENT_REVIEW.md), [validation](skill-calibration/validation.json).

## Retention and continuation

The isolated73–75 retention packet passed root checks of 177 artifact references, 81 source revisions, the full ER73 deferred state and a relocated restore. It remains queued behind the existing single canonical writer. EM75 and PC76 are being prepared as separate deferred tracking cards; this checkpoint does not claim those imports or their S3 publication are complete. [Retention audit](retention-28/REVIEW.md).

At07:20 UTC, local receipts still showed 951 successful GitHub pages, last completed batch06:54 UTC, last published research lineage `b57a565…752` at06:49 UTC, and newer local snapshot `1dd2460…966f`. No fresh remote/VM verification was performed. [Observation](retention-28/publication-observation.json), [delivery hashes](source-copy-manifest-28.json).

The next paper follow-up concerns reusing rejected speculative work. Its DSpark/Qwen results do not establish transfer to our block verifier: proposal conditioning, tree-attention requirements and rejected-cache ownership are being reviewed separately. Broader non-speculative discovery continues alongside it.
