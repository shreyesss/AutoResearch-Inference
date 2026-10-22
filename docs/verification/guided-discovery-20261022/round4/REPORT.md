# AT03 round 4: source20/consumer geometry gate

**Finding: special source20 SWA metadata does not inherently prevent reuse.** The pinned planner intentionally reserves an upper bound independent of replay start. Source20 and consumers can gather different SWA lengths into the same compressed-prefix offset and combined-buffer geometry. This closes one concrete source-level objection; it does not establish latency benefit or GPU correctness.

Round3 artifacts remain frozen. This report extends AT03 revision2 (unconditional source-entry fill; no across-call memoization).

## Exact pinned dataflow

All references are `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`.

1. `nvidia/model_state.py:539–549` prepares source20's special SWA metadata from **the same kept_batch, block tables and slot mappings** as the other replay layers. Its `ReplayAttnMetadata(replay_start)` differs from the consumers' `_kept_kv_start`.
2. `sparse_swa.py:_build_deepseek_v4_metadata` assigns CPU sequence/query lengths from that same kept batch. Replay start only influences the exact GPU `prefill_gather_lens`.
3. `get_prefill_chunk_plan` uses CPU sequence/query lengths, window, compression ratio and configured capacity. It does **not** read replay start or exact gather lengths. It uses the conservative tail bound `query + clamp(seq-query, 0, window-1)`.
4. Therefore, equal kept sequence/query order and configuration give identical chunk boundaries, compressed-prefix width N, and combined width M, even when actual source20 and consumer SWA gather lengths differ.
5. Both `nvidia/flashmla.py` and `nvidia/flash_mla_mega_attn.py` use that plan, gather compressed KV at offset0, and gather each layer's SWA at offsetN. Reuse must keep each layer's own SWA gather and combined indices.

This is a dependency/dataflow argument, not object-identity reasoning. Executing the same planner with identical derived inputs is a check of the arithmetic and examples; it does not independently prove that a live deployment supplies those inputs. The pinned two `prepare_attn` calls supply the source-level equivalence evidence.

## Concrete 8K regimes

Window128, ratio1, head dimension512, BF16 workspace:

| Scenario | Kept query rows | Source20 actual SWA | Consumer actual SWA | N | M | Combined buffer/request |
|---|---:|---:|---:|---:|---:|---:|
| Ordinary complete8192-token prefill |8192|8192|8192|8192|16384|16MiB|
| Complete8192-token prefill trimmed to last128 rows |128|255|128|8192|8447|8.249MiB|
| Incremental64 rows at sequence8192, replay start8000 |64|191|191|8192|8383|8.187MiB|

The trimmed row uses source replay_start0 versus consumer8064. Source20 wrote full-batch KV before replay; its special attention metadata can see an older SWA prefix. The consumer's actual tail is shorter, but both retain the same planned capacity. No extra full-buffer clearing is needed; doing so would destroy the cached compressed prefix.

Ordinary and trimmed paths both have a source-supported eligible **single-request, single-chunk geometry**. Actual runtime activation of ordinary/replay path, batching, backend, and memory headroom is unverified. This does not assert that every agent-75 request executes this exact shape.

## CPU execution and saved workload scenarios

Executed `chunk_geometry.py`. It extracts the **exact pinned Python method AST** into `get_prefill_chunk_plan.extracted.py`, using small CPU integer-vector substitutes only for tensor subtraction/addition, clamp, floor division, zero creation and `.item()`. No torch/vLLM import, CUDA call, model load or GPU kernel execution. Added postponed annotations solely to run the unchanged method body under the available Python version; the original extracted method and hashes are retained.

The exact gather-length and kept-start equations are scalar transcriptions of the cited Triton kernels, explicitly labelled as such. They are not execution of those GPU kernels.

| Saved input set | Requests | Singleton scenarios executed | Plan mismatches | Scenarios with differing actual SWA lengths |
|---|---:|---:|---:|---:|
| Mooncake median |4004|16016|0|8008|
| Mooncake burst |4220|16880|0|8440|
| Mooncake cache-heavy |4053|16212|0|8106|
| Total |12277|49108|0|24554|

Each saved requested input length is evaluated with `query=min(length,8192)`, ordinary/trimmed variants and two replay-start scenarios. These are **constructed metadata scenarios from real input lengths**, not observed scheduling, prefix-hit or cache traces. All singleton scenarios fit one chunk. Their maximum combined capacities approach125–131MiB/request for the longest saved contexts; eligibility does not imply this is a good HBM allocation.

No pinned planned `max_model_len` or `max_num_batched_tokens` was found. Example calculations explicitly assume131072 and8192; a capacity sweep also uses32768 and16384. Source model maximum position is not substituted for CLI configuration. Batch scenarios with total query tokens exceeding the assumed capacity are marked inadmissible. Equality itself is independent of those capacity choices when source and consumers share them.

## Why the shorter SWA tail cannot reveal stale source20 values

Reviewer independently inspected `combine_topk_swa_indices`: each layer uses its **actual** gather length g. Gather start is `seq-g`. For a query position p, the selected SWA range begins at `max(p-window+1, 0, seq-g)` and ends at p; after subtracting gather start, emitted tail offsets lie in `[0,g-1]`. Combined length limits consumption to valid indices. Thus source20 tail cells beyond a later consumer's actual g are unreachable under the existing kernel contract. Original scratch already leaves unwritten padding; this proposal must preserve those masks and lengths exactly.

## Fixed-capacity allocation trap

Do not allocate `[B,max_M,D]`, slice `[:, :actual_M]`, and assume the current `view(-1,1,D)` has contiguous actual_M row spacing. For B>1, that slice retains max_M row stride; flattening may fail or change row mapping. The narrow design should reserve flat fixed-capacity storage and create a contiguous prefix view of the current required `[B,actual_M,D]`, shared by source and consumers, or explicitly support strides throughout. The former preserves existing kernel addressing without copying. Graph capture must still include the source fill on every replay and use a compatible plan; this report does not validate dynamic view/capture integration.

## Updated disposition and next bounded work

**Geometry objection resolved for the audited ordinary/trimmed dataflow. Implementation remains deferred.** A new hypothesis is not counted: this is an AT03 refinement.

Required remaining gates:

1. Complete source20 write/attention-read inventory and stream ordering; no compressed-cache mutation between designated fill and consumer reads.
2. Actual selected backend and graph path, including full vs piecewise replay and source20 fill dominance. An outer write-only source operation is not the fill site.
3. Fixed memory-capacity policy with per-lane/stream accounting, contiguous prefix view, warmup behavior and fallback when one chunk or capacity is unavailable.
4. Existing saved profiles, if available, must show material exposed gather work. No new GPU collection under current authorization. Without such evidence, retain unknown ROI.

Any future implementation keeps source-entry gather unconditional, per-layer SWA/indices/Q/sink unchanged, and falls back for unsupported multi-chunk/layout cases. Existing Mooncake and agent-75 remain the first service evaluators; this gate supplies no reason to invent a custom benchmark.


## Independent review completed

See `../review/round4/GEOMETRY_AND_WRITER_REVIEW.md` and `review.json`. Reviewer confirmed faithful exact-method extraction and independently checked the same-kept-batch premise. Their `tail_bounds.py/json` adds7,687 scalar boundary checks and a counterexample showing that caching source20 combined indices would change support after the SWA tail shortens; only the compressed representation is reusable.

The vLLM-side writer inventory is also positive: compressors are created only on KV-source layers; consumers21–39 have none. Source20 prewrite and ordinary insert precede its attention, and the inspected multi-stream helper waits for insertion completion. This supports source20 compressed immutability across the selected consumer stage. External FlashMLA/Mega input-mutation and length contracts still need dependency-pin inspection; Python input signatures do not prove them.

Updated next priorities are external reader contract, exact workspace resource-manager warmup/lock/lane behavior with CPU stubs, and saved batch metadata for real eligibility/capacity. **AT03 remains a source-supported diagnostic, not a proven optimization or an authorized GPU experiment.**
