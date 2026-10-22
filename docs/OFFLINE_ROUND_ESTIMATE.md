# Offline conditional round estimator

`researchctl round-estimate --record input.json` (MCP: `estimate_rounds(inputs)`)
computes **E[number of rounds | one supplied output trajectory]**. It loads no
model, acquires no probabilities, and makes no provider/GPU calls. Input and
result are retained under `research/records/round-estimate-*`, with the normal
command journal and local snapshot. `--defer-snapshot` defers that snapshot to
an explicit checkpoint. Prefer an isolated research state during a long backfill.

This diagnostic combines the round-start occupancy construction in
[EDR, 2610.10411v1](https://arxiv.org/html/2610.10411v1) with a fixed-block
posterior derived from [Sun et al., 2403.10444v3](https://arxiv.org/html/2403.10444v3).
The campaign's round87 report records the derivation, exact finite enumeration,
and independent review. This is a selective use of a training paper's evaluator;
no drafter training is required to perform the arithmetic.

## When it is useful

Use it to compare proposed fixed-block sampling policies when the required
probabilities already exist. Averages over target-law sampled trajectories can
estimate expected rounds under the stated ideal law. Arbitrary benchmark text
gives conditional diagnostics, not an unbiased workload expectation.

**Current DSpark with AV is outside this tool's contract.** Holding recorded AV
lengths fixed does not make a changed-policy evaluator exact. This tool does not
predict ITL, TTFT, goodput, or native floating-point/RNG behavior. Missing input
probabilities remain a real data requirement; do not invent them from confidence
heads, marginal acceptance averages, top-k scores, or visited-anchor logs.

## Input contract

For output length L and block size B:

- `target_probabilities[t]` is the probability of the realized token at t under
  the normalized target distribution after temperature/top-p/etc. It must be >0.
- `proposal_probabilities_by_anchor[n][j]` is the actual normalized proposal
  probability of that same token at n+j, conditioned on the preceding realized
  path **and on starting the draft at n**. All L anchors are required, each with
  `min(B,L-n)` entries. Zero proposal support is allowed.
- Scalar probabilities cannot establish whole-vocabulary normalization. The
  provenance declaration is retained and explicitly marked unverified.
- Horizon: generate a full B-token draft each round, commit accepted prefix plus
  correction/bonus, truncate at a fixed output cap. No EOS or special stop logic.
  Near-cap draft shortening is a different policy.
- Both laws assume ideal independent verifier coins, correct residual sampling,
  and a target-correct continuation. Hidden adaptive/history state is unsupported.

Example synthetic ternary path `abc`:

```json
{
  "schema_version": 1,
  "law": "block",
  "block_size": 2,
  "horizon": "fixed_output_cap_no_eos_full_block",
  "adaptive_verification": false,
  "probability_semantics": "normalized_after_sampling_transforms_all_anchors",
  "provenance": {
    "kind": "synthetic",
    "target": "normalized ternary fixture",
    "proposal": "anchor-conditioned ternary fixture",
    "trajectory": "abc",
    "probability_source": "hand-derived fixture; not model outputs"
  },
  "target_probabilities": [0.25, 0.5, 0.5],
  "proposal_probabilities_by_anchor": [[0.5, 0.125], [0.5, 0.5], [0.5]]
}
```

This yields **1.5 conditional rounds** for `block`, versus **1.75** for
`ordinary`. This difference is a mathematical control, not an optimization win:
the native baseline already uses block verification. `kind` can also be
`target_sampled` or `user_supplied`; the tool does not certify that declaration.
For real data, provenance should identify checkpoint, sampling transformations,
trajectory artifact/hash and probability-collection artifact/hash.

## Arithmetic and interpretation

At an anchor, let p_j and q_j be realized-token probabilities and P_j/Q_j their
prefix products. Ordinary first-rejection posterior survival is
`product(min(1,q_j/p_j))`. Block posterior survival is
`a_j = min(1,Q_1/P_1,...,Q_j/P_j)`. A round commits j+1 tokens with probability
`a_j-a_(j+1)` for j<B, and B+1 with probability a_B; cap-crossing events finish
the current round. Forward accumulation of round-start occupancies gives their
sum as the conditional expected number of rounds, in O(LB) time.

Implementation uses binary64 log ratios, avoiding prefix-product underflow.
Extremely tiny survival probabilities can still underflow to zero. This is a
numerical diagnostic, not exact rational or compiled-native execution. The
output includes the input hash, origin, round-start probabilities, terminal mass,
limitations and zero model/GPU/network-call counts. It makes no qualification
decision and does not alter any hypothesis status.
