# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## H1

Test a shape-aware choice among eligible existing expert GEMM backends for low-concurrency DeepSeek decode on B200. EPS-MoE establishes grouped-versus-dense selection by token count as prior work; a vLLM PR reports a small-load backend comparison on GB300 and GLM-5.2, but neither establishes the best choice or a bottleneck for this target. Profile routed tokens per expert and the full MoE path first. If backend eligibility and distinct performance regions are confirmed, capture a fixed backend for each supported batch-shape bucket and select its graph before replay. The prediction is lower decode TPOT only in buckets where expert computation exceeds selection and staging costs. A kernel-time improvement alone would not establish a serving benefit.

**Decision:** defer/reject

**Reasons:** Critic gate: evidence_entails_claims; Critic gate: distinct_from_prior_art

**Cheap test:** Predeclared shape-bucket selection among the same eligible backends, with a captured path per bucket.

**Reject if:** No eligible second backend exists, graph replay or correctness fails, or treatment does not improve TPOT against the best static control.
