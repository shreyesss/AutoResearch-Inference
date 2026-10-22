# Round89 — reusable CPU round-count diagnostic

## Decision and actual change

Round87's reviewed selective synthesis is now an executable diagnostic:
`researchctl round-estimate --record INPUT.json`, also exposed as MCP
`estimate_rounds(inputs)`. This is a new tool capability, not a new serving
hypothesis or performance result. No GPU, model, serving change, probability
collection or provider query ran for this work.

The core is a small standard-library module. It combines the EDR round-start
occupancy construction with the block-specific posterior derived using Sun et
al.'s block law. Ordinary and block modes intentionally differ. Every potential
anchor needs normalized realized-token proposal probabilities; the target path
needs positive normalized target probabilities. Input provenance is preserved
but explicitly unverified. Missing data is not filled with confidence or overlap.

The tool accepts only fixed block/full-block-before-cap/no-EOS semantics and
rejects AV. It returns conditional expected rounds, round-start probabilities,
terminal mass and a canonical-JSON input hash. The actual input is retained
alongside the result for replay, including through the MCP temporary-input path.
The standard journal and snapshot boundary are reused. No new agent scheduler,
probability collector, automatic promotion rule or cloud dependency was added.

## Verification actually run

- Final research suite:408 tests and29 subtests pass; `pytest-final.txt`.
- Bootstrap dry run passed; no installation or serving changes.
- Complete rational forward-sampler enumeration versus the reusable binary64
  implementation:240 conditional means, maximum absolute difference
  `8.881784197001252e-16`. This reference enumerates proposal paths, latest-pass
  thresholds, residual draws and continuation; it is not the same posterior
  recurrence. All cases are finite synthetic controls.
- Ternary hand-derived control: conditional expected rounds1.5 for block versus
  1.75 for ordinary. This does not claim block is a newly available optimization;
  the pinned native baseline already uses block verification.
- Meaningful input controls cover missing anchor/depth cells, zero proposal
  support, zero target conditioning, tiny probabilities, AV/EOS rejection,
  exact-proposal and one-token-cap limits. Real CLI and MCP tests retain inputs.
- Executed both actual CLI modes in isolated `state`, using the documentation
  example. Receipts `block-receipt.json` and `ordinary-receipt.json` preserve
  result paths. No canonical state was written by these runs.

The independent reviewer requested strict schema-version/law/kind type guards
and safe huge-integer rejection. These were applied before the final suite.
This improves malformed-input handling, not the estimator's scientific scope.
Final independent review additionally ran160 exact-rational backward-Bellman
comparisons,23 focused CLI/MCP checks and a malformed-secret-input/no-new-record
control. Review manifest:
`f272bb8cd840b21e434f3aba96c624f95eb3b523e0d0f5fb09795bbf4fb5c1db`.

## Skill and interpretation boundary

One routing bullet in inference-discovery points to
`docs/OFFLINE_ROUND_ESTIMATE.md`. It prevents an agent from treating this tool as
a source of missing model probabilities, an AV evaluator or an ITL predictor.
The skill-creator validator could not run because PyYAML is absent from the
available Python environments; no validator pass is claimed. This was a one-line
body change with the existing frontmatter unchanged.

The implementation's binary64 log ratios avoid prefix-product underflow but
vanishing survival mass can still round to zero. Native finite precision,
indexed RNG, stopping, hidden scheduling state and model data remain separate.
An average over actual target-law trajectories can estimate the stated ideal
round expectation; arbitrary text supplies conditional diagnostics only.

## Yield and next use

One useful cross-paper evaluator refinement became a reusable CLI/MCP command.
Zero new optimization identities, implementation promotions or measured service
wins. The next relevant use is on legitimately retained all-anchor probability
data, or a scoped future collection plan—not another synthetic arithmetic score
presented as deployment evidence. Current PC76 AV/data gates remain open.
