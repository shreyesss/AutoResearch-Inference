# Hypothesis shortlist

Untested proposals. Publication novelty is not established.

Citation checks: PASS

## H01: Coordinate prefill admission within an active expert-parallel collective group

**adaptation · confidence Moderate mechanism plausibility; low confidence in target benefit or implementation novelty. · Trace gate only. Resolve the historical active backend and process groups, then require material mixed prefill/decode rank skew before implementation.**

Proposed, untested adaptation: ranks that must enter the same MoE collective agree on an iteration-level prefill limit based on the slowest predicted participating rank. Each rank retains local request ownership. The group is resolved from the active backend and process groups; independent replicas decide separately.

**Nearest prior art:** SLOWeave supplies the deadline-based chunk rule. P-PAS supplies online token-budget adaptation. FlowPrefill and fairness-aware scheduling address granularity and starvation. The earlier B200 shortlist proposed fixed cadence.

**Proposed addition:** A group-scoped admission contract would account for rank skew, collective participation, graph-compatible shapes, and KV capacity. Its absence from the historical pinned runtime is unverified.

**Code surface:** After active-backend resolution: scheduler admission and token budgeting, per-rank timing and deadline summaries, process-group coordination, graph-shape checks, KV reservation, and stale-state fallback.

**Strongest objection:** The central deadline rule and adaptive budgeting are prior art. The supplied participation requirement applies to a passthrough all-to-all path, while the pinned active backend is unknown. The supplied FlashInfer path already obtains cross-rank token metadata for workspace selection, so a separate admission exchange may duplicate existing coordination. Target traces may show little mixed-step rank skew, in which case coordination and smaller chunks could lose to fixed settings.

**Cheapest test:** The proposed collective-group policy under the same graph and memory limits.

**Control:** Qualify DEP8 and two DEP4 replicas independently. At matched model, backend, precision, MTP/DSpark state, graph repertoire, KV capacity, cache preparation, request bodies, and concurrency, compare unchanged pinned behavior, a fixed cadence and budget sweep, and an applicable SLOWeave-style controller. Include the refreshed guide's DEP4 cadence only at applicable load and configuration.

**Reject if:** Rank skew is immaterial; no reliable group contract exists on the active backend; prediction or coordination consumes available slack; prefill starves; or the best matched comparator meets or beats the treatment on required service and quality criteria.

**Revision:** Replaced both invalid excerpts with exact substrings from their specified diff bodies. Retained one trace-gated adaptation and made the existing FlashInfer cross-rank metadata a substantive objection. Group membership follows the resolved collective; independent replicas do not coordinate.

Evidence:

- `arxiv:2609.07883` (challenges): The core deadline selection rule is prior art.
- `arxiv:2608.15171` (challenges): Online budget adaptation is prior work.
- `arxiv:2606.09061` (challenges): Aging to limit prefill starvation is also prior work.
- `github:vllm-project/vllm:62073:files:vllm/model_executor/layers/fused_moe/modular_kernel.py` (supports): The supplied diff identifies a participation requirement for its passthrough path; applicability to the pinned backend remains unknown.
- `github:vllm-project/vllm:62073:files:vllm/model_executor/layers/fused_moe/flashinfer_moe_ep.py` (context): This FlashInfer path constrains capacity across its EP group; the diff does not establish that the path is active at the historical pin.
- `github:vllm-project/vllm:62073:files:vllm/model_executor/layers/fused_moe/flashinfer_moe_ep.py` (challenges): The branch already consumes cross-rank token metadata for workspace selection; any new admission coordination must justify its additional role.
- `github:vllm-project/vllm:62541:files:recipes/models/deepseek-ai/DeepSeek-V4.1-Flash.yaml` (context): The refreshed DEP4 guide supplies a fixed-cadence comparator at a qualified load, without proving historical-image inclusion.
- `hf:2602.16603` (challenges): Smaller chunks have an efficiency tradeoff in prior work.

## Comparators

- Unchanged historical vLLM ac9126e58aa7bbab1856ba6593ba4d5003fea516 and deepseek_serve 2e6fa287d90adf7318ad314de27aa2f595aac821, recording the actual backend, precision, MTP/DSpark state, graph capture, and cache policy. Named pins alone do not prove runtime activation.
- Supplied PR #62541 state: open and unmerged; main base aa3564ceefbd605f1d28238fa0fbbb964201c6b8; guide-only head 64d4d308b50432449b25fdd4f73576f98b5ae5a5. Its DEP4 cadence and graph settings are qualified comparators where applicable. Main-branch targeting, guide availability, historical-image inclusion, and runtime use are separate.
- Supplied PR #62073 state: open and unmerged; stacked branch base woosuk/beam-fused-allreduce at 4fb4e7530ef9b2b558c842853edb6c7bb087d7ea; head 86a5bbe75a7971275952477bb1ce03e715bcc339. Its Beam-oriented deferred finalize and decode workspace are existing branch work. Nightly FlashInfer runtime validation is incomplete. An earlier conflict comment does not establish current conflict state.
- SLOWeave-style deadline control, P-PAS, fairness-aware scheduling, FlowPrefill, the earlier fixed DP-aligned cadence, and a matched fixed chunk and budget sweep are scheduling alternatives.
- For a separately justified cache study, compare the pinned policy, qualified LRU, tuned fixed partial eviction, compatible RR-EVICT and CacheWise integrations, and native CPU KV offload only in a supported layout. These are outside the mechanism shortlist.

## Rejected Leads

- Round-robin idle-history tail eviction closely matches RR-EVICT's implemented policy. A model-specific integration study requires demonstrated eviction pressure and exact ownership and invalidation rules.
- Speculative speculative decoding has a distinct-hardware assumption in the supplied full text; maintainer discussion identifies substantial scheduler and KV redesign and questions value for MTP/EAGLE-style workloads. Target transfer is unshown.
- Generic adaptive speculative length overlaps vLLM RFC #4565, FASER, and the earlier DP-coordinated DSpark-k idea; target acceptance and verification traces are absent.
- An unchanged port of PR #62073's deferred finalize or decode workspace is existing stacked-branch work with unproved target applicability.
- Mixed expert precision and generic MoE overlap have close prior art; target sensitivity, active kernels, conversion cost, bottleneck, and quality are unknown.
- Feature activations, unchanged upstream ports, unrelated search-title matches, and abstract-only transfer claims do not fill the mechanism count.

## Gaps

- Five mechanisms were requested; one defensible conditional card survives, leaving a shortfall of four.
- No supplied historical checkout or runtime trace resolves the active MoE backend, collective groups, precision path, MTP/DSpark state, graph shapes, KV representation, or memory fit for DEP8 versus two DEP4 replicas.
- No target request, rank, collective, cache, memory, concurrency, or quality trace establishes the proposed bottleneck. The 75% cacheability target is not a measured cache-hit rate.
- Branch availability, main-branch inclusion, historical-image inclusion, and runtime activation remain separate and unproved. PR #62541 reports its InferenceX #3837 relationship; independent ancestry evidence was not supplied.
- Abstracts and results from other workloads do not establish implementation absence, correctness, or measured B200 transfer. The proposal is untested.
