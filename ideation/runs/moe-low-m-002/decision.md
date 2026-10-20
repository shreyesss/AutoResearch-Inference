# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## H1

For a specified DeepSeek checkpoint on B200, test whether a small set of capture-compatible expert GEMM paths should be selected by decode shape and routed rows per expert. Low concurrency can produce small expert matrices, but the supplied sources do not establish that expert GEMM dominates this target’s TPOT or that its current dispatch is static. Prior work already switches between grouped and dense GEMM by token count, so this is a conditional workload adaptation. First identify eligible backends and trace complete decode steps. Then compare a predeclared selection policy with current dispatch and the best eligible static choice under the same CUDA Graph mode. A kernel-level gain alone would not justify the change: the policy must reduce repeated end-to-end TPOT.

**Decision:** defer/reject

**Reasons:** Critic gate: distinct_from_prior_art

**Cheap test:** Predeclared shape policy over those eligible backends; capture each selected path with stable buffers.

**Reject if:** Neither target regime improves TPOT over the best static control, or correctness or replay fails.
