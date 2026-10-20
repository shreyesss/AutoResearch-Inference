# Execution records

| Run | Scope / state | Plan and evaluator | Result / evidence |
| --- | --- | --- | --- |
| C03 / c03-test-plan-001 | H200, pinned vLLM, DSpark k5, two TP1/DP4/EP4 replicas, Mooncake 0.5x. Original environment protected. | [Execution brief](../runs/c03-test-plan-001/EXECUTION_BRIEF.md) | Planning history retained; see completed run below. |
| C03 / c03-execution-001 | Complete at frozen screen stop; deferred/inconclusive, no promotion. Includes earlier diagnostic failures and triage. | [Independent evaluator review](../runs/c03-execution-001/evaluator-review.md) | [Report](../runs/c03-execution-001/REPORT.md), [paired result](../runs/c03-execution-001/screen-paired-result.json), [full archive and restoration](../evidence/c03-20261020/README.md). ITL +1.85%, TTFT p99 +7.83%, E2E p99 −5.33%. |
| C24 / av-k5-timing-001 | Baseline timing qualification for adaptive verification at existing k5. Diagnostic preparation, not a full hypothesis attempt. | [Run directory](../runs/av-k5-timing-001/) | Initial baseline keeps adaptive verification off. Outcome is recorded after independent timing review. |

C03 A and B are completed runs, although both failed service SLO eligibility. That is different from an incomplete export or a failed benchmark. A had one HTTP failure among 4,004 requests; B had none. The original artifacts preserve those distinctions.

The grouped-Humming C01 result reported on node 219 is external evidence; its raw result is unavailable here. It is not silently counted as a local run. [C01 record](../hypotheses/C01.md).
