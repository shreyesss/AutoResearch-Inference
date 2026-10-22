# Round 82 — shared-prefix storage versus exact sparse attention reuse

**Outcome: zero new hypothesis identities.** Reject the direct GraniKV dense-prefix/HOT–COLD port for the current sparse attention contract; retain its physical-owner grouping and bounded-fallback implementation as an **AT02 refinement**, conditional on actual cross-request selected-slot overlap. A storage-only contiguous-slab change remains unqualified and low priority, not disproved. No native execution, GPU/model import, compilation, serving change, canonical write, or service gain.

Target source remains callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883`, its retained FlashMLA dependency, and planned Flash1017 TP1/DP4/EP4 on B200. No live backend, prefix-cache activation, or physical-sharing attestation was obtained.

## 1. Adaptive retrieval and version boundaries

Fresh isolated prior recall retrieved all **149 compact cards** in two pages with matching inventory hash `c543328973294852aa37233bfbec2144a5a970e9e8d0c7f90d6f05b5d6eea809`. Targeted card inspection opened AT02 and the existing Feather prefix-homogeneous batching proposal. Readonly canonical report searches covered shared-prefix attention, cross-request, Hydragen and cascade; selected round51 exact reuse was read to distinguish its Engram projected-result cache. This is bounded lexical coverage, not semantic deduplication certification. Historical cards and baselines remain unchanged.

Two actual online queries changed the next decision:

1. OpenAlex, Aug1–Oct23 exclusive: shared-prefix/cross-request/decode/memory reuse, ten results. Most concern storage tiers, trained reuse or prefill admission rather than the missing exact sparse execution component.
2. arXiv, Jun1–Oct23 exclusive: explicit shared-prefix/prefix-sharing/cascade-attention alternatives with attention/kernel/decoding, ten results. **GraniKV 2608.15584** was selected. Exact retained-title/ID lookup found no copy. FoldAttention is a prior screened mechanism, not a fresh candidate.

The provider returned GraniKV **v2**, updated Aug23. Normal `investigate` failed its fulltext fetch; retry returned the cached missing-source failure. A browser fallback exposed the explicit primary **v1**, Aug16. We deliberately fetched that URL through `Sources.fetch(refresh=True)`, retained it as `fulltext:2608.15584v1`, and do not call it v2 or the latest paper. Its main architecture, kernel decomposition, limitations and artifact section were read. No later-revision conclusions are claimed.

The paper links an anonymous artifact. Browser opening failed, but its public API supplied README, reproduction guide and four selected implementation/test files. Their full SHA256 hashes and retrieval receipts identify the inspected snapshot; no Git commit or immutable correspondence to either paper revision is exposed. A directory-list request failed, and README paths provided the bounded follow-up. No install, device query, server test or donor script was executed.

Local PR searches found 0 GraniKV title hits, 15 cascade+sparse hits and 170 shared-prefix+decode hits; only five per nonempty query were inspected. Ten selected records were imported and the production `pr-search` replayed that subset. SGLang #29288 describes a separate opt-in cascade backend and graph/sync integration. Its retained body is corroborating context, not proof of current merge status or absence in our pin; absence/contract claims below come from inspected target code.

## 2. Paper components and actual donor code

GraniKV v1 separates a contiguous HOT prefix pool from a token-granular COLD suffix pool. It provides a dense grouped-prefix contraction and a cascade alternative, with a measured hardware-dependent dispatcher. All reported hardware is A100; the limitations explicitly exclude MoE/EP evaluation and describe short-prefix regressions. None of its throughput ratios or saturation thresholds transfers to B200 sparse MLA.

The inspected released kernel `_granikv_grouped_prefix_kernel`:

- groups by a physical prefix base and length;
- stacks distinct request queries, preserving separate row softmax/output state;
- loops `range(0, prefix_len, BLOCK_N)` and addresses `base_slot + offs_n`;
- masks prefix bounds and padded query/head rows, **not a query-specific selected-token list**;
- reads separate K and V arrays and merges suffix partial outputs using their normalization information.

Thus it reuses KV loads, not attention maps or normalized outputs across different queries. Its grouping is more precise than text-prefix equality, but the common dense prefix support is essential to this implementation.

The graph metadata code retains request-to-prefix information and reconstructs groups by `(base, length)`, bounded to request tiles. It also calls `req_pool_indices.cpu().tolist()` during replay preparation and may copy sequence lengths. This is a concrete integration cost to avoid or account for, not a measured latency objection. The allocator has contiguous slab allocation/reuse and refcount integration described by the paper; its availability does not make it compatible with the target's packed cache groups.

The inspected correctness suite includes multiple backend comparisons but its common helper collects short greedy outputs sequentially and disables CUDA graphs for server launch. It was not executed here. It does not establish target quantized sparse semantics, concurrent grouping, temperature-1 distribution preservation, graph replay or B200 performance. Changed reduction topology can change finite arithmetic even when the real-arithmetic attention decomposition is valid.

## 3. Exact target: what already exists and what is missing

`nvidia/model.py` makes Mega attention the SM100 default only when its availability predicates pass, otherwise selecting another backend. This source default is not evidence of the currently selected runtime.

In the Mega decode path, `_decode_compressed_kv_and_topk` maps each query's local selected indices through **that request's block table**. `compute_global_topk_indices_and_lens` already fuses local-to-physical mapping, valid counts and padding-token lengths. `_forward_decode_mega` then passes two typed cache/selection regions: per-layer SWA and optional compressed KV. The native dependency schedules a query row through `s_q_idx = cta_x_idx / CLUSTER_SIZE`; heads within that row share computation. This is not a cross-request grouped-prefix pass.

The target consumes packed quantized records, explicit positions, an attention sink, Q/output RoPE, and output quantization in its fused reader. The planned profile says FP8 KV; source also supports a conditional NVFP4 compressed format. Neither can be replaced by the donor's dense separate-K/V path by changing a pointer or CLI flag. Contiguous physical allocation still leaves **sparse selected positions** to gather; it does not turn Top512 into a dense original-prefix contraction.

Prefix caching has source default `True`, and bounded SWA replay also defaults `True`. The inspected model-state path explains that eligible bounded replay excludes SWA from prefix caching and reconstructs its window after a hit. Attention disables that path for unsupported runner/PCP/platform cases. These are source capabilities and guards, not resolved launch settings. We found no exact live attestation in the retained campaign brief. Even when prefix caching is enabled, an actual hit and retained owner/slot identity must be observed.

The standard agent workload's eight logical prefixes are therefore only a possible source of locality. Different requests can diverge in positions, histories and selected compressed indices. At sufficiently late live positions, SWA may contain none of the original shared prefix. Same token IDs or logical positions across SWA and compressed storage do not imply interchangeable occurrences. CED/index-sharing groups can already reuse state within a request/layer group; that is distinct from sharing between concurrent request queries.

## 4. Dispositions and overlap

| Component | Decision | Precise reason |
|---|---|---|
| Direct dense-prefix GraniKV backend/HOT–COLD port | Rejected as scoped | It includes all dense prefix keys, replacing target query-specific sparse support and fused typed-reader semantics. |
| Exact masked grouping of queries with overlapping selected physical KV | Retain as AT02 refinement, deferred | Same mechanism as existing support-preserving grouping/QUILT; donor adds a concrete physical-owner grouping and fallback implementation reference. No new identity. |
| Contiguous prefix slabs without changing selected support | Unqualified, low priority | Mathematically possible storage change, but selected addresses remain irregular; no trace establishes remaining mapping/transaction cost or that allocator complexity pays back. Not an impossibility result. |
| Prefix-homogeneous admission or smaller batches | Existing Feather/placement family | Changes scheduling/locality rather than adding a missing grouping kernel; do not count again. |
| Output/logit memoization solely from shared prefix | Not proposed | Different queries and supports require their own scores, normalization and output. |

AT02's older baseline is preserved. CR64 changes L2 priority for shared compressed payload; it does not implement grouped loads and may reduce the exposed traffic left for grouping. MP17 reuses already-computed physical indices within a compatible index group; it does not authorize cross-request support reuse. Their benefits are not additive by assumption.

A sparse adaptation must preserve every query's original typed occurrence multiset, causal bounds, positions and sink contribution; partial attention merges require the correct per-query partition functions. Prior AT02/QUILT CPU controls already reject averaging normalized outputs, repeating sinks or deduplicating distinct typed occurrences. We do not rerun those toys or present the donor's real-arithmetic decomposition as native numerical qualification.

## 5. Smallest honest diagnostic and evaluation

The executed `source_contract_audit.py` uses only stdlib AST/text inspection. Ten observations confirm the donor's dense range and lack of a TopK argument, its grouping key/host-copy call, and the target's mapping/reader/config surfaces. These checks execute **no source function** and establish no latency, cache hit or numerical result. This is enough to stop the direct transplant branch.

The next useful CPU diagnostic needs an existing, representative trace of **executed** query rows: cache owner and generation, typed physical selected slots, original query/request/position, valid lengths, actual graph batch, layer/source-cache group and chronological order. Group only simultaneously executable rows on the same device with a compatible owner and numerical contract. Count intersections and union/packing work after existing prefix caching, avoiding padded rows and logical-prefix-only grouping. No such trace is supplied; manufacturing a shared-prefix synthetic trace would predetermine success.

If a trace later establishes worthwhile overlap, an AT02 implementation can compare original reader, metadata-only grouping, and exact-mask grouped reader with the same memory budget. Preserve quantization, RoPE, sink, per-query output mapping, capture sizes and safe fallback; bound grouping work and test no-overlap paths. Test actual native numerical/output contracts before service measurements. Use the existing agent75 and Mooncake schedules for ITL, throughput, TTFT and tail guards; no new benchmark is justified merely to guarantee common prefixes. Shared logical payload size or a reduced union count is not measured HBM traffic or a service speedup.

## 6. Yield and tool lessons

Two provider queries, 20 unique returned paper identities, 20 abstract screens, one selected fulltext read at v1, four selected anonymous code/test files, ten PR subset records, three scoped intervention components, zero new formal cards and zero promotions. One exact-support refinement survives within AT02; no target ROI estimate is justified.

Operational errors are retained: unsupported `--defer-snapshot init`, the resulting failed seed attempt and empty isolated recalls (invalid prior coverage), corrected initialization/backup and matching 149-card recalls; an invalid observation status `noisy` caught by the new safe enum error and explicitly corrected; unavailable v2 fulltext; unavailable browser repository and directory endpoint; two initial local source-path mistakes corrected by `rg --files`. The query executed despite the expansion failure in that shell sequence; corrected expansion is a subsequent validated plan receipt, not falsely predated execution. No query or accepted enum was silently broadened. These observations support using the existing safe guidance and dependency checks, not another speculative tool feature.
