# Round12 independent DSpark context-projection review

**Verdict: retain a distinct source-grounded diagnostic; defer implementation/service qualification.** The pinned source genuinely computes unused context-Q outputs. Start with KV-only per-layer projection on a verified compatible backend; cross-layer stacking and shared activation quantization are separate optional arms. No GPU/model import/runtime patch.

## Mechanism and actual exposure

At `nvidia/dspark.py165–195`, each of three draft layers receives identical projected target `main_x`. It calls its own `attn.fused_wqa_wkv(main_x)`, drops the first `q_lora_rank` columns, retains KV, applies that layer's `kv_norm`, and inserts context KV with its own slot mapping/RoPE/cache. `attention.py371` constructs a replicated merged linear (disable_tp=True) with output partitions[q_lora_rank,head_dim]. Exact saved Flash1017 config gives K5120, Q1280, KV512. Removing discarded Q would remove1280/1792=71.43% of this projection's nominal output arithmetic, **not71% of context time or service latency**. Three-layer nominal work per context row changes55,050,240→15,728,640 FLOPs; no duration has been measured.

This is repeated on proposal iterations, not recomputation of the entire historical context. DFlash `_precompute_context_kv` slices current target hidden states/context positions. Eager execution calls it over current target tokens. FULL capture handles its fixed graph context rows (up to requests×(k+1)) inside `_prepare_graph_forward`; additional prefill rows are handled before replay. Those ranges partition work rather than duplicate it. Rejected/padded positions can remain in projection shapes, with PAD_SLOT_ID suppressing writes. Preserve that contract; don't claim every projected row is useful or every invocation has identical token count.

## Distinctness from prior R2-03

R2-03 proposed omitting query-backbone/Markov work on unfinished-prefill iterations and was obstructed by confidence/KV side effects. This proposal preserves context preparation on **all** iterations, and only removes output columns immediately discarded in that preparation. It neither skips draft query forward nor changes confidence scheduling, token draws, or collectives. It therefore merits a separate identity with an explicit comparison to R2-03. The same full fused projection must remain available for actual draft-query attention, which needs Q.

## Quantized layout audit

A generic `weight[q_rank:]` is unsafe. In the exact supported FlashInfer MXFP8 implementations:

- CUTLASS preprocessing stores contiguous[N,K]. The output-row range1280:1792 is a contiguous512×5120 element range.
- CuTe preprocessing stores the transpose[K,N] with column-major strides(1,K). Columns1280:1792 cover the same contiguous physical range; using a row slice is wrong.
- Both preprocess scale rows into F8_128x4 over output dimensionN with160 groups alongK. Because1280 and512 are multiples128, the KV scale tile region is a contiguous subview starting204800 bytes, length81920 bytes. The exact source offset helper verified all81920 row/group coordinates for this target. Wrong flat start1280 and misaligned output boundaries fail negative controls.

This is integer address algebra, **not a torch stride check or backend execution**. These implementations' apply methods infer N/K from actual tensors, which makes a narrow view-holder adapter plausible. Confirm runtime selected kernel, tensor shapes/strides, storage type and quant metadata; do not apply it to TRTLLM shuffled weights, Marlin, other formats, LoRA or arbitrary fused layouts. Maintain bias=None and original input quantization initially. Shape-dependent GEMM tactic/arithmetic can change rounding even when the algebra is identical. Context KV, subsequent draft proposals and confidence deserve differential tests; target-only final accuracy alone would miss a draft-cache regression.

The checkpoint is native[32,32] UE8M0 with FP4 experts; `_linear_scale_param_name` documents the ModelOpt-linear route. Live selected backend/image is unknown. Full-model query projections and all loader parameters stay intact; adapter views must be created/rebound after final preprocessing and renewed if weights reload. Do not cache views across replaced parameters without lifecycle binding.

## Donor and upstream interpretation

Retained local PR record SGLang31986 describes stacking per-layer context-KV projections, norms and RoPE, with a **quantized-weight fallback**. Its merged status in the retained corpus is not verification of the current online head or target compatibility. It supports selective reuse of the shared-input observation; it does not supply a turnkey target quantized implementation or target speedup. The current c455 target source still loops full fusedQ+KV calls, so it has not already eliminated this exact waste.

The same local search found SGLang33265's packed projection loader issue (GPTQ/AWQ input/output axes differ). That is a useful generic warning about layout-dependent slicing, not evidence our MXFP8 loader is broken. No need to port its unrelated fix.

## Recommended isolated arms and stopping rules

A. Keep three context calls, but evaluate KV-only views using exact compatible processed weights/scales; keep original kv_norm/insert and per-layer slots. No permanent duplication required under demonstrated layout.
B. Separately test one shared QuantizedActivation for identical main_x if every consumer has the same input quant key **and actual scale ABI/algorithm**; preserve original dtype/shape. Do not assume matching names alone prove equivalence.
C. Only afterA/B establish value, consider stacked512×3 output and batched normalization/insertion. Different layer weights, norm parameters, cache groups and slot maps must remain distinct; donor dense code's quantized fallback is material.

First verify source/live route and exact prepared-weight layout without starting GPU work. Later authorized component parity must include actual context KV bytes or numeric tolerances justified against baseline, draft acceptance/confidence and graph/eager/PAD slots, not just final target outputs. Reuse standard agent-p75/Mooncake for endpoint evaluation after correctness; extra instrumentation is for component attribution. Amdahl bound depends on exposed projection share and applies only to that share. Unknown share means deferred ROI, not immediate rejection or a forecast.
