# Round75 — reuse existing request mapping inside Engram hashing

**Outcome: one source-supported, deferred component for investigation; zero new typed hypotheses, implementation qualification or performance results.** The exact pinned V2 SWA metadata already carries an AV-aware token→batch-request mapping. Engram reads the same metadata object's query boundaries but independently searches them again. A direct pointer substitution is incorrect for padded rows. A guarded reuse design can preserve that difference without building another map or adding synchronization. Native validation and exposure remain unknown.

Target: planned Flash1017 revision1bae0e1088993b9b82de08f59de5be5a34e42170, callgideon/vllm c4557869393db4d75c483d92edd02a5125500883, B200 TP1/DP4/EP4 baseline d464. No runtime/image attestation is implied. Objective remains long-output ITL with existing quality, progress and tail guards.

## Prior recall and scope

Read the entire compact canonical inventory in one SQLite mode=ro transaction:147 identities, two pages, terminal next_offset=None; saved prior-inventory.json. This is literal retrieval plus manual comparison, not a proof of novel research. Read retained MP17 mapping,55 temporal staging,68 AV copy-elision reports and73 arithmetic candidate. Relevant identities are in prior-selected.json.

- MP17 publishes physical sparse Top-K slot IDs and lengths once per eligible index group. This component instead reuses an **already-produced per-input-token request index** in Engram's hash. No Top-K or page-table mapping changes; no source20/index-group reuse assumption.
- EG01 changes table activation representation; EG02 caches/deduplicates rows; A01 overlaps WKV;51 projected lookup reuse and55 cross-step staging require different ownership/exposure. Here all token history, table hash arithmetic, staging, WKV and events remain baseline.
- AV68 removes two overwritten same-step H2Ds. It is relevant to choosing the final device boundaries, not the work removed here.
- ER73 changes prime remainder arithmetic in the same hash kernel. This component changes only request-index discovery. No gain or timing is imported from ER73; competing optimizations in one kernel cannot have additive ROI assumed.

No relevant paper is needed to establish this exact existing-dataflow question. No online paper/PR calls were made. Recent-paper exploration is useful when it can change the decision, rather than supplying decorative citations to a source-proven common-subexpression opportunity.

## Actual dataflow

1. `input_batch.py:48–52,690–734` distinguishes `expanded_idx_mapping`: it is indexed by **logits** and contains persistent request-state slot IDs, with boundaries from cu_num_logits. It is not the batch request row index used by Engram; reject this tempting substitute.
2. V2 `model_runner.py:1449–1453` reallocates AV drafts before later metadata preparation. `CommonAttentionMetadata.token_to_req_indices` at backend.py493–514 explicitly reads **device query_start_loc**, since AV's CPU boundaries may differ per request. Its CPU final total supplies the mapped extent under the existing equal-total invariant; no CPU repeat-interleave reconstruction is appropriate.
3. The builder makes one map through `compute_token_to_req_indices` (ops/metadata.py10–50), cached on common metadata. `attn_utils.py:496,547,582` carries the cached tensor across compatible groups within the build, avoiding repeated mapping computation already.
4. Shared SWA builder sparse_swa.py619–621 obtains that map; return fields750–758 store both query_start_loc and token_to_req_indices. V4.1's builder delegates to it; this is target code, not a conventional-transformer assumption. The PCP>1 branch changes metadata, so it is excluded from the first bounded design.
5. `model.py:898–905` picks Engram's first local layer SWA prefix. At990–1018 the model retrieves **one swa_metadata object**, then gives its query_start_loc to NgramHashState.forward. The mapping is already in this same object. The current call and NgramHashState.forward signature do not pass it.
6. `engram.py:329–348` repeats an upper-bound search over request ends for every token vector and Engram-layer grid dimension, then loads the chunk-start position. The launch at562 is one hash kernel with grid `(ceil(num_tokens/32), num_layers)`. It is not forty separate layer launches or one launch per hash head. Current target Engram layout has two layers; the removed operation is the repeated boundary search within this existing kernel, not a kernel launch.

## Concrete incompatibilities and bounded repair

### Padding is not interchangeable

The existing metadata kernel stores request0 for `token >= num_mapped_tokens` (metadata.py29). Engram instead clamps its upper-bound search to `num_query_rows-1` (engram.py344), including repeated trailing boundaries. Example: query_start_loc=[0,2,2], mapped total2, hash input length4. At token2 or3, the cached map contains0 but native search returns1. These are source-derived integer values, not a native test. The subsequent chunk-start/history selection depends on req; do not assume padded output hashes or speculative history reads can change merely because attention eventually masks a row.

For a validated matching mapping domain, a possible existing-kernel adapter is:

- Keep query_start_loc, original chunk-start clamping, position/dead/history reads, XOR/modulo/offsets and output masking unchanged.
- Use mapped req only for rows before the **final device query boundary**, with masked pointer loads; use the original last-query-row result at/after that boundary, including inactive vector lanes. This preserves the native search result on trailing padding without a new reduction or host synchronization.
- Require nonempty query-row domain and map dtype/device/stride compatibility. For active rows the map must be produced from these exact device boundaries and the existing CPU mapped-total invariant must hold. Pointer identity across steps alone is insufficient.

This is proposed source reasoning, not an implemented adapter or native correctness proof.

### Extent and ownership admission

DefaultModelState.prepare_attn at184–190 uses padded token/request counts in FULL mode but unpadded counts in eager/PIECEWISE. Do not read mapping beyond its visible extent simply because a larger underlying allocation may exist. Initial admission can require `mapping is not None` and shape coverage of the entire hash input, otherwise retain the existing hash search. The shape check uses existing host metadata, not a device readback. Empty/profile paths keep their existing behavior. FULL source coverage is plausible; actual captured pointer/shape behavior must still be verified natively.

Use only the mapping attached to Engram's current swa_metadata, for this invocation and lane. Do not store it in cross-step Python state or fetch another layer's mapping. Metadata is constructed before model invocation; Engram runs its hash on the model stream before staging readers. Reusing an existing map introduces an earlier reader within that invocation, not an extra producer stream/event. Graph capture must retain the same existing owner and fresh contents each replay. No detached pointer cache is proposed.

Bounded replay does not justify claiming an alias bug: model_state.py522–547 uses copied attention groups for kept replay batches, and _copy_attn_groups at667–684 gives them their own builders. The original whole-input metadata remains the object selected at model entry. This source ownership is positive evidence, not an executed concurrency guarantee. First admission should exclude PCP and unsupported DBO/partial entry paths until the exact lane metadata and input coverage are checked; the existing fallback need not prohibit those baseline paths.

## Decision and next falsifier

Retain the component as deferred source-level work, without creating another formal card in this round. The source gap is real for the inspected route; it is not evidence of a material bottleneck. At batch1 the search is already very short. Reuse trades a vector search for an existing int32 map load plus a scalar end-boundary load/selection; register allocation, memory locality and compiled control flow can erase the saving. No launch, table lookup, hash arithmetic or output bytes are removed. All eligible-shape frequency, exposed hash time and service gain remain unmeasured.

The next decisive artifact is an existing exact-run dispatch/graph/shape record establishing the admitted V2 hash route and map/input extents. A saved representative CPU/device boundary+map dump could falsify the equivalence on padding, AV redistribution, mixed prefill/decode, request reorder, empty/dummy and kept-replay transitions; absent such a record, do not fabricate exposure with a new synthetic workload. Native implementation, captured execution and byte-exact hash/history differential tests require separate authorization. If admitted, compare A original, B guarded mapping reuse; any ER73 arithmetic arm must be held fixed or tested as a separate interaction, not credited twice.

Stop/park if no material eligible hash exposure exists, mapping reuse needs another map kernel/sync, or the required lane/extent invariant cannot be established cheaply. Unknown ROI alone does not refute the mechanism. No GPU, native/model import, repository change, new hypothesis/status transition or provider call occurred; only previously approved independent retention writers continue outside this scientific packet.
