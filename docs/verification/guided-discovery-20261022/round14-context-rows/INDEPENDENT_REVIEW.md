# Round14 independent context-row trimming audit

**Verdict: retain as a known upstream component-port diagnostic, deferred and low service-ROI confidence.** The pinned c455 source lacks this row restriction. It is distinct from prior query skipping/output-column trimming, but not novel: vLLM PR60320 implements the idea. No GPU/model import/runtime patch or online fetch by reviewer.

## Exact gap and donor limits

Pinned DFlash/DSpark context preparation computes current target context rows for every draft layer. Exact Flash1017 native draft has three sliding-window layers, window128, default anchor-sampling query lengthQ=5. Context reads in the noncausal SWA kernel use `[max(seq_len-Q-window,0), seq_len)`, including the query block. Earlier current-prefill rows need not be newly projected into draft KV if no other consumer can later request them.

PR60320 head `69a504902ad6296f46567d8d9d4a2abf0a085470` (open in retained API snapshot) selects per-request trailing rows and gates them on pure sliding-window groups, cacheability, no connector and no context-anchor override. It requires at least2048 omitted rows to amortize gathers. Its tests/profiling are donor-reported: GB200 context path2.57→about0.2ms, but TTFT changes only−0.3% to−1.3% with **every95% bootstrap interval including zero**. Calling that a demonstrated endpoint improvement is not justified. Test run uses a different serving/source configuration, synthetic acceptance for TTFT and output length1. Separate GSM8K/acceptance results do not certify byte equality for all state transitions.

The current fork already moves context combine into FULL graphs (#59511-related path). Donor diff predates that arrangement and cannot be copied over `propose` without reconciling `_prepare_graph_forward` and `_prepare_graph_replay`. Keep captured prefix processing unchanged initially, and restrict any extra eager-tail work conservatively.

## Tail bound and its premises

LetE be actual absolute scheduled context end (exclusive),R the rejected suffix, A=E−R the accepted end, M=max_model_len, Q=query block length, W=window128. Pinned prepare sets `seq_len=min(A+Q,M)`. The oldest needed context position is `max(min(A+Q,M)-Q-W,0)`.

Keeping W+R rows alone fails nearM because the clamped query block shifts its window earlier. W+Q is sufficient provided **E<=M andR<=Q**: `R+max(0,A+Q-M)<=Q`. Rejection and clamp margins cannot both independently reach their worst case under those premises. Native DSparkQ5 differs from ordinary DFlashQ6; inspect effective sample_from_anchor rather than assuming either.

`tail_bound.py/json` checks116,372 integer interval cases forQ5/6 and three model lengths. It also detects three intentionally unsafe designs:

1. W+R misses required earlier context at the max-length clamp.
2. CPU row endpoints that differ from device-compacted `query_start_loc` can select an entirely wrong tail.
3. A future request reusing a shorter cached prefix can require old rows omitted for the current long request.

This is a mathematical model with explicit premises, **not execution of source kernels/scheduler or proof that live metadata satisfies them**. The original donor uses device ends for a reason. A first adapter may disallow adaptive compaction, CP and other unmatched row-coordinate transformations, or use verified device row selection. No new host synchronization to read rejection counts should be introduced just to recover the bound.

## Required state/lifetime gates

- Every draft cache group must have finite supported sliding-window semantics. One full-context or differently anchored consumer invalidates the common crop.
- Preserve all `prepare_dflash_inputs` initialization. Pinned code writes zero positions/PAD_SLOT_ID for rejected suffixes and forbids null-block writes; its full-span initialization prevents stale graph metadata. Do not crop metadata initialization merely because projection rows shrink.
- Prefix caching off **or every relevant draft group non-prefix-cacheable** is essential. `SlidingWindowMLASpec.prefix_cacheable` is `not bounded_replay`. Configured bounded replay is an eligibility condition, not proof it is active for the live groups. This gate also constrains future-prefix reuse and partial restoration; preemption/restart must recompute all newly needed window rows.
- No KV connector: external cache transfer may require older records even if the local current draft does not read them.
- No context-anchor override. Base `prepare_context_anchor` is empty; other drafters may read combined hidden states by original row. Keep the exact type/method gate and audit future users.
- Previous context rows outside the current target chunk may still be needed when a chunk has fewer thanW valid positions. Cropping only the current chunk must preserve prior resident required KV; this is not permission to evict or clear all older cache.
- FULL graph retains its staged prefix `[0,G)` and projects that prefix in replay. Current eager work covers the remainder. Selecting the required tail intersected with `[G,end)` while retaining the whole prefix is interval-safe, but multiple-request coordinate mappings, empty/padded requests, cache groups and graph resource initialization still need actual tests.
- Dummy/profile/capture paths must preserve workspace reservation and PAD slots. A timing improvement from skipping profile work is not serving benefit.

## Prior overlap and choice of first experiment

R2-03 removes unused **query-backbone/Markov work** during unfinished prefill and encountered confidence side effects. This proposal keeps that execution and omits only unneeded **context rows**. PJ01 removes discarded **output columns** from context projections on all steps. Historical DeepInfer N02 concerns target consumer replay, not this separate draft context construction. Thus a distinct retained intervention is defensible, linked to these relatives and PR60320; it must not be branded novel.

Rows and columns share a cost denominator. Their gains are not additive: after near-total row trimming on long prefills, fewer rows remain for PJ01 to accelerate. Conversely PJ01 reducing per-row cost lowers row-trimming headroom. Compare separate arms before a combination.

For the frozen long-output ITL objective, direct value is weak: ordinary small decode batches do not meet the donor2048-omitted-row threshold and use the unchanged path. Mixed load could indirectly improve queueing/ITL by reducing prefill work, but current schedule exposure and effect are unmeasured. Existing agent-p75 and Mooncake remain appropriate endpoint workloads; do not substitute donor max_tokens1 TTFT as our long-output result. Component timing and metadata/state comparisons are additional diagnostics, not a new endpoint benchmark requirement.

## Actionable disposition

Retain deferred upstream-port investigation with **no predicted gain**. Verify exact group/cache/connector/anchor/row-coordinate eligibility first. Prefer the conservative current FULL-prefix-preserving eager-context path, retaining mandatory metadata initialization. Later authorized correctness checks must include partial/final prefill, rejection, max-length clamp, cached-prefix boundaries, preemption, no-resident/null slots and FULL/eager parity. Only after those gates should paired standard-workload results decide whether the small potential TTFT gain merits maintenance. All present CPU evidence is inconclusive for runtime correctness and service value.

### Worker scope refinement

The worker's proposed initial TR01 arm explicitly keeps **all hidden-state/main_proj computation and FULL graph prefix unchanged** and trims only eligible eager context-KV projection/insertion rows. This is a narrower, easier-to-audit adapter than the donor's full aux gather+combine trimming. Consequently it cannot claim all donor context-path savings: the already small donor step fraction includes main_proj work this arm retains. The worker's6720 source-window/24 ragged partition/12 monotonic-chunk checks are symbolic scope checks, not actual cache-gate or GPU evidence. This refinement strengthens the low-priority/deferred disposition while making the initial intervention more precise.
