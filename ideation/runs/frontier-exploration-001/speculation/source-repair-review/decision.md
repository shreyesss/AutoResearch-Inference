# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## R1

Inspect the deployed launch flags, checkout, patch, and container first: the supplied profile says DSpark k5 has adaptive verification disabled, while its CSV says DSpark is off. If verification is inactive and the DeepSeek-specific graph safety conditions are present or can be qualified, enable adaptive verification while retaining draft k5. The proposed mechanism is to spend less target verification work when a full drafted block is unlikely to be useful. This is a transfer inference, not an observed B200 benefit. The B300 concurrent-prefill failure makes mixed-batch graph eligibility a prerequisite, and the B200 tuning PR favors fixed k5. Advance only if same-topology tests improve SLO-qualified cost and throughput without sampling, rollback, or latency regressions.

**Decision:** deferred

**Reasons:** correctness_and_safety: The design retains draft k5 and gates activation on sampling, KV rollback, and graph-safe mixed-prefill checks. Safety is unresolved: issue #59970 reports “IMA within 1 min at c96 (4/4)” on B300, while PR #59986 says its B300 reproducer was “Not run.” Neither establishes safety on the target B200 deployment.

**Cheap test:** Graph-safe adaptive verification with draft k5, with safety changes already fixed in every relevant arm.

**Reject if:** Mixed-batch safety or exact sampling and KV rollback fails, or qualified adaptive k5 cannot outperform the strongest eligible static comparator under the prespecified decision rule.

## R2

Consider verification-cost calibration only if deployed inspection shows adaptive verification is eligible, graph safety is qualified, and its cost model uses profiling shapes above the reachable decode ceiling. A B200 issue reports that such shapes can be mistaken for uniform decode; an open PR proposes schedulable mixed prefill and decode tails. Port or enable that behavior only if absent from the frozen runtime, and retain the current captured decode shapes. The mechanism is a more faithful cost estimate for the batches that actually occur, which might change adaptive decisions under prefill pressure. No supplied evidence shows that calibration improves serving performance on this target; if the behavior already exists or decisions do not change, stop.

**Decision:** deferred

**Reasons:** task_value: A cheap inspection can establish whether mixed-tail profiling is absent and adaptive verification is eligible. Issue #54046 reports a concrete shape mismatch for B200 at k7, but whether the target k5 deployment reaches the mismatch, changes policy decisions, or improves cost and latency is unknown. This is a valid first falsification question.; correctness_and_safety: The design keeps draft k5, acceptance and rollback rules, and captured decode shapes, and makes R1’s safety qualification a prerequisite. PR #54077 claims the change “does not modify sampling or verification kernels,” but also says “A full DSpark model-serving evaluation was not run.” Target correctness and graph safety remain unverified.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Adaptive k5 with only schedulable mixed-tail profiling changed, after graph safety and activation are frozen.

**Reject if:** Equivalent behavior is already deployed, relevant shapes are reachable, decisions do not change, or the strongest qualified comparator remains better under the prespecified rule.
