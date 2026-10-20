# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 4. Requested: 4.

## h200-continuation-001:H01

Continue C24 by testing whether its existing k5 verification controller should price the actual target and draft graph dispatches after DP synchronization. The installed objective already charges drafting, but that charge depends only on request count; supplied source analysis shows verification-budget changes can enlarge the draft graph. A synthetic CPU example changes the selected budget when this dependency is included, without establishing real latency. The proposed optimization corrects the existing cost model while preserving five-token proposals and probabilistic verification. First repair the offline measurement design and reconstruct legal dispatches. Retain C24's completed instrumentation-inconclusive result and GPU hold until qualified measurements establish whether reduced verification work outweighs draft padding, lost accepted progress and controller overhead.

**Decision:** accepted

**Reasons:** Passed structural and critic gates; engineering review remains

**Cheap test:** Cheapest pilot: at most 8 engineering hours of offline reader, dispatch and objective checks, with zero GPU-hours. Stop before implementation if an equivalent correction exists or the dependency cannot occur. A later GPU pilot requires explicit resolution of the C24 measurement hold. Its maximum is one 60-minute baseline timing allocation, followed only on adequacy success by two 60-minute component/integration allocations for baseline and an AV harness. Compare stock, corrected and static policies on matched states within the harness. Total cap: 180 minutes on eight allocated GPUs, 24 GPU-hours, zero automatic retries. Use the exact diagnostic prefix and fixed capture schedule; exclude profiled results from the service frontier.

**Reject if:** Stop for incompatible attention/graph support, incorrect compaction or verification, an already equivalent objective, or adequately measured unfavorable net tradeoffs. Reject the correction if the unchanged or locked static policy matches or beats it after controller and synchronization costs. Do not relabel rejection of this correction as proof that every AV policy fails.

## h200-continuation-001:H02

Test an isolated port of the unsharded DSpark Markov sampler fusion while retaining the existing H200 executor, Marlin experts and five-token proposal. Installed code exposes repeated embedding, logits, sampling and storage work at each sequential position; the supplied patch combines several of these operations while retaining the bias GEMM. Unlike C03's occasional graph-padding reduction, this could affect every eligible dense draft invocation. Eligibility is unresolved: upstream weight access requires specialized decode, and initialization excludes draft watermarking, top-k and adaptive verification. The baseline's watermark setting must therefore be traced to the actual draft object. Preserve the frozen semantics and reject a port that requires disabling them. Upstream GB300 bundle gains do not predict isolated H200 savings.

**Decision:** rejected

**Reasons:** Unknown source: runs/c03-mechanism-review-001/REPORT.md

**Cheap test:** Cheapest pilot: a maximum 4-hour CPU/source gate audit, zero GPU-hours. Stop if preserving the active watermark or other required semantics is incompatible. After a reviewed adapter and complete source are available, cap a standalone SM90 compile/correctness/component pilot at 45 minutes of eight-GPU reservation = 6 GPU-hours. Only a passing component result permits two 60-minute all-rank integration allocations = 16 GPU-hours, using a fixed diagnostic prefix and actual probabilistic acceptance. Total future pilot cap: 165 minutes, 22 GPU-hours, no automatic retries. Treat unsupported configurations as explicit fallbacks and record their frequency.

**Reject if:** Stop for an incompatible active watermark/top-k/layout requirement, inability to detach specialization safely, sampling or cache mismatch, unsafe scratch reuse, or adequately measured nonpositive exposed savings. Reject an activation-only result as insufficient for allocation. Do not weaken probabilistic decoding or watermark semantics to obtain a benchmark.

## h200-continuation-001:H03

Check whether the installed DeepSeek learned router reaches the FP32-weight GEMM branch targeted by the proposed Hopper BF16x3 kernel, then port only that kernel and its qualified dispatch if it does. The supplied nominal model constructs GateLinear with FP32 output, which does not establish FP32 weights or active GEMM execution; early hash-routing layers further limit exposure. This makes a short dtype, loader and dispatch audit the first decision point. If eligible, faster routing could shorten repeated target verification steps without replacing Marlin experts or communication. Count padded token rows rather than requests. Upstream H200 measurements support a hardware-specific lead, but their different models, shapes and workloads provide no DeepSeek service estimate.

**Decision:** accepted

**Reasons:** Passed structural and critic gates; engineering review remains

**Cheap test:** Cheapest pilot: maximum 3 engineering hours of CPU/source/metadata eligibility inspection, zero GPU-hours. Stop for an absent or already optimized path. Only after exact kernel review and correctness design, cap a standalone shape/graph test at 30 minutes of eight-GPU reservation = 4 GPU-hours. A passing result permits two 60-minute all-rank integration allocations = 16 GPU-hours. Total future pilot cap: 150 minutes, 20 GPU-hours, zero automatic retries. Use fixed native diagnostic traffic and exclude profiled runs from the service frontier.

**Reject if:** Stop if weights are ineligible, the GEMM is bypassed, an equivalent optimization is already active, local shapes are unsupported within scope, correctness/quality fails, or adequately measured net exposed savings are unfavorable or immaterial for allocation. Do not change router precision or the workload merely to activate the candidate.

## h200-continuation-001:H01:r2

Continue C24 by testing whether verification budgets should price the target and draft graphs actually selected after four-rank synchronization. The installed controller already includes drafting cost, but indexes that term only by request count. Supplied source analysis identifies budget-dependent draft expansion, and a synthetic CPU example demonstrates decision sensitivity without measuring latency. The proposed correction must beat AV-off k5, unchanged AV and a locked static verification policy after accounting for accepted progress and coordination overhead. First resolve the offline measurement design and reconstruct joint-rank dispatch. C24 remains completed and instrumentation-inconclusive; neither its occupied-time fractions nor the synthetic example releases the GPU hold. No C03 padding patch is included.

**Decision:** accepted

**Reasons:** Passed structural and critic gates; engineering review remains

**Cheap test:** Cheapest decision pilot: an eight-engineering-hour offline cap, zero GPU-hours, covering equivalent-feature inspection, trace-reader fixtures and joint-rank dispatch reconstruction. Missing traces/source remain pending rather than presumed inspected. Before any GPU release, independently review a concrete instrumentation addendum: explicit native-cycle identities, validated correlation schema, device-boundary timing compatible with existing stream dependencies, and capture termination based on complete native cycles rather than profiler-step count. Proposed captures request 40 complete decode cycles per rank in each fixed window, with a 30-second window cap and no post-result window shifts. Buffer/export scheduling must avoid the former bracket contamination. Conditional future GPU ceiling: one 60-minute baseline qualification slot; only if adequate, two additional 60-minute control/AV-harness slots. Total 180 minutes on eight allocated GPUs, 24 GPU-hours, no retries. The harness compares stock, coupled and locked-static policies on matched joint states; it is not a service frontier run.

**Reject if:** Stop the scoped correction for an already equivalent objective, incompatible backend behavior, correctness failure, or required coordination exceeding feasibility scope. With adequate measurements, stop allocation if AV-off or the locked static policy is at least as good after progress and overhead, or if the upper uncertainty bound on the opportunity proxy is below 2%. This rejects the correction or its allocation value, not every possible AV policy.

## h200-continuation-001:H02:r2

Qualify an isolated unsharded DSpark sampler fusion that preserves the existing H200 executor, bias GEMMs and five sequential proposal positions. Installed source exposes repeated logits, sampling and storage operations; the supplied proposed kernel combines some of that work. Unlike occasional padding changes, the opportunity could recur on every eligible dense draft call, but its frequency and exposed cost are unknown. First resolve specialized weight access and every constructor gate, especially whether the baseline watermark reaches the draft sampler. Preserve active semantics and stop if the port requires disabling them. Complete reduction and launcher code is missing, so implementation remains held. GB300 results bundled with other changes do not estimate this port's H200 benefit.

**Decision:** deferred

**Reasons:** Critic: factual support needs inspection

**Cheap test:** Cheapest pilot: four engineering hours of CPU/source inspection, zero GPU-hours. Resolve every constructor predicate and equivalent-feature presence. If complete code or a semantics-preserving adapter is unavailable, stop before implementation. Conditional GPU sequence: one 45-minute standalone SM90 compilation/correctness/component allocation, followed only on success by two 60-minute all-rank integration allocations. Total wall cap 165 minutes on eight allocated GPUs=22 GPU-hours; no retries. Pin native shapes before measurements. Integration uses fixed diagnostic traffic and unchanged k5 AV-off settings; profiled measurements remain outside the frontier.

**Reject if:** Stop for unsupported active draft watermarking, incompatible layout/top-k requirements, unsafe specialization removal, cache/RNG/token mismatch, or unsafe arrival-counter/scratch reuse. With adequate timing, stop allocation for nonpositive savings or an upper-bound opportunity proxy below 2%. Do not disable a required feature or compare against artificially uncaptured execution.

## h200-continuation-001:H03:r2

Check whether the installed learned router actually executes the FP32-weight GEMM targeted by the proposed Hopper BF16x3 kernel. The supplied constructor requests FP32 output, which establishes neither weight dtype nor active GEMM execution; hash routing may further reduce eligible work. A three-hour loader and dispatch audit is therefore the first decision point. If an eligible baseline branch is active and an equivalent optimization is absent, qualify a minimal kernel port while retaining Marlin experts and communication. Count actual padded token rows, not requests. Author-reported H200 results justify inspecting this hardware-specific lead, but different model shapes and cache conditions leave DeepSeek savings unknown. Complete kernel source and numerical qualification remain prerequisites.

**Decision:** accepted

**Reasons:** Passed structural and critic gates; engineering review remains

**Cheap test:** Cheapest pilot: three engineering hours of CPU/source/metadata eligibility work, zero GPU-hours. Establish an active eligible baseline branch and absence of an equivalent optimization. If these cannot be established, defer. After exact kernel review, allow one 30-minute standalone SM90 shape/correctness allocation, then only on success two 60-minute all-rank integration allocations. Total wall cap 150 minutes on eight allocated GPUs=20 GPU-hours; no retries. Freeze shapes, fixtures, phase windows and analysis before timing.

**Reject if:** Stop for ineligible weights, bypassed GEMM, an already active equivalent optimization, unsupported local shapes, numerical/quality failure or scope-expanding precision changes. With adequate timing, stop allocation for unfavorable net savings or an upper-bound opportunity proxy below 2%. Do not change workload or router precision merely to create eligibility.
