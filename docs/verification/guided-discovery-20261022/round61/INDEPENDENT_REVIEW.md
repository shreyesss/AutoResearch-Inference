# Independent adversarial review — RM61 active request ownership

**Verdict: retain one deferred investigation, with no implementation or service qualification. No blocking factual correction to the frozen author packet.** This is a state-protocol design obligation supported by source, not a demonstrated safe protocol or a trace-supported benefit.

## Independent checks

- Verified all44 author artifact hashes against manifest `34b82cb453e523aad8084231ad599fa6ad46d30922f337656feaead8ae7c08d1`.
- Verified all six exact source quotes in retained bodies.
- Independently executed a byte-identical copy of the author's stdlib/AST probe in this reviewer directory. Its eight routing/prompt-match observations reproduce exactly; original author files remain unchanged. This executes no vLLM imports, tensors, transfer, device or native runtime.
- Read exact target routing, NIXL pull/finished-export, scheduler rejection/stale-output accounting, DP descriptors/dummy participation, cache-group metadata and DSpark sampling calls. Read selected Pallas protocol and EdgeFlow representation portions.
- Added source checks of output processor/detokenizer and effective sampling seed initialization, retained below. No online queries or GPU action.

## Supported mechanism and important exclusions

The owner table returns an existing in-flight owner before examining a newly requested rank. The normal remote-decode matcher caps accepted external tokens at the original prompt length. Normal NIXL export is a finished stopped/length-capped path; abort is not an equivalent transferable finish, and D-side export requires bidirectional transfer. Together these directly refute a reroute-and-resume shortcut; they do not imply every building block must be rewritten.

The scheduler counts in-flight work optimistically and rolls rejected speculative tokens/placeholders back only on applicable non-stale results. A transfer boundary must drain the applicable accounting and cache writes. A raw mid-step `num_computed_tokens`, output length or locally observed sampled count is insufficient. The exact committed/uncomputed frontier also matters: treating the last emitted token as already cached can cause a skipped forward or duplicate token.

The paper's single-owner/epoch/coverage/synchronization ideas are useful, but the independent vLLM-engine prefix-recomputation implementation cannot simply execute concurrently inside one shared EP4 collective group. Draft/SWA/indexer/compressed groups and rebuildable replicas need an actual group inventory, and sliding windows/partial blocks cannot be assumed immutable historical KV. EdgeFlow's conventional2H cache transfer premise does not describe a528-byte target latent record. The author's10,240-vs528 comparison is correctly scoped as a representation counterexample, not total request state.

## Streaming, stop and RNG state are separate from KV

The pinned frontend `RequestState` owns detokenizer and logprobs processor, output budget, input/output role distinction and `sent_tokens_offset`. Output processing updates incremental detokenization and stop-string decisions; a terminal event removes or finalizes state. A migration can potentially keep that original frontend object and redirect the internal owner, rather than copying it across GPUs. It cannot silently send finish/restart, replay generated history as a fresh prompt, or reset the output offset. Reasoning/parser buffering, partial Unicode/stop strings, cumulative usage and external/internal IDs remain part of the contract. A request cancellation crossing the handoff must have one effective owner and no extra terminal output.

Concrete additional seed gate: `sample/states.py:54–58` generates an effective random int64 seed when `sampling_params.seed is None`, and separately tracks `seeds_set`. Reconstructing a request with the same original `seed=None` creates a different effective seed. The transfer must preserve the generated seed and its explicit-seed eligibility flag, not merely serialized SamplingParams. DSpark and target rejection calls consume seed arrays and absolute positions, so an opaque whole-device RNG snapshot is not automatically necessary for these inspected paths. Other enabled fused sampling/custom processor paths must be admitted separately. Turning an implicit seed into an explicit request option can itself affect sampler eligibility; preserve semantics rather than assuming those flags are interchangeable.

Even an exact state/cache copy can change batch geometry, padding, tactic selection or reduction grouping on the destination. Frozen weights and preserved effective RNG keys do not certify next logits or exact output. The author added this gate before freeze. Direct-copy correctness must be checked separately from recomputation, and a deliberate distributional contract cannot be silently substituted for sequence equality.

## Real max-padding premise

The ordinary graph branch synchronizes maximum rank token count, dispatches the real graph descriptor and propagates its padded count. A move only saves this work if the **actual descriptor** changes; equal maxima or the same bucket save no graph rows. Query-length/LoRA/request/graph-mode constraints remain. Normal non-microbatched eager mode preserves local token counts, so common graph padding is absent there. Microbatch mode explicitly requires equal split/pad and dummy empty microbatches. Moving a request must not let a rank skip an EP collective, invent a separate forward or block progress needed by the transfer.

Balanced request counts do not prove balanced decode cost. Fixed sparse Top512 work, candidate compression, DSpark accepted progress, prompt chunks and request length/cost heterogeneity matter. Holding token/routing results fixed, relocation does not remove their aggregate routed expert work; padded tokens may already be masked from routing. Consequently a raw context-sum or padded-MAC forecast is not valid. The proposed metadata replay against exact descriptors and measured non-MoE straggler work is the right next gate, but no suitable trace or profitable move was established here.

## Qualification

This is distinct from initial routing, M05 placement between independent groups and CMR within-owner microbatch permutation. It has a concrete missing active-state handoff and a cheap source shortcut falsifier. That supports **deferred investigation**, not priority above measured component wins or an integration-ready implementation. Stop-copy can add a large visible ITL gap and duplicate-memory pressure; proactive staging is an optional subsequent arm, not assumed free overlap. Existing Mooncake/agent-75 service tests remain appropriate after correctness/liveness proof, with affected-request pause tails reported separately.

No canonical identity/status change was made by this review. Source-level protocol conditions are necessary conditions; eight stubbed routing checks are not a migration lifecycle test.
