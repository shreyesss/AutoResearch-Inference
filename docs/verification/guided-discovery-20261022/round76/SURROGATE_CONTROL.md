# PC76: a teacher-forced acceptance score can rank a scalar change incorrectly

This is an exact CPU mathematical control, not a model simulation, DSpark implementation test or latency estimate. It examines the proposed use of a training-paper objective as a prescreen for one frozen-weight draft temperature. It does not reject that hypothesis.

## Defined experiment

A two-token autoregressive proposal has two possible tokens at each position, positive support, no EOS, and ordinary sequential p/q rejection that stops at the first rejection. The target distributions are:

- root: (9/10, 1/10);
- after token0: (17/20, 3/20);
- after token1: (9/10, 1/10).

At T=1, draft probabilities are normalized squared weights from (8,1), (4,2), (1,8) at those states. Dividing the original logits by T=2 gives the normalized unsquared weights exactly. Target probabilities remain fixed. Thus this is a genuine single-temperature intervention with no support change or neural update.

Let A(s)=sum_v min(p(v|s),q(v|s)). A teacher-forced two-position overlap-window surrogate averaged over target-generated first tokens is:

    S(q) = A(root) * [1 + sum_v p(v|root) * A(v)]

For this sampler, expected actually accepted draft count is instead:

    E[L] = A(root) + sum_v min(p(v|root),q(v|root)) * A(v)

The probability of reaching a particular accepted first token is min(p,q), so its conditional distribution after acceptance is not generally p. Enumerating all four draft paths with their independent acceptance probabilities gives the same E[L].

| Draft temperature | Teacher-forced surrogate | Exact expected accepted draft count |
|---|---:|---:|
| 1 | 1.708600592 | 1.772159763 |
| 2 | 1.736598765 | 1.735925926 |

The surrogate improves while actual progress decreases. `control.py` uses exact Fraction arithmetic, asserts the reversal, cross-checks the path enumeration, and checks the null q=p case gives two accepted tokens for both formulas. All assertions passed. The numerical case was deliberately selected with seeded random search for a counterexample; it is not a representative workload or estimate of failure prevalence.

## Source connection and scope

The retained [Acceptance-Aware Draft Model Training v1](https://arxiv.org/html/2609.24150v1) Eq.4 describes its conditional-independence window construction; Eq.15 and Figure1 evaluate overlaps on common teacher-forced target prefixes. This control tests the inference-time qualification one might incorrectly infer from that form. It does not dispute that the objective can be useful for optimization, or claim to reproduce the authors' complete training/evaluation protocol.

Native DSpark uses a block verifier with additional state and scheduling. Neither this sequential formula nor its result is a replacement for the native estimator. An actual PC76 calibration study needs its real verifier, proposal-conditioned states and workload/scheduling exposure. Request-disjoint splits prevent leakage but do not fix a structurally wrong progress estimator. Unknown on-policy progress remains unknown; no CPU overlap improvement is promoted to an estimated ITL gain.

This control complements the separate residual-consistency control: one checks output-law correctness, the other checks inference from a fitting objective to progress. Both are scalar diagnostics, not measured serving improvements.
