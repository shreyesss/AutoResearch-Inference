# AT03: external reader and workspace contract audit

## Decision

**A bounded adapter is source-plausible. Selected SM100 sparse and Mega prefill kernels read the supplied BF16 KV and write separate outputs; existing workspace ownership can isolate a retained prefix.** This resolves the earlier missing external-reader source at the configured dependency pin. It is not compiled-code, CUDA race, graph-replay or output-equivalence proof. AT03 remains deferred implementation/target validation, with no new hypothesis count and no GPU execution.

## Exact dependency chain

Pinned target `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883` CMake blob `daec85069c82aaa25e00d7390f01281d29b1351f` selects `vllm-project/FlashMLA@5dceadbd9eabc9acfc547ef18ec8f7b14b980682`. CMake vendors the Python interface from that checkout and changes its torch-ops import. `FLASH_MLA_SRC_DIR` can override it; the live build's source override/binary remains unknown. The selected sources cover SM100 H64/dim512 sparse prefill and fused Mega prefill used by the planned TP1 target, not every dispatch/hardware variant. Full tree and nine pinned files retained with hashes.

## Reader contract: stronger than a function-signature guess

- `csrc/api/api.cpp:10,12` marks only optional output tensors mutable in operator schemas; KV is an input. This declaration alone is insufficient, so implementations were inspected.
- `sparse_prefill.cpp:208–230` puts KV pointer into `SparseAttnFwdParams`, allocates separate lse/max_logits, and accepts caller output. Selected H64 kernel `phase1.cuh:640–665` puts KV in a TMA source descriptor. Producer at418–477 uses TMA gather into shared memory. Global stores at321–323 and400 onward target max_logits/lse/output, not KV.
- Mega API `fused_norm_rope_attn_rope_cast_fwd.cpp:201–244` uses separate output-FP8/scales plus lse/max_logits. Prefill kernel `core_attn/kernel.cuh:1512–1570` gathers BF16 KV into shared-memory slots; descriptor1643 onward references input KV. Writes to dequantized “KV slots” elsewhere are shared memory and/or decode-specific, not writes into the global BF16 prefill input. Output global stores at792–794 target out_sf/out_fp8. No global write to the prefill KV input was found in the selected path.
- Both APIs launch on the current CUDA stream. Existing target caller allocates attention output separately, while the proposed retained KV must be a dedicated allocation. Do not permit output/KV aliasing merely because the API accepts both tensor arguments; it does not check all alias possibilities.
- Mixed prefill/decode does not inherently overwrite retained BF16 KV: target decode reads the original packed compressed cache through its separate path. This does not prove arbitrary overlapping/reentrant invocations safe.

## Important padding/NaN caveat, and why current target is compatible

FlashMLA interface237–238 warns that a **valid padded index beyond topk_length pointing to NaN KV can contaminate output**. Thus “topk_length masks everything” would be an overclaim. The actual target wrapper `cache_utils.py917–965` fills the entire combined-index output with -1 on every call, then writes current valid compressed and SWA entries. Keep that fill and regenerate indices/lens per layer. Do not reuse a prior layer's indices or leave stale in-range padded entries.

The earlier round4 SWA-tail proof shows currently emitted SWA indices address only this layer's newly written tail. Together with explicit -1 padding, this keeps a longer source20 tail outside the consumer's valid support. It does not authorize dropping initialization in a proposed faster variant. Zeroing all retained KV is unnecessary solely for these padded entries under the inspected index contract; exact NaN/corner tests remain future validation.

## Workspace ownership and lifecycle

`WorkspaceManager` supplies distinct persistent-resource maps for `(dbo_current_ubatch_id(), workspace_lane)`. DBO IDs are thread-context based (`ubatching.py154–157`), not inferred from CUDA streams. `gpu_worker.py121–128` gives V2 DSpark two lanes; runner208–210 selects draft lane1 and wraps draft calls/capture. Target uses lane0. The manager initializes two ubatches when DBO is enabled (gpu_worker555). Each local process/device owns its manager.

`get_persistent_resource`127–153 retains an object and returns it for the same key; new resources are forbidden after lock. It does not protect the object from caller resize, add stream isolation, or track per-step validity. Its own documentation requires callers not to resize/replace tensor storage after lock and to include a stream dimension if uses overlap.

`gpu/model_runner.py1130–1133` locks workspaces after actual capture. Both current attention dummy paths reserve only ordinary scratch (`flashmla.py97–123`, Mega289–303). A retained resource therefore needs explicit warmup in **every eligible target ubatch/lane before lock**, including no-real-metadata dummy runs. Creating it lazily on the first real prefill would assert after capture. The source20 unconditional fill must execute during each actual invocation/replay, not only warmup/capture.

Ordinary `get_simultaneous` allocations are shared scratch; any intervening layer can overwrite them. A new resource must use independent persistent storage. Persistent factory execution is not wrapped in `_alloc_context` in this source, unlike scratch allocation; sleep/pool accounting must be explicitly handled if that feature is used. Manager lifetime ownership alone is not a guarantee of a desired memory-pool tag.

CPU execution of the exact selected manager methods (`workspace_contract.py/json`) confirms four independent resources for2ubatches×2lanes, factory called once per slot, stable same-key object, rejection of an unwarmed key after lock, and rejection of an unconfigured lane. **This checks Python ownership/control only**, with object factories and no torch import; it does not test GPU allocation, streams or graph pointers.

## Bounded adapter design

1. Restrict initial implementation to source20 and consumers21–39, compression ratio1, selected BF16-gather prefill backends, unchanged source group and **a single matching chunk plan**. Multi-chunk calls use the original path: source20's loop otherwise overwrites chunk0 with later chunks before consumer21 needs chunk0. Supporting multi-chunk reuse later requires separate retained prefixes per chunk and an explicit memory budget.
2. Preallocate one flat BF16 backing store for the group per eligible ubatch/lane, with a stable key containing model/group identity, dtype and a fixed configured capacity. Add a stream dimension only where actual concurrent uses exist and prewarm those exact keys. Do not key by request or variable shape, which would grow memory and fail after lock.
3. For eligible current shape, take a contiguous required-length prefix and view it as `[chunk_size, chunk_M,512]`. Do not slice a `[B,maxM,D]` allocation to `actualM`: row strides would stay maxM while existing flatten/index arithmetic assumes actualM.
4. At source20, after original compressed insertion/event join, always gather compressed prefix into this store. Consumer21–39 skip only that gather, overwrite their current SWA portion, and call the original full -1 index fill plus index/lens generation. Outputs and temporary index buffers remain separate.
5. Source20 and consumers independently evaluate the same static eligibility/geometry contract. No cross-call generation oracle, reuse-after-source-absence, or persistent Python “valid” boolean is needed. Unsupported plan, capacity, backend, source group or execution layout follows original gather throughout the group. Ordinary and replay paths must preserve source20 entry, as earlier wrapper audit established for this source pin.
6. Keep allocation pointers fixed across capture/replay. Prewarm capacity before memory accounting/lock; never grow it under graph execution. Reinitializing the manager or changing capacity requires rebuilding dependent graphs. Use the existing current-stream ordering and verify no new auxiliary stream consumes the retained storage without an event.

## Memory and expected benefit boundary

PREFILL_CHUNK_SIZE is4 (attention.py209). Blindly duplicating the old worst-case scratch bound creates a substantial allocation: for illustrative max_model_len131072, max_num_batched_tokens8192, window128, head_dim512, a four-request BF16 combined buffer is `4*(131072+128+8192)*512*2 = 570,949,632 bytes = 544.5 MiB` per warmed slot. Those limits are planning inputs, not verified live configuration. Two ubatches multiply the resource footprint. A fixed byte cap with fallback can limit incremental memory; its value must be chosen from actual memory and workload evidence.

This is primarily prefill work/TTFT reduction, with possible mixed-load interference relief. Read-only correctness and a donor's fewer calls do not establish lower frozen long-output ITL. No measured target latency gain, GPU compatibility or performance result was produced here.

## Remaining decisive checks

- Fingerprint actual loaded FlashMLA extension and relevant flags/overrides from saved or future authorized environment evidence.
- Implement bounded resource path with shared eligibility and meaningful memory accounting, then CPU metadata/branch tests.
- Under future GPU authorization: exact gathered-prefix/output equality, short/long/mixed and NaN/sentinel cases, graph replay with changed same-address source, lane/ubatch concurrency and capture memory; then paired serving measurements.

The current result supports selective adaptation; it does not require rejecting AT03 because external input mutability was previously unknown.
