# Independent round40 PJ01 invocation review

**Verdict: retain this bounded refinement on the same PJ01 identity, implementation deferred. No blocking factual correction.** The existing backend accepts dimensions from the supplied tensors, so a view proxy is a plausible smaller integration surface than a separately registered linear module. No numerical, native execution, graph-lifetime or performance qualification follows.

## Independently checked

- Verified all19 author-manifest hashes, read the report and complete probe, then read pinned FlashInfer CUTLASS/CuTe `apply_weights` and preprocessing bodies, DSpark context method, `ModelOptLinearMethod.apply`, default `FormatScheme.apply`, linear forward and the attention constructor.
- The real methods derive N/K from `layer.weight`, consult only weight/scale on the supplied proxy, and do not read kernel.config. Default FormatScheme delegates unchanged. Replicated merged Q|KV construction sets disable_tp=True and bias=False; the ordinary linear forward gathers only if TP>1 and preserves optional tuple return.
- CUTLASS takes [N,K], makes it contiguous only if necessary, then transposes. The proposed [1280:1792,:] view is contiguous for the stated final layout. CuTe already stores [K,N] column-major; selecting columns1280:1792 preserves that layout and owner. The flattened scale region is inherited from earlier reviewed F8_128x4 offset proof, not independently validated by this new invocation fixture.
- Replayed a reviewer-local copy of the unmodified author metadata probe. Its JSON exactly matches:12 wrapper cases,6 guard fallbacks,2 config-denial cases, parameter-owner replacement control and6 context-control cases. Only unchanged Python method bodies are executed. Torch/native imports are absent.
- Context loops retain all three per-layer projections/norms, including None/profiling mappings; only eligible GEMM width changes to512. Query-forward full module is not replaced in this proposed design.

## What the fixture cannot establish

The fake tensors and GEMM return shape/stride/owner labels; they do not allocate device memory, prove storage aliasing in PyTorch, validate dtype/device/quantization representation, execute norms/cache insertion, or select/benchmark a real smaller GEMM. Zero-row Python shape passage is not empty native GEMM support.

Exact stand-in types and a simplified hooks list are a proposed guard demonstration, not actual runtime admission. Real module hooks, global hooks, tensor subclasses, instance forward overrides, LoRA/compilation wrappers and loader state need actual checks. The fake fallback calls demonstrate which branch is chosen; they do not reproduce real bias/wrapper behavior. These limits are disclosed by the author.

None/profiling mappings still running projection and norm does **not** prove equivalent workspace reservation: the smaller N may allocate/cache a different native tactic/workspace. Existing full-width query warmup might cover that need, but this was not shown. Keep profiling/capture workspace ownership as an implementation gate.

Fresh views on each Python call correctly avoid the specific stale Python-owner cache illustrated by the fixture. Captured graph replay does not re-execute that Python view creation; weight refit/replacement needs existing runtime invalidation/recapture. No fresh-view claim should bypass that lifecycle.

A different output width can change GEMM tactics/rounding despite selecting identical weights. Only actual prepared-tensor comparison through norm and cache writes, followed by proposal/confidence/acceptance checks, can close numerical feasibility. Actual installed backend and exposed duration remain absent. Repeating address arithmetic or adding a paper would not resolve those gaps.

## Scope

No GPU, device availability call, native build, model, serving patch or canonical write. The independent replay validates the retained CPU metadata receipt, not a second numerical experiment. Original science artifacts untouched.
