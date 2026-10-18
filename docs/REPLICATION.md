# Replication and result criteria

## Terms used in this repository

| Label | Required evidence | Does not establish |
|---|---|---|
| Valid point | Complete cohort, exact input/output counts, frozen request identities, usable latency/throughput records | Improvement |
| Development improvement | Candidate beats its matched development B0 on the declared metric at the same load | Generalization or repeatability |
| Same-input repeat | Independent execution of the same configuration, inputs and protocol | Unseen-input performance |
| Held-out validation | Configuration selected before test outcomes, evaluated on frozen unseen inputs with matched B0 | Repeated-run significance or production equivalence |
| Repeatable improvement | Predeclared objective/tradeoff, repeated matched runs, reported variation and consistent evidence beyond drift | Universal benefit across all workloads |
| SLA capacity | Sustained offered-load study, explicit per-class percentile/error policy, verified dispatch and queue behavior, independent boundary confirmation | Achieved by a short closed-loop Pareto point alone |

A Pareto point is nondominated on the selected observed objectives. It can have unacceptable service latency, and small noise can change membership. It is not an automatic promotion.

## What was actually done in direct Optuna v1

- Search: B0 + 24 candidate trials, two 120-request development points per trial, score at 32 clients. No latency-based pruning; a point timeout or invalid cohort fails the trial.
- Exact repeat: search trials 10 and 11 used the same settings and development inputs. Their p90 TTFT differed by 14.4% at 32 clients.
- Frozen selection: throughput/TTFT/TPOT extrema of the development three-objective frontier, yielding trials 9/10/24. Selection was saved before test execution.
- Test sequence: B0 → 9 → 10 → 24 → B0; each at 16/32/64 clients, 120 requests per point. Test results did not feed the optimizer.
- Two B0 observations expose drift; their range is not a confidence interval. Each candidate has one held-out evaluation.
- Request latencies share queue/server conditions. Do not treat 120 requests as 120 independent hardware experiments or bootstrap them as if that establishes run-to-run significance.
- Aggregate p90 uses 120 requests; class counts are only 54/24/24/18. p99 is descriptive. No arbitrary sample-count threshold converts those observations into an SLA guarantee.

## Conclusions allowed by the evidence

**Trial 9:** development +10% throughput did not reproduce at the test anchor. Do not promote that throughput claim.

**Trial 10:** held-out p90 TTFT at 32 clients was 29–34% below both B0 observations, throughput within 1%, TPOT 1.3–3.3% higher. This is a useful latency tradeoff with held-out support. It is not a confirmed all-metric or all-class win. At 64 clients the TTFT difference is much smaller.

**Trial 24:** lower TPOT with severe TTFT/throughput regressions. Frontier membership alone does not make it useful for the service targets.

## Proposed next checkpoint

Before executing another study, version a new protocol with:

1. B0 and trial 10 fixed; primary question is whether the p90 TTFT improvement at 32 clients repeats. Keep per-class and other percentiles visible.
2. An explicit acceptable throughput/TPOT tradeoff. The current results do not define the user's acceptable regression budget.
3. Several independent matched B0/candidate pairs with balanced or seeded randomized order, frozen workload/caching and recorded startup/measurement times. Three pairs is a possible initial budget, not a universal statistical minimum or an implemented gate.
4. A predeclared time budget, stopping rule and treatment of failed runs. Retain failures and stop rather than silently replace invalid evidence with shorter measurements.
5. Run-level differences and baseline drift reported alongside every point; increase evidence only if it resolves a concrete uncertainty. If the effect remains ambiguous, report inconclusive.
6. New unseen inputs if further tuning is guided by the present test results. The existing test set is now exposed and cannot remain a sealed final test for an adaptive follow-up.

This is a proposed design checklist, not an automatic promotion rule already enforced in code. No new GPU campaign is started by the reporting or archival commands.
