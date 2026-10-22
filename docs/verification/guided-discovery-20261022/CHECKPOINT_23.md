# Checkpoint 23 — make the next uncertainty smaller

The guided research loop continues without GPU calls, native model execution or serving changes. Recent paper discovery remains adaptive: follow a promising citation, inspect the actual PR and target code, and revise the component when a direct port fails. No implementation-qualified candidate or measured inference gain is claimed.

## LP63: interrupt prefill at a safe layer boundary

[Round63](round63/REPORT.md) searched three queries, with 20 hit references covering 16 paper identities, and read four selected fulltexts. A follow-up prompted by a citation found a September paper on communication-safe prefill segmentation. Local PR triangulation led to a layered-prefill proposal; the agent inspected its exact head and target model source.

The transferable idea is to let decode advance between segments of a large prefill, while preserving larger prefill matrices. The first proposed arm **serializes** complete shared MegaMoE calls in an identical all-rank phase order. Concurrent execution with independent buffers is a separate arm with additional proof obligations.

The existing donor rejects speculative decoding and DP. Its ordinary pipeline-parallel layer adapter also does not respect our target's stored decoder-replay endpoint: requesting layers 0–4 can run 0–19 or 0–39. The source-extracted scalar probe falsifies that direct adapter. It does not falsify a model-specific continuation implementation. Hidden/residual state alone is insufficient: mHC mixing, auxiliary draft rows, Engram preparation, attention/indexer metadata and replay state must survive an intervening decode.

A separate allocator-key check shows that changing a supplied P/D phase label does not allocate a different MegaMoE buffer. Two streams therefore do not establish isolation. This is a proposed-concurrency constraint, not an observed race in current serial execution.

**Disposition: LP63-01 deferred, lower readiness than PJ01/CF59.** Existing prefill admission/chunk/cadence controls are the cheaper comparator; source presence does not prove their effective deployment settings. No compatible trace establishes remaining interference or a profitable continuation boundary. Independent review additionally identifies shared model-level candidate/top-k buffers: intervening decode can overwrite values needed after resumption. Protect those live ranges or select boundaries where they are dead; serializing MegaMoE alone is insufficient. The probe’s empty early-range equalities also do not certify a forward: the target asserts nonempty continuation state after that loop. These are source constraints, not executed race or numerical tests. [Independent source review](round63/INDEPENDENT_REVIEW.md) retains the deferred disposition and suggests inspecting a boundary before source layer 20 first; that boundary is not yet proved legal.

## Negative findings matter to selection

The DLFP paper's completion-aware controller still worsened its reported Qwen tail ITL; replacing a host timer with completion timing was insufficient. These are author-reported results on another model, not our measurements. More interruptions can replace one large gap with more moderately bad gaps. Tail coverage and token-level distributions remain necessary.

The inspected Mooncake traces contain only 22/21/37 requests with requested output at least1024, among roughly 4,000 each. Agent-p75 requests 1024 output tokens and can create replacement-prefill overlap at concurrency above 1, but warm prefixes and actual batch placement matter. Start with both standard suites; add a controlled mixture only if their observed eligible overlap is insufficient. Requested length alone is not exposure evidence.

## Current ordering and the observation that would change it

| Direction | Why retain it | Next discriminating observation | Current limit |
|---|---|---|---|
| PJ01: remove unused context-projection columns | Narrow, source-visible work removal | Actual active backend/view contract and exposed component duration | Nominal removed MACs are not service ROI |
| CF59: overlap eligible context work with sampling | Source identifies a dependency window | Complete scratch/consumer ownership and graph-mode admission | Optional prompt-logprob work and competing resource use can erase/safely exclude the window |
| RM61: migrate an active request within EP4 | May reduce repeated rank-local imbalance or a common graph bucket | Compatible retained rank metadata and exact descriptor selection | No profitable move established; major ownership/cache/frontend protocol work |
| LP63: partial-depth prefill continuation | Changes interruption granularity beyond token admission | Remaining prefill interference after existing controls, then exact continuation inventory | Major model/scheduler/collective integration; no native continuation proof |

This is an engineering-readiness ordering, not a measured speedup ranking. The next bounded audit targets CF59 dependencies instead of creating another paper-named hypothesis. A separate lane continues recent-paper discovery for attention/indexer data movement, checking prior coverage first.

## Retention and tool changes

RM61's normal proposal, six claims, screen and deferred decision completed in isolated state. The proposed61/62 retention package contains exactly one hypothesis, with no copied historical ledger. Root independently verified 29 operational files, 208 restored artifacts and 119 source-revision fingerprints; exact immutable RM61 fields match the author dossier. Retry did not add typed events/identities. The public-source filename alias and original failed receipts remain visible. [Root checks](retention-23/root-checks.json), [operations](retention-23/OPERATIONS.md).

Canonical application is sequenced after the existing 58/59/60 import and CF59 refinement. At this checkpoint, that first import is still waiting at the normal writer lock. No completed canonical 61/62 update or S3 publication is claimed.

The PR-research skill now tells agents to reuse the reader's exact pinned-code source identity and existing revision before registering another alias. The motivating CF59 review found identical code already retained under the stable identity. This uses existing show/import tools; it does not claim automatic deduplication or a measured quality improvement. Skill validation passed. No runtime code changed in this checkpoint; the preceding code gate remains 365 tests plus 29 subtests.

Delivery hashes: [copy manifest](source-copy-manifest-23.json). Raw evidence remains outside Git. One new deferred integration direction is not counted as an accepted implementation; refinements and refutations remain attached to prior work.
