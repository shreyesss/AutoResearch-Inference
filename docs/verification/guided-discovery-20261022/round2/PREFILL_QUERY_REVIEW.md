# RUNTIME-R2-03 adversarial repair: unused non-final-prefill query work

This note preserves and refines the original direct-P/D-port rejection. It does not authorize implementation or GPU experiments. Source reference c455786; live image match unknown.

## Original rejection was too broad

The paper's disaggregated Qwen multi-forward MTP change is not a direct Flash-1017 port. However, 'aggregated DSpark proposals always have a verification consumer' is not a sufficient rejection reason. Pinned code explicitly represents non-final chunked-prefill rows and discards their generated token proposals.

Independently inspected evidence:

1. `v1/core/sched/scheduler.py:2641–2655` ignores draft tokens for `request.is_prefill_chunk`.
2. `v1/core/sched/async_scheduler.py:34` also skips speculative placeholders for unfinished prefill.
3. `v1/worker/gpu/input_batch.py:440` exits token combination when sequence length has not exceeded prefill length; draft IDs do not replace prompt tokens.
4. `gpu/spec_decode/dflash/speculator.py:681–686` explicitly uses the next prompt token when `num_sampled==0`, with a chunked-prefill comment.
5. The same `propose` path performs the query graph/forward for the batch at599–622 after context preparation. No simple non-final-prefill exclusion appears in the inspected proposal path.
6. `models/deepseek_v41/nvidia/dspark.py:165` separately derives every draft layer's context KV from projected target hidden states. Those writes are required and must remain.

## Narrow repair worth investigating

For an iteration where every participating EP rank has only **non-final** prefills and no request can use a draft, preserve target execution and complete draft-context preparation, then omit only unused query-backbone/Markov-sampling work if its side effects are proven unnecessary. Mixed or final-prefill/decode iterations keep the existing behavior initially. This deliberately avoids first attempting per-row compaction or unilateral rank skipping.

## Unresolved obligations

- DSpark query forward writes speculative query KV after the context. Prove those entries are overwritten or masked before any later use; do not infer pure computation merely from discarded token output.
- Preserve context slots, pending graph-staged context work, per-layer cache-group ownership, preemption/restoration and next-chunk transition.
- Audit confidence/adaptive-verification bookkeeping, request output handlers, deterministic RNG semantics, draft token buffers and subsequent graph replay initialization.
- EP collectives require consistent participation. A local `num_sampled==0` guard is unsafe when another rank executes query MoE. Establish all-rank eligibility without a new blocking GPU readback; CPU prefill progress may provide the local predicate but its global agreement still needs a contract.
- A first diagnostic should use source/CPU state-machine fixtures for multi-chunk prompts, boundary final chunks, empty ranks and mixed ranks. Runtime equivalence and benefit remain unmeasured.
- Existing agent-p75 8K prompts may fit a single prefill chunk under some schedules; exposure cannot be inferred from prompt length alone. Mooncake may expose chunking under load, but actual schedule/remaining-length distributions are required. No custom long-prompt benchmark should be substituted to claim a gain on the standard suite.

## Revised reviewer disposition

**Reject the original direct P/D MTP port; reopen a narrower non-final-prefill query-work diagnostic.** Source establishes discarded proposals and separated context construction, not removable query side effects. Until those dependencies are checked, this is an investigation candidate rather than an accepted implementation or service improvement. It should be recorded as a substantive revision of RUNTIME-R2-03, not counted as an unrelated new idea.

## Follow-up: independently confirmed confidence consumer

`adaptive_verification.py:256–280` records every row, flips the stale/read and write slots, and publishes previous-step confidence. `get_num_tokens:309` reads that stale buffer; it is not conditioned on the previous step having consumed draft IDs. `gpu/model_runner.py:2282` records after every proposal when adaptive verification exists. Under an ordinary sequential three-chunk prefill lifecycle, first decode can therefore read the penultimate unfinished-prefill confidence. The worker's CPU buffer illustration is consistent with these assignments; it is not an execution or interleaving test.

`dspark/speculator.py:106–113,155–198` confirms that the trained confidence head uses the anchor and preceding sampled-token Markov embeddings. Preserving five confidence outputs requires the first four draws. Discarded proposal IDs do not establish that the query backbone or complete Markov sampling is dead. Whole-query skipping is **obstructed under this adaptive mode** unless a separately tested confidence-transition policy changes it. Exact effective mode remains to be pinned.

The narrower terminal fifth draw may not feed a later confidence parent, but existing code projects all five base-logit rows together and caches logits; omitting one step requires inspecting those live-outs and graph structure. Earlier C025 evidence makes material ROI doubtful for a single terminal step on only some prefill iterations. This is a low-priority residual, not an accepted speedup.

### Review of worker revision1

Reviewed `round2-runtime/R2-03-REVISION.md` and `candidates-revision1.json`. Their replacement of blanket rejection with a bounded CPU dependency diagnostic is justified. Preserve the original card and explicit revision relation. Count **one revised direction**, not an additional independent hypothesis or service-qualified acceptance. No GPU work or serving patch was performed. The direct disaggregated-MTP port remains rejected; context-only transfer remains unresolved.
