# Execution records

| Run | Scope / state | Plan and evaluator | Result / evidence |
| --- | --- | --- | --- |
| C03 / c03-test-plan-001 | H200, pinned vLLM, DSpark k5, two TP1/DP4/EP4 replicas, Mooncake 0.5x. Original environment protected. | [Execution brief](../runs/c03-test-plan-001/EXECUTION_BRIEF.md) | Planning history retained; see completed run below. |
| C03 / c03-execution-001 | Complete at frozen screen stop; deferred/inconclusive, no promotion. Includes earlier diagnostic failures and triage. | [Independent evaluator review](../runs/c03-execution-001/evaluator-review.md) | [Report](../runs/c03-execution-001/REPORT.md), [paired result](../runs/c03-execution-001/screen-paired-result.json), [full archive and restoration](../evidence/c03-20261020/README.md). ITL +1.85%, TTFT p99 +7.83%, E2E p99 −5.33%. |
| C24 / av-k5-timing-001 | Complete baseline diagnostic; instrumentation inconclusive. AV remained off. Two full attempts remain. | [Contract and independent review](../runs/av-k5-timing-001/) | [Report](../runs/av-k5-timing-001/REPORT.md), [full evidence](../evidence/av-k5-timing-001/README.md). 986/986 successes, replay p99 4.65ms; one cell has4 usable decode cycles and five have timestamp-association uncertainty. Original environments preserved, node idle. |

C03 A and B are completed runs, although both failed service SLO eligibility. That is different from an incomplete export or a failed benchmark. A had one HTTP failure among 4,004 requests; B had none. The original artifacts preserve those distinctions.

The grouped-Humming C01 result reported on node 219 is external evidence; its raw result is unavailable here. It is not silently counted as a local run. [C01 record](../hypotheses/C01.md).

## Overnight C24–C26 continuation (in progress)

[Run report](../runs/h200-overnight-001/REPORT.md), [status](../runs/h200-overnight-001/status.json), [evidence archive](../evidence/h200-overnight-001/README.md). C25 passed exact real-weight sampler-component checks and improved component graph duration by 25–40% across eight shapes; three native allocations closed without candidate measurements: two baseline setup/observation failures and one candidate startup interruption. C24's bounded instrument probes were clean but did not repair its historical timing failure. C26's FP32-weight mechanism is inapplicable to the actual BF16 baseline. The failed initial checkpoint mount, three native allocation failures and both clean probes remain retained. A 65,536-event-pair engineering check passed in 5.5 supervised seconds. Completed allocations total 6.689683 visible GPU-hours; a distinct candidate-first live plan awaits ownership clarification after unresolved SIGTERM. No new service result or full attempt is claimed.
