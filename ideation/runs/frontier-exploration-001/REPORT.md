# B200 frontier exploration: six grounded experiment designs

## Result

Three subagents operated the actual GitHub/research/hypothesis tools with different search and reasoning strategies. They made **32 initial and follow-up keyword-search calls recorded in their search logs**, read seven distinct paper full texts, inspected PR/issue bodies and pinned implementation files, then ran evidence extraction and task-derived proposal/critique. Additional hypothesis-stage prior-implementation queries are saved in each run and are not included in32.

**Six designs are ready for baseline/eligibility investigation. None is a validated optimization or cleared for an unconditional GPU sweep.** All six latest model reviews are deferred; earlier rejected drafts and repair ancestry remain visible. Numeric scores from different rubrics are not comparable, so the priority below is an engineering judgment about investigation cost and directness of evidence.

The next executable step is reconstructing the baseline from archived launch/image artifacts. Read-only SSH checks found both `bitlane-n4` and `bitlane-n5` terminated. No instances were started and no GPU work was run.

## What to investigate first

| Priority | Design | Concrete change | First falsifier / dependency |
|---|---|---|---|
| 1 | **R1: warm-prefix overload escape** | Preserve prefix locality to the final DP rank, but escape a warm sticky destination when queue cost exceeds saved prefill work | Trace endpoint→API process→rank. If no recoverable misses or warm-key queue hotspots, prune |
| 2 | **R2: pressure-aware prefill admission** | Reduce aggregate prefill work during decode pressure, with a maximum-age guard for prefills | Verify prefill/decode interference; beat the best fixed2K/4K/8K/16K budget |
| 3 | **SPEC-2: correct mixed-shape verification profiling** | Replace unschedulable pure-decode profiling tails; add mix/context strata only if residual errors change decisions | Requires the table to participate in a safety-qualified adaptive mode; otherwise it cannot improve the current adaptive-off baseline |
| 4 | **SPEC-1: safety-qualified adaptive verification** | Keep k5 drafting; selectively verify less work after graph/DP safety prerequisites | Explicit contrary report says gain was within noise. Safety-patched adaptive-off control is mandatory |
| 5 | **K1: decode-sized MoE workspace** | Use a smaller secondary workspace for eligible decode/verification batches, with globally agreed capacity | Active backend must support the FlashInfer CuTeDSL path. Preserve DSpark's multi-token bound and KV memory headroom |
| 6 | **K2: communication resource partition** | Offline-select a small legal communication resource partition to reduce contention with compute | Inspected CuTeDSL adapter disables shared-expert overlap. Stop unless a different active backend exposes a legal knob and measurable contention |

These are source-backed engineering hypotheses, not claims of publication novelty. Some reuse upstream work; the meaningful difference is relative to a reconstructed deployment. Unknown inclusion is recorded explicitly.

## R1 — escape overloaded warm prefixes, not just misses

**Evidence:** [PR43483](https://github.com/vllm-project/vllm/pull/43483) and its pinned router code; [PR58757](https://github.com/vllm-project/vllm/pull/58757) on engine routing; [CacheRoute](https://arxiv.org/abs/2608.19677) on locality/skew tradeoffs. The inspected route code applies its miss-balancing escape inside `_would_miss`; the proposed extension also considers overload on warm hits. An open PR is not proof that this behavior is deployed.

**Hypothesis:** preserving final-rank cache locality can save prefill work, but hot prefixes can concentrate queues. A bounded queue-cost escape can recover the saved work without creating a hotspot.

**Experiment:** baseline and strongest load-only routing versus endpoint-only affinity, final-rank affinity, and affinity plus warm-hit escape. Hold engine configuration constant. Measure executed prefill tokens, actual cached tokens, queue wait/skew, CPU overhead and SLO capacity. Include many-key reuse, cold prefixes and a deliberately skewed hot key. If hit rate rises but goodput falls, reject the treatment. Exact-prefix engine validation remains unchanged.

The final warm-hit rule is the subagent's implementation-grounded refinement, not a claim that the model reviewer separately approved every detail. [Full routing findings](routing/FINDINGS.md) · [Experiment contracts](routing/experiments.json).

## R2 — cap prefill work when it harms decode, without starving it

**Evidence:** [RFC52906 /P-PAS](https://github.com/vllm-project/vllm/issues/52906), [paper2608.15171](https://arxiv.org/abs/2608.15171), [PR56848](https://github.com/vllm-project/vllm/pull/56848), and [SLOWeave](https://arxiv.org/abs/2609.07883). These provide a reusable pressure rule, a scheduler implementation and explicit TTFT/decode tradeoffs; they do not measure the B200 baseline.

**Hypothesis:** a nominal16K prefill budget can be too large during mixed decode pressure. A small pressure rule plus an oldest-request age limit may improve tail behavior while preserving throughput at low pressure.

**Experiment:** compare against the strongest fixed2K/4K/8K/16K setting, then adaptive budget with/without the age guard. Record iteration composition, accepted speculative tokens, graph mode, KV preemption and per-request waiting time. Include a long-prefill burst and held-out arrival schedule. Lower decode ITL with worse TTFT, starvation or end-to-end goodput is a failed tradeoff.

## SPEC-2 — fix the profiling workload before inventing another allocator

**Evidence:** [B200 issue54046](https://github.com/vllm-project/vllm/issues/54046), [PR54077](https://github.com/vllm-project/vllm/pull/54077), and exact historical `adaptive_verification.py`. Existing code already accounts for confidence and graph padding; those are not new contributions. [DScale](https://arxiv.org/abs/2609.37532) and [EVICT](https://arxiv.org/abs/2605.00342) provide adjacent verification-cost mechanisms with different hardware/model assumptions.

**Hypothesis:** cost estimates built from unschedulable uniform decode batches or an unrepresentative context can choose poor verification budgets. First fix valid mixed-tail profiling; only then test a small, frozen lookup stratified by prefill fraction and context.

**Experiment:** stock table versus valid-shapes-only versus valid shapes plus strata, with identical allocator, graph/safety mode and weights. Both arms must actually use adaptive verification, after its safety prerequisite is met. Measure prediction residuals, chosen budget changes, accepted tokens per full-step millisecond and serving metrics. If better predictions do not alter useful decisions, stop. Keep an oracle timing table diagnostic-only and avoid hot-path host synchronization. [Speculation findings](speculation/FINDINGS.md) · [Designs](speculation/experiments.json).

## SPEC-1 — test adaptive verification with safety changes held constant

**Evidence:** [B200 recipe62541](https://github.com/vllm-project/vllm/pull/62541) explicitly retains full verification; [issue59970](https://github.com/vllm-project/vllm/issues/59970) reports illegal access with mixed prefills and throughput within noise; [fix59986](https://github.com/vllm-project/vllm/pull/59986) is proposed, not a reproduced production fix. [DP issue45963](https://github.com/vllm-project/vllm/pull/45963) warns against independently changing K by rank.

**Hypothesis:** reducing low-value verification work may help a subset of workloads, but can lose to compaction, synchronization and graph-mode costs. This is deliberately a low-confidence diagnostic with clear negative evidence.

**Experiment:** current fixed k5, safety-patched adaptive-off, and identical safety-patched adaptive-on. Keep draft K fixed. Stress concurrent prefill, cancellation, batch drain and rank skew first. Inspect [PR61806](https://github.com/vllm-project/vllm/pull/61806)'s target/drafter padding interaction as a prerequisite. Measure complete-step cost and accepted output, then capacity/tails. Do not credit graph changes or rank-padding fixes to adaptive verification.

## K1 — smaller MoE workspace, with the memory cost counted

**Evidence:** [PR62073](https://github.com/vllm-project/vllm/pull/62073), full pinned adapter and workspace selection logic. The implementation provides a real separate-workspace mechanism, but no controlled DeepSeek/B200 decode result is established by the inspected sources.

**Hypothesis:** eligible decode/verification batches can avoid prefill-sized workspace costs. Additional allocation can also shrink KV cache and erase any kernel saving.

**Experiment:** identical kernels/backend with primary-only workspace versus globally agreed secondary workspace. Add a memory-only allocation ablation that allocates the secondary buffer but never selects it. Include idle/skewed ranks, capacity boundaries, mixed-prefill fallback and graph replay. Size capacity for actual speculative verification, not one token per sequence. Measure full MoE interval, allocation/KV pressure and end-to-end goodput. A backend switch is a separate experiment, not part of this attribution. [Kernel findings](kernels/FINDINGS.md) · [Designs](kernels/experiments.json).

## K2 — prevent communication/computation overlap from becoming contention

**Evidence:** [September2026 resource-contention paper](https://arxiv.org/abs/2609.07536) studied A100/COMET; [PR52781](https://github.com/vllm-project/vllm/pull/52781) supplies an overlap boundary and synchronization ablation. The inspected CuTeDSL adapter reports shared-expert overlap unsupported.

**Hypothesis:** on a different eligible backend, maximizing communication resources may slow simultaneous GEMMs. A bounded offline partition table may reduce the critical path.

**Experiment:** synchronous, asynchronous fixed partition, asynchronous selected partition and forced early-wait ablation. Hold GEMM tactics and precision fixed. Require a legal resource knob and actual contention in a short trace before coding the policy. Otherwise defer this branch. Do not assume A100 gains transfer to B200 or silently replace the entire backend.

## How evaluation will decide

[EVALUATION_PROTOCOL.md](EVALUATION_PROTOCOL.md) is the consolidated contract. All percent thresholds are **proposed choices**, not expected gains:

1. Reconstruct baseline and check inclusion/eligibility using CPU/source artifacts first.
2. Test correctness and mechanism engagement with one isolated change.
3. Screen a bounded set against the strongest static comparator; separate closed-loop concurrency from open-loop capacity.
4. Freeze one variant before held-out confirmation; randomized paired blocks, confidence intervals, complete failure accounting.
5. Promote only a meaningful capacity or fixed-load latency improvement with quality, tail and cost guards. No gain from a kernel microbenchmark alone.

The common contract uses a5% material improvement target and2% tail-regression guard as proposed defaults, with confidence and correctness checks. Initial screening is capped at45node-minutes per idea (6GPU-hours at8GPUs), then confirmation needs a separately allocated budget. Original agent designs contain larger/more varied budgets and guards; those are preserved as exploratory drafts. **The consolidated plan's effective contract takes precedence** so future agents do not mix thresholds.

## Important findings from auditing the existing benchmark

- R7b c512 is33.762 raw requests/s; its CSV balanced-tier goodput is20.149. These are not interchangeable.
- R7b median replay gives6.629 custom length-aware goodput but4.673 AIPerf goodput. Pin both scorers and report them separately.
- Exact observed8192/1024 token filtering leaves51 native points and10 p50/cost frontier points, compared with55/11 under the original broader case label. Four NVFP4 points have8418input tokens; precision equivalence also needs verification.
- Profiles, overlays and historical manifests disagree or are incomplete. Both known B200 hosts are terminated. No live backend inclusion was verified.

See [BASELINE_AUDIT.md](BASELINE_AUDIT.md) and [machine-readable baseline data](baseline-audit.json). These limitations influence test design; they do not erase the historical measurements.

## Honest assessment of the agent system

The useful work came from varied search strategies, reading implementations, comparing negative evidence and designing causal ablations. The system's quote validator caught a missing baseline citation; a same-policy repair retained the original rejection. Another repair corrected ambiguous “no gain” wording. The kernel rubric also generated an overly broad paper-full-text requirement for an engineering port. That policy was retained during repair, and its effect is visible rather than hidden by forcing acceptance.

The model's accept/defer decision is not scientific validity. A deferred design can still be a valuable CPU/source diagnostic. Conversely, an accepted card would not demonstrate a speedup. Deployment reconstruction, executable patches, GPU trials and automatic measurement judging remain to be done.

## Artifact index

- `experiment-bundle.json`: six consolidated, scoped designs, immutable input hashes and effective evaluation contract.
- `registered-plans.json`: persistent memory/test IDs; planned only.
- `verification.json`: query/paper counts, quote checks, state and no-execution audit.
- `routing/`, `speculation/`, `kernels/`: exact searches, selected source snapshots, evidence packets, generated rubrics, original reviews, repaired reviews, findings and detailed designs.

The authoring agent's refinements are distinguished from model-reviewed statements. The memory graph retains original rejected/deferred candidates, repaired children, evidence and test plans. No rejected result was deleted or relabelled as an experimental success.
