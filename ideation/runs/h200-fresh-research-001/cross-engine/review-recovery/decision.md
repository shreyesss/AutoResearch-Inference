# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 3.

## R1

Fuse full Top-K selection with physical KV-slot mapping for eligible Hopper decode consumers, extending the earlier selector-only hypothesis. First inspect the pinned vLLM selector, installed DeepSelect extension, and downstream representation requirements to establish whether this fusion is absent and usable. SGLang #41561 reports a Hopper integration that writes mapped slots directly, suggesting that separate index processing, gathers, and copies may be removable. However, later sorting changes and withdrawn mocked tests leave the final contract unverified, while #41659 shows that some prefill consumers require raw positions. Limit the initial port to consumers needing physical slots, preserve required ordering and raw-ID fallbacks, and compare against both the native path and the same fast selector with separate mapping. H200 serving benefit remains unknown.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The reported Hopper integration provides a plausible port path, and the proposal covers raw-index fallback, ordering, block64 boundaries, causal bounds and graph replay. However, the dependency implementation, installed SM90 build, destination consumer contracts and final ordering behavior are unavailable. DeepSelect #14 supplies an explicit SM90 build lead; its BF16 cluster results do not establish eligibility of this particular integration.

**Cheap test:** First inspect source, extension build targets, effective dispatch, and existing logs for equivalent fusion. If absent and eligible, introduce only fused selection/mapping. Follow attestation, activation, correctness, unprofiled screening, separate mechanism diagnosis, then paired confirmation. Use native agent-f75 8K/1K prefixes and fixed-schedule Mooncake anchors adapted to seq64. Confirm small effects with at least five alternating paired full-run blocks, drift checks, and full-run intervals; exclude profiled runs from the frontier.

**Reject if:** Inspection proves equivalent fusion already active with no useful delta, adequate primary-workload coverage establishes no eligible opportunities, correctness fails without a credible remedy, or sufficiently precise paired results rule out the useful-gain margin or establish regression.

## R2

Evaluate a workload-matched SGLang control, then isolate its H200 group32 GEMM configuration tuning as the first optimization arm. The supplied #41251 reports substantial H200 improvements from a multi-change SGLang bundle, but compares against SGLang main under TP8/EP1, another checkpoint, disabled host Engram, and bounded replay. Those results cannot predict an engine replacement here. First establish whether SGLang can preserve the target model revision, two independent TP1/DP4/EP4 replicas, Marlin recipe, host Engram, prefix behavior, and real DSpark policy. If it can, compare matched engines and separately enable only applicable group32 tuning configurations. Hold weight expansion, compensated projections, communication, and other fusions fixed. The hypothesis is that better launch configurations reduce exposed GEMM time on actual target shapes; the bundle's contribution from this mechanism is unknown.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: H200 execution is author-reported, but under TP8/EP1 and materially different checkpoint, Engram and replay settings. No pinned matched SGLang build or implementation evidence establishes the required TP1/DP4/EP4, host Engram, FP8 KV and real DSpark semantics together. The parity checklist is sound; whether its requirements can be met remains unknown.; Priority below this task's threshold; reconsider with evidence or a revised policy

**Cheap test:** First inspect whether exact deployment semantics, target shapes, and tuning-only controls exist. Establish S0 readiness and correctness before timing. S1 changes only applicable group32 configuration entries. Measure A versus S0 as an engine comparison, S0 versus S1 as the tuning attribution, and A versus S1 for deployment value. Use attestation, activation, correctness, unprofiled native-workload screening, separate mechanism profiling, then at least five alternating paired full-run confirmation blocks for small gains, with drift checks and full-run intervals.

**Reject if:** Inspection finds no applicable untuned shapes or no useful configuration delta; matching requirements are demonstrably unsupported without a credible remedy; or adequately precise serving results rule out practical improvement or establish regression. A tuning win that still loses to vLLM is not a deployment win.

## R3

Test direct-NVLink DeepEP dispatch in two attributable stages: compatible backend activation, followed by the triple-buffered prefetch change in #693. First verify the effective baseline transport, four-rank NVLink connectivity, and whether the pinned engine can reach the elastic direct-NVLink implementation while preserving Marlin and its activation payload. The supplied patch overlaps preparation of the next token with outstanding remote stores, but its positive evidence is an eight-H100, remote-only bandwidth test. Four-rank serving may have more local traffic, smaller messages, and greater resource contention. Compare unmodified DeepEP with the baseline before comparing patched and unmodified DeepEP at fixed compute and numeric settings. Resolve the buffer-lifetime invariant and graph behavior before performance testing. Historical mixed-configuration regressions motivate these controls but do not establish that DeepEP will lose here.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The supplied H100 implementation is a plausible Hopper transfer lead, and buffer-lifetime, graph, token-identity and distributed checks are well scoped. The pinned engine's elastic adapter, Marlin payload compatibility, workspace requirements and actual peer connectivity remain unknown. DeepEP #763 adds a concrete version restriction: "Migrate from ElasticBuffer to the dedicated buffer APIs." No target dependency inventory resolves which API generation applies.

**Cheap test:** First inspect effective source/config/logs, NVLink placement, adapter/API compatibility, and whether #693 is already included. Stage A versus B isolates backend activation; B versus C isolates triple buffering. Establish activation and correctness before unprofiled agent-f75 and fixed-schedule Mooncake screening. Diagnose communication separately with profiling, then confirm useful small effects using at least five alternating paired full-run blocks, drift checks, and run-level intervals. Do not combine this arm with SGLang migration or numeric changes.

**Reject if:** Inspection establishes no useful delta, incompatible transport/compute contracts lack a credible remedy, synchronization correctness fails, or adequately precise primary-workload comparisons rule out practical improvement. A patch that improves B but still loses to A is not a baseline deployment improvement.
