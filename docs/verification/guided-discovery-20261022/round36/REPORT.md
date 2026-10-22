# Round36 — preserve the low-rank output chain, remove its representation round trip

**Disposition:** OP36-01 is a distinct **deferred** output-projection intervention. No GPU/model/native backend imports, patch, benchmark or performance claim. Planned Flash-1017, c455, TP1/DP4/EP4; actual loaded backend/dependency versions remain unattested.

## What changed our decision

1. Compact recall of all pages and the full MF19 card plus linked research confirms MF19 is pre-FFN symmetric-input staging. Its card explicitly excludes WO-A changes; round29 refines the small-row mHC producer. OP36 shares a donor citation and representation principle but changes a different producer/consumer path. It is not a novelty claim or a second count of MF19's implementation.
2. Initial recent OpenAlex query mixed low-rank model changes, diffusion kernels and compiler work. A second agent-authored query relaxed low-rank terminology to back-to-back GEMM scheduling. All results and read depths are preserved. ComFuse's full text describes the relevant tile-production/consumption mismatch and cluster partial reductions. It cautions against treating an intermediate as free to remove; its whole compiler is not adopted.
3. Target MegaAttention already fuses inverse RoPE and FP8 attention output. Its override `_o_proj` still writes BF16 grouped WO-A output and then calls WO-B, which quantizes it again. The alternative non-Mega `dsv41_o_proj` already fuses small-row inverse-RoPE/WO-A/output quantization. That threshold does **not** govern the Mega override. Initial scope is Mega only.
4. Local PR search finds #57977 describing precisely an FP8 WO-A handoff. But its retained head18aac398's actual19-file patch does not modify Mega `_o_proj`, add `fp8_z`, or request packed WO-B input. The body is stale relative to that retained diff. Its 2D DeepGEMM consumer/typed packed-layout machinery is reusable code; the advertised WO-A integration itself is not verified implemented there.
5. Actual pinned DeepGEMM a7a supports tuple FP8 output for exactly `bhr,hdr->bhd` and rounds to BF16 before quantization. This is a concrete existing primitive, stronger evidence than the PR prose. However its scale floor differs from the donor's separate quantizer, so a turnkey exact port is **not** established.

## OP36-01 mechanism and smallest credible adaptation

Pinned `flash_mla_mega_attn.py:212–236` allocates `z[tokens,groups,o_lora_rank]` BF16, runs grouped `fp8_einsum`, then sends `z.flatten(1)` into `_wo_b_proj`. For the configuration this is8groups×1024=8192 intermediate values per token. Main hidden width is5120. The existing FlashInfer consumer `apply_weights` accepts BF16 and invokes `mxfp8_e4m3_quantize` before GEMM.

Adapt only the grouped producer output and its next consumer: use DeepGEMM's already-supported FP8 `(z, scale)` epilogue, retain the BF16 rounding boundary, pass an explicitly packed-layout activation into a compatible 2D DeepGEMM WO-B. Retain both factor matrices and their trained weights. Do not change attention support, inverse RoPE, DSpark, routing or mHC. Preserve all fallback branches.

This can remove the BF16 intermediate store and subsequent quantizer read (32KiB/token logical store-plus-read count by source shape; not measured HBM traffic), and the separate activation-quant launch if no replacement conversion is added. The FP8 intermediate write/read and scale traffic remain. Quantization arithmetic moves into the producer; it does not vanish. Backend conversion, extra epilogue instructions or a slower WO-B can erase the savings. First useful consumer is WO-B; its result is consumed by the existing post-attention mHC/FFN boundary. No claim that this is the dominant service path.

### Exact producer API and graph layout

`csrc/apis/einsum.hpp` at a7a accepts a tensor or `(d,sfd)` only for `bhr,hdr->bhd`. It permutes data's token/group dimensions while preserving flattened scale columns. It requires arch major10, last output stride1, group stride equal to output rank, rank divisible128, and packed int32 per32 scales with flattened dimension `groups*rank`. Contiguous `[M,8,1024]` payload satisfies the static layout. Rank1024 is divisible128, so a packed four-scale word does not cross a group boundary.

Upstream `tests/test_einsum.py` shows scales shaped `[M, ceil(8192/128)]` with stride `(1,align(M,4))`, and checks the tuple output against its own BF16-output-plus-DeepGEMM-cast reference. Those upstream tests are source evidence; we did not run them, and they do not establish parity with FlashInfer or vLLM's different standalone quantizer.

Use graph-stable PyTorch-owned payload/scales through existing allocation/capture conventions, preserve the full required backing extent and alias lifetime until WO-B completes. Verify zero/padding rows and metadata in actual compiled graphs later. No runtime source override was loaded to attest this API is installed.

### Activation ABI is not a shape view

DeepGEMM scales are packed four UE8M0 bytes per int32 with aligned token stride. FlashInfer expects a flat F8_128x4 swizzled uint8 buffer. The existing broad `kMxfp8Dynamic` tag appears in both contexts and is insufficient by itself. **Never label the tuple with that generic key and pass it to the unchanged FlashInfer WO-B.** Reuse donor's `kMxfp8DynamicPacked` and exact consumer guard, or an equivalently explicit layout contract. A separate repack kernel would alter the proposed launch/traffic saving and needs its own comparison.

### Weight loading and ownership

Target checkpoint scales are [32,32] UE8M0. ModelOpt's scale loader repeats each checkpoint scale row32 times into per-output-row group32 scales; it registers weights `[N,K]` and scales `[N,K/32]`. Current FlashInfer CuTe post-load transposes weights to `[K,N]` and swizzles scales. The donor DeepGEMM 2D kernel instead invokes the existing `deepgemm_post_process_fp8_weight_block(...quant_block_shape=(1,32), use_e8m0=False,is_bmm=False)`, retaining FP8 payload while repacking scales for its consumer.

Select the compatible kernel **before the original post-load conversion**, and request/expose the packed input key there, following donor's ModelOpt hook. Do not reinterpret already transposed/swizzled FlashInfer parameters as raw weights or transform an active serving layer in place. Initial scope excludes preprocessed-weight checkpoints and runtime reload unless their conversion/idempotency contract is explicitly supported. Startup allocation/ownership and warmup registration belong to the adapter. No extra dense merged matrix or permanent duplicate weight copy is proposed; transient loader/scale allocations still need accounting. Dependency/API pin and actual model/kernel class must be checked before execution.

## Numerical boundary that blocks a ready-to-run claim

| Property | Source evidence | Remaining boundary |
|---|---|---|
| Intermediate rounding | DeepGEMM store epilogue rounds FP32 accumulator into BF16 pairs before group amax/FP8 | Necessary; changed GEMM tactic/reduction can still change BF16 values |
| Scale domain | Group32 UE8M0 in both producer and proposed consumer | Packed layout differs from FlashInfer; exact layout adapter required |
| Tiny-value floor | DG epilogue minimum scale exponent105, i.e.2^-22; vLLM packed standalone additionally clamps **scale** to1e-10, rounded to2^-33 (byte94) | Different algorithms; upstream own-helper test does not resolve it |
| Zero | Payload zero may agree, while minimum scale byte differs | Require explicit scale policy, not only dequantized-value comparison |
| FP8 conversion | DG uses packed BF16→E4M3 conversion; native helper has its own multiply/convert path | Tie rounding, saturation, signed zero, NaN/inf and subnormal behavior not certified here |
| Current baseline | SM100 `mxfp8_e4m3_quantize` explicitly delegates to external FlashInfer cute-dsl | Installed FlashInfer implementation/version not pinned in this packet; torch fallback is not baseline proof |

`contract_bounds.py` actually executed only scalar formulas and shape accounting. A group of exact BF16 value2^-34 yields DG exponent105 and normalized2^-12, below half the E4M3 minimum subnormal; the packed standalone formula yields exponent94 and normalized0.5. Thus the first rounds to zero while the second is representable. This is a legal formula counterexample, not an observed target activation or CUDA run. It falsifies blanket parity based solely on preserved BF16 rounding.

A separate scalar example gives258 versus256 if an intermediate BF16 rounding boundary is removed. It is illustrative of why algebraic merging is not generally bit-identical, not a test of actual target weights.

**Required adaptation:** first establish the original baseline quantization policy; then make the separate-quant control and producer epilogue use the same policy. If the existing DG epilogue cannot express it, a narrow epilogue change and its differential tests are required. Alternatively classify any intentional numerical change openly and evaluate it under an explicitly authorized quality contract. Do not quietly change the target policy to make the optimization easier.

## Three-arm future experiment

A. Original Mega WO-A BF16 output → original FlashInfer quantization/WO-B.

B. Same WO-A BF16 output → separate quantization with **the agreed identical policy** → converted DeepGEMM WO-B. This isolates backend/weight-layout changes. The donor's default packed helper does not automatically qualify as this control because of its scale floor.

C. WO-A epilogue emits packed FP8 under that same policy → same DeepGEMM WO-B as B. B→C isolates producer handoff; A→C is the service intervention. The upstream PR's compound TP4 speedups are not an estimate for any arm.

Before performance, compare payload/scales/output through every boundary, tiny and zero groups, exponent/tie boundaries, nonfinite policy, ragged/group stride and captured shapes, output hashes and target-only greedy equality. Record actual upstream test scope separately. Later paired graph timing must include both WO-A and WO-B and the next useful boundary, because a faster producer with a slower consumer can regress overall. Existing Mooncake and agent-75 are the serving tests with frozen long-output ITL and separate tail/TTFT/error guards. They do not replace the new ABI/quantization differential. No new custom serving workload is justified yet.

## Other components retained rather than overclaimed

- ComFuse B2BGEMM cluster partial reductions: theoretically reuse intermediate tiles on-chip, but target grouped WO-A output must feed dense WO-B across8192 contraction elements, with group32 quantization and BF16 boundaries. Cluster partial reductions change accumulation order; output tiling can duplicate producer work or add reduction/storage. No ready exact implementation was identified. Retain as a deferred design alternative within this lane, not a second qualified hypothesis.
- Merge WO-A and WO-B into one dense weight: rejected as scoped. Factored coefficient count is33,554,432+41,943,040=75,497,472; dense32768→5120 has167,772,160,2.22× more coefficients before precision/scales. Removing intermediate quantization is not algebraically exact. Fewer launches alone does not justify this change.
- Adopt non-Mega fused WO-A directly in Mega path: rejected as a direct port. It accepts BF16 heads and performs inverse RoPE/input quantization already fused in Mega; doing these again changes semantics or repeats work. Its output-quantization component can inspire an adapter, but its whole input pipeline is not interchangeable.
- INT8 diffusion, pruning/KV-low-rank, all-reduce and cross-SM compiler results were screened; none justify changing frozen weights or importing donor performance. Reusing ComFuse is a deeper read of an existing source, not an independent discovery count.

## Tool use and yield

Two actual online paper queries; retained all hits and duplicate identities. One fulltext read plus four exact pinned dependency files through `investigate`. Three bounded whole-corpus read-only PR queries and an actual isolated subset `pr-search` replay; replay does not add corpus coverage. One failed invocation used wrong CLI option placement; help corrected it before any provider work. A local subset-import helper used nonexistent `upsert`, leaving an empty-scope search receipt; retry with `put` succeeded. Both failures are retained, not counted as scientific zero hits. One distinct deferred OP36 intervention, no accepted implementation or service win. No canonical writes or publication claimed.
