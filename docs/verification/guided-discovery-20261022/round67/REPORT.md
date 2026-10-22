# Round67 — PJ01 capture preparation and minimal handoff

**Same PJ01 identity, zero new hypotheses. No implementation or service qualification.** This source-only round resolves one integration question: the native DFlash graph manager already warms the context-preparation callback before recording the same callback. A separate PJ01 warmup framework is not justified by the inspected source. The unresolved external FlashInfer workspace, actual prepared tensors, numerical behavior and runtime exposure still prevent claiming an executable or beneficial implementation.

Hypothesis: `hypothesis:f5836985004cdae101771b82988058329daca79464a067c9d33eac05925869c7`. Original immutable baseline: `baseline:3b223afd8c30209a2c71d6f8cdd36e4da640b4bc67cdf331f108d2d2496131ca`. Canonical read-only dossier remains **deferred**. This round does not alter its baseline, card or decision.

## Question and prior coverage

Read rounds12,14,40, the independent round40 review, the current read-only dossier, and later round48. Round40 already established the guarded processed-weight views and Python consumer ABI; repeating its 81920 scale-offset equations or metadata-tensor cases would add little. Round48 already covers optional three-to-one activation quantization reuse. Round14 removes eligible context rows and is a separate intervention.

The independent round40 review left a precise question: does retaining projection/norm on None/profiling inputs establish native workspace reservation after reducing N? It does not. This round follows actual warmup/capture routing to narrow the handoff instead of assuming full-query warmup covers the smaller projection.

## Source result: existing callback covers the candidate shape

Exact source is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; retained files and URLs are in `source-manifest.json`.

1. `dflash/speculator.py:169–188` marks context slot mappings PAD, then calls the graph manager with `prepare_forward=self._prepare_graph_forward`.
2. `_prepare_graph_forward:190–206` calls `_precompute_context_kv(0, num_context)` without the dummy override. The helper at379–396 therefore passes actual mapping tensors, potentially containing only PAD values. PAD suppresses cache writes; it is not a missing projection or a Python None sentinel.
3. `dflash/cudagraph.py:106–155` builds a closure that invokes `prepare_forward(num_reqs, attn_metadata)` before the query forward. Its `warmup` argument does not select a different preparation route.
4. `cudagraph_utils.py:467–509` creates this closure with `warmup=True`, invokes it, then creates a fresh closure with `warmup=False` and invokes it inside graph capture. Thus a fixed admitted KV-view branch installed before capture is reached during the existing warmup and recording paths. This is a source-control statement, not successful device execution.
5. `cudagraph_utils.py:561–574` replay calls the recorded graph. Fresh Python views on later eager calls cannot update addresses already captured by this graph.
6. The memory-profiling shortcut in `speculator.py:477–499` calls context preparation without a mapping; other dummy paths explicitly pass None. They still execute context projection and norm. The choice between full and KV-only projection must not infer its phase solely from mapping=None or PAD content.
7. `utils/flashinfer.py:1054–1076` forwards the tensors to external `flashinfer.mm_mxfp8` with `out=None`. The target wrapper does not specify workspace capacity or certify allocation behavior. No loaded external dependency version or current runtime tensor manifest was recovered in this round.

**What changes:** there is a concrete existing place to warm the admitted smaller shape. Use that mechanism, keeping the selection stable across preparation and recording. This removes the need to invent a second warmup subsystem. It does not prove that warmup succeeds, every eager tail shape is prepared, a graph's memory fits, or smaller-N outputs are numerically equivalent.

## Minimal implementation handoff, not implemented here

Initial scope is **PJ01 columns only**. Keep input quantization per layer; defer round48 reuse and TR01 row trimming so the first comparison isolates one change.

- Add one opt-in helper at the existing context projection site in `nvidia/dspark.py`. Use the original full merged module plus slice as fallback. Preserve the three distinct norms, positions, cache insertions and full query-forward modules.
- Admit only round40's exact replicated, no-bias, unwrapped module/default-format/ModelOpt path and exact FlashInfer CUTLASS or CuTe implementations, with validated processed shapes, strides, dtype, device, F8_128x4 scale layout and no observing hooks/overrides. A quantization key or class name alone is insufficient. Unsupported setup stays on the original route.
- Reuse current owner tensors: CUTLASS `[1280:1792,:]`, CuTe `[:,1280:1792]`, flat processed scales `[204800:286720]`. Do not register duplicate Parameters or re-run loading/swizzling on these views. These slices are prior source evidence, not newly tested native views.
- Decide eligibility and opt-in before profiling/capture. Keep the admitted implementation consistent across None/profiling, PAD capture and ordinary invocations; mapping content remains only an insertion guard. Do not skip quantization/projection/norm on PAD or None and do not toggle the feature after capture. Exact eligibility must be checked again or invalidated on owner/layout replacement.
- Let the existing DFlash callback warm and capture the selected projection. Preserve the existing graph/eager partition. Eager context tails are separate invocations and may have shapes not in captured decode descriptors.
- A changed owner/layout or feature setting requires graph invalidation and recapture through the serving stack's existing lifecycle. Per-call fresh views alone do not repair captured pointers. No new graph lifecycle API is asserted here.
- Do not catch a native runtime failure and continue as if a safe fallback occurred: it may leave allocator/device state unsafe. Admission fallback is before execution; backend/capture failures are diagnostic failures.

This is a small source patch boundary, not production code. The missing actual backend/prepared-tensor contract must be resolved before asserting the helper is usable.

## First decisive checks when execution is separately authorized

No GPU run is authorized by this plan. The next useful check is a compatible loaded-artifact/runtime validation, not another symbolic geometry loop.

1. Record exact loaded backend and external FlashInfer revision/build, real prepared weight/scale shapes, strides and devices for all three layers. A different layout rejects this arm or requires a separately reviewed adapter.
2. Under the same quantizer and backend, compare full-projection KV slice with smaller projection, then per-layer norm and inserted cache values. Preserve the target's exact correctness contract; smaller N can change tactics/reduction order. Source algebra does not establish equality.
3. Run the existing profiling and graph preparation paths with the feature fixed before capture. Verify successful allocation/capture for actual captured shapes, correct PAD/None behavior and eager-tail behavior, repeated changing inputs, and invalidation after owner replacement. Do not rely on full-query warmup alone.
4. Only after correctness, compare original versus columns-only under the same native DSpark, standard Mooncake and agent-p75 configurations. They exercise this path when that deployment is active; no new serving workload is justified here. Measure component time and frozen long-output ITL plus tail guards. Graph/eager and request-count distributions determine exposure; do not multiply by five speculative positions or add round48/TR01 savings.

A null numerical/capture result stops or narrows the arm. Correctness with negligible service improvement leaves it unpromoted. No estimate of percentage improvement, accepted-length gain or service readiness is made.

## Executed evidence and stop rule

`control_audit.py` performs **eight static AST observations** over the exact saved files: PAD-before-capture, context call without dummy override, explicit dummy-to-None mapping, prepare-before-query ordering, separate warmup/capture closure creation and invocation, graph replay, and external out=None delegation. It executes no extracted target method, tensor operation, allocator, model or backend. All eight observations passed. They support source-control statements only; no independent numerical or device proof is implied.

Read-only ledger access used SQLite `mode=ro`, without migration constructors; saved dossier includes original hypothesis, linked research, records and claims. Sources were copied locally and hashed. One initial convenience command used unavailable `python`; it was rerun with `python3` successfully. No online query was issued because a new paper cannot resolve the installed backend/allocation contract and existing source answered the bounded control question. No additional broad artifact inventory was repeated.

**Disposition:** retain a minimal PJ01 implementation/evaluation handoff and this capture clarification. Scientific priority is unchanged: strong source work-removal premise, implementation deferred, actual exposure unknown. Stop CPU expansion here unless a real compatible runtime artifact or a specific new source contract becomes available. No new identity, promotion, canonical mutation, GPU execution, build, cloud operation or Git change.
