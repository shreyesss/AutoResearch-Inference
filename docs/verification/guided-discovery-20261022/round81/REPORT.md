# Round 81 — CF59 temporary-buffer ownership and a narrower overlap interval

## Decision

**Same CF59, still deferred. Zero new hypotheses, no implementation or native execution.** This source check removes one overly broad hazard premise: the inspected native block-rejection path does not call the same FlashInfer MXFP8 GEMM/workspace API as context projection. A shared external scratch *race* has not been demonstrated. This is useful evidence for a bounded first arm; it does not establish allocator, graph-capture, numerical or performance safety.

Identity: `hypothesis:f11b4ac30a88d38e295c1a9001afe052315832b69a37e16e2952bbb382e336cf`. Planned baseline remains `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`, exact Flash1017 revision1bae0e1 and callgideon/vllm c4557869393db4d75c483d92edd02a5125500883. The read-only canonical receipt includes the actual latest decision node, status `deferred`. No event or selection was changed.

## Question and source scope

CF59 moves unchanged target-feature combination plus three different layer context projections/norms onto another stream while native rejection sampling runs. It separates these operations from rejection-dependent positions, slot mapping and KV insertion. Round59 already requires unchanged padded row partition, explicit FULL/eager consumers, original early AsyncOutput, and generation-owned projected output. Its prompt-logprob addendum found additional possible head calls after the first LM head; those must be gated or independently audited.

This follow-up asks which resources **actually have overlapping users** in that narrower interval. It reads exact retained target source, donor PR61869 patches at yaoyaoding/vllm9a1541d118524bffb13f66d87481def3d3428556, prior CF59/PJ01 capture reports and the current canonical CF59 decision. No new paper search was needed: another general overlap paper would not resolve this source ownership question.

The local source archive manifest explicitly lists only `vllm` and `csrc`. Its4,146members contain no requirements, Dockerfile or pyproject entry. This bounds dependency evidence; it is **not** evidence those files are absent upstream. No exact installed FlashInfer implementation/version or actual selected projection backend was recovered. No network or runtime probe was made.

## Concrete ownership findings

| Resource/path | What pinned source establishes | Remaining boundary |
|---|---|---|
| Native block rejection | `rejection_sample` creates explicit `new_empty` tensors for target/draft statistics, cumulative ratios, residual mass and sampled outputs, then invokes Triton kernels. It does not call MXFP8 GEMM or the vLLM WorkspaceManager. | Direct call inventory plus manually read path; external/dynamic extensions are outside this statement. No native allocator trace. |
| Logits preprocessing | `Sampler.apply_sampling_params` returns the original logits when `needs_logits_processing` is false for every admitted row. | Temperature1/top_p1 alone does **not** imply this flag: penalties, thinking budget, custom processors and other options can activate work. Admit the actual flag state or audit the active branch. |
| Ordinary sampler | `sample()` uses ordinary `Sampler` when `num_draft_tokens==0`; that sampler can call FlashInfer sampling. | Scope first overlap arm to the native nonempty block-rejection branch. Do not infer all sampling paths avoid the library. |
| Context projection | `main_proj` is ReplicatedLinear with quant config; context WQA/WKV linears and per-layer norms are separate calls. Named CuTe/CUTLASS MXFP8 apply methods quantize activations when needed and call the wrapper. | Actual main-projection quant method, processed weights and selected backend remain unobserved. No assumption that all operators use these two kernels. |
| External MXFP8 calls | Wrapper forwards to `flashinfer.mm_mxfp8` with `out=None`; SM100 quantization dispatch forwards to FlashInfer CuTe DSL. No local explicit workspace is supplied. | Opaque allocation/cache behavior is unresolved. `out=None` does not prove aliasing or unsafe allocation. A shared allocator is not itself a shared live tensor. |
| vLLM workspace lanes | Resource/workspace indexing includes ubatch and explicit lane. Current native DSpark proposal runs under `_draft_workspace_lane=1`; donor fork also wraps the lane. | CUDA stream context alone does not set this ContextVar. Carry explicit lane scope. Lane separation covers manager users only, not arbitrary external library caches. |
| AsyncOutput | Retains sampler output and sampled-count tensors, waits copy stream on main and enqueues D2H before postprocess/proposal. | These are sampling outputs, not context inputs/projected outputs. Retaining them does not retain context tensors. Preserve early enqueue and existing output-copy ownership. |
| FULL graph staging | Current DFlash combines captured prefix rows from `_aux_staging`, eager tail separately. Donor sets `_aux_staging=None` and changes graph preparation when side stream is initialized. | Graphs must match the split; moving eager work while replaying an old graph can repeat work. Target FULL alone remains insufficient for draft projected-buffer consumption. |

Source references are recorded in `source-manifest.json` and exact short excerpts in `source-audit.json`. The statement about no common caller applies to the selected Python/Triton call path, not an exhaustive proof of every kernel implementation or all process threads.

## Narrow first arm and actual lifetime requirements

A useful first arm forks **after the sampled-row LM head** and joins **immediately after the original AsyncOutput enqueue, before postprocess and draft-input preparation**. Joining at this earlier point is allowed by CF59's dependency split and reduces the concurrent main-stream surface. It deliberately forgoes any additional overlap with state update or draft preparation. It does not move the D2H enqueue behind context completion.

```text
main: target features + LM head -> native block rejection -> AsyncOutput enqueue -> join -> postprocess/slots -> insert -> draft query
side:                         wait -> combine + three projection/norms + owned staging -> done
copy:                                                     wait(main so far) -> D2H
```

Initial admission must establish the actual native rejection path, compatible graph/row consumer, no active later prompt-logprob head, no unknown custom callbacks, and no unreviewed connector or auxiliary-output work within the interval. This is a fail-closed eligibility check, not permission to disable requested features, AV, fault handling or output semantics. Ineligible steps keep current serial behavior. Optional hooks that are required in the intended deployment need a bounded source audit before widening this arm.

The required lifetime rules are concrete:

1. **Producer readiness:** side stream waits for the current target features and first head. Input references and contents remain valid through side consumption. A Python reference prevents reclamation but cannot stop a future graph from overwriting a persistent output. The main join must precede the next producer reuse.
2. **One context owner per generation:** side writes a dedicated combined/context staging owner. No other consumer overwrites speculator hidden/context storage before join; projected outputs remain live through KV insertion. A staged output is not free merely because Python has queued a wait. Use correct stream recording or explicit owner/event lifetime in an eventual adapter.
3. **Temporary ownership:** concatenation/quantization/GEMM/norm intermediates are created and consumed in side order. Same-stream sequential reuse across the three layers is not a simultaneous race. Weight/scale tensors are read-only during the attempt; reload/recapture must occur only after users retire.
4. **No graph shortcut:** ensure captured prefix and eager tail both consume the intended projection once, at unchanged M/padding and dtype. Static allocation and event capture must be established in the actual backend. The existing FULL graph cannot simply be left unchanged and assumed to consume new staging.
5. **Output release:** retain the existing copy-stream source owner and wait-before-reuse behavior. A new side-stream join must not accidentally be recorded before AsyncOutput's wait/copy enqueue. Capturing a different graph region is a separate control.

The inspected rejection path has no caller-level need for the external GEMM resource concurrently used by context math. Therefore a new global scratch partitioner is **not justified solely by this audit**. Exact backend inspection and native lifetime checks remain needed for implementation, but missing installed-version evidence does not invalidate this narrower static finding.

## What this changes, and what it does not

Previously the workspace gate was broad. It can now be phrased as: preserve context tensor owners and captured input/output lifetimes, establish actual external backend allocation behavior, and admit a main-stream interval with no second GEMM or unreviewed callback. There is no demonstrated blanket same-scratch conflict between native block rejection and the named context MXFP8 calls.

This does not establish useful overlap. Let C be context work and S the admitted sampling/output-enqueue interval; contention, staging, launch and join costs remain unknown. Optimistic savings remain bounded by min(C,S) minus added costs, with no numerical forecast. Earlier PJ01 columns, quantization reuse and TR01 rows change C; sampler optimization changes S. Their gains cannot be added. Joining before postprocess narrows S further relative to any broader scheduling arm.

Existing agent-p75 and Mooncake remain the service evaluators. The next authorized native check should identify exact backend/version, record stream/resource ownership and show original early D2H enqueue, then test graph/eager, repeated generation, empty ranks, mixed batches and numerical/proposal parity. No new synthetic service benchmark or arbitrary success threshold is proposed. Source evidence is enough to continue CF59 as a bounded diagnostic candidate, not enough to implement or promote it here.

## Work actually performed and failures

- Read-only canonical lookup confirms the same identity and deferred decision; no canonical writes.
- Copied22 selected source/prior artifacts with exact byte hashes (471,679bytes).
- `python3 build_audit.py` parses source AST only, inventories8functions and verifies7 exact excerpts. It is a navigation/integrity check, not eight runtime tests or a concurrency proof.
- First helper used an incorrect CuTe class spelling and failed with StopIteration; retained `build_audit.attempt1.py` and failure note. Corrected to the actual class and conditional wrapper location. No source implementation changed.
- Early shell glob/path lookups failed; corrected to actual directory/module names. A dependency-manifest search returned empty because the retained archive scope excludes those directories; scope is disclosed rather than claiming global absence.
- Zero online queries, newly read papers, native/GPU calls, model runs, service measurements, typed hypotheses or decisions. No cloud/Git mutations. Stop here: the remaining opaque backend/capture behavior cannot be resolved by more AST case counts.
