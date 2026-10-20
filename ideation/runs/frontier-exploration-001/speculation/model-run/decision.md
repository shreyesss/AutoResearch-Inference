# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## b200-adaptive-verification-1

Inspect the deployed launch flags, checkout, patch, and container first: the supplied profile says DSpark k5 has adaptive verification disabled, while its CSV says DSpark is off. If verification is inactive and the DeepSeek-specific graph safety conditions are present or can be qualified, enable adaptive verification while retaining draft k5. The proposed mechanism is to spend less target verification work when a full drafted block is unlikely to be useful. This is a transfer inference, not an observed B200 benefit. The B300 concurrent-prefill failure makes mixed-batch graph eligibility a prerequisite, and the B200 tuning PR favors fixed k5. Advance only if same-topology tests improve SLO-qualified cost and throughput without sampling, rollback, or latency regressions.

**Decision:** rejected

**Reasons:** Unknown source: brief:baseline; task_value: The cheap flag inspection can resolve whether activation is a real baseline delta: the brief says “CSV dspark_config off contradicts profile on; runtime flags not inspected.” The same-topology experiment targets the required cost and latency metrics. The target verification bottleneck and benefit remain unknown.; correctness_and_safety: The proposal retains draft k5 and calls for sampling, KV rollback, and graph-safe decode checks. Safety is unqualified: issue #59970 reports “IMA within 1 min at c96 (4/4)” on B300, while PR #59986 says its end-to-end reproducer was “Not run.” Neither establishes safety on this B200 deployment.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Graph-safe adaptive verification with draft k5, with safety changes already fixed in every relevant arm.

**Reject if:** Mixed-batch safety or exact sampling and KV rollback fails, or qualified adaptive k5 cannot outperform the strongest eligible static comparator under the prespecified decision rule.

## b200-schedulable-cost-calibration-2

Consider verification-cost calibration only if deployed inspection shows adaptive verification is eligible, graph safety is qualified, and its cost model uses profiling shapes above the reachable decode ceiling. A B200 issue reports that such shapes can be mistaken for uniform decode; an open PR proposes schedulable mixed prefill and decode tails. Port or enable that behavior only if absent from the frozen runtime, and retain the current captured decode shapes. The mechanism is a more faithful cost estimate for the batches that actually occur, which might change adaptive decisions under prefill pressure. No supplied evidence shows that calibration improves serving performance on this target; if the behavior already exists or decisions do not change, stop.

**Decision:** deferred

**Reasons:** task_value: Issue #54046 describes a concrete profiling mismatch: “Anything the profiler measures above 1024 tokens cannot be decode” for its k7, seq128 example. Whether the frozen k5 runtime has the behavior, reaches relevant tail shapes, changes decisions, or improves target cost and latency is unknown. The proposed code-presence and shape checks are cheap.; correctness_and_safety: The proposal preserves draft k5 and makes graph safety and adaptive eligibility prerequisites. PR #54077 claims it changes startup profiling shapes and “does not modify sampling or verification kernels,” but target sampling, rollback, and concurrent-prefill safety have not been qualified.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Adaptive k5 with only schedulable mixed-tail profiling changed, after graph safety and activation are frozen.

**Reject if:** Equivalent behavior is already deployed, relevant shapes are reachable, decisions do not change, or the strongest qualified comparator remains better under the prespecified rule.
