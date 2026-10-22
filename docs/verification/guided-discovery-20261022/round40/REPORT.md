# Round40 — PJ01: a smaller existing-backend call, without a new weight owner

**Same PJ01 identity, implementation deferred.** This round checks a concrete adapter boundary for removing discarded draft-context projection columns. No numerical tensors, GPU execution, device probes, model loading, serving changes or canonical mutations occurred. No new hypothesis is counted.

PJ01 remains `hypothesis:f5836985004cdae101771b82988058329daca79464a067c9d33eac05925869c7` on its immutable `baseline:3b223afd8c30209a2c71d6f8cdd36e4da640b4bc67cdf331f108d2d2496131ca`. The source applicability discussion uses c455/Flash-1017; it does not replace that historical baseline identity or attest a running node.

## The decision-changing source observation

The earlier proposal contemplated creating a separate KV-only module after loader preprocessing and rebinding it after parameter replacement. The pinned FlashInfer CuTe and CUTLASS `apply_weights` methods provide a narrower interface: **N and K are read from the supplied current weight tensor, not from the kernel object's original config**. They need only `layer.weight` and `layer.weight_scale`. Their existing quantization, GEMM and output reshape already support that call shape at the Python interface.

A context-only adapter can therefore:

1. Keep the original complete fused Q|KV module, parameters and query-forward path intact.
2. On the context-precompute Python path, establish an exact eligible module/method/backend/layout contract.
3. Create views of the **current processed** weight and swizzled scale region. Do not call `process_weights_after_loading` again, create a second registered Parameter, or reload checkpoint shards.
4. Pass a lightweight weight/scale proxy into the existing kernel instance's `apply_weights`, obtaining512 output columns.
5. Continue the existing per-layer KV norm and cache insertion. None/profiling mappings still run the projection and norm; query projection still computes1792 columns.

This removes a separate module's loader/schema/parameter ownership problem. It does **not** prove the underlying smaller GEMM is faster or numerically equivalent.

### Exact backend view contract

| Current processed backend | Existing weight | Context-only view | Existing scale slice |
|---|---|---|---|
| `FlashInferCutlassMxfp8LinearKernel` | [1792,5120], stride[5120,1] | `[1280:1792,:]`, contiguous [512,5120] | flattened uint8 `[204800:286720]` |
| `FlashInferCutedslMxfp8LinearKernel` | [5120,1792], stride[1,5120] | `[:,1280:1792]`, column-major [5120,512] | same F8_128x4 byte slice |

The prior81920-offset check already established the aligned scale region; it is retained, not rerun as new validation. New here is actual execution of the unchanged **Python backend bodies** showing that the smaller views reach `mm_mxfp8` with B=[5120,512], unchanged input quantization and no extra `.contiguous()` copy on the tested metadata layouts.

## Guards and boundaries

Initial eligibility must be explicit and narrow:

- Exact unwrapped merged linear, exact `ModelOptLinearMethod`, exact no-op `FormatScheme`, and one of the two inspected kernel types. A format wrapper can change semantics even with an identical quant key.
- Replicated `disable_tp=True`, TP size1, no bias, unchanged return tuple semantics and expected5120→1792 split. No forward hooks, global/module adaptation hooks or LoRA wrapper may be silently bypassed.
- Exact postprocessed weight dimensions/strides/dtype and flattened uint8 F8_128x4 scales. A shared `kMxfp8Dynamic` key alone does not establish layout, as round36 demonstrated.
- Actual `main_x` input contract, dtype/device and weight/scale placement still need runtime verification. The CPU stubs do not test these.
- Unsupported geometry/backend/wrapper uses the original call and slices its output; it must not reinterpret TRTLLM-shuffled weights or another backend by name similarity.

The diagnostic adapter uses stand-in exact type identities and a simplified hooks field. It is not installable production code and is not a complete validator of PyTorch hooks, compilation, tensor subclasses, devices or ownership. A real implementation must express these guards with actual module/type identities and normal execution lifecycle.

### Reload and graphs

Using current owner tensors each Python invocation avoids a stale cached Python view after parameter replacement. The probe verifies owner replacement between calls. That does **not** update an already-captured CUDA graph, because replay does not reconstruct Python views. Refits/reloads that change storage must invalidate and recapture affected graphs using the serving runtime's existing lifecycle; no new guarantee is claimed here. No snapshot of pointers should be cached across runs.

The loader already documents parameter replacement and reconciles replicated TP metadata after preprocessing. The proxy neither registers a new parameter nor invokes the loader, so it avoids duplicating that responsibility. It still depends on the original module having reached its final prepared layout (including preprocessed-weight loading).

## What actually ran

Command:

```sh
PYTHONPATH=ideation .venv/bin/python /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/round40-pj01-contract/invocation_probe.py
```

-12 wrapper cases: two backend classes × rows0/1/8/16/32/65. Extracted `input_quant_key` and `apply_weights` bodies are unchanged; constructors/imports and native calls are replaced by explicit CPU metadata/call stubs.
-Each candidate call reaches B=[5120,512], the retained weight/scale owner and correct offsets; one input-quantizer call remains. Original full call reaches B=[5120,1792]. No candidate `.contiguous()` branch is taken under those metadata conditions.
-Two config-access-denied controls confirm these extracted methods do not consult the original full-width kernel config.
-Parameter replacement control uses the new weight/scale owners on the next Python invocation.
-Six negative eligibility controls route to the original full call: format wrapper, bias, TP partition, forward hook, wrong scale layout, wrapped module. These test proposed guards, not real hook/LoRA execution.
-Six context-control cases: two backends × None/all/middle-None mappings. The unchanged context method is compared with a two-statement proposed substitution. Three per-layer GEMM calls become N512, three input quantizers remain, and norm/insertion **control records and shapes** match. No norm values or cache bytes are computed.

Zero rows only exercises Python metadata handling; it is not a claim that the external GEMM supports empty launches. The fake GEMM returns shape-only output. Therefore none of these observations is numerical correctness, GPU allocation/capture validation, runtime support, timing or service improvement. We deliberately did not repeat nominal MAC arithmetic as new evidence.

## Remaining decisive evidence

The previously audited52 local metadata files and retained benchmark compatibility matrix do not contain a compatible c455/Flash-1017 selected-backend/processed-tensor manifest or attributable context-projection trace. This round reuses that bounded audit, not a new comprehensive filesystem/S3 search. Older unsuffixed Flash/H200/C025 records can inform workload and evaluator design but cannot supply current exposure or numeric equivalence.

The smallest next implementation diagnostic, **only after separately authorized GPU work**, is one actual eligible layer: original complete projection's512-column KV slice versus the view-proxy call on identical quantized input/weights, through post-norm and KV storage, before testing all three layers and graph/eager/refit paths. Different output width can change GEMM tactics/reduction rounding; equal selected weights do not prove equal draft proposals/confidence/acceptance. Keep target-only correctness and accepted progress separate.

Existing Mooncake and agent-p75 remain the right later service workloads. Record actual captured rows and eager tails, selected kernel, quant/projection/norm/cache timings and exposed critical path. No new endpoint evaluator or numerical gain threshold is invented. No service gain or ITL bound can be computed from the current evidence.

## Outcome and next action

**Positive, bounded refinement:** a separate registered KV module is unnecessary for the two inspected backends; the existing backend interface can accept the view proxy without using stale full-width config. The first useful consumer, per-layer KV norm, receives the intended512-column shape, and cache-write control is retained.

**Not closed:** numerical/backend feasibility, graph lifetime after refit, installed dispatch and exposed duration. Keep PJ01 deferred. Stop adding address/shape simulations: the remaining question needs actual prepared tensors or a retained compatible record. No fresh paper query was needed for this existing strongest candidate; another citation would not settle this interface or exposure gate.
