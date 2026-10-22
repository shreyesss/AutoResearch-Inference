# Round63 — prefill interference during long decoding

**One deferred integration direction, no measured improvement or implementation-qualified result.** Frozen source plan: Flash-1017, `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, planned TP1/DP4/EP4 with native DSpark. Runtime flags and actual mixed-load exposure remain unknown. No GPU, native/model import, serving change or canonical mutation.

## 1. Research question and outcome

**LP63-01: a model-specific, collective-aligned partial-depth prefill continuation could let full-depth decode advance between larger prefill layer segments.** This changes the unit of interruption rather than just reducing a token budget. It may preserve large prefill matrices while limiting how much prefill can hold up each decode round. It shares weights and request KV, without separate P/D engines or cache transfer.

The useful component combines September AInfer-PD's rank-aligned safe boundaries with a concrete vLLM layered-prefill continuation implementation. The direct ports are ineligible. The initial target arm should serialize shared MegaMoE invocations at completed native-call boundaries with an identical all-rank phase/layer schedule, **not** invent an interruption inside the persistent native kernel. Concurrent phase execution is a separate, later arm requiring actual buffer/protocol isolation and resource-progress proof.

This is a substantial scheduler/model/graph integration. It ranks below narrower PJ01 and CF59 until compatible traces establish substantial exposed prefill interference after existing controls are tuned. No donor headline is used as an ROI estimate. No novelty or acceptance quota is imposed.

## 2. Adaptive search and prior coverage

Compact recall paginated the current inventory; bounded report text and selected PR source searches checked admission, cadence, preemption and layered execution. Existing priors include `B200-R7b-PREFILL-ADMIT-1` (adaptive prefill budget), H01 group-aware prefill admission/chunks, R4 coordinated FIRE/HOLD release, CMR01 within-rank microbatch membership and N03 resource allocation. They must remain comparators, not be counted again under new paper names.

Actual queries:

1. August–October: `LLM prefill decode interference kernel scheduling latency` — yielded pressure policies and their failure studies.
2. June–October: `GPU LLM prefill decode interference memory bandwidth cache isolation` — mostly repeated policies or hardware substitutions; did not establish a useful B200 cache-isolation component.
3. Following a citation in P-PAS, explicit January–October exception: `From tokens to layers redefining stall free scheduling MoE layered prefill`. This did not find the older titled paper directly; it surfaced September AInfer-PD and February FlowPrefill. The date widening and failed exact-title retrieval are retained, not silently presented as recent-only coverage.

20 query hits cover 16 distinct identities. Four selected fulltexts were fetched after retained-source lookup: P-PAS, DLFP, Crossflow and AInfer-PD. Unversioned arXiv bodies are retained by hash but are not immutable version pins. FlowPrefill and the 2025 layered-prefill paper were not read in full; their relevance here comes from the read citation and the independently inspected implementation proposal. All other hits have abstract-only dispositions.

Three bounded canonical PR searches and one actual isolated `pr-search` led to vLLM #62689/#62690. We fetched current PR metadata and all 29 file-change records, then used actual code-only `investigate` for three full files at head `cae2940461d0c08946d6bc03d91084026ffa9f26`. This is stronger evidence than the opening body, but is not a built or executed donor. The PR's reported serving table predates its final refactor; it is not target evidence.

## 3. What the recent papers actually establish

### P-PAS / P-PAS+ — arXiv2608.15171

[Fulltext](https://arxiv.org/html/2608.15171), selected control algorithm and heterogeneous-workload sections. The policy selects calibrated large/small **global** token budgets based on active decoding and prefill pressure. P-PAS+ adds a case where a single running prefill has unusually large remaining work beside multiple decodes. This is a concrete refinement of the existing adaptive-admission prior, not a new hypothesis identity. The target's adaptive *per-request threshold floor* is not identical to this global budget switch.

Reported endpoint choices and thresholds depend on model/workload. Their end-to-end benefit does not establish the frozen long-output ITL objective. Useful next step for this policy is a fair comparison with the target's existing threshold/cadence controls, after actual activation and exposure are known.

### DLFP — arXiv2609.38386

[Fulltext](https://arxiv.org/html/2609.38386), selected §3 and §6. It adjusts prefill cap proportionally from an observed interval. The paper explicitly identifies scheduler-call cadence as a poor proxy for device completion. More importantly, its **completion-aware bounded-step revision also fails**: on the stated Qwen3-32B setting, P99 ITL rises from 41.1 to 194.8 ms and SLO passes fall from 5/12 to 4/12. The earlier small-model benefit does not rescue this result.

Therefore “replace the timer with completed-step time” is a diagnostic requirement, not a supported performance hypothesis by itself. Fragmenting one large stall can create more moderate stalls and worsen a global percentile. This counterevidence narrows feedback-control claims; it does not prove every adaptive budget is useless.

### Crossflow — arXiv2609.27085

[Fulltext](https://arxiv.org/html/2609.27085), selected lease/controller sections. Short-lived, versioned leases bound compute, KV, projected output, transfer and spill slots; consumed reservations reduce available credit. This is useful admission bookkeeping for independent P/D pools. The current planned group is aggregated and EP-coupled. Treating each DP rank as an independent lease issuer would miss group interference and collective constraints. No distinct local mechanism was established beyond the existing admission priors in this round; retain the component and its limits.

### AInfer-PD — arXiv2609.00993

[Fulltext](https://arxiv.org/html/2609.00993), selected §3–6. It separates a long prefill epoch into communication-safe segments, aligns all-rank host enqueue phases, and orders conflicting device collectives. Its DeepEP normal-prefill and low-latency-decode paths use phase-owned buffers, counters, workspaces, events and transport ranges. The DeepEP boundary is after notification and before routed data movement; cancelling a partially advanced operation requires quiescent retirement. Decode graph inputs and background prefill inputs are separate, and MTP draft+verify enqueue stays inside one decode phase.

Two pieces must remain distinct:

- The specific crossed attention-TP/DP AllReduce versus ReduceScatter/AllGather cycle is not automatically present in planned **TP1**. No benefit is credited to fixing an unobserved deadlock.
- Safe segment admission and phase-state ownership are still relevant to shared-device EP execution. The target uses MegaMoE, not the donor's split DeepEP dispatcher. A whole MegaMoE invocation is the currently exposed host boundary; no mid-kernel yield exists in the inspected wrapper.

The donor's rollout completion improvements, H20-class evaluation, and three-step NextN MTP settings are not predictions for B200 native DSpark or client ITL. Operator/layer interruption is retained selectively; the exact direct communication patch is rejected as a port.

## 4. Pinned target and donor compatibility

### Existing scheduling is meaningful counterevidence

`vllm/config/scheduler.py` exposes long-prefill threshold, an adaptive floor, maximum admitted requests and `prefill_schedule_interval`. In scheduler `650–710`, the adaptive threshold is `max(configured_threshold, input_budget // eligible_requests)` and is disabled for the single eligible request. The capacity-bound escape can stop cadence throttling to avoid an ever-growing prefill queue. Core `2354–2364` coordinates DP cadence from a shared step counter. Source presence does **not** establish these options are enabled in the frozen launch; they remain valid lower-cost activation/tuning controls.

DP graph coordination (`gpu/dp_utils.py:44–201`) agrees on sizes/mode and uses the maximum rank token count for graph dispatch; microbatch splits/padding are collective contracts. Ordinary eager has different local-count behavior. A phase plan cannot independently skip or reorder one rank. Native engine dummy-step behavior remains necessary on idle ranks. Scheduler nonblocking execution and batch queues (`engine/core.py:657–809`) also make host scheduling cadence unsuitable as an automatic device-latency signal.

### The concrete donor does not run on this target unchanged

At PR62690 head `cae294...`, `VllmConfig._validate_layered_prefill` explicitly rejects speculative decoding, DP, DBO, EPLB and KV/EC transfer. It requires synchronous scheduling and disables compilation. Bypassing those checks does not implement their contracts.

The donor `layer_group_context` narrows `start_layer/end_layer` and temporarily substitutes PP first/last flags. Its runner retains per-request `IntermediateTensors`, stages them in batch order and synchronizes bounded in-flight tick storage. This is useful continuation and ownership code, but assumes the model follows the ordinary PP contract.

The target does not simply loop over the narrowed end. Its constructor stores `decoder_replay_start`; `forward` later calls `_run_layers(range(self.start_layer, self.decoder_replay_start), ...)` before a separate CED replay wrapper. With source20 replay, asking for group `[0,5)` still executes early layers `[0,20)`; without replay, the stored endpoint is40 and the same naive adaptation runs `[0,40)`. A source-extracted CPU probe verifies these control expressions. This is a repairable adapter mismatch, not proof that partial-depth execution is impossible.

The target continuation also includes mHC residual/pre/post/res mixing state, pending cross-layer MoE finalization where the separate `fuse_mhc_all_reduce` branch is enabled, auxiliary hidden rows consumed by DSpark, Engram prepared data, input/position/attention metadata, candidate/indexer buffers and the decoder-replay context. `_run_layers` returns five coupled values and updates auxiliary state because one layer's post is fused into its successor's pre. Retaining just hidden states and residuals or calling final collapse at every artificial boundary can change arithmetic and work. Partial prompt KV must remain unavailable to prefix-cache consumers until its required layers are complete; request cancellation cannot free storage still used by enqueued segments.

### MegaMoE state and progress

`deep_gemm_mega_moe.py:606–650` caches a symmetric buffer by EP device group, device and model/shape/format properties. It does not include phase identity. Its forward writes activations, scales, routing IDs and weights into that buffer, then submits one native fused MegaMoE call (`790–854`). The stored native scheduler/kernel bodies contain their own barriers, task/ring progression and termination; no host preemption callback is exposed by this call.

The CPU probe evaluates the exact allocator key with equal-shape synthetic P/D metadata: adding different phase fields does not change the key. That does not expose a bug in current serial execution. It refutes the proposal that two streams alone create isolated state. Creating a second allocation is likewise not proof of independent native protocol state or progress.

**Narrow initial adaptation:** stop enqueueing P at explicit model-safe boundaries, complete/order its entire shared native invocation before D overwrites the same buffer, run a globally agreed D phase, then resume P. Stream FIFO/events must cover real readers/writers; no mid-MegaMoE suspension, global-mutable PP monkeypatch shared between concurrent threads, or separate collective sequence per rank. Fine-grained overlap is a later arm requiring phase-specific buffers, graph inputs and dependencies, not an assumed property of this serial continuation arm. Full-SM persistent kernels can obstruct concurrent progress even if allocations are disjoint.

## 5. Executed diagnostics and limits

`adapter_contract_probe.py/json` runs only the donor integer range helper and exact target AST expressions. Six range cases include a positive aligned-group control and both stored replay endpoint branches. The `[0,5)` mismatch falsifies the direct adapter; equal key results falsify automatic phase isolation. No model arithmetic, graph capture, CUDA work, barriers, lifetime events or latency are simulated as if measured.

The next cheap check is **a complete continuation read/write inventory** at one proposed boundary, including which arrays are overwritten by an intervening decode and which auxiliary/Engram/CED state must survive. A skeleton that merely receives perfect epoch/phase events would not prove the runner emits those events. After that, a future CPU control harness can execute the actual modified scheduler and graph selection without tensors; numerical continuation still requires separately authorized native differential tests.

## 6. Standard evaluator coverage and value gate

Retained workload metadata (`workload-coverage.json`) gives:

| Existing trace | Requests | Median requested output | Requests with output ≥1024 |
|---|---:|---:|---:|
| Mooncake median | 4004 | 29 | 22 |
| Mooncake burst | 4220 | 33 | 21 |
| Mooncake cache-heavy | 4053 | 31 | 37 |

Their scheduled arrivals, context diversity and real prefix identities are useful for mixed-load interference and TTFT/tail guards. Requested lengths do not establish actual executed prefill, cache hits, EP placement or overlap duration. These traces alone have limited long-output coverage.

The retained agent-p75 workload is closed-loop, 8192 input (6144 shared +2048 unique),1024 output,8prefixes. At concurrency above1, replacement requests can create prefill while other requests decode, but selected concurrency, warm-prefix hits and actual overlap must be observed. Keep the existing standard suites first. Only add a clearly separate controlled mixture if those runs show insufficient eligible overlap; do not replace the standard objective with an easy donor workload. Historical October17 benchmark manifests use a different checkpoint/runtime and cannot supply c455 exposure or ROI.

Primary remains long-output ITL with separate tail guards. More prefill segments may lower one maximum pause while increasing the fraction of token gaps in the tail; average/median improvement alone is insufficient. Check TTFT/E2E, throughput, every-token/tail SLA, cancellation/OOM and active-state memory. Additional mHC continuation storage reduces KV headroom and may cause more preemption. Different batching/GEMM tactics can change numerical outputs even with identical weights and mathematical layer order.

No compatible mixed-step durations, remaining stall contribution, boundary frequency or continuation-memory peak were established. Do not convert donor speedup, MAC count, layer count or preserved large token batch into service gain. The intervention is deferred with lower readiness than PJ01/CF59. Existing admission/cadence controls should be checked first.

## 7. Proposed future comparison, not authorization

1. Record effective existing chunk/admission/cadence/graph/DSpark settings and standard-load eligible overlap. Compare sensible existing controls first.
2. Prove one exact target continuation boundary without disabling native DSpark or changing weights. Preserve original arithmetic boundaries, request KV ownership, auxiliary output semantics and single sampling after completed prompts.
3. Compare baseline versus **serialized collective-aligned layer continuation**, holding initial workload/admission policy fixed. This isolates interruption granularity from concurrent resource partitioning.
4. Only if useful, compare the same continuation schedule with explicitly isolated overlapping P/D state. Do not attribute the bundle to a buffer allocation or selective stream route alone.
5. Require exact relevant outputs/logits within a declared native numerical contract, all-rank liveness including no-work ranks, full/partial graph paths and cancellation/rejection cases before serving metrics.

## 8. Dispositions and durability

LP63-01 is one deferred target integration direction, not a direct-port win. P-PAS is a refinement of existing adaptive-admission hypotheses; DLFP supplies negative/control evidence; Crossflow leases are retained without claiming a new local policy; the direct DeepEP and PP-adapter ports are rejected as scoped. No fresh candidate is counted for each component.

Receipts, all paper dispositions, exact donor/target bodies, API metadata/diffs, source hashes, CPU scopes and export accompany the report. Local isolated state only; no typed canonical card, recovery publication or S3 sync is claimed. Independent review follows separately.
