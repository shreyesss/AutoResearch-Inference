# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## H01

On the eight-B200 DeepSeek-V4.1-Flash node, trial a capped asynchronous draft cache that prepares likely verification continuations while the target verifies the current MTP batch. A scheduler would spend a per-request token and memory budget only when traces show material draft wait and verification outcomes that can be predicted affordably; otherwise it would use fixed MTP. Prepared continuations would carry request and KV-state epochs and expire on mismatch, preemption, prefix-cache reset, or budget pressure. This could reduce TPOT when a prepared continuation matches, but discarded work could reduce throughput. No supplied source measures draft wait, outcome predictability, or discarded-work cost for this model. Reported SSD gains elsewhere are author claims. Compare within the same eight-GPU budget against qualified fixed MTP and a static branch policy.

**Decision:** defer/reject

**Reasons:** Critic gate: evidence_entails_claims; Critic gate: distinct_from_prior_art; Critic gate: test_discriminates_alternatives; Critic gate: feasible_within_constraints

**Cheap test:** Capped asynchronous outcome branches with trace-gated spending, expiry, and epoch-based invalidation.

**Reject if:** Exposed draft wait is negligible, branch matches are too rare, stale-state correctness fails, or added work erases the latency gain under the equal-resource comparison.
