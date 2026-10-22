# HS30-01 review refinement: the repeated work is smaller than an insertion

Same deferred HS30-01 direction; no new hypothesis identity. Original author packet remains unchanged. This addendum incorporates root's source review and narrows the operation and possible implementation.

## Corrected work accounting

At the pinned target, `BlockPool._get_partial_block_hash` indexes an already computed request hash. It does **not** recompute the prefix cryptographic hash. `_insert_block_hash` returns immediately if the requested key is already the block's primary hash, or after another presence lookup if the alias already exists. Thus repeated calls in the original probe are **not repeated map insertions or hash computation**. The original report's wording "enters insertion bookkeeping" must be read as entering this already-fast-pathed helper, not performing an insertion.

The original 1024-call probe only established caller reachability under synthetic geometry. It did not establish 1024 expensive cache mutations. This correction lowers materiality further.

## Lower-risk alternative within the same direction

Consider returning the already calculated `block_hash_with_group_id` from `cache_partial_block` when `already_cached and not replace_existing_hashes`, before calling `_insert_block_hash`.

The current intervening promotion/removal branch requires `not already_cached`, so cannot execute in this arm. The later stored-event branch also requires `not already_cached`. The existing insertion helper would either return on primary equality or repeat the alias-presence check then return. This narrow shortcut therefore removes one helper call, and in the alias case one duplicate presence lookup. It leaves prompt boundary computation, request-hash lookup, key construction and the first presence check intact.

Unlike donor request-local memoization, this candidate arm adds no persistent memo and rechecks current alias ownership on every call. It consequently avoids introducing a separate memo invalidation protocol. Production correctness still needs the actual block-map implementation and lifecycle tests; the source argument is not permission to modify serving code.

**Replacement must remain active.** If `replace_existing_hashes=True`, even an existing alias must be removed and re-established according to current behavior, including events. Returning solely on `already_cached` is incorrect.

## Donor transplant warning

Donor head `b00d7cc0829c3b1ca2fd638a3f9bb61b9fc9f837` computes the prompt boundary directly from `request.num_prompt_tokens`. Current target uses full prompt for EAGLE groups and `prompt_len-1` otherwise. Copying the donor's entire helper would lose that newer semantic distinction. Any memo arm must retain the current boundary and caller rules. The stateless pool shortcut leaves them untouched.

## Bounded CPU check actually run

`probe.py` AST-extracts six actual pinned BlockPool methods, then constructs a diagnostic version with the single early-return condition. No repository code was patched. Block/map/event objects are explicit small fixtures, not the real imported allocator.

* 24 cases compare return value, primary hash/length, alias set, map keys and emitted fixture events: existing primary, existing alias, new alias, primary promotion, fresh block and null block, each with replacement/events enabled or disabled. These observations match.
* Existing-primary repetitions: baseline enters insertion helper1024 times and performs **zero map insertions**; shortcut enters helper0 times and still performs zero insertions.
* Existing-alias repetitions: baseline performs2048 presence lookups and1024 helper calls; shortcut performs1024 lookups and0 helper calls. **Both perform zero map insertions.**
* Deliberately omitting the replacement guard changes primary/alias/event observations and is detected.

These are finite source-control and fixture-state checks, not production BlockPool integration, thread-safety, scheduler replay, latency, GPU or endpoint tests. No timing was collected. All original runtime geometry/exposure gates remain.

## Decision

Keep HS30-01 **deferred and low priority**. Prefer investigating this stateless shortcut before a persistent per-request memo if real traces show sufficient repeated helper cost. The memo may avoid more work but has a larger correctness surface. Neither arm inherits donor throughput numbers. Count them as alternatives addressing one repeated-bookkeeping direction, never additive gains or separate accepted hypotheses.
