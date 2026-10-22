# Independent source review — expert-output combine representation

**No blocker to the explicitly deferred research disposition.** Final review checked the frozen 64-file author packet (manifest bba5ad26c3d8f5e78989015c7233597e13a93f275aeec6fd946531ba99d391c3), eight exact source-revision quotations, report and candidate. No native/tensor/GPU execution, model loading or compilation.

## Source findings

The selected donor component is separable from W4A4. `use_fp8_combine` is independently passed through allocation and kernel dispatch; the FP8 activation arm supports fused shared experts while the new FP4 activation arm excludes them. This supports selective implementation design, not executing the whole donor or importing its benchmark gain.

The producer loads FP32 TMEM output, rounds it through `cast_into_bf16_and_pack`, stores BF16 in shared memory, then rereads that BF16 before group scaling and FP8 conversion. Thus a faithful selective arm must preserve this BF16 boundary. The new FP8 transport is still lossy; frozen weights do not imply identical target logits, output distribution or tokens. Strict exact-output admission fails unless a separate exact reconstruction/fallback is supplied; no such exact codec is present in this donor.

Each half warp gathers eight BF16 values per lane, reduces amax over16 lanes, and writes128 FP8 values with one UE8M0 scale. `BLOCK_N == 128` is asserted, matching one scale per output n-block. H5120 satisfies the source divisibility constraint and forces two chunks because hidden>4096; each2560-element chunk has20 groups. These are geometry checks, not compilation, shared-memory resource, performance or EP4 runtime validation.

The current a7a target differs materially from the donor scheduler: target token-chunk work distribution, shared-first FP32 accumulation, local grid synchronization, per-peer readiness release/acquire and selected-rank wait must remain. The older donor uses a global NVLink barrier and routed-first accumulation. A whole donor transplant would add those unrelated changes. New payload and scale stores must both complete before the target readiness notification and remain alive until the same consumers retire. Shrinking TMA payload bytes without matching barrier transaction counts, scale indices and workspace layout is invalid.

The target finite FP32 combine order matters even before additional FP8 loss. The decoder also needs explicit behavior for zeros, subnormal scale computation, nonfinite inputs and scale overflow. Source fast exponent helpers are not a comprehensive numerical contract. Independent source inspection does not certify these boundaries.

## Cost and evidence limits

For H5120, raw encoded values plus40 scale bytes occupy5160 bytes versus10240 BF16 bytes per encoded partial, before alignment/allocation. This is a logical representation comparison, not measured NVLink traffic or latency. Only actually remote routed slots save inter-rank payload; shared output and locally routed slots still incur conversion when enabled but are local. Top6 plus shared means seven allocated slots, not seven guaranteed network transfers.

The donor documentation compares revisions that both already use FP8 combine with native MXFP4 activations on GB300. Their speedup does not isolate combine compression and cannot be transferred to B200. The retained single-rank test has H2048/top2/no shared; its tolerated reference differences are not target EP4/shared correctness evidence or exact-output certification.

## Final numerical and adapter judgment

The author finite control is sound within its stated scope. Exactly BF16-representable partials129/128 and−1 with group scales1/256 normalize to258 and−256; ideal E4M3 rounds258 to256. Baseline FP32 addition then BF16 gives1/128, while compressed reconstruction gives0. These simple values introduce no ambiguous FP32 addition or final BF16 rounding. This is a representational non-losslessness witness, not evidence these activations occur in the target or a prevalence estimate. I inspected the rational construction and checked its arithmetic; no native converter or author experiment was executed by this reviewer.

The final report correctly requires actual numerical/generated-output admission and does not invent a task-quality tolerance. Finite prompt equality alone would not prove general distribution equivalence; the candidate explicitly makes no lossless target-distribution claim. If the governing task requires a universally exact numerical transformation, this source already rules out the direct lossy codec. The deferred entry must retain that boundary and cannot be promoted merely through small average tensor error or unchanged weights.

The target adapter lacks a combine-format argument and omits that format from its symmetric-buffer cache key. The final report now requires a static format-specific owner key, consistent allocation/JIT/consumer parameters and invalidation/recapture of old graphs if layout changes. The checkpoint says expert_dtype=fp4 with dynamic FP8 and one shared expert, consistent with the narrowly selected source arm; live dispatch remains unattested. Keeping current router weights/policy does not certify later expert selections after perturbed activations.

The selected RAC paper contributes explicit codec cost/quality discipline, not a compatible trained reference predictor or NVLink speed forecast. I read the retained codec description and checked the predictor source quote. I did not rerun provider queries, certify search completeness, inspect every unrelated PR patch, or test codegen/resources. One deferred author proposal is justified as a distinct conditional intervention; no implementation or service qualification, native validation or new typed identity is established by this review.
