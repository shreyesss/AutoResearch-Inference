# Round 105 — recent scheduling papers, selective cache-restoration accounting

**Disposition: zero new formal hypotheses, zero implementations, zero service qualifications.** One recent paper was read in full. Its restoration-budget cache reservation is retained as a conditional component, while its generic deadline scheduling overlaps prior work. No GPU, native/model imports, builds, serving changes, canonical writes or cloud publication occurred.

## Decision and selected component

[FairInference, arXiv:2609.18112v1](https://arxiv.org/html/2609.18112v1) separates scheduling delay from cache-restoration delay. It converts an allowed restoration delay into evictable cache capacity, then reserves the remaining fair share. This can be useful independently of the complete scheduler: choose eviction/preemption victims using the future recomputation cost that eviction creates, rather than only recency or request order.

That principle survives screening, but an actionable target intervention is not established here. The inspected implementation has two different operations: reuse of unreferenced cache blocks and preemption of an active request. A cache-only reservation patch cannot implement the paper's active-request guarantees. The paper's cost model and ownership rules also do not yet specify restoration of this target's hybrid compressed/SWA/shared-layer state. The next useful action is pressure/exposure attribution, not adding another scheduler or synthetic throughput estimate.

This is **not rejection of the paper for using a different engine**, nor a claim that unknown ROI alone disqualifies a useful experiment. The missing premise is which current eviction/preemption decision should change and which retained state would avoid an actual exposed restoration stall. The narrow source candidates already retained elsewhere have more concrete operations and correctness boundaries.

## Adaptive search and provenance

The complete retained 153-card compact inventory was inspected, with 76 scheduling/host/prefill-related records selected for comparison. It is a historical inventory, not a current canonical count. Standalone reports 59, 63, 65, 68 and 90 were also located/read or compared; compact recall alone does not cover later untyped screens.

1. A September–October arXiv query combined LLM with scheduler/prefill terms and broad `metadata`. All ten returned abstracts concerned dataset, tool or application metadata rather than serving execution. This was an agent-authored query-scoping failure.
2. The next query placed an LLM-serving/inference/prefill anchor outside the mechanism OR and removed metadata. It returned ten serving papers. All twenty abstracts have individual dispositions in `paper-dispositions.json`.
3. FairInference was selected because cache restoration accounting could add something beyond deadline-aware admission. Exact canonical title/ID lookup found no retained source, so one versioned fulltext was fetched through normal `investigate`: one HTTP cache miss, no provider error, no automatic citation/repository expansion.
4. A bounded readonly local PR recall using restoration/preemption/tenant-eviction vocabulary returned 30 rows. Three exact existing PR identities were imported through normal `import-corpus`; normal `pr-search` then inspected that selected subset. The latter is not an exhaustive search of the canonical corpus. No donor head/diff was fetched because body-level transfer objections already resolved the selected question.

Both actual paper searches used **after 2026-09-01 inclusive, before 2026-10-23 exclusive**. The original expansion recipes accidentally recorded null date fields because the dates were only in prose constraints. Root caught this. `*-dated-addendum.json` retains corrected offline expansions and the second recipe's `based_on` link to the first executed paper-query ID. Original plans/receipts remain unchanged; no search was rerun. This repairs provenance, not provider behavior or measured research quality.

The actual command journal is exported from `state/commands.sqlite`, not the deferred snapshot mirror: ten completed normal commands. Journal arguments are normalized/redacted persisted fields, not raw shell argv. State remains local with deferred snapshot; no S3 durability claim.

## What the selected fulltext supports—and limits

Sections 5.2–5.4 describe per-client usage, last-access ownership of shared blocks, a fair share, and a reservation derived from the number of blocks restorable within the cache-delay budget. The residual capacity may be evicted; running requests can also be retracted. This requires accounting and policy, not just inserting an extra comparison into ordinary LRU.

The scheduling component prioritizes per-token deadlines and below-share clients. This overlaps prior H01/B200-R7b/LP63 admission and interference work; it is not another new proposal here. The reservation component differs from CF59 projection overlap, HM65 dirty-array elision and AV68 dead-copy elision. It also differs from bounded-tail retention and prefix admission, although they address overlapping recomputation costs.

The donor implementation is SGLang 0.3.0, evaluated with Llama-3 8B and deployment-specific latency models. It reports roughly 20 ms added scheduling work per prefill and per series of ten decode steps. Those are author reports in a different system, not target measurements. This paper therefore cannot substantiate a claim to reduce our host scheduling overhead.

Its isolation guarantees depend on a modeled isolated execution, pooled-decode headroom, bounded arrival rates and restoration estimates. Section 5.5 explicitly limits guarantees for clients whose isolated decode is much faster than the chosen maximum pooled batch. The default single delay budget is measured in seconds in examples. Neither that SLO nor its fitted coefficients transfer to Flash1017. Model-estimation errors and shared-block ownership can change deadline behavior.

## Exact pinned target boundary

All target copies are from `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; source hashes, URLs and exact excerpts are retained. These are planned/source facts, not live runtime attestation.

- `vllm/v1/core/block_pool.py:666–698`: ordinary allocation removes blocks from the free queue and requires `ref_cnt == 0`. `touch` removes a zero-reference cache hit from that queue before incrementing its count. Thus ordinary cached-block eviction does not arbitrarily evict still-referenced active state. This does **not** claim all useful active/session state is always referenced: unpin/watchers and window-state policies need their own contracts.
- `vllm/v1/core/sched/scheduler.py:835–899`: when allocation fails for running work, the scheduler may preempt the lowest-priority request or the last running request. It checks whether block freeing is safe before selection proceeds. `955+` admits waiting work after running work; this is not the paper's old prefill-prioritizing loop.
- `_preempt_request:1651+` frees the request's blocks, resets computed-token accounting, clears speculative IDs and requeues it while preserving special handling of in-flight stale outputs. `_free_request_blocks:2857+` can defer frees across an asynchronous write lifetime. A reservation policy cannot bypass these guards.
- `kv_cache_manager.py:604–616,782–792` already caches eligible computed blocks. Freeing references does not imply every decoded token must be recomputed. Recovery depends on surviving reusable blocks and hybrid cache constraints. Counting all preempted tokens as saved work would overstate benefit.
- `Request` carries priority, cache salt, session and `client_index`, but the inspected block structure does not contain the paper's tenant fair-share/reservation state. `core_client.py:1333–1336` overwrites `request.client_index` from its frontend client instance. That routing identity is **not established as an end-user/tenant identity**.

No target class or native dependency was imported. AST parsing only located seven relevant methods; nine retained excerpts were checked against exact file bodies. This is a source audit, not nine correctness tests or an empirical cache trace.

## Single-tenant and prefix-class adaptation

Multiple tenants are not necessary for every useful component. With one client, the fair-share ordering between clients disappears, but a restoration-budget reservation could still protect inactive cached state. It would reduce allocatable cache headroom, possibly deferring new work or moving pressure into active-request preemption. The paper does not establish that this trade improves our workload.

Prefix/session classes could supply a policy grouping even in one service account. They must be deliberately defined: a shared prefix is not automatically an independent tenant; overlapping blocks require a charging rule; last-access ownership can transfer usage without changing physical storage. A byte or block count alone does not determine restoration cost for shared compressed KV plus SWA windows. A cost-aware variant should compare existing bounded-tail/prefix-admission policies rather than claim a novel fair scheduler from renamed prefix classes.

The retained agent-p75 workload describes eight prefix prompts, 8192 input and 1024 output tokens. Mooncake describes trace/hash-prefix reuse. Neither retained YAML establishes tenant shares, per-group eviction/restoration attribution or preemption frequency. No claim is made that the workloads never experience memory pressure; those data simply were not recovered in this bounded source exercise.

## PR triangulation and counterevidence

- **SGLang #45686**, retained opening body: priority preemption on KV exhaustion plus optional preservation of retracted KV. The target already has allocation-failure preemption, so that generic fix is not missing. The donor itself says kept-KV speed was not measured separately, notes long-answer tail regressions under aggressive preemption, and excludes SWA/speculative/DP-attention testing. Its best-effort unlocked retention is not the paper's reservation guarantee. No donor-code correctness claim is made without head/diff inspection.
- **Mooncake #4809**, retained body: tenant quota namespace policy explicitly unwired in that PR. This is an external object-store policy, not evidence of an active GPU block-pool reservation mechanism.
- **SGLang #45430**, retained body: preserve a prompt-end SWA window last. This is the already explored bounded-tail/prefix-state family; it is not cross-tenant restoration-budget accounting. Its reported times/gains are not transferred.

The remaining PR recall rows were title-level leads, not independently inspected implementations. The bodies are source-revision retained, but no exact head was hydrated or claimed.

## Cheapest next falsifier and evaluation boundary

First inspect already recorded target request/metrics data for **preemption events, failed allocations, cache reuse after requeue, recomputed rows and client-visible stalls**, with the exact model/source/config pins. Associate these with explicit policy groups only if the request data supports them. If no costly restoration is observed under the intended workload, park this policy without implementing it. Lack of a metric is inconclusive, not a zero counter.

If exposure is established, compare current victim selection, existing request priority, bounded-tail retention, and one explicit restoration-budget policy at equal capacity and arrivals. Required controls include shared-prefix charge transfers, referenced versus unpinned blocks, request finish/cancel/preemption, delayed frees, hybrid cache groups and DSpark output continuity. Preserve target weights/output policy and distributed collective order. A legal local victim order does not imply a profitable DP4/EP4 schedule.

The possible saving is exposed recomputation/queue delay actually avoided, minus accounting, reduced batching/headroom and replacement-victim cost. If the relevant restoration events do not occur, this mechanism saves none of that work. No latency, throughput, SLA or numerical ROI estimate is available here. Standard agent-p75/Mooncake evaluation can remain the service comparator; a tenant-isolation extension would be an explicitly different workload, not silently invented evidence.

## Yield

Two online searches; twenty unique returned paper identities/abstracts; one new selected fulltext; three retained PR bodies selected, zero donor diffs; six pinned target source files; seven AST method locations; zero runtime tests. Source export contains 24 documents, 26 immutable revisions and 126 edges (edges include imported historical provenance, not 126 read sources). One conditional component retained, zero new formal cards, zero accepted implementations or measured improvements.

Stop reason: the selected component is distinct enough to preserve, but further broad searches do not resolve its missing exposure/accounting premise. All first-query misses, abstract-only rejects, source-read path mistakes, truncated-output follow-ups and dated-plan corrections remain in the packet.
