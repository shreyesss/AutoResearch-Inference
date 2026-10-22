# Round87 — a block-specific offline occupancy contract

**Result:** the attempted matched-input falsification found no counterexample. More usefully, combining EDR's occupancy construction with the original block-verification law gives a trajectory-only fixed-B posterior kernel under the mathematical assumptions below. Complete rational forward enumeration agrees with this reduction in the finite controls. This is an evaluation-method refinement for PC76 and related policies, not a new optimization identity, native implementation qualification, novel theorem claim, or serving gain.

No GPU, model, target runtime, native library, compiler or canonical writer ran. The only execution was standard-library finite probability arithmetic and isolated research tooling.

## Question and retained inputs

Round85 correctly rejected substituting the ordinary first-rejection transition directly into native block verification. The next question was narrower: does block verification inherently need off-output-path distributions for an exact offline round evaluator?

For a selected output `x = a…a`, we held fixed the **complete normalized target distributions** at every prefix, and the **complete normalized proposal distributions at every relevant anchor and position** on that output. We additionally held the all-a continuation fixed beyond the finite output cap. Models differed only after a prefix containing b: target-only, proposal-only, or both. Input tables and SHA256 fingerprints are saved per model. No result uses a comparison where the retained trajectory inputs changed.

The initial complete forward calculation gave identical conditional round-count distributions in all matched comparisons. We retained that null and investigated why. It does not prove sufficiency by itself; the algebra and primary source below supply the stronger explanation.

## Primary sources and exact native mapping

Recent EDR paper [2610.10411v1](https://arxiv.org/html/2610.10411v1), retained from round85, supplies the round-start occupancy method. The exact native c455 block branch cites Sun et al.'s [Block Verification Accelerates Speculative Decoding, 2403.10444v3](https://arxiv.org/html/2403.10444v3). This older paper is an explicit recency exception: its Algorithm2, Lemma3 and proofs B.1/B.3 directly establish the native rule's probability contract. No broad new query was needed. One explicit versioned fulltext fetch was performed; no donor package was imported.

In c455 `rejection_sampler_utils.py`, the running ratio clips `r_(j-1) * p_j / q_j` to one; the lookahead residual determines intermediate thresholds; accepted length is the latest passing threshold; residual recovery uses `[r_j*p-q]+`; a fully accepted block draws a target bonus. We read the exact copied source already retained in round85. Greedy, placeholders, synthetic rates, floating arithmetic and effective runtime selection are separate concerns.

Sun's Lemma3 conditions on a **draft prefix**, not on a target output: `Pr(K>=j | proposed prefix)=r_j`. The target-output posterior is a different quantity. The result below derives it using the correction law as well as that lemma; it does not equate the two conditioning operations. We do not transfer Sun's global optimality claim to arbitrary anchor-dependent drafter policies.

## Derivation: integrate discarded branches instead of retaining them

Fix a round anchor n, block size B and a positive-probability target output path. Write p_j and q_j for the probabilities of its j-th token, with q conditioned on that anchor and the preceding proposed tokens. Define prefix products and accepted-prefix joint mass:

```
P_0 = Q_0 = beta_0 = 1
P_j = product_{k=1..j} p_k
Q_j = product_{k=1..j} q_k
beta_j = min(beta_(j-1) * p_j, Q_j)
a_j = beta_j / P_j = min(1, Q_1/P_1, ..., Q_j/P_j)
```

On proposal-supported prefixes, `beta_j = Q_j * r_j` follows directly from the native clipped ratio. The beta recurrence also remains defined when Q becomes zero, without dividing by a zero proposal probability.

For j<B, let `Z_j = sum_v [r_j*p(v)-q(v)]_+` at the accepted prefix. Lemma3 and one-step marginalization give

```
Pr(K=j | proposed prefix of length j)
    = r_j - sum_v q(v)*r_(j+1)(v)
    = Z_j.
```

For j=0, r_0=1 and this is the ordinary root residual mass. Multiplying by Q_j and by the normalized correction distribution yields joint mass for a particular output chunk ending in correction token v:

```
Q_j * [r_j*p(v)-q(v)]_+
    = beta_j*p(v) - beta_(j+1)(v).
```

For j=B, the full accepted prefix plus bonus has mass `beta_B*p(v)`. Subsequent rounds start at the committed chunk and generate the target conditional suffix under the block sampler's distribution guarantee. Dividing the joint complete-output mass by the target path probability gives the conditional boundary probabilities:

```
Pr(commit j+1 tokens | complete target output, anchor n) = a_j - a_(j+1), j<B
Pr(commit B+1 tokens | complete target output, anchor n) = a_B
```

They are nonnegative and sum to one. The posterior probability of reaching at least j accepted drafts is a_j. Therefore an EDR-style occupancy recursion can use posterior survival transition `a_j/a_(j-1)` when `a_(j-1)>0`. When prior survival is zero, that state has zero occupancy; set its unused transition to zero without evaluating 0/0. The bonus boundary forces a new round. At a fixed output cap, all transitions reaching or crossing the cap terminate in the current round.

This algebra explains the matched-input null: discarded branches have been integrated out by the block residual law. In this fixed-B ideal model, they are not additional required input data. The original ordinary posterior `min(1,q_j/p_j)` is still generally wrong for this block process; the new transition depends on the running prefix likelihood ratio.

### Assumptions and scope

Normalized p/q, exact real arithmetic, ideal independent verifier coins and an independent correct residual draw, fixed B, anchor-conditioned proposal laws, positive target path probability, and target-correct subsequent rounds are assumed. The selected path must use the same target sampling transformations and actual proposal family. No graph/kernel numerical equivalence follows. Learned confidence, adaptive lengths, batched scheduling state, or history not determined by the anchor/prefix are not silently integrated. No claim is made that arbitrary native seeds produce independent ideal coins.

The finite control uses no EOS: each round generates a full B-token proposal, commits accepted prefix plus correction/bonus, then truncates at a fixed output cap. This models that explicitly stated horizon, not every engine's near-limit scheduling or EOS policy. EOS/stop processors and any last-round draft shortening need their own exact contract before reuse.

## Executed checks

`forward_enum.py` contains three calculations:

1. Complete forward enumeration of all draft paths, latest-passing threshold events, correction/bonus draws and subsequent rounds. Every complete output's marginal is checked against the target law.
2. A separate trajectory-only recursion using the derived boundary distribution. It compares the **whole conditional round-count distribution**, not only the mean.
3. EDR-style forward state occupancy using the derived posterior hazard, checked against the boundary recursion's mean.

| Coverage | Actual result |
|---|---|
| Positive-support models |20 models; B=1,2,3; output caps 3 or 4; context- and anchor-dependent laws |
| Matched off-path comparisons |16, all retained-input fingerprints identical; zero posterior counterexamples |
| Conditional output comparisons |240 exact equalities between full forward law and trajectory-only law; occupancy means also equal |
| Separate zero-support controls |Nine model/block cases: deterministic disjoint p/q, zero proposal on positive target support, identical deterministic p/q |
| Zero-support conditional outputs |30 positive-target outputs checked; zero-target-probability outputs excluded from conditioning |
| Zero occupancy |Unused hazard set to zero; no 0/0; no native log/NaN claim |

These are finite synthetic checks, not model workloads, native tests, calibration data, GPU benchmarks, or a prevalence estimate. The mathematical derivation has broader stated assumptions; the finite tests alone do not establish it. The earlier round85 ordinary-versus-block discriminator remains valid and is not overwritten.

## What changes the next decision

The fixed-B block transition need not be rejected as requiring arbitrary off-path model evaluation. A bounded evaluator adapter is now worth designing around all-anchor **realized-token probabilities** with proper normalization, plus stopping semantics. Existing EDR occupancy machinery may be reused after replacing its ordinary transition. Do not blindly substitute the donor's cost-based `expected_passes` field for the per-trajectory sum of round-start occupancies; round85 final review explains that difference.

Producing normalized q at every relevant anchor still requires correct drafter state and potentially model inference; baseline traces containing only visited anchors are insufficient. This result does not supply missing probabilities. It also does not remove the AV gate: the native manager ranks confidence products across requests, reads stale host state and cost tables, and changes admitted lengths. Holding baseline lengths fixed is a replay diagnostic, not an exact changed-policy evaluator. No automatic extension or disabled-AV primary comparison is proposed.

The smallest next contract is a fixed-B CPU adapter at the existing donor recurrence boundary, with explicit cap/EOS semantics and exact normalization/zero-support handling. Numerical native validation and obtaining missing target/draft probabilities remain separately gated. Expected rounds still does not predict ITL without real round costs, confidence/AV effects, graphs and queueing. No quality waiver, acceptance quota or new serving hypothesis follows.

## Tool usefulness and failures

One targeted older primary theorem resolved a specific mathematical gap that another recent-paper synonym query would not. EDR and c455 source were selected-imported from the existing isolated corpus. A caller mistakenly attempted to store the `Sources.fetch` receipt as a document after the tool had already successfully stored the fulltext; it raised `KeyError: source`. Recovery used read-only `Store.get`, without a second fetch. The error and original miss receipt are retained. No new tool change is justified by that caller mistake.
