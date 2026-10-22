# Independent OP36 source and numerical-contract review

**Verdict: retain one distinct deferred investigation. No implementation or service promotion.** The missing representation handoff is supported on the conditional Mega-attention path; neither the donor description nor upstream kernel capability establishes an exact, executable target adaptation.

## Scope actually reviewed

Read the pinned c455 target selection, Mega attention override, generic output-projection path, grouped linear loader, FlashInfer CuTe/CUTLASS consumers, native packed quantizer and forwarding wrapper. Read the retained DeepGEMM a7a einsum API, SM100 output epilogue, scale math and test source. Read the retained PR57977 2D consumer patch and full MF19 card. Executed only a standard-library scalar/layout counterexample script. Did not run upstream GPU tests, import serving libraries, select a device, compile a kernel, load a model, fetch new sources or modify runtime/canonical state.

## 1. Reachable path, and an initial review objection corrected

The generic `dsv41_o_proj` already has a small-row fused WO-A route. The exact config has64heads/8groups, so8heads/group satisfies that geometry; its calculated generic token threshold is32. That would be an important duplicate objection **if the generic method were used**.

Tracing the actual subclass resolves it: `DeepseekV4MegaAttnAttention._o_proj` directly allocates BF16 `z`, calls grouped `fp8_einsum`, and sends flattened `z` into `_wo_b_proj`. It does not call the generic small-row method. Mega already performed inverse RoPE and initial attention-output quantization, so adopting the whole generic kernel would redo those operations. The NVIDIA selector prefers Mega when its availability predicate holds, with explicit backend/PCP/platform exceptions. Source default is not an attested deployed backend. Keep OP36 conditional on that selected route.

Main-path dimensions support the proposed boundary:8 grouped4096→1024 projections followed by8192→5120. The removed logical BF16 store+read is32KiB per token; actual HBM/cache traffic and exposed latency remain unknown. Remaining FP8 payload store+read is16KiB per token before scales/padding. No multiplication by all model layers or speculative depth establishes service savings.

## 2. Existing primitive is real, but installation is unverified

DeepGEMM a7a supports FP8 `(d,sfd)` output for the exact expression `bhr,hdr->bhd`. It checks SM100, final output stride1, batch/group stride equal to output width, output width divisible128, and packed per32 int32 scales over the flattened group×rank columns. Contiguous `[M,8,1024]` data and `[M,64]` packed scales with token stride1/column strideceil4(M) fit these necessary layout rules. Group boundaries do not split scale groups or packed words.

Pinned vLLM's `fp8_einsum(*args, **kwargs)` forwards its arguments to the loaded dependency. This establishes no Python-wrapper obstacle, not proof that a serving image loaded the a7a API. Upstream tests inspect tuple output against DeepGEMM's own standalone cast at several batch sizes; they are test-source evidence, not tests executed in this review and not evidence of FlashInfer parity.

## 3. BF16 rounding survives; scale policy still disagrees

The SM100 epilogue explicitly rounds accumulators to BF16 before computing group amax and FP8 output. This preserves a necessary intermediate rounding boundary. It does not make distinct scale policies equal or guarantee the same GEMM tactic/reduction.

The exact source-formula counterexample in `contract_counterexamples.json` uses a group filled with the finite, exactly BF16-representable value2^-34:

- DeepGEMM's exponent floor105 means scale2^-22; normalized value2^-12 rounds to E4M3 zero.
- c455 native packed quantization floors **scale** at1e-10 after amax/448, rounding to exponent94 (2^-33); normalized value0.5 is representable and reconstructs2^-34.

The native helper also starts local amax at eps1e-10, but confusing that with its separate scale clamp would produce the wrong interpretation. The formula counterexample is not an observed target activation or a CUDA execution result. It refutes blanket equality from BF16 pre-rounding alone.

The current SM100 baseline dispatches quantization to external FlashInfer cute-dsl. Its installed implementation/version has not been established here. The local torch fallback's scale convention cannot stand in for that baseline. Zero, tiny values, ties, saturation and nonfinite behavior remain explicit contracts, not assumptions.

## 4. Activation and weight ABI

The generic `kMxfp8Dynamic` tag is not sufficient: Mega's existing packed DeepGEMM attention output and FlashInfer's F8_128x4 consumer both use that tag in different contexts. Directly wrapping tuple output with that tag can bypass the FlashInfer quantizer while supplying the wrong physical scale buffer.

Independent offset counterexamples make the mismatch concrete. With M2/K8192, row1/group0 maps to byte4 in the DeepGEMM packed buffer but byte16 in the FlashInfer swizzle. Further examples cover a group boundary and row32. These are layout-formula checks, not compiled-kernel verification. Reuse an explicit packed-layout key and compatible consumer, or account for a real conversion; never substitute a shape view.

PR57977's 2D DeepGEMM consumer and packed key are relevant reusable components. Current c455 only registers the DeepGEMM grouped BMM route in this MXFP8 family, while ordinary WO-B prefers available FlashInfer kernels. The donor consumes raw logical[N,K] FP8 weights plus per-row group32 scales, then calls the existing DeepGEMM postprocessor. Its route must be selected before FlashInfer transposes/swizzles parameters. Reinterpreting already processed FlashInfer weights/scales is unsupported. Checkpoint[32,32] scale-row expansion, preprocessed checkpoints, warmup, reload idempotency and graph buffer lifetime need explicit handling.

## 5. Controls and prior identity

Preserve the three-arm design:

1. Current BF16 handoff and FlashInfer consumer.
2. Same BF16 handoff, separate quantization under the **same agreed policy**, compatible converted DeepGEMM consumer.
3. Packed producer epilogue under that same policy and the same DeepGEMM consumer as arm2.

The donor's current packed helper and the existing DeepGEMM epilogue do not yet meet the shared-policy requirement. Until they do, arm2→arm3 conflates fusion and numerical changes. Likewise backend isolation from arm1 requires the actual baseline policy. Compare both projections and the next useful boundary; producer time alone cannot exclude a slower consumer.

MF19 explicitly excludes attention/WO-A changes and targets pre-FFN mHC/MegaMoE staging. This is a different producer/consumer boundary despite sharing PR57977 and a representation-elimination principle. Retain one OP36 direction, with any ComFuse cluster design as an unqualified alternative rather than another accepted card. Do not adopt stale PR-body claims as implemented code.

## Remaining gates

- Actual selected attention/linear classes, dependency version and processed weight ABI.
- Matching quantization semantics across all three arms, plus boundary-level differential checks and target output/quality contract.
- Correct owned payload/scale backing storage through capture, padding and consumer completion.
- Measured occurrence and exposed producer/consumer time under the frozen workload; contention, input quantization and consumer cost remain.

No speedup is inferred from C++ capability, logical bytes, a source-level rounding test or the donor's compound benchmark. Existing Mooncake and agent-75 remain the eventual service tests; ABI/numerical checks are additional correctness gates, not a new service workload.
