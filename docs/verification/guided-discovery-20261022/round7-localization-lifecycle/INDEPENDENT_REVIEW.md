# RD01 lifecycle refinement: independent review

**Verdict: retain deferred integration. No runtime or service qualification.** Reviewed round7-localization-lifecycle REPORT.md and domain_components.py/json against pinned vLLM `c4557869393db4d75c483d92edd02a5125500883` and earlier dependency evidence. This is the existing RD01 refinement, not a new direction. No GPU, MPS availability query, or CUDA import executed.

## Source findings supported

- Native V4.1 model.load_weights invokes its model post-load method (model.py1701–1704); generic loader finalization invokes model post-load again (utils.py209–210) after quantization/module processing. A naive unconditional localization in that hook can run too early or twice. Idempotence and an explicit final boundary are necessary.
- A localized matrix's per-domain slices can be exported as contiguous `(E,-1)` components. Existing rebalancer loops over component lists and stages data before copying back. This supports a smaller adapter than replacing EPLB. It does not demonstrate NIXL/driver compatibility with externally imported MLOPart allocations.
- Existing target loader indexes expert-first parameters; a domain-first replacement breaks that contract. Preserving weight_loader attributes on a Parameter is necessary bookkeeping but not a repair for incompatible index semantics. Reload must be adapted into stable localized buffers, or rejected before any write for an explicitly static-weight experiment.
- Source owner tensors must remain alive and pointers stable before graph capture, EPLB buffer construction and communicator registration. Re-localizing after registration invalidates captured views and exchanged pointers.

## Important runner correction

The submitted initial report used legacy `gpu_model_runner.py5025` as its primary runner chain. The selected V2 path has been independently checked and supports the same proposed boundary:

`v1/worker/gpu/model_runner.py383–425`: prepare EPLB -> DeviceMemoryProfiler -> model_loader.load_model at401 inside the JIT warmup registry -> optional LoRA setup -> speculator loading/possible EPLB registration at420–425. Main model EPLB registration is at534–537 after model-state initialization.

Therefore finalize the target after loader return, before any draft binding/registration and before main EPLB registration. Account for JIT provider registration if the finalizer introduces any new registered kernels. External `model=` bypasses the loader; it needs explicit eligibility rather than blindly assuming fully prepared weights. LoRA and alternate loaders remain separately scoped. This resolves the runner mismatch without claiming the legacy chain alone proved V2 behavior.

## Component-list invariants are stronger than “same order”

EplbState.add_model492 allocates `expert_buffer` from **the first layer's components only**. Rebalancing subsequently reuses that list for every layer. `zip(expert_weights, expert_buffer)` can truncate if lengths differ; there is no universal corrective layer-by-layer allocation here. Thus every layer in a given EPLB model must expose matching component count, per-component shape/dtype/order. Do not selectively localize just some layers while returning two-domain components for those and one ordinary component for others. Either normalize representations into consistent components or keep the entire relevant model's policy uniform and validated. Different draft/target models may have distinct model-state lists, which must be audited separately.

NIXL remote descriptors are indexed by `(layer,tensor_index)`; add_recv457–459 checks receiving byte count equals remote stride. Cross-rank component order and byte size must match, not merely reconstruct correctly on a local toy. Additional components increase descriptor/communication operations even when useful bytes are unchanged. A future adapter must preserve existing staging and synchronization, including duplicate expert propagation.

## What the byte diagnostic proves and does not prove

Inspected `domain_components.py`: 102 seeded mappings construct writable byte slices in two padded domain regions, stage immutable source copies, apply permutations/duplicates/remote-bank mappings, and reconstruct packed payload/scales. Four deliberate negative controls catch omitted domain, omitted scale, unstaged swap, and stale old-storage view. The artifact accurately labels itself a symbolic representation/copy diagnostic.

It does **not** execute target get_expert_weights, vLLM rebalancing functions, real Torch striding, MLOPart allocations, GPU numerical kernels, NIXL registration, asynchronous copies, graph capture or actual remote communication. The earlier round5 exact-method fake-tensor shape test is complementary but likewise not GPU evidence. The 102 cases must not be reported as 102 successful EPLB or inference experiments.

The stale-registration negative control shows a view of old storage cannot modify the new allocation. It does not test actual communicator teardown/re-registration, whose source contracts remain separate.

## Physical memory interpretation

The full-size arithmetic uses 96 local routed experts, hidden5120/intermediate2304, routed packed FP4, fused shared FP8 and unchanged scales. These are stated source/config assumptions, not live allocation observations. Padding scenarios64KiB/2MiB are illustrative; actual CUDA granularity has not been queried.

The old and new payload coexist during copying. Sequential replacement reduces peak only if old owner references are released, asynchronous copying is complete, and PyTorch cached physical allocations are actually returned so the external allocator can use them. A per-layer arithmetic bound is not a whole-model peak guarantee. Temporary copy/mapping/probe allocations and communicator buffers also matter.

`DeviceMemoryProfiler` calls CUDA platform.get_current_memory_usage; cuda.py369–374 empties cache, resets Torch peak stats, and reads max_memory_allocated. External from_blob storage can disappear from this Torch-only model-memory report. The later `mem_utils.py309–323` explicitly uses device free-memory difference plus transient Torch headroom, so claiming an inevitable KV sizing bug would be incorrect. Future validation must measure physical memory at load and profile phases and account for other GPU users; current no-GPU restrictions prevent that measurement.

## Next gate

Retain a uniform MXFP4/shared finalizer and domain-component EPLB adapter design, with explicit pre-registration ordering and reload policy. Before implementing GPU experiments, resolve actual selected binary/config, MLOPart eligibility and useful affinity map, component parity across layers/ranks, physical headroom, and runtime registration support. The existing evidence supports continued engineering; it does not predict an ITL gain or satisfy service promotion.
