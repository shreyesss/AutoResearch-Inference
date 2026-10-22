# Round 51 — exact reuse across requests: Engram projection memoization

**Disposition: deferred variant of EG02; no new hypothesis card or implementation promotion.** Source-only investigation, 22 October 2026. No GPU, model execution, native numerical test, or service measurement. Independent review pending.

## 1. Search and selective synthesis

The actual production `expand` and `paper-search` tools ran against an isolated state directory. One arXiv query searched inference plus redundant computation/computation reuse/common subexpression, with `after=2026-09-01`, exclusive `before=2026-10-23`, limit 10. All ten returned abstracts were inspected. One selected paper was fetched through `investigate`: one logical HTTP cache miss, full version-pinned HTML available, no provider errors. Relevant method, numerical validation, preparation and lifetime passages were read; this is not a claim to have inspected every figure or all 184,700 characters. No model reasoning call was used by the tool; the chat agent performed the synthesis.

| Source | Component screen / next action |
|---|---|
| PreCoG, 2610.13174 | Cached video trajectory editing changes the generative process; no exact frozen autoregressive substitution established. Abstract only. |
| ADER, 2609.22824 | Trained intermediate exits/adapters; no established frozen V4.1 exit. Abstract only. |
| Energy-efficient operation of neural operators for virtual sensing, 2609.30580v1 | Selected exact static-input reuse component; relevant fulltext passages read. |
| CNSF, 2609.16054 | New recurrent tracking architecture, not a serving-only rewrite of the target. Abstract only. |
| PointEvent, 2609.20066 | New vision representation/architecture. Abstract only. |
| GSM, 2609.33465 | Shared-state architecture requires different model structure/training; existing V4.1 CED sharing is not an absent optimization merely because another paper describes sharing. Abstract only. |
| SpikCTU, 2610.14594 | Speech architecture with learned conditional execution. Abstract only. |
| PARSEE-VAD, 2609.33236 | Visual-task prefix reuse; ordinary shared-prefix computation already has KV prefix caching here. A new missing exact component is not established. Abstract only. |
| BridgeWAM, 2610.14746 | Trained video/action architecture. Abstract only. |
| CoWindow, 2609.32704 | Changed attention partition/training; cannot assume original attention semantics. Abstract only. |

These are task-specific screens, not claims that those papers contain no useful ideas. Only the selected paper supports the following deeper adaptation.

### Paper component retained

[The neural-operator paper](https://arxiv.org/html/2609.30580v1) separates a changing observation branch from a geometry-dependent trunk. Fixed geometry permits reuse of the frozen trunk result. Its controls distinguish compiler freezing, graph replay, preparation and worker lifetime. The inspected validation reports within-device byte equality for 310 output fields; that does not establish cross-device byte identity. This supplies a dependency and amortization pattern, not a measured LLM speedup. Our adaptation is to look for a target computation whose entire input repeats, retain its exact result, and leave the genuinely changing computation intact. No energy or latency percentage is transferred to V4.1.

## 2. Exact target and source boundary

Pinned callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883`; Flash-1017 config `1bae0e1088993b9b82de08f59de5be5a34e42170`. Planned eight-B200 layout: two independent TP1/DP4/EP4 groups, native DSpark5 and host Engram. This is the existing research baseline, not a new live deployment attestation. Baseline ID: `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`.

Pinned `vllm/models/deepseek_v41/common/engram.py`:

- `Engram.__init__` constructs WKV from `(max_ngram_size-1)*n_heads*head_dim` input columns to `hidden_size*(hc_mult+1)` output columns.
- `forward`, around lines 1689–1691, applies WKV to either the prepared quantized embedding or the flattened looked-up rows. Hidden state is not an argument to that WKV call.
- The subsequent post-WKV kernel takes current hidden states, WKV output, normalization weights and token mask. That gate remains dynamic.
- Existing `hash_cache` stores compressed token IDs for rolling n-gram construction. It is not a cache of projected WKV results.
- Existing Engram batching, DP lookup exchange, prefetch streams, readiness events and persistent staging already remove/overlap some work. A projected cache must coexist with these, not count them as newly invented savings.

Selected source bytes are retained from the earlier frozen round26 packet and hash-checked against it. That packet's code URLs use the upstream repository name with a fork commit; the new source manifest corrects the repository owner to `callgideon` without changing historical bytes.

## 3. Proposed component and its limits

**Conditional proposal:** maintain a small device-resident, exact-key cache of the pre-gate WKV output, independently for each Engram layer. On an eligible hit, reuse that output and execute the current hidden-state-dependent gate normally. On a miss, execute the original projection and optionally populate the cache. Do not cache the final Engram output.

A cache key must identify the complete ordered 24-row hash tuple for the layer, plus an immutable weight/table epoch and compatible numerical execution contract. A short fingerprint alone is insufficient: compare the full key to exclude collisions. Table quantization, prepared input representation, WKV backend/precision and weight reload invalidate compatibility. Per-row hotness does not imply a complete-tuple hit.

The paper's geometry is fixed across requests. Here token-derived tuples change. **The target's useful recurrence rate is unknown.** The eight shared agent prefixes do not prove useful hits: prefix caching can skip those positions before they reach WKV. Count only rows actually executed after existing prefix-cache behavior, separated into prefill, target decode and relevant speculative verification positions.

There are two materially different scopes:

1. **Projection-only hit:** preserve current lookup/prefetch/staging, replace WKV for hits. This isolates the new component but still pays lookup and transfers. Mixed hit/miss batches need an implementation that avoids recomputing hits without making misses slower.
2. **Lookup-plus-projection hit:** also suppress corresponding raw lookup and exchange. This requires earlier cache decisions and distributed/staging integration. It is not included automatically in projection-only benefit; it overlaps more strongly with existing EG02 raw-row caching.

Miss compaction, scatter/gather, key lookup, insertion, eviction, output reads and changed GEMM batch shape are real costs. If the baseline projection is overlapped or tiny, even many hits can fail to improve service latency. An all-miss path should bypass the cache machinery cheaply; that remains an implementation requirement, not a verified property.

## 4. Capacity audit from the actual model config

Config: H=5120, hc_mult=4, max_ngram=4, n_heads=8, head_dim=256, two Engram layers `[1,14]`.

| Quantity | Derived value |
|---|---:|
| Ordered hash IDs per token/layer | `(4-1)*8 = 24` |
| Flattened embedding elements | `24*256 = 6,144` |
| BF16 embedding payload | 12,288 bytes |
| WKV output elements | `(4+1)*5120 = 25,600` |
| BF16 projected payload per entry/layer | **51,200 bytes = 50 KiB** |
| 1,024 entries in each of two layers | **100 MiB output payload alone** |

`capacity-audit.json` records this stdlib/config calculation, including separate illustrative 32-bit/64-bit full-key payloads. It is not an allocation measurement. Metadata, eviction state, temporary compacted batches and graph buffers are extra. Native packed MXFP8 input transfer uses a different payload/layout; no unverified packed-byte claim is needed for this decision.

A host-resident projected cache would move a much larger result than the BF16 raw input payload, and should not be assumed beneficial. The initial conditional proposal is device-resident and bounded. Across all eight ranks the memory reservation multiplies; whether that removes usable KV blocks is not measured. Any service comparison must account for the same node memory budget.

## 5. Why mathematical reuse is not yet a correctness proof

Same raw tuple and frozen weights define the same real-arithmetic WKV result. Native kernels can select different tactics or reduction orders as M, padding, layout, backend or graph shape changes. Quantization preparation may also matter. Reusing a result produced under one context can differ from recomputing it under another. Miss compaction itself changes M. This paper's numerical checks do not establish our native equivalence.

Before implementation promotion, identify the exact numerical contract and either prove stability across allowed contexts or restrict the cache to compatible contexts. That restriction can reduce hits. Future native differential testing must cover all-hit/all-miss/mixed, same tuple at different M and row positions, graph replay/eager tails, reload/reset, concurrent requests, eviction, DP staging and masks. Greedy equality alone is insufficient for the temperature-1 workload: compare downstream logits/probability and exact sampler assumptions as required. No such native test has run here.

Do not infer raw input identity from compressed token resemblance without reproducing the exact layer hash/layout. Full hash tuples intentionally define table lookups; arbitrary shorter token keys require their own equivalence argument.

## 6. Prior hypothesis audit and non-duplication

The saved read-only canonical query returned 17 cards whose JSON contains Engram, including unrelated cards mentioning it as a guard. That is not 17 competing cache proposals.

- **EG02** (`hypothesis:f677b614fbee94e7256b4bcfd8c773c0b3a35b2766b48678e8e84a0d0deebd3e`): exact raw-row deduplication/bounded hot-row caching, already deferred. This is a distinct cache value and larger key granularity within the same Engram reuse family. Retain it as an optional projected-result variant, not a new success count.
- **EG01:** bypass dequantization/requantization during raw-row preparation. Different operation; can change the numerical/cache compatibility contract.
- **A01 / round26:** look ahead and overlap WKV with other work. That can reduce the exposed time available to this proposal. Do not add their isolated savings.
- **PJ01:** reuse quantization of an identical context projection input across draft layers within a call. Different lifetime, values and memory scale.

Existing STAPLE-derived raw-cache ideas and the earlier observation that hardware caching can already hide Engram lookup make a generic “cache Engram” claim insufficient. The only delta retained here is exact **pre-gate projected-result** reuse, conditional on recurrence and numerical context.

## 7. ROI screen and the cheapest next evidence

Let `T0` be the measured unprofiled baseline request/round critical-path time; `P_exposed` the portion that can actually be removed by this WKV cache; `h_eligible` the hit fraction under the complete numerical/key contract; `O` cache handling and changed miss execution overhead. Even the rough expression `h_eligible*P_exposed-O` needs measured inputs, and batch interactions can invalidate linear scaling. A stricter optimistic ceiling is removal of all exposed eligible WKV work with zero overhead. None of `P_exposed`, `h_eligible` or `O` is supplied for the exact pinned target. No percentage ROI forecast is justified.

**Next permitted CPU diagnosis, only if an existing representative trace is found:** replay actual executed per-layer hash tuples and numerical contexts through a bounded cache simulator, using chronological request order and request-disjoint tuning/holdout. Include cold starts, eviction and weight epochs. Report tuple hit rates and reuse distance, output-capacity cost, and phase breakdown. This can reject poor locality; it cannot measure native latency or prove a win. No synthetic Zipf trace should substitute for the real workload.

No such trace was produced in this round. If absent, retain the precise missing artifact rather than launching a GPU run: executed row trace containing layer, complete hash tuple, numerical context, phase, request/round identity, ordering and epoch. Obtaining that later is a separate authorized instrumentation step.

Future service evaluation, if correctness and exposure gates pass, can use existing agent-75 and fixed-schedule Mooncake. Keep request order/prefix conditions and memory accounting fixed; report primary long-output ITL, throughput/goodput, TTFT and tail guards, acceptance, KV pressure and cache overhead. A custom service evaluator is not justified now. The only additional evidence is mechanism instrumentation to explain hits, exposed work and numerical equivalence. A warm synthetic repetitive prompt is diagnostic only, not promotion evidence.

## 8. Rubric and yield

| Criterion | Finding |
|---|---|
| Primary source and exact component | Pass for dependency/reuse pattern, with selective-read coverage stated. |
| Missing implementation | WKV result memoization absent in inspected Engram path; whole-repository absence is not claimed. |
| Frozen-model adaptation | Mathematically plausible pre-gate split; native numerical equivalence unresolved. |
| Existing-hypothesis overlap | EG02 variant; no new card needed. |
| Target exposure and recurrence | Unknown; blocks a service forecast. |
| Memory/correctness cost | Material and explicit: 50 KiB per entry/layer, batching/quantization/graph constraints. |
| Cheapest falsification | Existing-trace locality/capacity replay if trace becomes available. |
| Disposition | Deferred, low priority until representative recurrence and exposed WKV evidence exist. |

Actual round yield: **one online query, ten abstracts screened, one selected fulltext retrieved, one conditional component adaptation, zero new formal cards, zero implementation promotions, zero GPU experiments, zero service gains.** This improves the specificity of an existing family; it does not increase accepted-hypothesis count.

Tool usefulness: explicit semantic expansion into cross-domain exact reuse found a useful dependency pattern that an LLM-only keyword query could miss. Most results required architecture/training changes. No evidence yet warrants a hardcoded “cross-domain” ranking bonus or tool patch. The next query should narrow to exact frozen-runtime reuse or pursue a different bottleneck; repeating this query merely to accumulate papers would not improve this decision.
