# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 1. Requested: 3.

## R1

Continue C24 by testing whether verification budgets should price the target and draft graphs actually selected after four-rank synchronization. The installed controller already includes drafting cost, but indexes that term only by request count. Supplied source analysis identifies budget-dependent draft expansion, and a synthetic CPU example demonstrates decision sensitivity without measuring latency. The proposed correction must beat AV-off k5, unchanged AV and a locked static verification policy after accounting for accepted progress and coordination overhead. First resolve the offline measurement design and reconstruct joint-rank dispatch. C24 remains completed and instrumentation-inconclusive; neither its occupied-time fractions nor the synthetic example releases the GPU hold. No C03 padding patch is included.

**Decision:** accepted

**Reasons:** Passed structural and critic gates; engineering review remains

**Cheap test:** Cheapest decision pilot: an eight-engineering-hour offline cap, zero GPU-hours, covering equivalent-feature inspection, trace-reader fixtures and joint-rank dispatch reconstruction. Missing traces/source remain pending rather than presumed inspected. Before any GPU release, independently review a concrete instrumentation addendum: explicit native-cycle identities, validated correlation schema, device-boundary timing compatible with existing stream dependencies, and capture termination based on complete native cycles rather than profiler-step count. Proposed captures request 40 complete decode cycles per rank in each fixed window, with a 30-second window cap and no post-result window shifts. Buffer/export scheduling must avoid the former bracket contamination. Conditional future GPU ceiling: one 60-minute baseline qualification slot; only if adequate, two additional 60-minute control/AV-harness slots. Total 180 minutes on eight allocated GPUs, 24 GPU-hours, no retries. The harness compares stock, coupled and locked-static policies on matched joint states; it is not a service frontier run.

**Reject if:** Stop the scoped correction for an already equivalent objective, incompatible backend behavior, correctness failure, or required coordination exceeding feasibility scope. With adequate measurements, stop allocation if AV-off or the locked static policy is at least as good after progress and overhead, or if the upper uncertainty bound on the opportunity proxy is below 2%. This rejects the correction or its allocation value, not every possible AV policy.

## R2

Qualify an isolated unsharded DSpark sampler fusion that preserves the existing H200 executor, bias GEMMs and five sequential proposal positions. Installed source exposes repeated logits, sampling and storage operations; the supplied proposed kernel combines some of that work. Unlike occasional padding changes, the opportunity could recur on every eligible dense draft call, but its frequency and exposed cost are unknown. First resolve specialized weight access and every constructor gate, especially whether the baseline watermark reaches the draft sampler. Preserve active semantics and stop if the port requires disabling them. Complete reduction and launcher code is missing, so implementation remains held. GB300 results bundled with other changes do not estimate this port's H200 benefit.

**Decision:** deferred

**Reasons:** Critic: factual support needs inspection

**Cheap test:** Cheapest pilot: four engineering hours of CPU/source inspection, zero GPU-hours. Resolve every constructor predicate and equivalent-feature presence. If complete code or a semantics-preserving adapter is unavailable, stop before implementation. Conditional GPU sequence: one 45-minute standalone SM90 compilation/correctness/component allocation, followed only on success by two 60-minute all-rank integration allocations. Total wall cap 165 minutes on eight allocated GPUs=22 GPU-hours; no retries. Pin native shapes before measurements. Integration uses fixed diagnostic traffic and unchanged k5 AV-off settings; profiled measurements remain outside the frontier.

**Reject if:** Stop for unsupported active draft watermarking, incompatible layout/top-k requirements, unsafe specialization removal, cache/RNG/token mismatch, or unsafe arrival-counter/scratch reuse. With adequate timing, stop allocation for nonpositive savings or an upper-bound opportunity proxy below 2%. Do not disable a required feature or compare against artificially uncaptured execution.

## R3

Check whether the installed learned router actually executes the FP32-weight GEMM targeted by the proposed Hopper BF16x3 kernel. The supplied constructor requests FP32 output, which establishes neither weight dtype nor active GEMM execution; hash routing may further reduce eligible work. A three-hour loader and dispatch audit is therefore the first decision point. If an eligible baseline branch is active and an equivalent optimization is absent, qualify a minimal kernel port while retaining Marlin experts and communication. Count actual padded token rows, not requests. Author-reported H200 results justify inspecting this hardware-specific lead, but different model shapes and cache conditions leave DeepSeek savings unknown. Complete kernel source and numerical qualification remain prerequisites.

**Decision:** deferred

**Reasons:** baseline_relative_value: The proposed causal path applies only to an active FP32-weight router branch. New checkpoint evidence reports three sampled weights as BF16, while nominal GateLinear requires "self.weight.dtype == torch.float32" for BF16x3 eligibility. This materially weakens applicability without proving loaded dtype. The remaining three-hour loader/cast audit is justified; optimization value remains unresolved.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Cheapest pilot: three engineering hours of CPU/source/metadata eligibility work, zero GPU-hours. Establish an active eligible baseline branch and absence of an equivalent optimization. If these cannot be established, defer. After exact kernel review, allow one 30-minute standalone SM90 shape/correctness allocation, then only on success two 60-minute all-rank integration allocations. Total wall cap 150 minutes on eight allocated GPUs=20 GPU-hours; no retries. Freeze shapes, fixtures, phase windows and analysis before timing.

**Reject if:** Stop for ineligible weights, bypassed GEMM, an already active equivalent optimization, unsupported local shapes, numerical/quality failure or scope-expanding precision changes. With adequate timing, stop allocation for unfavorable net savings or an upper-bound opportunity proxy below 2%. Do not change workload or router precision merely to create eligibility.
