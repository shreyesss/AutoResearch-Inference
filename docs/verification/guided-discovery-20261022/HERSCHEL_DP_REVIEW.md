# Herschel DP preplanning: delegated source audit

CPU/source only; no profiling or GPU/model/service calls. Reference vLLM c455786; live image match unknown.

## Source-paper claim and scope

[Herschel §9.2](https://arxiv.org/html/2609.40247v1) relocates DP agreement before worker dispatch and derives execution plans while preserving hybrid-model handoff, graph and idle-rank semantics. Its gains are from Qwen/XPU configurations, reported as the mean of two maximum observed paired gains at two concurrency levels. Neither that setup nor this selected statistic supplies a target forecast. The transferable idea is dependency-aware preplanning; the reported percentage is not transferred.

## Direct repeated target-to-draft collective claim is already addressed

Independently inspected the complete relevant source chain:

1. `config/vllm.py:705`: V2 defaults after capability checks; `_get_v1_model_runner_unsupported_features` at3071 explicitly excludes DSpark from V1.
2. `gpu/model_runner.py:2276`: actual proposal call passes the target `dp_sync_state`.
3. `gpu/spec_decode/dspark/speculator.py:40`: DSpark inherits DFlash.
4. `gpu/spec_decode/dflash/speculator.py:543–559`: derives uniform batch agreement from that target state and passes it to draft dispatch.
5. `gpu/spec_decode/speculator.py:549`: changes uniform token counts using known request maximum.
6. `gpu/dp_utils.py:293–310`: validates supplied state and returns without executing a fresh synchronization collective; additional graph padding is handled locally and consistently.

Thus reading legacy `gpu_model_runner.py` alone would falsely report an unresolved repeated-collective opportunity for the pinned DSpark route. **Reject the direct repeated target/draft synchronization-removal proposal.** This is a pinned-code conclusion, not a live serving trace.

## Residual first-target agreement relocation remains a different question

`gpu/model_runner.py:1797` still dispatches and synchronizes the first target batch. Inputs include actual batch request-state token counts, graph manager eligibility, active LoRA count, PCP dispatch sizing, profile/eager state, ubatching and uniform-decode conditions. Some are irrelevant to the intended plain DEP4 profile; the exact supported subset can be narrowed rather than requiring every backend feature.

Moving this call to EngineCore does not automatically remove its latency. A blocking collective at the sender can simply delay worker dispatch by the same amount. To qualify a useful relocation, establish which required values are available earlier and which useful work overlaps the moved coordination. Account for cancellation, empty ranks, queued prior outputs, graph bucket compatibility and fallback paths. Do not confuse agreement transport speed, rank arrival skew and critical-path exposure.

**Verdict: defer residual preplanning adaptation until that dependency/capability audit exists.** It is distinct from old Gloo transport tuning, but current evidence does not establish a safe beneficial move. CPU source/control-flow audit can proceed under current scope; GPU trace collection cannot. No new accepted service hypothesis is counted from this paper in this round.
