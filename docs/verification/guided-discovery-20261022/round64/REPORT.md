# Round 64 — Retain shared compressed KV across Mega decode layers

## Decision

**CR64-01 is a concrete, narrow future experiment worth retaining.** In the inspected SM100 Mega attention decode kernel, both per-layer SWA and shared compressed KV use `EVICT_FIRST` on their TMA gather4 payload reads. Test `EVICT_NORMAL` and `EVICT_LAST` **only for compressed/extra-cache reads**, while keeping SWA, query, output, separate scale staging, addresses, precision and barriers unchanged.

The hypothesis is that a less disposable policy for physically reused compressed-cache lines reduces exposed memory stalls across decoder layers or neighboring verification queries. **There is no measured locality, cache-miss, latency or service gain here.** The scientific premise is source-grounded and the proposed change is small; effectiveness remains unknown. Execution is deferred under the user's GPU prohibition. This is not implementation or deployment qualification, and it is not an H200 recommendation.

Yield: **3 dated paper searches, 16 hits / 16 paper identities, 1 fetched fulltext with selected sections read; 3 local PR queries, 26 returned references / 26 unique PR identities; 5 PR bodies retained and inspected; 1 new target-scoped intervention retained for review; 0 GPU experiments and 0 implementation-qualified hypotheses.** Counts describe bounded retrieval, not exhaustive coverage. The exact third paper query returned zero results, without hidden broadening. June was an explicit recency relaxation after August–October results mostly addressed a different cache level.

## 1. Exact source baseline and first useful consumer

This is the frozen source plan, not a live-node audit:

- `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`.
- FlashMLA dependency `5dceadbd9eabc9acfc547ef18ec8f7b14b980682` and its CUTLASS gitlink `4faf1a1568cf1e4ad8ff71846a13e16f2a6a6f6b`.
- DeepSeek-V4.1-Flash-1017 configuration revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, planned B200 TP1/DP4/EP4, native DSpark. The intervention is conditional on actual SM100 Mega attention dispatch; source defaults and availability checks do not attest the installed backend.

`vllm/models/deepseek_v41/attention.py:592–619` sets each consumer's compressed-cache owner. `_compressed_kv_cache():1222–1230` returns `source.kv_cache` through the static forward context: consumers use the source tensor, rather than an equal-valued per-layer copy. The config gives source20 to layers20–39. Index sources20/24/28/32/36 refresh selected support; do not assume all20 layers read the same512 positions. The shared source allocation alone also does not prove cache residency.

`nvidia/flash_mla_mega_attn.py:305–364` computes physical compressed slot IDs and passes that same compressed-cache tensor as the native **extra cache**, alongside the current layer's SWA cache as the original cache. The immediate useful consumer is the native decode gather/attention pipeline, not a later hypothetical cache manager. No model weights, attention support, cache representation, request placement or token schedule need change.

The pinned native `core_attn/kernel.cuh:326–358` passes `CacheHintSm90::EVICT_FIRST` in every `issue_raw_gathers` call. Its decode caller at1375–1422 chooses original/extra tensor maps and mixed boundaries, but not different policies. In contrast, the **prefill** BF16 gather at1553/1562 already uses `EVICT_LAST`; this is counterevidence to any blanket assertion that the whole implementation lacks retention hints. Prefill is excluded from CR64.

Pinned `kerutils/device/cuda/sm100/intrinsics.cuh:12–21` forwards the operand to `cp.async.bulk.tensor...tile::gather4...L2::cache_hint`. CUTLASS `copy_sm90_desc.hpp:186–190` defines NORMAL/FIRST/LAST as distinct64-bit operands. Thus this is an L2 hint change in the actual inspected payload-copy instruction, not a change to logical prefix eviction or a naming inference. [NVIDIA's PTX documentation](https://docs.nvidia.com/cuda/parallel-thread-execution/#cache-eviction-priority-hints) describes eviction priority as a performance hint: it does not reserve capacity or guarantee retention. The current documentation is contextual; the implementation definitions are pinned separately.

## 2. Minimal intervention and contracts

Preserve the same gather count, coordinates, tensor maps, slots, transaction bytes, barrier arrival/wait sequence, dequantization, softmax and reduction order. Introduce a compressed-cache policy operand or compile-time variant at the existing role boundary:

- Original/SWA group: retain FIRST.
- Extra/compressed group: independently select FIRST (control), NORMAL or LAST.
- Mixed block: choose the policy at the same four-row group boundary used for the tensor map.
- Non-mixed block: preserve **which role** the sole tensor map represents. `MIXED_BLOCK=false` can mean all-extra, not just all-original. Passing only the current Boolean is insufficient.
- Two-CTA decode: its separate `copy_kv_scales_async` staging and all completion accounting remain untouched. A payload hint is not a claim that every scale load changes policy.
- SWA-only layers and generic callers remain on the original policy. The host ABI may need a narrowly scoped variant/parameter if this helper serves non-sharing models; do not enable it globally merely because a cache is called extra.

No L2 set-aside, new allocation, prefetch kernel, layer reordering, cross-rank movement or persistent cache protocol is proposed. Changing an inline helper still requires verifying emitted policy operands and resource use. A per-group select or extra specialization can add register/instruction cost. Hints can affect competing data, including indexer keys, weights, scales and other requests. All-rank execution time can be governed by another rank even when local reads improve.

## 3. Literature and PR triangulation — useful boundaries

The first online query returned eight papers about provenance, shared host caches, RAG composition, custom L1 hardware, edited contexts, memory-wall analysis and approximate/adapted representations. These do not establish a GPU cross-layer cache-policy benefit. Each disposition is retained in `paper-dispositions.json`; a broad paper's mismatch is not treated as proof that every component is unusable.

The follow-up found **Cache-Resident LLM Inference in GB-Scale Last-Level Caches**, arXiv2606.25353. Its selected introduction/architecture sections distinguish weight and attention-state reuse, then separate them into dedicated resource domains and relax synchronization to true dependencies. It runs a multi-socket CPU/cache-resident architecture. This is **background motivating the resource-contention question**, not a donor implementation, an L2 policy prescription, or evidence of a B200 speedup. Its whole CPU architecture is rejected as a direct port; its locality/dependency reasoning is reusable only as a design question.

Other follow-up hits included die-locality work already underlying RD01, a custom ARM cache scratchpad, HBF simulation, hybrid linear-attention tree speculation, RISC-V prefetching, ELDR already explored, and a broad agent systems reference. None warrants another whole-system port. The exact arXiv policy query then returned zero. We stopped retrieval because source inspection, rather than more loosely related papers, identified the next decisive question.

Local corpus triangulation supplied useful **counterevidence**, with bodies inspected but no donor code claimed:

- FlashInfer#6111 uses per-item hints only for selected uniform workloads, leaves mixed/heavy cases unchanged, and measures graph kernels with L2 flushed **before every launch**. Such a measurement does not exercise our proposed inter-layer warm reuse.
- FlashInfer#5402 says once-read pages use FIRST while split programs retain the default after a reported regression. This supports keeping NORMAL and the original FIRST as controls; a universal LAST policy is not justified.
- FlashInfer#6071's evict-last partials are SM120 split/merge buffers, not B200 shared compressed-cache lines.
- FlashInfer#5119 has a target-family mixed-cache reader but different implementation/precision/API constraints; its body describes L1 bypass/default policy, not proof that this exact native helper already has role-specific L2 retention.
- SGLang#33358 separates streaming inputs from reused weights/frequencies in a norm/RoPE store kernel. Its large-N ILP and measurements are a different producer; no transfer of those speedups to decode reads.

The actual `pr-search` ran against the explicitly imported five-document subset. Earlier canonical FTS queries were read-only. Neither receipt is a current GitHub refresh or repository-complete code absence proof.

## 4. Prior overlap

The compact inventory had143 records with stable pagination; standalone reports were also checked.

| Prior | Relationship to CR64 |
|---|---|
| AT03 | Reuses prefill BF16 materialization and its workspace lifetime. CR64 keeps compressed bytes and all gathers, changing a decode payload hint. |
| AT02 / QUILT | Groups neighboring queries to share loaded KV and exact partitioned attention. CR64 changes neither query grouping nor arithmetic. |
| WP38 | Physical weight packets, with a separate routed-weight FIRST arm. Keep weights fixed here; do not combine arms or borrow its gain. |
| P50-02 | Indexer-key FIRST policy, default-off sparse exposure. CR64 concerns the main attention reader's compressed KV and tests the opposite retention direction. |
| RD01 | Physical memory-domain weight placement; no replacement or additional instance of it. |
| MP17 / round57 / LC | Schedule reuse, already planar indexer layout and resident-cache compression. No schedule/layout/codec change here. |

The reusable principle is known. The missing target component is specifically **role-aware retention in the pinned Mega decode gather**. This is a target-scoped intervention, not a claim of new academic IP. Shared citations do not imply ancestry; the closest priors are comparison links.

## 5. Executed CPU/source diagnostic

`role_contract_probe.py` extracts the actual Python `_compressed_kv_cache` method and executes it with object sentinels. Source and consumer return the same object. It also reads the real config's20–39 ownership/index-source groups. This establishes the inspected host ownership contract; it does not measure device addresses, pointer stability through actual replay or cache behavior.

Fifteen **symbolic** original/extra/mixed role cases check the proposed policy-selection contract. Two negative controls expose design mistakes: treating every non-mixed call as original, and replacing the helper's constant globally. These are illustrative operand-routing checks, not a compiled-kernel test, a cache simulation or independent proof of performance. The initial probe mistakenly looked for config fields outside `text_config`; that author error was corrected and retained in the tool ledger.

## 6. Fastest informative future test and promotion gates

No GPU work is authorized or executed. The future experiment can remain narrow:

1. Confirm actual backend, dependency/build pin, cache formats, captured row shapes and source-owner mapping. Check emitted gather instructions differ only in the intended policy and any necessary role select; inspect register/resource changes. Prove SWA-only, all-extra, mixed, invalid-slot and two-CTA paths preserve addresses and transaction/barrier counts.
2. Differential outputs for identical cache bytes, selected indices and queries, including ragged/invalid/empty rows and graph replay. A cache hint is semantically narrow, but a source patch may accidentally alter metadata or synchronization; inspect and test it.
3. Compare **A=original FIRST**, **B=compressed NORMAL**, **C=compressed LAST**, with all other policies and model code fixed. Use an actual source20 consumer sequence with intervening layers/weights and repeated verification positions. An isolated cold-L2 launch can be a negative/control condition, but cannot answer whether cross-layer residency improves.
4. Measure dependency-visible attention time and relevant cache read/miss/stall counters, complete decode-round time and cross-rank maximum. Do not equate requested bytes, repeated source references or lower misses with saved critical-path time.
5. Existing agent-p75 and Mooncake remain the service evaluators. Agent-p75 long outputs expose repeated decode; Mooncake's context/cache distribution challenges the policy. Neither alone diagnoses cache residency. Keep frozen long-output ITL primary, separate TTFT/tail/goodput/failure guards, exact workloads and matched baseline. No new workload is justified until actual exposure in these standard runs is checked.

**Null/rejection:** FIRST or NORMAL wins; LAST merely redistributes misses, thrashes useful working sets, adds instruction cost, or leaves complete-round/service ITL unchanged. Preserve that outcome. Unknown overlap, working-set pressure and actual component criticality prevent a numerical ROI estimate. This option can be cheaper to test than a kernel rewrite, but cannot displace stronger measured candidates on evidence currently available.

## 7. Artifact and scope notes

`source-manifest.json` pins source bytes, `claims.json` contains exact source quotes, `candidate.json` records the deferred intervention, and `source-export.json`/`command-journal.json` preserve isolated research state. Fulltext is unversioned arXiv URL with exact retained revision hash; no author code from that CPU paper was inspected. Direct dependency fetches and a failed CMakeLists locator are recorded separately. No files in original source trees were changed; no canonical state, Git, S3, model, CUDA or serving operation occurred.
