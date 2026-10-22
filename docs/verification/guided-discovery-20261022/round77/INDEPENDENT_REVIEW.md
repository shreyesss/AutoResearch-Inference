# Independent review: round77 normalization reuse

**No blocker to the frozen zero-new disposition.** I read the author report, selected paper RMSNorm discussion/evaluation context, the pinned released RMSNorm code, target fused Q/KV normalization/quantization and mHC shared-intermediate branches. Independently verified all57 author artifact hashes and all6 exact source-revision quotes. No repository code, tensor/native package or GPU was executed; no new online query.

## What survives adversarial inspection

- The paper supplies a real cross-SM partial/reduce/partial method with on-chip retained partitions. Its normalization experiments use32K–80K widths. The inspected released `rms_norm` and `rms_norm_splitk` both launch one CTA per row group; the latter is a serial chunked loop within that CTA. Its name is not evidence of a distributed reduction. This is a scoped release-file finding, not proof the paper implementation never existed.
- Target Q1280/KV512 paths already retain loaded values through reduction and normalization; the eligible quantized Q arm explicitly casts through the original input dtype before group32 quantization. Gamma, epsilon and dtype differ from the ordinary released example, which cannot be substituted as-is. The fallback also loads gamma ahead of its PDL wait. These are source facts, not current-runtime frequency or optimality evidence.
- mHC coefficient statistics over4×5120 and collapsed-input normalization over5120 are different reductions. The inspected collapse kernel retains its weighted intermediate in shared memory. Crucially, only `save_pre_mix=True` accumulates squared sums from rounded BF16 values; its other branch sums FP32 `ol` before the BF16 shared store. The author incorporated this qualification before freeze. Both branches avoid the claimed HBM intermediate reload.
- The producer GEMM→norm boundary still exists. The author correctly does not claim generic fusion is already complete or infer a supported new GEMM epilogue from this RMSNorm example. That would need a concrete reduction/ownership/numerical adapter.

## Scope and remaining uncertainty

The body-only PR locators and donor timings are not native target validation. The paper has wider algorithms than the screened normalization component; none is rejected merely because it bundles a compiler. A genuinely exposed wide staged target operation or a compatible source implementation could reopen the retained component. Current evidence supports rejecting a direct substitution and parking the broader method, without another hypothesis identity or an invented CPU microbenchmark.

The review did not independently rerun searches, rebuild the released repository, inspect every PR diff or certify extracted PDF figures. Source identity/provenance, the observed retrieval failures and bounded PR coverage remain explicit in the author packet.
