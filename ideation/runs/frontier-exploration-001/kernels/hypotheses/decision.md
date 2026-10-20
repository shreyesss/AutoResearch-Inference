# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 2.

## H1

Test a decode-sized MegaMoE workspace for DeepSeek-V4.1-Flash on the eight-B200 node, conditional on the deployed engine selecting FlashInfer CuTeDSL MegaMoE and supporting the required workspace API. PR #62073 describes a capacity of `max_num_seqs × (1 + num_speculative_tokens)` per sequence-parallel rank, selected only when every data-parallel rank fits because peer offsets depend on shared capacity. A smaller active workspace might reduce decode address or capacity overhead, but its extra allocation and warmup could take memory from KV cache and reduce useful concurrency. The PR reports no decode gain; its measured throughput claim concerns Beam prefill on GB300. Establish backend inclusion and the actual DSpark verification token bound first, then compare full serving behavior and correctness against a fixed-workspace control. The B200 decode bottleneck and effect size are unknown.

**Decision:** rejected

**Reasons:** Critic: factual claims unsupported or contradicted; Task rubric needs paper full-text evidence; legal_correct_integration: The proposed global capacity agreement, fixed-workspace fallback, idle-rank participation, unequal and zero-rank tests, and DSpark token-bound check address the stated hazards. The active backend, required FlashInfer APIs, actual token bound, and complete workspace implementation are not established.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Decode-sized workspace selection with a fixed-workspace fallback when any rank exceeds the common capacity.

**Reject if:** The active path is ineligible, the token or peer-offset contract fails, correctness fails, or paired serving results show no useful net benefit after KV capacity is included.

## H2

Investigate launch-time selection of communication CTA count or compute/communication SM resources for shared-expert and combine overlap on the B200 deployment. The cited paper describes such selection for COMET on four A100 GPUs and reports prefill gains; it explicitly leaves newer architectures and decode for future work. A separate DeepEP v2 report shows that shared-expert GEMMs can overlap combine in a GB300 deployment, but it does not establish a legal resource-selection knob in the active B200 backend. First inspect the resolved backend and profile whether combine and shared-expert work overlap or contend for resources. Only if a legal knob exists, compare a small, capture-compatible launch-time policy with the strongest fixed resource setting and the current serving baseline. B200 contention, decode benefit, and effect size remain unknown.

**Decision:** deferred

**Reasons:** legal_correct_integration: The proposed collective-order, stream-dependency, and graph-replay checks are appropriate, but no supplied evidence identifies the active B200 combine backend or establishes a legal CTA/SM resource knob. The paper's COMET control cannot establish that precondition for this backend.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** A capture-compatible launch-time resource policy based on measured workload and residency constraints, using only documented legal settings.

**Reject if:** No legal knob or overlap path exists, traces show no relevant contention, correctness fails, or the best fixed setting matches or beats the policy.
