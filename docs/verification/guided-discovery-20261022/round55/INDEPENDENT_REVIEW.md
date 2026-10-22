# Independent round55 review — cross-step Engram preparation

**Agree: retain as a parked component, zero new identity or qualification.** Janus provides a usable exact-correction pattern, but its SSD append-prefill bottleneck is not evidence of exposed target Engram lookup time. Existing A01/EG01/EG02 statuses remain unchanged.

## Earliest availability and wrong-path handling

The V2 source starts asynchronous output copying, updates sampled/accepted history and computed positions, then enqueues native proposal. Only after proposal are draft IDs persisted and confidence recorded. This creates a potential source-defined early point; a Python return or assignment is not a host-visible device-completion guarantee. An independent producer stream must follow the GPU dependencies and retain its input buffers through consumption. The source does not measure how much time remains before the next forward.

Do not require a draft token to be accepted by the *next* verification before preparing its read-only Engram rows: an eventually rejected token can still be a legitimate next target verification input. The actual mismatch hazards are changed request membership/generation, EOS/cancellation, current accepted-history/bonus anchor, adaptive budget/position and row packing. Future rejection must not promote predicted suffixes into committed history or make stale prepared rows visible to a later generation. Exact per-row table/layer/hash identity plus ownership validation and baseline fallback can repair a prediction miss; fallback cannot reverse a prior write to live history or slot state.

The inspected V2 EngramHash path disables the optional slot cache and derives history from current rows plus gathered lookback. Its legacy V1 branch writes the slot cache before hashing. Therefore a generic early call to the hashing wrapper is not universally read-only; scope any eventual preparation to the verified path or a separate pure hash builder. The n-gram identity includes ordered head hash IDs, token-map/dead-image semantics and immutable table/version identity, not just row count or an old request slot.

## Existing overlap and resource ownership

Current model forward hashes once and initiates per-layer lookups before decoder execution. Engram already has a background stream, hash record_stream lifetime, per-layer ready event and large-batch inline policy. Thus this component could move the producer earlier across a step; it does not newly remove a synchronous per-layer lookup or overlap output copy with drafting.

Current staged_rows is a mutable fixed-address flat buffer. Reordering equal-size batches produces a real identity hazard. Generation-tagged immutable prepared rows must either be gathered safely into each current flat input or consumed through an adapter with the same representation contract. Reusing an event name does not establish which producer generation a wait covers. Bound capacity, cancellation, producer completion, consumer fences and retirement are explicit requirements; graph-static addresses alone are insufficient. Hash computation must read a consistent history snapshot and stay separate from live state updates.

Shared-host mode sets effective table DP size1 and excludes EngramBatch; that permits a narrower non-collective preparation concept, not proof the deployment uses it. Generic sharded/peer/all-to-all paths are group-slot dependent and cannot be opportunistically launched on one ready rank. Existing inline threshold also uses the DP maximum to avoid rank/persistent-kernel interference. Retain its policy or justify a replacement under rank agreement; do not infer all background copies are harmless.

## Benefit and next evidence

The report's min(current exposed wait, legal producer advance) is an optimistic single-wait bound only with unchanged lookup time/resources and consumer arrival. Additional work, misses, validation/copy cost and contention can make net gain negative. Summing waits from concurrent layers/ranks or adding A01/EG01 gains would double count. A01 moves WKV within a forward; EG01 changes representation; EG02 caches repeated data. Cross-step scheduling is a distinct intervention description but does not deserve another formal candidate while exposure is unknown.

The smallest useful next evidence is an actual compatible retained next-input/state trace plus residual lookup-wait/producer-window evidence. A host-only replay can falsify shape/slot keys and some lifetime assumptions, but cannot certify GPU adaptive spans, stream/event ordering, captures or collective safety. Existing trace inventory lacks that representative evidence. Do not manufacture hit rates or authorize a GPU run to fill the gap under current user constraints.

All33 author artifact hashes and four copied target files match. No native code, model, GPU or provider request was run. The author's AST ordering is lexical evidence, not a measured execution DAG. This review read selected Janus mechanism/evaluation passages and exact target branches, not every source/paper line.
