# Independent EDR preflight — useful evaluator, different native transition

**Verdict:** retain the paper's inference-only occupancy/evaluation component. Do not label its published recursion an exact evaluator of the planned native block-rejection + adaptive-verification policy. This is a precise scope objection, not a rejection of the training paper or of offline evaluation in principle. No neural training, model/native import, GPU, or canonical mutation was performed.

## What the primary source actually proves

Read retained `2610.10411v1`, selected Sections2,3.1,3.4, conclusion and AppendixB.1. Its fixed-block algorithm uses ordinary sequential rejection: at the first rejected draft, draw from `[p-q]+`, discard remaining drafts, and start a round after the correction. All accepted drafts yield a target bonus token. EOS terminates; the last EOS-containing round is counted.

The useful distinction from a local teacher-forced overlap surrogate is **round occupancy**. For each target-supported trajectory and every relevant anchor n, it needs `q_(n,t)` conditioned on the committed anchor and intervening accepted target tokens. Conditioned on the output token x, its acceptance probability is `min(1,q(x)/p(x))` (Eq3), not the forward proposal test `min(1,p(x)/q(x))`. The two are different conditioning operations, not a typo. Eq5 propagates probability mass over `(round_start, current_position)`; Eq16 sums diagonal occupancies. Averaging these conditional expectations over independently target-sampled trajectories is an unbiased expected-round estimator. MAL is a ratio of sample means and is consistent, not generally finite-sample unbiased.

This can compare frozen scalar-calibrated proposals without training. It requires q for counterfactual round anchors, not merely draft distributions from one baseline rollout. One target teacher-forced pass supplies target conditionals on that trajectory, but does not supply every drafter anchor/state. A fixed list of prompts or one observed native trajectory is not automatically an IID sample from the same transformed target distribution. EOS, forced output-length censoring, request processors and bonus semantics must match the evaluator's horizon. These are data/protocol requirements, not reasons to discard the component.

## Concrete native mismatch

Exact c455 `RejectionSampler.__init__` selects `use_block_verification=True` for `rejection_sample_method == "block"`; actual effective configuration remains a separate attestation. In `rejection_sampler_utils.py`:

- Lines361–399 compute a clipped running joint ratio: `r_i=min(r_(i-1)*p(y_i)/q(y_i),1)` in log space.
- Lines440–450 identify a lookahead residual mass from the next position; the full-vocabulary mass is `sum max(r_i*p_next-q_next,0)`.
- Lines613–645 use `h_i = residual/(residual+1-r_i)` when a next draft exists, otherwise `h_i=r_i`. The loop can update accepted length at a later position even when an earlier threshold did not select that prefix. This is not “stop at the first failed Bernoulli.”
- Lines869–881 recover with the block residual `[r_tau*p-q]+`, not the paper's unscaled local residual except when the multiplier is one.
- The separate ordinary branch at lines647–685 uses the sequential probability-ratio test and stops on rejection. Greedy is another branch; a stochastic theorem does not silently certify it.

Thus target-distribution preservation alone does not identify the joint law of output tokens and round boundaries. That joint law is exactly what the EDR posterior transitions need. The paper's AppendixB.1 derives `Pr(X_t=v, accepted | history)=min(p(v),q(v))` for its ordinary rule. Substituting this identity into the native block branch without a new derivation is unsupported.

### Bounded exact discriminator

Executed `transition_discriminator.py` with stdlib `Fraction`, no target code execution. Two-token fixed block: root p=(4/5,1/5), q=(1/2,1/2); either child's p=(1/2,1/2), q=(9/10,1/10). Integrating ideal independent uniforms over all four draft paths gives:

| Rule | Expected draft tokens accepted in the first block |
|---|---:|
| Native source block equations | 23/20 =1.15 |
| Ordinary first-rejection equations | 28/25 =1.12 |

On draft path(1,1), the first block threshold is1/7 and the final threshold is1: a failed earlier threshold can still lead to length2. This is a counterexample to equating the transition rules. It is not a reproduction of EDR's complete-horizon estimator, a floating-point/RNG validation, an actual DSpark observation, or a performance forecast. No implication that the paper's own theorem is false.

## Adaptive verification adds state beyond the paper's fixed B

The paper explicitly lists extending its fixed-B framework to adaptive block sizes as future work. Native `adaptive_verification.py`:

- `_assign_draft_token_budget` lines46–73 chooses globally highest survival scores across request/step slots, constrained by capacities.
- `record_confidences` lines256–281 publishes current scores while preserving stale CPU copies used for later budget selection.
- Budget selection lines285–350 combines scheduled request counts, stale confidence products, a maximum logits cap, and draft/verify cost tables. The device reallocation then changes actual per-request lengths.

This is not merely a constant shorter B. Under a changed proposal, parent tokens/confidences, round start times, batch membership and stale histories can differ. Holding recorded baseline lengths fixed produces a conditional/replay diagnostic, not the expected native adaptive-policy rounds. An exact extension may need augmented state and integration over off-trajectory proposals/policy randomness; a single per-request `(n,t)` chain is insufficient without a proof of reduction. Do not turn AV off for the primary proposal comparison merely to make the theorem fit.

## Smallest honest next use

1. Use the published fixed-B ordinary-sampler recursion as a **separate reference diagnostic**, with actual q at every evaluated anchor, consistent target sampling and explicit horizon. It is better motivated than an unweighted overlap-window surrogate, but does not qualify native PC76 progress.
2. For the native policy, first derive the output-conditioned block transition kernel, including residual correction, bonus/EOS and proposal suffix marginalization. The four-path control above must distinguish ordinary and block laws; exact tiny-vocabulary enumeration should validate any derived block evaluator before model traces are used.
3. Add AV only with an explicit policy-state model or label fixed recorded-length evaluation as replay. Do not claim exactness from observed baseline counts.
4. Keep standard serving evaluation for benefit. Expected rounds does not measure draft/verifier cost, queueing, ITL or goodput; the paper itself acknowledges per-round cost dependence.

No training is required for the retained evaluator idea. Native policy adaptation is a mathematical/implementation research gate, not a proven drop-in tool. This review does not create a new hypothesis or alter PC76's status.
