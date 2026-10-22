# Independent HM65 review

**Retain the narrow SamplingStates dirty-publication component for a future bounded experiment; defer native execution and performance qualification.** The donor whole-Sampler gate is broader than needed. Preserving all outer callbacks while avoiding unchanged five-array publication is a concrete, selectively reusable component. Unknown host exposure limits ranking and any forecast; it does not make the mechanism invalid.

## Source contract checked

The exact target `SamplingStates` constructor initializes five UVA-backed arrays; `add_request` writes temperature/top-p/top-k/min-p/effective-seed. The seed is drawn once on admission if unspecified. `apply_staged_writes` always publishes all five. `Sampler.apply_staged_writes` separately invokes every processor, thinking-budget, logprob-ID and optional trace-state flush. The new dirty gate must remain inside SamplingStates, leaving all these callbacks and their ordering untouched. Donor model_runner lines1251–1255 place the whole sampler flush under new admissions; its interface change is not a reason to silently change the target contract.

The literal/AST writer audit is useful bounded evidence, not an alias-complete proof. Removal alone does not need to change old static values because only active slot mappings should consume them; re-admission or resumed streaming admission must mark dirty before writes. External writes must invalidate or disable the optimization. Constructor dirtiness is conservative and avoids relying on the different initial pool rotations of top-k/top-p versus the other arrays.

`UvaBackedTensor.copy_to_uva` assigns a pool view after a CPU-to-CPU copy. The host source array is separate from that pinned published slot. Skipping a clean flush preserves values and a pointer; it does not eliminate five DMA launches on the UVA path. Four32-bit arrays plus one64-bit array give24*N logical copied bytes, not an elapsed-time or bus-transfer estimate. The non-UVA fallback and any captured argument binding remain separate admission/correctness checks.

## Lifetime and failure scope

The normal clean-step path need not inherit every issue in the donor's separate InputBuffers-pool arm. Given unchanged values and the existing bounded outstanding-step/retirement contract, leaving the same slot published through clean steps is plausible. Later dirty publications still need the exact reader-retirement and graph-pointer contract; current source alone does not establish deployed queue depth or replay arguments.

A partial flush followed by immediate retry is different. Some array pools can advance before another copy raises. At depth2, an old reader of slotA can coexist with the partial publication intoB; retry can rotate back toA without that reader having retired. This is a conditional source-derived counterexample, not an observed native race. The minimal dirty implementation should **preserve existing exception propagation/abort behavior**, not introduce automatic retry. If a separate recovery protocol is desired, retire/reset affected resources before retrying. Keeping dirty=true and preserving the generated seed proves only bookkeeping. This hazard also applies to pre-existing/manual whole-flush retry; it does not refute the steady-state skip.

## What the CPU records establish

The unchanged extracted methods check admission/flush call control under stubs. The dirty proxy implements the proposed flag externally and copies Python lists, so successful cases are not a native patch test. Its custom tick is a sentinel for the intended outer callback contract, not actual execution of all plugins. The untracked-write negative correctly demonstrates a missing-invalidation failure. The two-slot retry schedule is an illustration of a source-consistent outstanding-reader premise, not GPU concurrency execution.

The four manually supplied AV allocation cases concern a different parked arm; they neither validate the native confidence allocator nor add correctness credit to HM65. Likewise the donor's three InputBuffers pools are not part of this selected intervention. Keep these scopes separate in later evaluation and do not add their potential savings.

## Evaluation decision

A later implementation should first close actual all-writer, queue/graph binding and failure-abort contracts, preserving effective seeds, slot reuse and every processor callback. Then record clean-step frequency and exposed host publication cost under the exact baseline. The formula p*H is only a conditional optimistic step bound; it is not a long-output ITL estimate, particularly when progress or host/GPU overlap varies. The standard agent-p75/Mooncake runs remain the service controls with matched seeds/load and tail guards. No new benchmark or further symbolic case count substitutes for actual exposure.

The source-led result needs no decorative paper claim: ten abstracts yielded no useful fulltext, and the exact PR diff supplies the transferable component. The scoped prior distinctions are credible for RD02, MP17 and DP-sync work; they are not a global novelty proof. HM65 remains a small readiness candidate, with no evidence to rank its service gain above PJ01/CF59.

## Evidence depth

Verified all66 frozen files and all six claim quotations against their exact source revisions and retained bytes. The short donor quote mentions req_states, so I read the adjacent nested sampler call rather than treating that isolated line as proof of the whole scope. No native/library imports, network requests, GPU calls, timing, source mutations or repeated broad tests were performed. Original author records remain unchanged.
