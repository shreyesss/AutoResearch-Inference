# Independent review of round75: Engram request-map reuse

## Verdict

No blocker to retaining this as a deferred source component. The inspected target route really constructs a suitable mapping before Engram repeats the request-boundary search. A naive whole-buffer substitution is incorrect. The report's mapped-domain, padding, visible-extent and invocation-local guards are essential; native replay correctness and usefulness remain open. No new typed identity or implementation qualification is warranted by this review alone.

Verified all 25 author artifact hashes, all 13 source copies against the retained c455 checkout and 12 exact source anchors. Read the frozen report/component plus the decisive metadata, model, hash, AV and replay-builder sections. No executable model, tensor/native imports, GPU, compilation, network requests, new synthetic fixture or canonical mutation occurred. The integer padding illustration is a reading of source expressions, not an executed kernel test.

## Positive source evidence

The model retrieves one current SWA metadata object and passes its query_start_loc into NgramHashState. The same object carries token_to_req_indices. The target SWA builder obtains that map from CommonAttentionMetadata and returns both fields. This is stronger than matching two tensors by shape or logical data alone.

In V2, adaptive verification's reallocate_drafts follows the provisional H2D and precedes later attention metadata construction. The mapping kernel reads the final device query_start_loc. Its host mapped total uses the existing equal-total contract; a CPU per-request repeat-interleave would not preserve redistributed AV boundaries. This review does not broaden AV activation claims.

attn_utils initializes the mapping cache to None on each build and then shares it across compatible groups in that build. It is not an indefinite memo of old contents. Kept replay uses copied groups with their own builders; therefore no source evidence here establishes an alias race with original whole-input metadata. That ownership observation is not an executed concurrency proof.

## Admission and adversarial boundaries

**Padding:** metadata stores request 0 for token>=num_mapped. Engram's upper-bound search clamps to the final query row. With boundaries [0,2,2], tokens 2 and 3 differ. Keep the original last-row result at/after the final device boundary and preserve all chunk-start, history, position and dead-token operations. Do not justify changed padded hashes from an eventual attention mask.

**Domain and extent:** the returned map slice covers num_actual_tokens, not every byte of its underlying allocation. FULL metadata uses padded counts; eager/PIECEWISE uses unpadded counts. Require visible shape coverage for the entire hash input in the initial arm; otherwise use the original search. Pointer loads must be masked for inactive vector lanes as well as padding. Nonempty query-row domain, same device, int32 and admitted stride must be explicit. The final device total must agree with the mapping's mapped-total contract.

**Wrong map family:** expanded_idx_mapping is indexed by logits and stores persistent request-state slots. It is not a substitute for input-token batch request rows.

**Freshness and lifecycle:** same object or fixed allocation address is insufficient across calls or replay. Consume the mapping attached to this invocation's selected metadata, after its producer, without retaining a detached pointer or adding a map-production launch. Keep PCP and unverified DBO/partial-entry lanes outside initial admission. The model itself already has a V2 DBO lookback limitation; do not present this optimization as repairing it. Empty/profile/dummy paths retain baseline behavior.

## Strongest objection and next check

The strongest integration objection is fresh semantic content on the actual graph/lane path, not mathematical upper-bound equality on ordinary rows. The source order supports the proposed same-invocation route, but does not certify captured pointer/extent behavior for every runtime path. The cheapest next artifact is an existing exact-run route/metadata/graph receipt or saved device boundary/map dump. If unavailable, record that absence rather than generate a synthetic exposure estimate. Later authorized native differential checks must cover AV redistribution, padding, request reorder, mixed batches and replay transitions.

The search is short at small batch size; an extra map load, scalar boundary read and selection may not improve the compiled hash. No kernel launch, table lookup, hash arithmetic or output traffic is removed. The two Engram grid dimensions do not justify a factor for all decoder layers. ER73 changes a different operation in this same kernel, so any combined benefit requires an interaction control rather than summing forecasts. Existing service tests remain the evaluator; no new benchmark distribution is supported by this source review.
