# AT03 fixture critique and execution-boundary revision

## What the first fixture actually demonstrates

`kv_lifetime_falsifiers.py` is a readable model of a proposed contract. Its83 comparisons do not validate a target cache implementation. The script constructs reference and cached values from the same supplied `(generation, metadata)` arguments and refreshes on those arguments. It therefore assumes the hardest missing mechanism: obtaining and transporting a correct generation/metadata signal at every actual invocation. The assertions about different epoch strings and source-generation tuples are illustrations, not observed invalidation failures. The scratch alias and overwritten-chunk examples do demonstrate elementary ownership hazards, but not their exact runtime frequency.

It omits metadata objects whose contents mutate in place, captured graphs replayed without Python, nested decoder replay, ubatch identity distinct from lane identity, source mutation midway through a group, interleaved invocations on the same resource, changing request offsets in mixed decode/prefill batches, warmup capacity/lock failures and partially initialized buffers after abort. Listing these does not require solving every hypothetical deployment; freeze the supported first scope and fall back outside it.

## New pinned call-chain evidence

At c455786:

1. `nvidia/model.py:843–869` chooses last KV source20 as replay cut and binds `write_batch_kv=self.layers[20].write_kv`, `run_layers=self._run_replay_layers`.
2. `model.forward:1062–1085` runs layers below the cut, then invokes that wrapper. Without replay optimization, the ordinary `_run_layers` loop includes source20 before21–39.
3. `decoder_replay_layers.py:71–78` may prewrite full source KV before a replay break. `_run:111–126` invokes either its whole layer callback or its replay graph under the nested replay context.
4. `model._run_replay_layers:1224` explicitly traverses `range(self.decoder_replay_start,self.end_layer)` =20..39. There is no inspected dispatch that starts at21.
5. `nvidia/decoder_replay_cudagraph.py:54` wraps `layers.run_layers`; capture79–88 and run95–109 execute that whole callback. Replaying this graph still includes source20.
6. `model_state.py:460–558` rebuilds the replay batch and its context, including special first-layer SWA metadata539–549. Same outer request/forward does not imply identical metadata objects or gathered tail geometry.
7. `ForwardContext:141–202` contains metadata/graph descriptors but no source-write generation counter. Object identity is not a content version.

**Executed source-control check:** `decoder_replay_control_audit.py/json` extracts and executes the actual pinned DecoderReplayLayers class with pure CPU recorder callbacks. Five control branches enter the whole layer/graph callback and restore the nested context. The range20..39 binding is established separately from original model source; callbacks do not execute layers. No torch import, actual tensors, graph replay, allocator or GPU is tested. This is stronger than a newly written schedule simulator for wrapper dispatch, but it is not a correctness test for the proposed gather modification.

## Simpler proposed design

Replace cross-invocation memoization with **unconditional refresh at source20 attention entry**. Whenever the eligible source20 prefill attention runs, its original gather fills a stable dedicated combined buffer. Consumers21–39 reuse that prefix in the same ordered group and replace their own SWA tail. Every ordinary forward or replay group executes source20 first, so the fill is a real operation inside the replayed path. No Python cache-hit decision or invented generation/epoch oracle is required.

The lifetime is one stage invocation. Never reuse a previous invocation's data merely because shapes and addresses match. Allocate storage through a stable prewarmed per-ubatch/lane resource; source20 refresh determines content validity. Static schedule/layout eligibility must be established before choosing the optimized path. A direct call to a consumer, alternate graph partition, unsupported multi-chunk plan or concurrent shared-resource invocation must keep the baseline gather path. A host flag set only during graph capture is not a valid runtime freshness check.

This is a substantive revision of AT03, preserving the original card/fixture as superseded evidence. It does not add another independent hypothesis.

## Remaining falsifiable CPU work

1. **Execute original chunk planner:** extract the pinned `get_prefill_chunk_plan` method and run it on CPU metadata fixtures representing ordinary and `model_state._kept_input_batch` replay shapes. Compare source20 and consumer plans, including mixed decode-prefix offsets, unequal request lengths, full128-row replay, short remaining chunks, zero/idle requests, and the maximum supported single chunk. Output actual prefix width, row stride, required capacity and eligibility. A mismatch rejects reuse for that case instead of being explained away.
2. **Writer/call-site inventory:** enumerate every source20 cache insertion and actual invocation of `_run_replay_layers`/`forward_kv` at the pin. Establish that no permitted operation writes compressed source20 after its gather and before consumer39. If any supported path does, the simple stage invariant fails and must fall back. Source exclusivity is not proven by passing a generation argument to a simulator.
3. **Exercise actual resource-manager contract with CPU allocation stubs:** retain original `get_persistent_resource`/lock logic, verify separate ubatch/lane resources, prewarming both outer and nested replay capture shapes, no allocation after lock, and no same-key concurrent use. Stubs prove control/allocation bookkeeping only, not CUDA graph pointer behavior.
4. **Use available saved scheduling metadata:** count eligible source20 prefill groups and full compressed lengths, then compute resource envelope and removed gather bytes/calls. Absent such metadata, report exposure unknown. Do not manufacture a favorable request distribution.
5. A later implementation must still perform original-vs-reuse gathered byte and layer-output comparisons, but GPU execution remains unauthorized. CPU-only source work cannot certify driver ordering or device correctness.

## Relative priority

**AT03 first, AT01 second, AT02 deferred** for the next bounded diagnostic. AT03 has exact-target repeated work and reuses existing gather/attention kernels; its primary risks are a manageable lifetime/layout/memory contract. AT01 requires a new MXFP4 computed-score envelope, kernel mapping and useful pruning at much shorter compressed domains than the public implementation. A long numerical-development effort is not justified before its target-domain exposure screen.

Neither is a demonstrated improvement to the frozen long-output ITL objective. AT03 directly targets prefill cost; potential decode-tail benefit depends on actual concurrent-prefill blocking. AT01 is also a prefill proposal. Prioritize obtaining existing workload metadata/critical-path evidence, rather than implying a TTFT optimization necessarily improves sustained decode ITL. No unknown ROI alone is a rejection; it limits the stage and investment.

## Review of replacement `source_entry_lifetime.py/json`

The replacement removes the generation oracle and correctly refreshes on every source20 entry, including changed contents at the same source address. Its within-group mutation counterexample explicitly fails, which preserves the unresolved writer-exclusivity premise instead of inventing detection. Missing/reordered source, geometry mismatch and multi-chunk cases take a modeled fallback. This is a better design discriminator.

It remains symbolic: the complete schedule and `geometry_equal` are supplied truth values; fallback copies an already constructed reference; lanes are integers and their calls execute serially. The239 comparisons do not validate target memory, real ubatch/lane isolation, concurrency or captured replay. The actual wrapper-control audit supplies separate evidence for source-first traversal, but neither artifact establishes the patched gather placement. No blocker to retaining the revised card as a CPU diagnostic; no implementation approval or performance qualification follows.
