# Round14 — bounded DSpark context-row projection

**TR01: retain one known upstream component-port investigation, deferred and low priority.** No GPU, model load, serving patch, node probe or canonical write. No predicted service improvement.

## Discovery and exact source gap

The pinned `c4557869393db4d75c483d92edd02a5125500883` DFlash/DSpark proposer prepares context KV over the full current target-hidden span. Slot generation marks rejected or evicted rows PAD, but projection still runs before insertion. Exact Flash1017 config has three draft layers40–42, all compress_ratio0 and sliding_window128. Their noncausal attention reads a shared trailing128-token context window plus the query block. These facts leave a plausible opportunity to omit earlier current-prefill rows when no other consumer can need them later.

A local search returned26 DFlash/DSpark records. PR61261 referenced [PR60320](https://github.com/vllm-project/vllm/pull/60320), absent from the local corpus. Fetching its exact head `69a504902ad6296f46567d8d9d4a2abf0a085470` found this intervention already implemented upstream, currently open/unmerged in the saved API response. This is useful component recovery, not an original algorithm.

The donor reports GB200 context-path2.57→about0.2ms, but TTFT differences only0.3–1.3%, with every95% bootstrap interval including zero. Its TTFT workload uses synthetic acceptance and output length1. It does not establish a gain for our long-output ITL objective. The donor also trims auxiliary-hidden combination, which our initial conservative arm retains; its small step saving therefore cannot be assigned to our narrower arm.

## What the initial intervention would change

Keep original hidden-state combination/main_proj, all metadata initialization, captured FULL graph prefix, query forward, confidence, sampling and collectives. For eligible eager context work only, gather per-request tail rows and project/store those rows. Preserve original positions and each layer's slot mapping. No global compaction of buffers read by the captured graph.

For a request's flattened target span `[s,e)` and captured prefix `[0,G)`, retained eager rows are:

```
[max(G, s, e - (W + Q)), e)
```

The whole graph prefix remains untouched. This must be computed separately for each request; taking the last133 rows of the entire batch loses other requests. For initial implementation design, prefer no-draft-scheduled pure-prefill batches with exact host spans. Adaptive GPU request-budget reallocation can make CPU bounds differ from device `query_start_loc`; fall back instead of adding a synchronization to recover them.

This scope deliberately forgoes the donor's main_proj reduction and avoids changing graph-stage indexing. It is a correctness-first adaptation, not a completed implementation.

## Why133 can be a safe bound—and when it is not

Let E be actual absolute scheduled end, R rejected suffix, A=E−R, M=max model length, Q=query-block length and W=largest required draft window. Native prepare sets `seq_len=min(A+Q,M)`; native noncausal attention starts at `max(seq_len-Q-W,0)`.

If E≤M and R≤Q, then:

```
R + max(0, A + Q - M) <= Q
```

Therefore W+Q rows counted from actual scheduled end cover both rejection and the maximum-length clamp. Native anchor DSpark defaults Q=5, W=128, giving133. Ordinary DFlash can use Q=6; never inherit it silently. Keeping W+R alone fails near the clamp; using causal127 fails the native noncausal window.

These are interval premises, not proof of actual live metadata. Pure prefill has zero rejected tokens in the pinned sampler helper. Any broader path must prove its effective rejection bound, absolute end and row spans. Unknowns fall back. Rows from previous chunks still required by the current window must stay resident; this is not a cache-eviction proposal.

## Prefix caching is the main lifetime gate

Earlier rows unused by the present request could be needed when a later request reuses a shorter cached prefix. Require prefix caching already off **or every relevant draft group non-prefix-cacheable**. Do not disable global caching merely to activate this optimization.

The pinned defaults are global prefix caching=True and `swa_bounded_replay=True`. In the supported V2/CP1 source path, the latter propagates into draft SWA cache specs, whose `prefix_cacheable` property is `not bounded_replay`. Thus source defaults can satisfy the gate while retaining global prefix caching; actual effective group settings are unverified. Existing target bounded replay rebuilds a needed suffix after a prefix hit; that reconstruction contract must remain intact.

Also require no KV connector/transfer consumer, no context-anchor override, pure finite-window groups, supported position/slot mapping and no profiling/dummy/capture shortcut. A full-attention group or external consumer invalidates the crop. Preemption/restart/prefix restoration must rebuild newly needed state. Metadata still initializes the full span, including PAD/zero entries, to prevent stale graph reads.

## Source adaptation versus direct port

The donor predates the pinned FULL graph context preparation changes. Its global compaction in `propose` cannot be applied verbatim to current `_prepare_graph_forward`/`_prepare_graph_replay`. The current captured prefix and eager tail partition target rows; neither is duplicate whole-context work.

PJ01 removes discarded projection **columns**; TR01 removes unused **rows**. R2-03 removes unused **query work**, which has different confidence/state dependencies. Target SWA bounded replay concerns replaying target computation, not this draft projection. They are related but distinct mechanisms. Row and column improvements share a denominator: evaluate baseline, row-only, column-only and both, rather than add percentages.

## CPU checks actually executed

`python3 context_row_bounds.py`:

-6720 cases using extracted pinned noncausal-window expressions.
-24 ragged graph-prefix/eager-tail interval cases.
-12 monotonic chunk/decode trajectory steps.
-Seven counterexamples: causal127, omitted rejection margin, ignored clamp, global-tail packing, shorter-prefix reuse, stale CPU adaptive boundaries and a full-attention group.

The proposed fail-closed gate predicates are supplied assumptions, not extracted runtime validation. No real cache, tensor, token output, quantization, stream or kernel executed. Result: **inconclusive for runtime correctness and ROI**.

[Independent review](INDEPENDENT_REVIEW.md) separately checks116,372 interval cases and preserves the same limits. These are mathematical cases, not thousands of serving tests.

## Paper triangulation and negative findings

One online OpenAlex query returned six papers, all retained with original revisions/query edges. [Windowed-MTP](https://arxiv.org/html/2607.21535v1) was read in full: it limits a previously full-attention draft's context, while our draft already has SW128. Its direct change is redundant here; the useful principle is accounting for draft cost and eliminating state that no consumer reads. No reported speedup is transferred.

The other five papers received abstract triage: mobile-cloud placement/relaxed acceptance, far-memory repositioning, cardinality query scaling, trained decode-branch architecture and dynamic sparse recall. None established a more direct compatible way to remove already-unused native rows. This is a scoped exclusion, not a paper-wide rejection. Query expansion followed PR61261's concrete citation to60320, rather than another broad paper query.

## Evaluation plan and priority

First inspect an existing immutable deployment manifest for cache-group eligibility, connectors, exact sampler layout and adaptive reallocation. No new node probe is authorized in this work. If eligibility is absent, keep the direct port inactive; do not trade away prefix-cache benefit.

Later authorized component correctness must cover required KV values/slots across repeated chunks, final and unfinished prefill, rejection, max-length clamp, ragged batches, FULL/eager split, prefix restoration and preemption. Final target output alone can conceal draft-cache degradation. Measure gather/projection/insertion work separately and count how often eligible long-prefill batches occur.

Agent-p75 and Mooncake remain appropriate endpoint evaluators: fixed configurations/traces, real rejection, paired runs, ITL/goodput plus TTFT/E2E/tail/error guards. Add boundary correctness fixtures and component attribution, not a new service benchmark. The donor's2048 omitted-row threshold is an unqualified heuristic for our hardware/workload.

Ordinary small decode steps are unchanged. Mixed-prefill interference could affect ITL indirectly, but that link is unmeasured. This is therefore lower priority than an intervention with established exposed decode cost. Stop if compatibility fails, eligible exposure is negligible, or component savings do not improve the actual objective.

## Retention

`candidates.json`, `RETENTION_PACKET.json`, source/API files, original paper records/revisions, command history, local search, CPU artifacts and independent review are retained. One deferred direction, zero accepted implementations, zero measured service wins. Canonical import/S3 publication are not claimed.
