# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 4.

## h200-attn-20261020-01

Share FlashMLA decode plans across compatible KV-cache groups within one metadata-building pass, conditional on the pinned H200 runner still creating duplicate plans. The supplied patch implements per-pass holder sharing; the author reports fewer planner launches on H20 TP8, using synthetic acceptance for serving measurements. That establishes an implementation mechanism, not an H200 benefit. Unlike small-head kernels, this change does not require TP4 or TP8 and can plausibly apply to TP1. Its value depends on exposed redundant planner work under real DSpark rejection. Reuse must preserve equal live lengths, masks and replay state, rather than merely matching tensor shapes. First inspect baseline membership and builder dispatch; then compare unchanged execution with sharing alone, preserving all serving settings and measuring primary-workload latency and throughput.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The three-file Python patch provides a plausible SM90 port without requiring small TP-local head counts. Active runner dispatch and compatibility across groups remain unknown. The patch states "FlashMLA checks only shapes"; its cache key does not itself establish equal live lengths, masks or replay state. The proposed correctness checks appropriately target these unresolved invariants.

**Cheap test:** First perform the source/configuration presence check. Then attest the port, verify activation and correctness, run an unprofiled screen, collect a separate mechanism diagnostic, and confirm with at least five alternating paired full-run blocks for small gains. Preserve native agent-f75 8K/1K prefixes and fixed-schedule Mooncake anchors adapted to seq64. Keep 1K/1K diagnostics separate.

**Reject if:** Equivalent sharing is already active; adequately covered execution has no redundant compatible plans; reuse violates live-value invariants; or adequately powered confirmation rules out the predeclared useful serving improvement.

## h200-attn-20261020-02

Test direct paged candidate-only indexer scoring as a conditional replacement for dense scoring followed by masking in consumer layers. The supplied #62463 patch describes reading candidate K in place and retaining device-resident live lengths; #62000 instead gathers K before scoring. These are competing implementations of the same work-elimination mechanism, not cumulative optimizations. H20 evidence is conflicting: gathering regressed at one request, while direct scoring's lower ITL came from tiny samples and did not consistently improve throughput. The transfer hypothesis is that avoiding both discarded scoring and intermediate K copies helps eligible H200 long-context decode. First establish actual indexer shapes, cache format and baseline dispatch. Keep dense scoring as the short-context comparator and default; require native 8K/1K evidence before claiming a useful change to this deployment.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: An explicit SM90 FP8 implementation path is proposed, preserving dense fallback and device-resident live inputs. Complete scoring and dispatch bodies are absent from the excerpts. Actual indexer layout, shapes, dependency compatibility and graph behavior remain unknown. Independent numerical, causal, remapping, replay and model-quality checks are appropriately scoped.

**Cheap test:** Start with source/configuration membership and eligibility checks. After activation and correctness, screen each arm unprofiled on native agent-f75 and fixed-schedule Mooncake at seq64, then run separate long-context and cache-isolated diagnostics. Compare surviving arms in at least five alternating paired full-run blocks for small gains. Keep topology, speculation, prefixes, logging and scheduler settings fixed. Do not add a host context-length branch inside captured execution; any future mixed-workload routing requires separate graph-safe qualification.

**Reject if:** The feature already executes equivalently; required cache or shape contracts cannot be satisfied; numerical, causal or replay correctness fails without a credible repair; or adequately powered tests show no useful improvement over dense or the strongest eligible alternative. A native-workload regression rejects blanket activation even if a long-context diagnostic improves.

## h200-attn-20261020-03

Port or activate DeepSelect for eligible FP32 indexer top-k calls on SM90, only after checking the installed selector and extension build. The supplied vLLM patch adds a Hopper availability path and explicit dtype, width, k and alignment checks. Its value would come from faster selection over unchanged logits, independently of attention-head padding or candidate scoring. However, the DeepSelect library's headline H20 results concern small-batch BF16 inputs, while this integration requires FP32; a commenter also reports a competing radix advantage at k=2048. Therefore, compare against the fastest eligible existing vLLM backend chosen on calibration workloads, not merely torch.topk. Preserve existing fallbacks and isolate this selector change initially with dense scoring. Any later compact-logit combination needs separate confirmation because the remaining selection workload is different.

**Decision:** deferred

**Reasons:** h200_applicability_and_correctness_required: The patch explicitly adds "or current_platform.is_device_capability(90)" and Hopper FP32 input validation. This provides a plausible port path while retaining separate sparse-scoring gates. Installed resolver behavior, SM90 extension build, actual input eligibility and complete fallback integration are unknown. The proposed tie, ordering, bounds, graph and quality checks address the relevant risks.

**Cheap test:** Begin with source, build and configuration inspection. After a compatible port or activation, establish per-rank dispatch, pass correctness, screen unprofiled native agent-f75 and fixed-schedule Mooncake at seq64, then collect separate operator diagnostics. Confirm small serving gains with at least five alternating paired full-run blocks, baseline-drift checks and intervals based on full runs.

**Reject if:** Equivalent eligible dispatch is already active; the necessary build or layout contracts cannot be met without erasing the benefit; correctness fails without a credible remedy; or adequately powered tests favor the best native selector or rule out useful serving improvement.
