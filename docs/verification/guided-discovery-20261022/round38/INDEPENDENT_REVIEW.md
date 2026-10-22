# DeepGEMM #394 independent source review

## Verdict

**Retain a distinct, source-backed deferred packet-layout hypothesis. No implementation, numerical, runtime or service qualification.** This is not RD01 physical-memory-domain localization. Direct package replacement or calling the donor public transform on finalized target parameters is unsafe. A bounded adapter/port is required before any performance test.

Reviewed donor `deepseek-ai/DeepGEMM#394` head `d1e73685349137b5019ec7b75fe640509e89fbd4`, pinned vLLM `c4557869393db4d75c483d92edd02a5125500883`, and retained DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5` source. Target geometry is conditional on the saved exact Flash-1017 config and planned EP4 with 384 physical experts, no redundant slots. Actual installed backend and kernel row distribution are unverified.

## What is actually missing and potentially useful

Donor `_pack_fp4_weight_tiles` lays already interleaved FP4 weight bytes and UTCCP-transposed scale words in packet order **expert → N CTA pair → K256 tile → CTA peer**. Each packet contains 16,384 weight bytes then 1,024 scale bytes. A single allocation supplies weight and scale views. Three-dimensional TMA descriptors select the pair's adjacent packets. K128 compute tiles select halves of the same K256 packet. This reorganizes access locality; it neither compresses weights nor changes expert routing.

Pinned a7a has MegaMoE already, including persistent scheduling and the existing SwapAB regime. The added component is the packet allocation/TMA addressing, plus separately controlled small-row output-warpgroup and eviction policy. Calling this a new persistent MoE engine or new SwapAB would duplicate existing functionality.

Donor small-token heuristic uses `num_tokens * num_ranks * num_topk / num_experts <= 8.5`; `num_tokens` is `y.size(0)`. Under E384/EP4/top6 that is physical rows <=136, not number of client requests, accepted tokens or guaranteed live rows. Graph padding can change eligibility. Extra physical experts change the cutoff. Packet shape is detected from dimensions; pointer/stride checks then validate the shared allocation.

The donor changes output warpgroup count from 2 to 1 in that branch and selects EVICT_FIRST on routed packet TMA loads. Shared FP8 weights retain ordinary TMA and cache policy, **but shared computation still runs in the selected kernel specialization and shares epilogue/combine resources**. Therefore the no-shared donor benchmark does not cover the target's shared-expert behavior. Source dispatch explicitly supports shared FP8 operands; shared experts are not a categorical exclusion.

## Target geometry and loader contract

For H5120/I2304, EP4/E384 gives 96 local experts. L1 N4608/K5120 has 36 N tiles (18 pairs), 20 K tiles, hence 720 packets/expert. L2 N5120/K2304 has 40 N tiles (20 pairs), 9 K tiles, hence 360 packets/expert. Both satisfy N multiple256, K multiple256, pair completeness and the packet K128/K256 addressing assumptions. Static geometry does not certify JIT compilation or shared-memory resource limits.

Payload per layer and rank is 1,804,861,440 bytes for routed L1+L2 including scales: 1,698,693,120 weight bytes +106,168,320 scale bytes. This equals the ordinary packed representation's payload; it is **not reduced memory traffic or an additional permanent allocation by definition**. Conversion temporarily needs source and destination, and the donor reshape/permute creates other temporaries. Do not multiply this into a model-wide memory claim without loading/lifetime analysis; do not retain both full representations by default.

Target `_register_weight`, `_load_weight`, `_kernel_layout_shard` already write interleaved L1 weights and UTCCP-transposed scales. Donor `transform_weights_for_mega_moe(tile_pack=True)` repeats those transforms. Adapt the **packing-only** helper to finalized bytes instead. The UTCCP permutation is not idempotent: row1 goes to4, a second transform to16. This is a source-coordinate counterexample, not a tensor test.

Current target `_kernel_weights` exposes registered raw-format parameters. `get_expert_weights` asserts axis0 equals local expert count, then permits contiguous or a specific scale transpose. Donor weight/scale views flatten expert and tile axes: axis0 is 69,120/34,560, not96; the views also alias one allocation. Direct replacement fails the export contract. A plausible repair is one owned expert-leading contiguous byte arena per projection, exposing a single `(E, bytes_per_expert)` EPLB component; derive the two donor runtime views from that owner. Never register/export overlapping weight and scale regions independently with accidental omissions or double writes.

That repair is only a proposed interface. It must preserve checkpoint loading/reload, expert remapping and redundant expert copies, EPLB/NIXL registration, distributed transfer units, view lifetime and graph pointer stability. Conversion must precede registration/capture. A side cache that leaves EPLB moving original parameters would silently become stale. The current `update_expert_map` no-op does not implement repacking on reload. A kernel view over moved owner storage must continue to follow physical expert slot numbering.

## Library compatibility and numerical scope

Port into pinned a7a rather than replacing the package with this older donor branch. Preserve current locality-aware scheduling, buffer APIs, shared `get_block_m_for_mega_moe`, activation options and extension/Python ABI. Donor signature lacks newer alpha/beta parameters, but target deliberately omits default alpha1/beta0 and uses swiglu; this omission alone is **not** a Flash-1017 blocker.

Packing copies already quantized bytes and scales and does not intentionally change routing, values, activation clamp, expert statistics or combine weights. That gives a strong correctness premise. It does **not** prove bitwise outputs: TMA ordering, half-packet addressing, epilogue specialization, shared work, distributed schedule and memory lifetime still require executable checks. The upstream bitwise claim applies to reported GB200 H7168/I3072/no-shared cases; its own body states a clean-branch four-GPU rerun is pending. Neither claim is independently reproduced here.

The reported small-token 9.51%/4.37% improvement is a **bundle** of packing, one output warpgroup and EVICT_FIRST. It is not evidence of packing alone, target H5120/I2304 performance or long-output ITL. Larger rows retain the default compute setting in the report, but remain different geometry/workloads.

## Relation to prior work and future decision design

RD01 changes physical allocation across GPU locality domains while keeping scale layout and leveraging an already present domain-aware scheduler. #394 changes tile/scale layout and neighboring CTA load addresses. These are distinct interventions with a common weight-read bottleneck and shared ownership risks. Do not add expected gains or compose domain layouts blindly. M01 route-dependent tile selection is also distinct from fixed packet layout; preserve it as a comparator, not the packet's claimed novelty.

Start with an opt-in standalone port with baseline routing, quantization, shared fusion and EPLB retained. First validate byte/scale reconstruction, K128/K256 addresses, shared/nonshared cases, redundant expert movement, reload and capture pointers. Then separate controls for row-major baseline; packet-only with baseline warpgroup/cache policy; packet+one warpgroup; packet+eviction; combined bundle. Reject unsupported shapes rather than silently choosing incorrect descriptors. Only after correctness, measure joint MoE time and complete decode rounds with committed progress; then unchanged standard Mooncake and agent-75 workloads, including TTFT/tail/throughput guards. No new workload is justified merely by this source mechanism. Actual kernel row histograms and exposed MoE fraction are required for ROI.

## Independent CPU check and limits

`geometry_check.py` imports only stdlib. It checks all target packet coordinates and K128 halves (207,360 arithmetic comparisons), owner expert boundaries, payload accounting, cutoff136/137 and symbolic negative controls. It does not execute donor code, allocate tensors, test EPLB, simulate hardware, compile kernels or prove numerical equality. A provenance-label negative is only an illustration that moving weights without matching scales is wrong; it is not a race test. This review makes no service-speed claim.
