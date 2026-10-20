# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 1.

## R1

Test a decode-sized MegaMoE workspace for DeepSeek-V4.1-Flash on the eight-B200 node, conditional on the deployed engine selecting FlashInfer CuTeDSL MegaMoE and supporting the required workspace API. PR #62073 describes a capacity of `max_num_seqs × (1 + num_speculative_tokens)` per sequence-parallel rank, selected only when every data-parallel rank fits because peer offsets depend on shared capacity. A smaller active workspace might reduce decode address or capacity overhead, but its extra allocation and warmup could take memory from KV cache and reduce useful concurrency. No controlled DeepSeek B200 decode performance measurement appears in the inspected sources; the PR throughput measurement concerns Beam prefill on GB300. Establish backend inclusion and the actual DSpark verification token bound first, then compare full serving behavior and correctness against a fixed-workspace control. The B200 decode bottleneck and effect size are unknown.

**Decision:** deferred

**Reasons:** Task rubric needs paper full-text evidence; legal_correct_integration: The newer adapter says, “Every EP rank must use the same capacity,” and the proposal plans a fallback and zero-rank tests. The active backend, required API, DSpark verification token bound, and multi-rank correctness remain unverified. PR #62073 says, “The MegaMoE runtime paths still need CI or a nightly-FlashInfer machine.”; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Decode-sized workspace selection with a fixed-workspace fallback when any rank exceeds the common capacity.

**Reject if:** The active path is ineligible, the token or peer-offset contract fails, correctness fails, or paired serving results show no useful net benefit after KV capacity is included.
