# Round61 — ongoing request ownership inside an EP group

**Disposition: one new source-grounded candidate for deferred investigation; zero implementation-qualified or measured improvements.** No GPU, model/backend import, live-node inspection, serving change or canonical mutation. The target is the frozen Flash-1017 source plan at `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, checkpoint config `1bae0e1088993b9b82de08f59de5be5a34e42170`, TP1/DP4/EP4 with native DSpark. It is not a live deployment attestation. Parent review and typed retention are separate from this report.

## 1. The missing component and why it could matter

**RM61-01: rebalance ownership of an already decoding request within its existing EP4 group, at a verified committed boundary, when repeated slow-rank work or shared graph padding can repay the handoff.** Keep the expert placement, weights, initial admission policy and logical client stream unchanged.

The source currently chooses an owner for a new request and preserves that owner while its ID is in flight. A long-lived request can therefore remain on an overloaded rank after other requests finish or their context/work profiles diverge. The DP graph coordinator dispatches against the maximum rank token count and then broadcasts the padded count. Repeated graph padding and rank-local attention/indexer/linear imbalance are potential costs. This is a source-supported possibility, not evidence that the benchmark currently encounters a profitable imbalance.

This does **not** remove the aggregate experts selected by the same tokens, their mandatory routed arithmetic, or the full EP exchange. Some graph padding is already excluded from expert routing. Ordinary non-microbatched eager mode preserves local token counts, so a graph-padding explanation does not apply there. A different rank ownership may still change critical-path imbalance or communication locality, but those effects need evidence and can be negative.

The smallest credible arm is a **stop-copy handoff** at a clean boundary. Proactive staging is a later arm only if the simple handoff is correct and its pause is the limiting cost. The hypothesis is not “adopt Pallas” or “migration improves ITL.”

## 2. Discovery and selective paper reuse

Two actual OpenAlex searches produced 16 hits/16 paper identities; all are retained in `paper-dispositions.json`. First query, August–October: `LLM inference decode live migration cache load imbalance`. Mostly routing, prefill elasticity and alternative memory hardware. The second question narrowed to `LLM request migration KV cache decoding`, with June–October bounds to avoid assuming the useful mechanism must be new in October. Both retain provider publication dates and arXiv identities; those dates are not silently equated.

Two exact-source lookups preceded fetching. Actual `investigate` selected Pallas and EdgeFlow: two HTTP cache misses, two completed fulltext reads, no model calls, no repository selection. Saved bodies and hashes are exact; arXiv URLs are unversioned and explicitly **not version pinned**. Selected mechanism/implementation sections were read, not every experiment in both papers.

### Pallas — arXiv2608.16477

[Primary fulltext](https://arxiv.org/html/2608.16477), selected §4.3 and §5. The transferable component is **single ownership, an epoch-tagged preparation, coverage of all transferred positions, and final synchronization at a completed decode step**. Its implementation reconstructs a stable prefix by target prefill, streams completed suffix blocks while the source decodes, then transfers the final boundary block and activates the destination. The paper describes independent vLLM0.8.5 engines, 16-token blocks and Python/gRPC state transport. No donor implementation was fetched or built.

We retain that protocol structure while changing the expensive preparation component: within one shared EP4 group, an independent target prefill is not free parallel work and may delay all participants. Exact cache copy is the initial target adaptation. CED/SWA and draft caches also make “all historical blocks are immutable” unsafe as a blanket assumption. Only demonstrably immutable group ranges could be staged early; mutable windows, partially written blocks and shared references need a cut-time snapshot or explicit invalidation.

The paper's network detour and handover comparisons do not estimate this target's DP critical-path gain. Its token-ID/coverage consistency argument also does not establish exact native FP8/DSpark state equivalence after reconstruction under another batch.

### EdgeFlow — arXiv2610.22172

[Primary fulltext](https://arxiv.org/html/2610.22172), selected migration model and activation reconstruction sections. Its transfer-saving argument replaces conventional per-layer K and V of width H with layer input activations of width H, then recomputes K/V. That `2H → H` premise is not the target's compressed latent cache representation. The retained config has H=5120; a BF16 hidden row alone is 10,240 bytes, while one SM100 FP8 latent-cache record is 528 bytes. This is a **representation counterexample, not a total request-transfer byte model**: source sharing, compression ratios, SWA, indexer and draft groups all change total state size. Historical layer inputs would also need storage or reconstruction.

Reject the direct activation-transfer arm as scoped. The broad idea of selecting copy versus recomputation remains useful, but no target-compatible activation reconstruction component or memory win was established.

### PR triangulation

Three bounded canonical FTS searches were copied into isolated state and queried through actual `pr-search`; this is a selected-subset replay, not a GitHub refresh or full PR coverage. `sgl-project/sglang#37401` moves **queued, not-yet-prefilled** requests with no allocated KV/radix state. It excludes active/chunked/retracted requests. Its opening-body comparison has a prefix-hit confound and near-flat decode ITL; it does not supply active decode handoff or target benefit. `#37951` has a runtime-role-switching title but the retained opening body is an unfilled template. That lead is unresolved, not evidence of an implementation. No PR diff was fetched in this round.

## 3. Exact pinned control paths

All cited bodies are retained under `sources/`; `source-manifest.json` gives exact Git URLs, pins and hashes.

| Target location | Source observation | Consequence |
|---|---|---|
| `vllm/v1/engine/core_client.py:1738–1799` | Existing `reqs_in_flight` ownership returns before a new explicit rank is considered. | A new desired rank is not a migration API. |
| `core_client.py:1805–1812,1857–1895` | Finished notifications remove ownership; abort routes through current owner, with a separate streaming-request broadcast path. | Owner handoff must coordinate completion, cancellation and stream lifetime. A hidden finish/restart cannot leak a terminal response. |
| `vllm/v1/worker/gpu/dp_utils.py:44–201` | All-rank descriptor agreement; ubatches split/pad equally; normal eager retains local sizes; graph mode uses max rank count. | Graph savings require actual bucket change. Moving work cannot let a rank skip collective order or independently run a target prefill. |
| `vllm/v1/engine/core.py:2392–2469` | Idle/not-ready ranks execute dummy passes while the group remains active; unfinished and pause state synchronize. | A rank waiting for a handoff must keep participating in required steps. Transfer progress must not depend on skipping those collective steps. |
| `.../nixl/pull_scheduler.py:34–106` | Remote-decode matching is bounded by `request.num_prompt_tokens`; recompute threshold can skip small pulls. | Existing generated-token state is not automatically loaded into an active request. |
| `.../nixl/pull_scheduler.py:191–302` | Normal export is finished-length/stopped state; D-side readback requires bidirectional transfer; blocks are clipped/pinned and given a TTL. | Useful donor infrastructure for a clean stop-copy arm; not evidence of a live migration or pre-staging endpoint. Abort is not an interchangeable finish. |
| `vllm/v1/request.py:161–185`; scheduler `2163–2212` | Computed tokens include optimistic in-flight work; returned speculative rejections roll back computed counts/placeholders. | Transfer frontier must be determined after applicable output accounting and writes complete, not by reading an optimistic scalar mid-step. |
| Scheduler `3185–3263` | Existing DSV41 reload checks whether all SWA replay groups loaded; otherwise bounded replay; a complete prompt hit may re-execute the final token. | Positive model-specific reload infrastructure. It does not prove draft-state continuity or a no-recompute live handoff. |
| `kv_cache_interface.py:1450–1538` | Explicit transfer groups, draft groups and rebuildable replicas; transferability differs from prefix-cacheability. | Inventory and transfer each required state class. A single generic KV tensor or prefix-cache export is insufficient. |
| DSpark speculator `136–148`; model `nvidia/dspark.py:165+` | Draft sampling keys use request seed and absolute sampled position; draft layers write their own SWA context KV. | Preserve seed, absolute position and draft context or explicitly rebuild it; don't invent an opaque RNG snapshot requirement or assume target KV alone suffices. |
| `common/engram.py:20–33` | V2 Engram lookbacks come from device token history; transferred KV does not include older slot-hash state. | Original token history/lookback reconstruction belongs in the handoff. Static host tables are not request KV to migrate. |

A separate compatibility guard in `nvidia/model.py:698–713` restricts PCP>1 to DP1 and excludes speculation/KV transfer among other features. Enabling PCP is not a shortcut for this planned DP4 path. This does not forbid ordinary KV transfer at PCP1.

### Clean boundary and ownership contract

The following are requirements, not implemented state-machine tests:

1. Stop scheduling additional source work for the selected request while the group continues its required collective steps. Drain all applicable output accounting; distinguish stale outputs from committed ones. Fence corresponding cache writes before exposing a stable transfer frontier.
2. Preserve original prompt/output roles, all committed token IDs, exact computed-versus-uncomputed frontier, remaining output budget, stop state, seed/absolute positions, sampler/processor/grammar state where enabled, and original stream identity. Initial feasibility scope can exclude grammar/custom processors and use fixed-seed greedy text, but must explicitly report reduced coverage.
3. Allocate destination group state with identical model/layout and adequate duplicate HBM; preserve correct mappings and group epochs. Copy required compressed, indexer, SWA and draft state or use a declared correct rebuild path. Prefix-cache reuse alone does not restore all mutable windows.
4. Keep exactly one active owner. All participants must agree on the first global iteration in which the destination schedules the request and the source does not. Empty owners still participate normally. No extra independent forward may reorder the shared EP collectives. A CPU-side transfer wait cannot block the group progress needed to finish that transfer.
5. Redirect the original client output/abort route atomically with ownership; avoid duplicates, missing tokens, premature terminal events, changed logprobs or stop-string behavior. Ignore stale epochs after timeout/cancellation; retain a safe single-owner failure path.

Even exact stop-copy state does not by itself guarantee identical next logits: changing owner changes batch shape, padding, kernel tactics or routed reduction order. Fixed weights, request seeds and absolute positions are necessary but not sufficient for sequence/distribution equivalence. Native differential tests must distinguish copied-state correctness from numerical changes due to the new execution grouping; positional DSpark sampling keys do not prove preservation of every host sampler/processor state.

No inspected current path implements this complete protocol. This is an integration gap across the client, scheduler and connector, not a one-flag performance experiment.

## 4. Executed CPU falsification

`route_contract_probe.py` executes the **exact AST-extracted Python methods** from the retained target using simple request/load records. It imports no vLLM, tensors or native backend. Source hashes and method spans are in its output.

- A new unpinned request chooses the lightly loaded rank; a new explicit rank is honored.
- Reusing an in-flight ID with a different desired rank retains its old owner.
- NIXL receives remote-count 7 for a request with prompt length 4 and output length 3: it matches only 4 tokens.
- Promoting history to a synthetic prompt length 7 makes that count 7; this is a caller-contract demonstration, **not a correct request conversion**.
- A one-token residual is counted, and an enabled threshold of 2 rejects that pull.

These eight observations refute the simple reroute-and-resume shortcut. They do not execute migration, cache copies, collective progress, source shutdown or sampler restoration. No dummy epoch simulation or same-equation timing toy is presented as lifecycle proof. Source audit, rather than fabricated state tests, establishes the remaining DSpark and streaming obligations.

## 5. Prior overlap and relevance rubric

| Prior | Shared concept | Material difference |
|---|---|---|
| M05 `hypothesis:16afdd0252fff1fd053fa91c480ae3cf24576b4684176969ac1a898f356231d9` | Request placement | M05 targets expert overlap across independent DEP4 groups. RM61 moves an ongoing request within one group to reduce rank-local/global-padding critical work; the expert union is unchanged. |
| CMR01 `hypothesis:b1a1ec300242c6d5f5f49fb71007fe6695de3108adac3573e81b3f260bd3fa65` | Work balancing | CMR permutes complete bundles between equal-capacity microbatches on one owner. It neither migrates persistent cache nor changes request owner. |
| N02 warm-prefix placement | Cache locality and routing | Initial/warm-session placement cannot move a request after its decode workload changes. Its simpler policy remains the first comparator, not presumed inferior. |
| Existing H01 EP prefill coordination | Same collective coupling | Those arms retain local ownership and alter admission/chunks; RM61 concerns active decode ownership. |
| SGLang37401 | Request migration terminology | Queued prefill migration avoids allocated state; this proposal explicitly pays and preserves active state. |

Compact recall covered 143 records over two pages with a stable inventory hash, plus targeted recall and bounded report-text search. This supports the stated comparison, not a claim that no other publication or uncaptured experiment has implemented migration.

**Rubric:** source mechanism and current missing complete API are supported; recent primary-paper component relevance is supported; exact native compatibility is unresolved; cheap shortcut falsifier executed; service exposure, transfer cost, critical-path magnitude and long-output ITL gain are unknown. No forecast or numerical score fills those gaps. The justified disposition is **deferred**, not rejected simply for lack of a GPU run and not accepted as implementation-ready.

## 6. ROI and the next decision-changing diagnostic

A request move is useful only if repeated future group critical-path savings exceed the one-time pause plus copying, duplicate-memory pressure and sustained interference. A symbolic necessary comparison is `sum(future saved group-step time) > handoff + transfer interference + induced queue/cache cost`; none of these quantities has been measured here. This is not a fitted ROI model. Remaining token count alone does not determine remaining rounds under DSpark acceptance and stop behavior.

Required exposure evidence is a compatible retained metadata trace with per-rank active request IDs, context/query lengths, actual graph descriptors/ubatch mode, admitted output horizon, cache group footprint, and step times. It should distinguish output imbalance from initial admission imbalance. No such eligible trace was established in this round. Raw context length is only a cost feature; fixed Top512 attention, producer-indexer compression/candidate caps, DSpark acceptance and shared EP work all limit a simplistic context sum model.

**Fast next gate:** replay actual scheduling metadata against a constrained one-owner relocation and the exact descriptor selector, preserving all-rank constraints. Count cases where a move changes the real max graph bucket or plausibly reduces the measured non-MoE straggler; compare against improved initial routing and CMR where enabled. If no eligible long-lived imbalance survives, park the mechanism before implementing transfer. Then inspect an actual group allocation/state manifest for stop-copy feasibility. Both are cheaper and more informative than a generic load-balancing simulator. This round does not request new GPU collection.

**Later authorized implementation/evaluation:** baseline; clean stop-copy only; then immutable-group pre-staging plus final mutable-tail copy with the same admission and move decisions. Verify lossless text/seed/state under DSpark rejection, variable acceptance, EOS, stop strings, cancellation, transfer failure, shared-prefix reference counts and window/block boundaries. Check all-rank liveness and global-step alignment before benchmarking. Measure unchanged Mooncake and agent-75 workloads, with controlled imbalance cases clearly separated from production mixture. Primary is frozen long-output ITL, with separate p95/p99 pause/ITL, TTFT/E2E, throughput, failure and memory guards. A better average ITL that introduces an unacceptable migration gap fails. Report affected-request coverage and zero-exposure cases. No GPU experiment is authorized by this plan.

## 7. Yield and retention

- 2 paper queries, 16 source hits/identities; 2 selected fulltexts with 2 actual cache misses; 0 model calls.
- 3 bounded canonical PR queries plus 1 actual isolated subset `pr-search`; bodies only, no downloaded diffs.
- 1 deferred new candidate RM61-01; 3 scoped transfer-component screens (direct independent-prefix recomputation, direct activation transfer, proactive staging extension). The latter are not additional independent hypotheses.
- 0 native or GPU executions, 0 performance results, 0 implementation-qualified candidates.
- `source-export.json` retains 68 documents, 70 revisions, 377 edges. Exact journal, receipts, source bodies and manifest accompany it. Local isolated state is preserved; no new recovery snapshot/S3 publication or typed canonical card is claimed.

Tool lessons: the actual selected-source investigation kept unrelated repository links as candidates without treating them as author code. Compact prior recall and exact method probes prevented misleading reuse of initial routing and prompt-only transfer. This is field usefulness evidence, not a controlled improvement in research quality. Failed local path guesses and corrected reads are recorded in `tool-use.json`.
