# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 5.

## R1

Separate the DP-wide maximum real request count from target CUDA-graph capacity when constructing DSpark draft batches. First inspect the installed uniform-batch helper and complete patch revision: the supplied excerpts establish DFlash inheritance and the proposed unpadded-count mechanism, but not the complete deployed dispatch path. If target padding makes the drafter select larger graphs, port the execution-shape fix while retaining startup capture capacity and coherent dummy-rank metadata. The predicted benefit is less draft work during ragged or partially occupied traffic, with little benefit when both counts select the same graph. H20 results motivate testing but do not predict H200 gains: acceptance changed, adaptive verification was enabled, and TTFT regressed at one reported load.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The Python execution-shape port is plausible on SM90, and the proposed dummy-rank, graph, KV and sampler checks are well scoped. However, code:h200:port-checks records "patch does not apply" in both dp_utils.py and speculator.py. Complete final patch behavior and deployed dispatch remain unverified. This requires adaptation, not an architecture-incompatibility rejection.

**Cheap test:** First inspect source/configuration and existing logs. After eligibility and correctness qualification, change logical-row propagation alone. Follow attestation, activation, correctness, unprofiled screening, separate mechanism diagnosis, paired confirmation and held-out evaluation.

**Reject if:** Complete inspection finds equivalent behavior already active; adequate eligible coverage shows no graph/work reduction; or correctness fails or serving performance regresses against the strongest comparator.

## R2

Replace eligible small CPU DP reductions with the recursive-doubling implementation from PR #61767, conditional on exposed synchronization cost. The supplied installed excerpt contains a distributed all-reduce call, while the patch shows the replacement algorithm and engine-state caller. For each four-rank replica, the power-of-two branch requires two exchange rounds; this arithmetic says nothing about serving speed. First confirm the actual process groups, call sites and whether an equivalent implementation is already active. Compare against stock Gloo under matched CPU placement, separating rank-arrival skew from collective service time. The prediction is shorter dispatch gaps when transport overhead is exposed, with negligible benefit when GPU work or late ranks dominate.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The CPU algorithm has a plausible DP4 path independent of GPU arithmetic. Nevertheless, actual process-group backend and invocation ordering are unknown, and code:h200:port-checks records a failed parallel_state.py hunk. The patch uses fixed reserved tags; scoped ordering, group-local rank, pause and fallback checks are necessary. The source says "ray backend not tested".

**Cheap test:** Inspect call-site membership and process groups first. Then qualify and test the replacement at worker metadata synchronization, followed by a separately attributed engine-state arm. Use the required staged evaluation sequence.

**Reject if:** Equivalent behavior is already active; supported eligible calls show no useful exposed-time reduction; the strongest static comparator matches or beats it; or ordering, correctness or serving regressions occur.

## R3

Test prefix affinity at the final DP-rank decision, with affinity information shared across the two API workers within each replica. First inspect existing routing and join requests to replica, API worker and final rank; endpoint affinity alone cannot establish reusable KV locality. Narrow the earlier queue-skew proposal to preferring a remembered compatible destination only among equally loaded ranks, preserving lower-load decisions. Compare shared state with both the existing process-local tie-break proposal and a stateless deterministic tie-break. The expected benefit is avoided prefill for retained exact prefixes. Reported throughput regressions and fragmented API-local maps make cache-hit improvement insufficient evidence; useful selection requires better serving results without unacceptable queue concentration.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: A host routing adaptation is plausible on SM90, with appropriate cache isolation, stale-entry, concurrency and bypass checks. The shared-table integration, installed routing behavior and exact prefix-key semantics remain unspecified or unverified. The source's local tie-break implementation does not establish the proposed shared implementation.

**Cheap test:** First inspect routing membership and collect final-destination joins. Then introduce bounded shared hints within each replica only, following activation and correctness qualification before unprofiled comparisons.

**Reject if:** Equivalent final-rank affinity is already active; adequate coverage finds negligible recoverable work; stateless/local comparators match the result; or higher hit rate accompanies worse qualified serving performance.

## R4

Test coordinated prefill release only if measured mixed-step interference survives tuning the existing scheduler and static prefill interval. PR #61834 supplies a concrete per-step coordination protocol, but its reported interactivity gains come from an earlier MI355X branch and include substantial TTFT penalties; PR #51199 reinforces the need for a static comparator. Adapt the policy to each DP4 replica with MBT16384 and add an agreed wall-clock escape so protected decode periods cannot indefinitely postpone expensive chunks. Keep the CPU collective implementation fixed during this experiment. The prediction is fewer disruptive mixed steps, not an automatic throughput gain; promotion requires a better TTFT/TPOT frontier after accounting for queueing and coordination overhead.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The host protocol is plausibly adaptable to fixed DP4/EP4, but installed scheduler compatibility and the proposed overdue mechanism are unverified. The source excludes elastic EP and custom schedulers. A wall-clock flag checked once per step can override HOLD decisions; it does not by itself establish a hard request-wait bound during long steps, repeated chunks or resource starvation.

**Cheap test:** Inspect existing policy and exposure first. Qualify the adapted coordinated delayer, then compare at the same offered schedule and seq64. Do not combine it initially with h200-systems-002.

**Reject if:** Static tuning matches or dominates; purported gains depend on delayed or unfinished requests; TTFT/wait limits fail; added collective overhead cancels savings; or distributed progress fails.

## R5

Test exact-size registration of CPU-offloaded Engram tables only after resolving whether this deployment uses private DP shards or shared host storage. The launch arguments establish offload and embedding_across_dp, but do not establish allocation ownership, rounding or backing. PR #59849 separates two effects: exact sizing reduces host allocation, while registration type changes lookup performance in its GB10 experiment. If the live private-table path still rounds allocations, port that allocation change with safe fallback and unchanged sorting and NUMA placement. Compare against exact-size cudaHostAlloc and supported existing THP settings. Predict serving benefit only if host pressure or exposed lookup latency falls; memory savings alone do not establish lower H200 cost per token.

**Decision:** rejected

**Reasons:** Critic: factual claims unsupported or contradicted; credible_improvement_required: The supplied code:h200:resolved-engram logs resolve "dp_shared_memory=True, use_thp=False" on both replicas. R5 explicitly targets rounded private tables and rejects shared storage. Its own cheap eligibility check therefore rules out the proposed delta as scoped. No change to the active shared-storage path is proposed.; h200_applicability_and_correctness_required: Generic CUDA host registration is plausibly portable, but the proposed private-table intervention does not match the resolved shared-storage deployment. R5 preserves ownership and explicitly excludes the shared-backing alternative, leaving no remedy within this proposal. This is a deployment-path mismatch, not evidence that H200 cannot register host memory.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** First inspect effective allocation and source presence. If eligible, change only exact-size registration and fallback handling; qualify before unprofiled serving tests.

**Reject if:** Tables are already exact/shared with no relevant delta; registration is unsupported; lookup gains remain entirely hidden; no serving value appears under adequately covered relevant conditions; or lifetime/correctness failures occur. Record memory-only savings separately.
