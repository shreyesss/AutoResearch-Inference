# AT03 independent round4 audit: geometry, tail visibility and writers

## Outcome

**The source20-versus-consumer SWA geometry objection is resolved for the inspected ordinary/trimmed replay construction, under the same pinned config and request ordering.** Different actual SWA gather lengths do not change the planned compressed prefix offset or row stride. Shorter consumer tails do not expose stale source20 tail values when each layer regenerates its own combined indices/lengths. This remains a CPU/source result; implementation, device correctness and benefit are deferred.

## Independent review of worker planner execution

Reviewed `round4-source20/chunk_geometry.py`, exact extracted method, JSON and report. The script executes the original Python `get_prefill_chunk_plan` body. Its integer-vector stubs faithfully cover the operations used here (integer subtraction/addition, clamp, floor division, zeros_like and scalar item) for equal-length nonnegative scenario vectors. It does not execute Torch tensors or the Triton gather metadata kernel. The source and consumer planner calls use the same arguments: by themselves they establish dependency invariance, not independent proof that runtime supplies identical arguments.

That additional premise is supported by source:

- `model_state.py:518–549` passes the **same kept_batch**, block tables and kept slot mappings to both metadata builds. The special first-SWA replacement changes only `ReplayAttnMetadata(replay_start)` versus `_kept_kv_start`.
- `ReplayAttnMetadata.get_extra_attn_kwargs:166–172` supplies replay_start only to SWA builders.
- `sparse_swa.py:984–989` derives CPU sequence and query-length fields from common batch arrays, independently of replay_start. Window and maximum sizing fields come from common config.
- `get_prefill_chunk_plan:260–337` uses those CPU fields and configuration; it does not read replay_start or the computed actual gather length.
- `_gather_replay_batch_kernel:137–144` changes kept KV start only when a request is trimmed. Worker scalar transcription matches that condition for its scenarios; the model's `_keeps_rows_np` and real scheduler selection are not replayed by those scenarios.

The49,108 singleton cases are generated query-split scenarios over12,277 saved input lengths, **not49,108 observed scheduler batches**. They do not estimate eligible-group frequency. Defaults131072/8192 and extra batch-capacity sweeps remain declared assumptions. Mixed-vector examples exercise chunk arithmetic; actual mixed decode/prefill partition and padding still need a dispatch integration check.

## Spatial proof for stale SWA tails

Let `s` be sequence length, `q` query length, `r` replay start and `W` window. The metadata kernel uses

    g = q + min(max(s-q-r, 0), W-1)
    gather_start = s-g

For valid queries, `g>=q`, so `gather_start<=s-q`. Query position `p` is within `[s-q,s-1]`. The combine kernel sets

    swa_start = max(p-W+1, 0, gather_start)
    swa_len = max(p-swa_start+1, 0)

Every emitted SWA address relative to its tail is consequently within `[0,g-1]`. The physical workspace address adds the unchanged `M*batch_idx + N`. Compressed addresses are separately restricted to `<N`. Therefore, after consumer gather overwrites only `[N,N+g_consumer)`, old values at `[N+g_consumer,N+g_source)` are not emitted by that consumer's freshly computed indices.

Code: `cache_utils.py:1073–1129` computes these per-layer values and writes `combined_len=topk_len+swa_len`. Both FlashMLA and Mega pass this length to attention. This relies on the same existing length/masking contract as the baseline; baseline scratch already leaves unfilled padding and unused index entries. We have not independently validated external kernel implementation of that contract in this round.

Executed `tail_bounds.py/json`:7,687 scalar boundary checks had no emitted tail index beyond its actual gather length. This is arithmetic verification, not a device test. A separate counterexample shows why **source20 combined indices must not be cached**: after255→128 tail replacement at seq8192, old last-query indices yield127 unique positions instead of128. Retain only compressed representation; recompute every layer's own SWA indices and lengths.

## Source20 writer inventory and ordering

Pinned-config source layers are2,8,14,20; consumers21–39 are not sources.

| Operation | Source ownership and ordering |
|---|---|
| Normal compressed main-cache insertion | `attention.py:591–600` constructs compressor only for `is_kv_source`; `:925–933` inserts before sparse attention. `compressor.py:386–418` resolves its own `k_cache_prefix` and writes via `rope_quant_insert`. |
| Full-KV prewrite for trimmed decoder replay | `model.py:843–869` binds source20's `write_kv`; `decoder_replay_layers.py:71–78` invokes it before entering replay layers. |
| `forward_kv` path | `attention.py:727–732` inserts compressed KV only when the layer owns a compressor. Source20 prewrite can occur; consumers have none. |
| Consumer ordinary KV preparation | `_prepare_and_attn:875–897` always prepares local SWA; compression path is absent when compressor isNone. This is not a compressed source20 write. |
| Indexer key publication | Owned index K is a separate cache; post-source indexers share it. Do not confuse it with main compressed representation. |
| Attention/gather input reads | Python dataflow treats compressed source/cache and gathered prefix as inputs; exact external FlashMLA/Mega mutation contract remains to be inspected at dependency pin. |

`multi_stream_utils.py:43–63` makes the current stream wait for auxiliary insertion completion before returning, or executes sequentially; breakable capture disables the auxiliary path. Thus the inspected source20 insertion is ordered before its attention gather at the source level. Consumers21–39 have no normal compressed-cache writer. This supports the stage invariant in the selected path; it does not certify arbitrary connectors, runtime patches, reentrant invocations or device races.

Source20 refresh must occur **inside its actual prefill attention invocation**, including each nested replay group. Source20 main-cache prewrite and ordinary source20 call can both happen before consumer21; unconditional fill after source20 preparation covers that sequence. No epoch counter is necessary for this bounded design.

## A concrete remaining layout trap

A persistent tensor `[B,maxM,D]` sliced to `[:,:actualM]` retains row stride`maxM*D`. Current kernels flatten `kv.view(-1,1,D)` and combined indices use stride`actualM`. For B>1 this may fail view compatibility or address the wrong row. The worker's correction is necessary: allocate stable **flat** storage, take the contiguous required prefix, and reshape to current `[B,M,D]`; alternatively explicitly change every kernel's stride contract. Do not silently keep capacity stride while emitting compact indices. The fixture records this distinct address mismatch too.

## Remaining gates and priority

- Inspect pinned external attention dependency for input-write behavior and length contract; Python signatures alone do not prove constness.
- Exercise actual workspace resource-manager key/lock/warmup logic with CPU stubs; separate ubatch/lane/concurrent stream allocation. The model's serial lane simulation does not test this.
- Freeze eligible layout, source20-first dispatch, one chunk, adequate prewarmed flat capacity, and fallback outside the supported domain. Do not use a host capture-time boolean as runtime freshness.
- Use saved *batch* metadata if available for actual eligibility and peak capacity. Input-length scenarios alone cannot quantify workload coverage or lost KV capacity.
- Future device differential tests and paired benchmark timing remain required and unauthorized now.

AT03 remains the highest-priority bounded diagnostic among these prefill leads because the target repeated work is source-demonstrated and uses existing kernels. AT01's numerical envelope is a larger port whose useful compressed-domain exposure is uncertain. Neither has demonstrated an improvement in the frozen decode-ITL objective.
