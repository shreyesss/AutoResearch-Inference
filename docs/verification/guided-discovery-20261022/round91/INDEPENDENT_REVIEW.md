# Independent review: round91 terminal exposure

## Verdict

**No blocker within the stated scope.** Detailed speculative metrics are scheduler-count metrics and do not determine effective AV terminal full-pass eligibility. The report correctly preserves FV86's deferred status, unknown exposed cost, and bounded prior-evidence coverage. No GPU/model/native execution or canonical changes occurred.

Verified all11 author manifest files, seven exact quotes against their immutable exported revisions, and six pinned-source file hashes. Replayed the author's stdlib witness only in a reviewer-owned copy; its JSON matches exactly. This is a replay of the same implementation, not independent native validation.

## Independent dataflow check

- Scheduler `update_from_output` reads `len(scheduled_spec_decode_tokens[req])`, subtracts grammar-invalidated count for metrics, and computes accepted count from sampled output length. Metrics observation precedes stop handling. `RequestSpecDecodeMetrics.observe` directly appends these inputs; aggregate per-position metrics have the same scheduled denominator.
- V2 runner creates CPU counts from the scheduled lists. AV `compact_batch` distributes a CPU budget evenly for layout; it does not mutate the scheduled lists. `reallocate_drafts` writes GPU capacities and GPU cumulative logits/query boundaries. The sampler receives those effective boundaries.
- `ModelRunnerOutput` has no effective-capacity field. `AsyncOutput.get_output` trims sampled token lists to the returned count and fills logs/masks/aux outputs; it does not overwrite scheduled draft lengths or inject AV capacities into metrics.
- Scheduler `update_draft_token_ids_in_output` can modify the lists for grammar validation but explicitly pads back to the original scheduled length; its separate invalid count is already accounted for in the report. It is not AV feedback.
- A bounded search of the V2 worker's scheduled-list writes found the warmup builder, not an AV-to-scheduler replacement. This is supported by the inspected call chain, not a repository-wide impossibility claim.

Thus identical accepted2/scheduled5 can describe either admitted2/full-pass or admitted5/partial-pass. The author witness is an information-loss illustration, correctly not an actual AV trajectory. My separate `fixed_budget_control.py` adds two requests with the same scheduled/accepted arrays and total budget7, but admissions [2,5] versus [5,2]. Positive monotone confidence-survival scores permit both arithmetic allocations. It establishes that a known aggregate budget alone need not remove the ambiguity. It does not establish model prevalence, native selection behavior or a timing benefit.

## Useful additional existing path, not a contradiction

There is an optional host-visible scalar path outside these metrics:

1. `rejection_sampler.py` calls `get_num_sampled_and_rejected` with effective GPU `input_batch.cu_num_logits`.
2. `input_batch.py` computes rejected = effective logit count minus sampled count (with a separate chunked-prefill override).
3. `AsyncOutput.__init__` copies this rejected count to CPU **only when a pending auxiliary output exists**.
4. The routed-expert auxiliary connector consumes it to discard rejected rows. `AuxRequestOutput` exports token start and rows, not the rejected count or admitted capacity. No connection back into `RequestSpecDecodeMetrics.observe` was found.

For eligible one-bonus verification, sampled plus rejected minus bonus can recover admitted drafts if this scalar is actually retained. This is a possible collection point, not evidence an existing run saved it. Auxiliary capture activation, its AV boundary correctness, output retention and cost were not established here. Enabling a potentially large routed-expert capture solely to collect one scalar is not automatically the cheapest approach. The report's preference for existing effective-capacity evidence or a small separately authorized diagnostic remains appropriate.

## Strongest limitation / cheapest remaining check

The matched-observable witness fixes only the named metrics, not every possible output or hidden GPU state. That is exactly its claim. An artifact with effective admission, a native terminal flag or suitable retained rejected counts would invalidate a broader absence claim; the report explicitly allows those alternatives.

Before any future collection, inspect a concrete compatible artifact for one of those effective fields and exact branch/source identity. If none exists, design a minimal asynchronous scalar/flag diagnostic around the existing output path. Standard workload latency alone cannot establish terminal eligibility or synchronization/numerical correctness. High eligibility frequency still does not establish exposed residual savings.

Read both prior local/remote applicability reports completely. They are bounded inspections with older runtime/model and forced-token limitations, not global proof that no compatible evidence exists. This review made no new remote query or large trace scan.
