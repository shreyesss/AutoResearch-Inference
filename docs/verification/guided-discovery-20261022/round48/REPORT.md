# Round48 — reuse DSpark context activation quantization

**Existing PJ01 refinement, zero new identities and no status promotion.** Source and CPU control evidence supports a bounded optional arm: quantize the common context input once per invocation and reuse it across the three compatible FlashInfer projection consumers. Actual device numerical equality, selected backend, capture ownership and latency remain unverified. No GPU/native backend imports or serving changes occurred.

## 1. What repeats, exactly?

Pinned [DSpark context method](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/nvidia/dspark.py)165–195 passes the same `main_x` to every draft layer's `fused_wqa_wkv`. The weights differ. Each output's query columns are discarded; each retained KV portion receives that layer's norm, RoPE/quantization and cache insertion. The proposed shared operation is **input activation quantization before these projections**, not the subsequent layer-dependent KV quantization. It preserves all three norms and caches, including the profiling behavior where `slot_mapping=None` skips only insertion.

Exact model metadata establishes three draft layers, hidden5120 and merged output1792 (Q1280+KV512). Source routing under native [32,32] UE8M0 scale config selects dynamic ModelOpt MXFP8 for eligible linear modules; ignored/unquantized or alternate model formats are outside this initial arm. Live loaded dtype/backend selection is not attested.

Both [FI CUTLASS and CuTe apply methods](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/model_executor/kernels/linear/mxfp8/flashinfer.py) perform the same fallback:

```python
input_mxfp8, input_scale = mxfp8_e4m3_quantize(
    x.view(-1, K), is_sf_swizzled_layout=True
)
```

The arguments depend on `main_x`, K and the fixed activation layout, not projection weights. Both also already accept `QuantizedActivation`, consuming its data/scales and original dtype/shape without that fallback call. Thus no new quantizer algorithm or precision is needed for this arm. On SM100 the helper calls external FlashInfer's CuTe-DSL quantizer; the torch fallback is not proof of the deployed quantizer.

## 2. Admission and lifetime contract

The existing [QA abstraction](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/model_executor/layers/fusion/quant_activation.py) exposes a capability key and hides it when a module requires unquantized input. Its explicit TODO says layout and padding are not encoded in that key. **Matching `kMxfp8Dynamic` is insufficient.** Initial eligibility must bind the exact FI CUTLASS/CuTe consumer implementations, F8_128x4 scale convention, K5120, original dtype/shape and compatible module/format wrappers. TRTLLM uses 8x4 scales and cannot be admitted by a general “MXFP8” test. Unsupported consumers, hooks requiring original input, LoRA/wrapped behavior and inconsistent layer metadata must retain original execution.

Audited Python wrapper chain is `ColumnParallelLinear.forward → ModelOptLinearMethod.apply → FormatScheme.apply → FI.apply_weights`. Default format passes the activation unchanged; the linear is replicated/disableTP and requires no input tensor collective. Other format hooks or future subclasses need their own admission, not structural name matching. The CPU probe's stand-in types are not production admission code.

Reuse scope is one context invocation, not a cache keyed by `main_x` pointer. The persistent input buffer changes contents each proposal. Full-graph context prefix and eager tail are distinct intervals/invocations; each needs its own quantized payload. No saved descriptor is reused across those boundaries or across requests. Three consumers may share the payload only while data and scale buffers remain valid and unchanged until all consumers finish. Python references and source-level read use suggest a feasible ownership scheme; external backend mutation/scratch behavior, stream ordering, CUDA graph allocator ownership and replay lifetime were not executed.

The existing graph path captures context work in `_prepare_graph_forward`; eager tail work is performed separately before replay. This is not a claim that ordinary torch.compile CSE automatically removes these calls. The audited context method contains no shared QA object; existing prequantized-consumer support does not itself activate reuse.

## 3. Prior comparison and useful donor limits

PJ01's frozen round12 report already listed “share one quantized main_x” as an optional later arm. This round gives that arm a concrete compatible consumer path; it is **not another discovery**. Keep the original full merged modules for query execution. Input sharing can be evaluated with full projections independently of PJ01's KV-only columns.

- **PJ01:** avoids dead Q output columns. Sharing removes two repeated input-quantization calls; factorial controls separate the effects. No additive percentage prediction.
- **OP36:** moves quantization into a producer epilogue and changes downstream backend/scale ABI. This arm instead calls the original quantizer once and reuses its output; no donor scale-floor substitution.
- **EG01:** bypasses raw Engram FP8→BF16→FP8 staging, with representation/rounding questions. This arm starts from the same BF16 `main_x` and keeps its original quantization policy. EG01's warning that keys omit layout still applies.
- **R2-03:** skipping draft query work can change confidence/RNG. This arm retains every projection/query/norm/cache and sample; it only changes reuse of an input representation.

[Retained SGLang31986](https://github.com/sgl-project/sglang/pull/31986) stacks per-layer context projections. Its exact retained code `_stacked_ctx_kv_params` refuses non-sliceable/quantized weights. Its shared-input observation supports the dependency reasoning, but this is not a direct port or a donor performance claim. No new freshness query was made for that already retained revision.

## 4. Actual adaptive tool use

Fresh isolated state; complete compact prior inventory and PJ01 dossier retained. After the source gap survived, `expand` and one actual arXiv query searched activation quantization + reuse/sharing/fusion for LLMs, August through October22. It returned one paper, **AlignQuant2610.07457**. Abstract screening found a changed weight-precision allocation scheme, not this exact activation fan-out component. No relevant paper claim is fabricated and no broad synonym retry was justified.

Three local FTS queries were noisy. A title-limited query clarified available fusion work but its newest50 cap omitted known31986; exact-ID selected import recovered it without HTTP churn. Full returned hit lists, title screens and source reuse are retained. Most PR hits were screened by title, not technical rejection of their implementations. Source/code was more useful than a second paper query here.

## 5. CPU control evidence and its limits

`quant_reuse_probe.py` extracts unchanged Python bodies for the native context method, both FI input-quant/apply methods, QA matcher/capability check, ColumnParallelLinear forward, ModelOpt apply and default format apply. It strips decorators/imports and uses symbolic tensors, quantizer and GEMM stubs. A declared diagnostic two-site modification prepares shared input and passes it to the projection call; no production source is edited.

- 36 cases: CUTLASS-only, CuTe-only and mixed compatible backend sequences; rows1/8/32/129; normal, partial-None and all-None mappings.
- Actual Python quantizer call count changes **3→1**; three distinct weight/scale consumers remain. Norm and insert control events agree.
- Five fallback controls: unquantized-input requirement, same-key/wrong-layout, different key, observing hook and incompatible width.
- Actual matcher accepts a same-key descriptor without checking layout, demonstrating why the extra layout guard is needed.
- Two consecutive invocations with the same symbolic input address quantize twice; there is no cross-round memoization.

These are invocation/control checks, not 36 numerical or GPU tests. The symbolic quantizer invents payload identities and scale capacity metadata; it does not compute actual FP8 values, exact padding or scale bytes. Mixed-backend compatibility is a wrapper-ABI observation, not measured backend parity. Zero-row device behavior, nonfinite handling, races, buffer aliasing and graph replay remain untested. CPU result is **inconclusive for implementation/service qualification**.

## 6. Conditional work and future evaluation

If all three projections use the audited paths, each context invocation can remove two quantizer calls. For T rows of BF16 hidden5120, the two redundant input reads amount to `2*T*5120*2 = 20480*T` logical bytes, plus redundant quantized-value/scale stores whose physical padding must be measured from the selected quantizer. This is not HBM traffic or elapsed time. Each GEMM still reads its input, all three weights and weight scales remain, all projections remain in the sharing-only arm, and layer-dependent KV work remains. Peak allocation can rise because one payload stays live until the last consumer; pointer reuse is not free lifetime proof.

Conditional exposed-time bound per invocation is at most the two removed quantizer durations, minus new preparation/admission/lifetime overhead. Their critical-path contribution is unknown; graph execution, small row count and existing scheduling can make service savings negligible. Do not multiply by five speculative tokens: context calls depend on the proposer and graph/eager partition, not one preparation per emitted draft position.

When GPU work is separately authorized: first compare original-vs-shared FP8 payload/scales and all three projection outputs under exact selected backend, then post-norm/RoPE/KV, draft/confidence outputs and repeated graph/eager/refit behavior. Preserve original full query module. Four controls: original full projections; full+shared-input; KV-only original quantization; KV-only+shared-input. Include padded rows, changing row counts and profile/None mappings. Component timing includes descriptor/quantization ownership costs; unprofiled service runs retain standard Mooncake and agent-p75. They already exercise this path when native DSpark is active; no new custom serving workload is justified. They do not replace targeted numerical/lifetime differential tests.

**Decision:** retain as a sharper PJ01 optional arm, implementation deferred. No model/weight change, new identity, accepted service claim, estimated percent gain or GPU experiment.
