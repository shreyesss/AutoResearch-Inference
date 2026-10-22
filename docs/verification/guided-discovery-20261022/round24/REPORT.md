# Round24 — exact selector paper, duplicate M02

## Decision

**Zero new hypotheses. Existing M02 remains rejected for direct transfer.** This is a source-pin refresh and an explicit contract counterexample, not a new optimization or accepted experiment. Existing identity: `hypothesis:1950794579687d2514af63db0ddd5fc8e153006c9f966b6c9e9b2b0a235a8adc`.

The first online query returned eight papers. Sample-Guided Exact Top-K (arXiv2609.08450v1) was read in fulltext and its implementation pinned at Tencent/hpc-ops2a2e26562433a8ba4b504858f1c938eb7612c901. Other returned papers were existing directions or changed-model/approximate methods; all are dispositioned with actual read depth.

## Why the mechanism looked useful

A sampled coarse threshold can classify candidates during the mandatory full-row pass, certify enough candidates, and refine only an unresolved FP32 frontier. Sampling affects work rather than the advertised exact top-k value set. This can avoid an additional full score-row pass. No GPU or serving improvement was inferred from its H20/Hy4 K2048 evaluation.

## Why it does not establish a new target improvement

1. Exact target config uses `index_topk=512`. The donor dispatch explicitly chooses `launch_one_cta_per_row<512, /*kSampled=*/false>` and says no sampled variant at512. The paper's selected mechanism is therefore not activated for this target setting. Changing targetK to2048 is not an allowed optimization.
2. Pinned vLLM already contains sampled top-k: estimate threshold, compact survivors, exact FP32 refinement, exact fallback for too few/many survivors. K512 threshold is98304 live positions, rows>64 and sufficient SMEM; no hardware properties were queried. Default source selector uses cooperative for eligible<=64rows and persistent above that. Static source conditions do not establish actual deployed dispatch.
3. Donor top-k allows any indices tied at the boundary and unordered outputs; its tests compare selected values when index sets differ. Equal indexer scores do not imply equal main-attention values. A two-element symbolic counterexample demonstrates this implication fails. It does not show observed target ties, nor a bug in either selector's stated contract. Target output/ordering compatibility would still need proof.
4. Donor's K512 direct-exact implementation could be an independent comparator only with a new concrete advantage, target shapes and contract evidence. The sampled paper speedup provides none. The existing M02 already permits a separately qualified candidate-producerK2048 comparison; this round does not reopen it.

## Recall and process correction

The saved67-hit mechanism recall included M02. I initially overlooked it in a long truncated read and described the paper as potentially distinct. Independent reviewer recall identified the duplicate before final disposition. `prior-M02.json` retains the exact predecessor. This is a recall-selection miss, not fresh discovery yield. Five local corpus searches, including refined exact `sampled_topk` and sampled/indexer terms, did not produce a more relevant new donor; no repository backfill was run.

## Verification scope

`contract_falsifier.py/json` reads exact source and config, checks K512 inactive sampling and existing baseline sampling, then executes only a small mathematical counterexample. No torch/vLLM imports, GPU calls, donor builds, kernel tests or timing. Sources and hashes are in `source-manifest.json`. The online query and eight document revisions remain in isolated state. `expand` records the executed first query and later adaptive local searches retrospectively; it is not claimed to have preceded the first search.

## Stop/reopen

Close this branch. Reopen only with evidence of a missing component at the actualK512 shape/dispatch, an independently supported producerK2048 use case, and resolved selected-index/output semantics. No implementation or service promotion and no new hypothesis identity.
