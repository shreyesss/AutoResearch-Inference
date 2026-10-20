# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 5.

## R1

Explicitly activate Humming for the shipped MXFP4 experts, then compare fixed indexed and grouped GEMM paths at unchanged activation precision. The supplied startup log selects MARLIN, and the installed automatic priority list omits Humming, so an indexed override alone cannot change execution. Installed code already exposes the override; #59488 supplies a narrower indexed-selection predicate for V4.1 on SM90 with compatible communication. First verify that explicit Humming selection reaches this loader and that the actual communication backend qualifies. The transfer hypothesis is that indexed execution reduces the complete routed-expert cost enough to improve serving. No supplied measurement establishes that cost or a Humming advantage over this MARLIN deployment.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The #59488 patch supplies an SM90 selector restricted to compatible communication, but pinned-loader registration and effective EP4 transport remain unknown. The supplied port-check artifact also reports that #59488 does not apply completely. Routing, rounding, empty ranks, graph replay, target/drafter behavior and quality checks are appropriately proposed; they do not establish current eligibility.

**Cheap test:** Future sequence: source/configuration eligibility check; activation verification; correctness; unprofiled three-arm screen; separate mechanism profiling; paired confirmation and held-out evaluation. Force each Humming GEMM choice statically. If explicit Humming cannot reach the installed MXFP4 loader, defer execution until a bounded integration is established.

**Reject if:** Adequately covered, precise comparisons rule out the prespecified useful improvement, or the best eligible Humming arm regresses. Reject indexed preference if grouped wins. Unrepaired numerical, routing, or distributed failures veto the affected path.

## R2

At a fixed, validated Humming GEMM selection, test per-token FP8 activations against BF16 while retaining native MXFP4 weights. This isolates activation traffic and arithmetic from backend selection. #59488 describes enforcing and logging the requested schema, while #60600 reports that installed Humming 0.1.16 rejects block-FP8/MXFP4 and can silently substitute per-token FP8 when fallback is allowed. Consequently, #61875's block-FP8 claim cannot justify enabling that format here. The transfer hypothesis is that per-token FP8 saves more expert work than quantization adds at the target's full-size EP4 experts. Establish named-format support or an equivalent verified configuration first; target quality, routed-MoE benefit, and effect size remain unknown.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: Per-token FP8 has relevant H200 engineering evidence, and excluding block-FP8/MXFP8 addresses the supplied 0.1.16 restrictions. However, installed named-format plumbing, actual W1/W2 schemas and target/drafter inheritance remain unknown. Proposed scale, clipping, graph and quality checks are suitable but not completed evidence.

**Cheap test:** First establish schema support without treating package presence as activation. Then verify actual FP8 inputs/scales, pass correctness, run an unprofiled precision screen, diagnose the complete expert boundary separately, and confirm paired serving results. If a source port is needed, run both precision arms on that same source build.

**Reject if:** Quality or numerical gates fail, quantization cost eliminates useful serving improvement with adequately precise measurements, or the incumbent remains superior across the intended primary operating range.

## R3

Port #61461's SM90 launch configuration for the delayed fused mHC post/pre-norm operation only in its supported one-to-eight-token band. The installed selector uses a GB300-derived configuration; for H5120 and confirmed hc_mult=4, the patch selects (12,10,256) instead of (2,8,128). Fewer projection tiles reduce repeated post-mapping work, offering a plausible latency saving when these launches are exposed. The author reports H20 operator improvements and a small low-concurrency serving gain, but no H200 measurement and no separated C64 gain. Count actual eligible kernel calls before porting: seq64 and DSpark k5 do not establish small-token occupancy. Retain the existing selection outside the band and evaluate this independently of coefficient overlap.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The patch explicitly guards SM90 and returns "return 12, hidden_size // 512, 256"; H5120 satisfies that condition. The source-hunk application check succeeds. However, live hc_mult and the delayed-kernel call path are not established. Numerical, warmup, replay and fallback checks are well scoped; the application check excludes tests and native dependencies.

**Cheap test:** First verify source absence and eligible dispatch. Port only the selector/warmup change, validate correctness, screen unprofiled, diagnose operator timing separately, then confirm serving and held-out effects. No simultaneous overlap or precision change.

**Reject if:** Covered eligible shapes regress, correctness fails, or sufficiently precise primary measurements exclude a useful gain. Adequately observed absence of eligible calls rejects primary-workload value, without claiming the kernel cannot help other traffic.

## R4

Test the existing mHC coefficient-stream overlap design on SM90 through an explicit opt-in, after repairing and validating any executed TF32 prenorm path. Installed source excludes SM90, while #60768 describes a constrained opt-in with CPU dispatch tests only. The proposed performance mechanism is to hide independent coefficient work behind other GPU work; at TP1, it cannot claim a fused TP all-reduce saving. First establish a legal overlap window and compare against the best validated synchronous fused mHC configuration. SGLang's bundled improvements do not isolate overlap, and the failed compensated-BF16 port supplies no reason to change arithmetic. Benefits, contention costs, and the suitability of the inherited sixteen-token threshold are unknown.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: An explicit guarded SM90 port is described, with a credible separate TF32 repair path. However, the complete overlap schedule, executed JIT artifact and Hopper stream/graph correctness are unverified. #60768 states "These mock capability checks validate dispatch only." The compensated-BF16 failure does not veto this distinct TF32 proposal.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** First establish dependencies, source applicability, and artifact correctness. Then enable only SM90 overlap, verify activation and numerical/graph behavior, screen unprofiled, diagnose overlap separately, and confirm serving results. Retain synchronous fallback and the initial sixteen-token threshold.

**Reject if:** No legal TP1 overlap window exists, the port has an unrepaired stream/numerical failure, or sufficiently precise measurements show overhead and contention eliminate useful improvement.

## R5

Investigate an opt-in native-MXFP4 FlashInfer MegaMoE adapter for each EP4 replica, with an eligibility check before implementation. #6517 describes SM90 FP4 kernels, checkpoint-layout requirements, and a workspace cleanup repair; its H200 push gains concern EP8 plans and do not transfer here. #62603 supplies complementary evidence that fused dispatch, expert computation, and combine can help eligible FP8 workloads, but it is not a native-MXFP4 V4.1 integration. The transfer hypothesis is that fusion reduces exposed communication and staging relative to the best validated static backend. Require exact E384/H5120/I2304/top6 support, swiglu_limit10, legal EP4 plans, and globally consistent workspace sizing. If these cannot be established, defer the port; do not substitute converted FP8 weights or an unclamped activation.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: Exact FlashInfer FP4 API availability, plan legality, scale conversion and swiglu_limit10 behavior are unresolved on 0.7.0.post1. Supplied DeepGEMM #411/#473 patches provide additional SM90 paths whose visible dimensional checks admit the target geometry, but the excerpts do not establish clamp semantics or complete eligibility. These are gaps, not demonstrated incompatibility.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** Source-only eligibility review first; stop pending missing clamp, geometry, or API evidence. If eligible, validate conversion and distributed kernel behavior, establish activation, screen unprofiled, diagnose the full MoE boundary separately, then perform paired confirmation and held-out evaluation. Keep workspace/plan selection fixed and validated initially.

**Reject if:** The branch cannot preserve required geometry or swiglu_limit10 without an unqualified redesign, conversion fails correctness, or precise measurements show fusion offers no useful serving improvement after workspace and KV costs.
