# Independent review: PJ01 context input quantization reuse

**Verdict: retain as the existing PJ01 optional arm, with implementation deferred.** The pinned source supports a real fan-out: three different projection weights receive the same context `main_x`. The two eligible FlashInfer Python consumers use the same `x.view(-1,K)` activation quantizer call and already accept prequantized input. Reusing that output can remove two calls per eligible context invocation without removing the three weight GEMMs, KV norms, RoPE/quantization or cache writes. This is a conditional source statement, not a measured kernel or service saving.

## What the evidence establishes

I read the pinned context body, both FI apply paths, QA capability/matcher, quantizer dispatch and fake shape function, ColumnParallelLinear forward, ModelOpt/default-format delegation, and the DFlash context graph/eager caller. The frozen source copies match the retained c455 tree. I independently checked all 38 artifact hashes and the 36 saved diagnostic event sequences, rather than rerunning the author script into its frozen directory.

The diagnostic executes actual extracted Python wrappers around symbolic inputs. For each supplied case it records three distinct weight consumers and matching norm/insertion events, with quantizer calls 3→1. It is meaningful control-flow evidence beyond a hand-written cost formula. Its tensor shape/layout metadata and nonmutating backend behavior are assumptions, so it does not prove byte capacity, FP8 equality, padding initialization, asynchronous safety or actual capture replay. The five fallback controls demonstrate the proposed diagnostic guard, not an existing complete production admission mechanism.

## Exact admission and ownership requirements

- Bind the selected complete module/format/kernel path, not only `kMxfp8Dynamic`. The actual matcher checks that key but not layout or padding. CUTLASS and CuTe wrappers consume F8_128x4; TRTLLM's separate quantizer/8x4 route is excluded. Preserve original dtype, full shape, K, value/scale strides and the selected quantizer's alignment. K5120 and raw source conventions are necessary, not live dispatch attestation.
- The SM100 quantizer wrapper calls external FlashInfer CuTe-DSL with alignment32 when default alignment is0. Reusing that exact output avoids inventing a new quantization rule, but external code/version, all padded scale bytes, nonfinites and consumer-read-only behavior remain unverified. Fake tensor shape functions and symbolic scale lengths are not that proof.
- Prepare once per exact `precompute_and_store_context_kv` invocation. The caller separately processes the eager tail and the FULL-graph prefix, and the hidden-state storage can change before graph replay. Do not share across those intervals or key a persistent cache only by tensor address. Preserve all-None profiling behavior: it still projects and normalizes all layers to establish workspace requirements.
- In a future adapter, compile/capture eligibility once for the loaded module set where possible; do not insert mutable Python policy checks into a replayed graph or assume weak references own data. The shared payload must survive all three asynchronous consumers, with buffer/lane/stream ownership and graph memory lifetime proven. Reevaluate eligibility after reload, wrapper, hook or backend changes. Keeping full query modules avoids the separate PJ01 column-slice/reload problem; it does not solve these ownership gates automatically.

## Materiality and experimental design

`20480*T` is a logical redundant input-read count, not HBM traffic; all GEMMs still read their own input and weights. Two fewer quantizer calls is not two removed service launches under arbitrary compilation, graph or scheduling behavior, and not five savings per speculative round. The larger live shared payload may change peak memory behavior. Component timing must include preparation and ownership costs.

The four-arm design is appropriate: full/original; full/shared-input; KV-only/original-quantization; KV-only/shared-input. It separates input sharing from removal of discarded Q columns; percentage gains must not be added. Source31986's quantized-weight fallback prevents treating its stacked-weight path as a direct port. AlignQuant's changed-weight policy is not supporting evidence for exact representation reuse.

The next decisive evidence is the actual loaded compatible consumer/layout and quantizer lifetime contract for the exact baseline; if unavailable, park implementation. Once hardware testing is separately authorized, payload/scales, three projection outputs, post-norm/RoPE/cache, confidence/sample outputs and graph/eager/reload behavior need differential checks before standard Mooncake/agent75 service evaluation. No new service workload or another metadata-only fixture is justified by this review.

No new hypothesis, status transition, numerical equality, target exposure, timing or service qualification is established here.
