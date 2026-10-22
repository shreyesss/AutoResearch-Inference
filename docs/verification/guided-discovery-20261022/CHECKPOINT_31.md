# Checkpoint31 — fix the baseline, then test the evaluator's assumptions

The CPU-only discovery loop remains active. The [candidate map](CANDIDATE_MAP_30.md) still describes conditional opportunities, not measured wins. This batch adds two useful refinements and rejects an already-present optimization premise. No GPU/model execution, serving change or target performance result occurred.

## 1. Cache precision: resolve the backend before proposing a format change

The recent QuantMLA fulltext prompted a source audit. In pinned c455, generic `fp8` follows the selected attention backend's preferred packed format. Eligible Mega selects **528-byte FP8 SWA rows plus288-byte NVFP4 compressed rows**. Explicit `fp8_ds_mla` selects a different branch. The generic CLI label alone does not establish all-FP8 storage, and no fresh running configuration was inspected.

An additive correction identifies affected passages in rounds13/37/47/61/82. Hypothetical528-byte arithmetic stays conditional; source-supported sparse-reader and migration objections survive. Frozen reports and baseline identities remain unchanged. The next missing fact is a resolved backend/dtype/slot-size receipt, not another quantization search. [Report](round83/REPORT.md), [scope correction](round83/BASELINE_SCOPE_ADDENDUM.md), [independent review](round83/INDEPENDENT_REVIEW.md).

QuantMLA also supplies a useful quality-check lesson: its positional-error bound fixes values, while our reader uses shared K=V. An exact scalar counterexample preserves QK score while changing value output. This limits the theorem's transfer; it does not refute the paper or demonstrate target quantization error. Native reconstruction, output and task quality remain separate checks.

## 2. Recent metadata-prefetch PR: a real change, already covered in this target

Date-qualified local scouts inspected126 unique PR titles/131 appearances, with explicit per-repository caps and created/updated fields. Only FlashInfer6951 received a complete selected head/base kernel comparison. Its donor moves dependent K-scale loads from softmax to producer warps. The pinned target already stages physical indices/scales and reconstructs rows before attention consumption. We found no missing operation that justifies another generic prefetch hypothesis.

This conclusion is scoped to the selected source path. The separate CTA0 scale-copy branch is conditional on `IS_2CTA`; assigned roles do not prove the pipeline has no stalls. The FlashMLA PR scout queried **deepseek-ai/FlashMLA**, whereas the target kernel belongs to **vllm-project/FlashMLA**. A mistaken source locator was corrected additively, preserving the real scout scope and exact original packet. Neither fork coverage nor current upstream completeness is claimed. [Report](round84/REPORT.md), [locator correction](round84/SOURCE_LOCATOR_CORRECTION.md), [independent review](round84/INDEPENDENT_REVIEW.md).

## 3. A training paper contributes an inference-only evaluation method

A recent Markov/parallel-sampling query found an [EDR paper](https://arxiv.org/html/2610.10411v1) with an offline round-count evaluator. Its useful component accounts for which draft-block starting positions are reached; the neural training procedure is unnecessary for that component. It refines the existing PC76 calibration evaluation rather than creating another optimization identity.

The independent rational control matched ordinary-rejection event enumeration in36 cases/270 output-sequence comparisons. Using the wrong conditional probability ratio failed all36. A separate reviewer integrated a two-token example and obtained expected accepted drafts23/20 under the source block equations versus28/25 under ordinary rejection. These finite CPU controls establish different mathematical contracts, not native correctness or model acceptance.

The published estimator assumes ordinary fixed-B rejection. Native block rejection and AV require their own transition/policy model; target-distribution preservation alone does not make round boundaries identical. It also needs actual target trajectories and normalized draft probabilities at all evaluated anchors. “Offline” describes the calculation once inputs exist, not free acquisition of missing model outputs. The donor's `eval_accept_rate.py` is a server-load script and was deliberately not executed. [Detailed method and next checks](round85/REPORT.md), [independent source preflight](review/round85-preflight/REVIEW.md), [exact control](round85/occupancy_control.py).

Final review independently replayed the exact control and clarified a donor API trap: its cost-based `expected_passes` is not automatically the per-trajectory occupancy sum. A future adapter must deliberately select the intended estimator. [Final independent review](round85/INDEPENDENT_REVIEW.md).

## Yield, tooling and next search

Rounds83–85: **one new paper query,12 returned paper identities, two selected fulltext papers, one newly hydrated PR optimization, zero new optimization identities and zero implementation promotions**. QuantMLA was a retained unread lead; its unversioned and explicit-v2 fetches are not two papers. PR title coverage is not full source review. The useful outputs are a corrected baseline premise and a better-scoped evaluation component. [Counts](yield-8385/counts.json).

No new tool interface or orchestration was justified. Existing explicit source imports, online search, pinned-file investigation, date-qualified PR search and recorded expansion supported the decisions. The canonical read command waited behind the writer; it was interrupted and replaced with WAL-aware readonly access, without unlocking or altering canonical state. Query and locator mistakes remain visible in receipts.

The next active source question is narrower: can testing the final accepted draft prefix first safely avoid interior residual scans in native block verification? This came from the newly relevant PR vocabulary. It must survive placeholder/AV, RNG, store/lifetime and overhead checks; it is not an accepted implementation yet.

## Persistence

Reports and exact artifact-copy hashes are delivered in Git. Canonical import, S3 publication and VM restoration remain separate steps; this checkpoint does not claim the latest external evidence is already in all three. The [round81 retention review](retention-31/81_REVIEW.md) approves a background-only refinement after prior serialized imports and exact-state checks. Original cards, baselines and decisions remain preserved. See [delivery hashes](source-copy-manifest-31.json) for frozen-packet validation and copied artifacts.
