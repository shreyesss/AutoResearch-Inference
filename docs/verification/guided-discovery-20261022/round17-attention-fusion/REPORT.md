# Round 17: exact attention traffic, fusion and metadata reuse

**Outcome:** one low-priority, target-scoped deferred child proposal, **MP17-01**, in the existing Top-K mapping optimization family. Zero service-qualified improvements. No GPU, serving, model-import, canonical-state or publication work occurred.

Target is the planned Flash-1017 checkpoint revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, vLLM `c4557869393db4d75c483d92edd02a5125500883`, TP1/DP4/EP4 groups. Live image, dispatch and workload equivalence remain unknown. The objective remains useful serving improvement, including long-output ITL with tail guards.

## 1. Actual adaptive search

Five online searches returned 33 records representing 31 explicit paper identities. Three selected full texts were read. Full per-hit reasons, raw responses, original revisions and cached full texts are retained locally.

| Step | Query / decision | Outcome |
|---|---|---|
| 1 | OpenAlex `sparse attention indexer topk fusion`, June onward | Mostly application fusion; HPC-Ops already examined; Vortex only background from abstract. |
| 2 | OpenAlex `GPU sparse attention indexer memory fusion`, August onward | AttnFuse selected for full text; Tessera and MSDA background; W4A16 outlier fusion doesn't match frozen target representation. |
| 3 | arXiv `ti:UlaCache` | Explicit seed from parent's new discovery, not independent discovery; retrieved pinned v1 full text. |
| 4 | arXiv `(indexer OR top-k) AND (fusion OR epilogue) AND (GPU OR attention)` | Eight off-domain results at returned abstract/title depth; no forced positive. |
| 5 | arXiv `GPU AND "sparse attention" AND (indexer OR top-k OR fusion)`, August onward | Relevant systems returned, mostly existing prior work; recent MLIPS selected for full text. |

All three actual arXiv calls completed. No HTTP failure status was observed in this round. This does not repair or reinterpret the earlier failed receipts. Query 5 is an adaptive development example, not a controlled search-quality or recall experiment: date range and query terms changed together.

Full-text investigation used `citations_per_paper=0`, `max_repositories=0`, one logical cache miss per paper. No model calls or Serper. Unselected papers retain **abstract/title-only** classification. Local FTS triangulation was bounded, not an exhaustive GitHub search, and did not refresh PRs.

## 2. UlaCache: reject the headline transfer, reuse a smaller component

[UlaCache v1](https://arxiv.org/html/2610.29820v1), October 21, addresses active-history capacity and distributed storage. Its §4.2 explicitly says DP reads its rank-local GPU pool **without** the selected-copy buffer used by TP. TP redistributes histories and caches fetched selected entries locally; optional CPU storage requires replacement and transfer protocols.

The benchmark is GLM-5.3, 8×H200/B300, FP8 weights/KV, 64–128K Multi-LexSum inputs, 2,048 outputs and MTP with two draft steps. The headline throughput comparison is against HiSparse at admitted capacity. **At batch size 1, UlaCache is slower than GPU-resident SGLang in all eight configurations** (§6.2). Thus its transfer/cache-capacity improvement is not evidence for a faster fully resident TP1/DP4 Flash-1017 decoder. No current capacity pressure is attested. The offload/capacity lane belongs with existing M04; it is not a new active-node win.

The useful smaller component is §4.2's **access-plan reuse across layers sharing sparse selection**. This can motivate an exact metadata-lifetime question even when no remote KV is present. No UlaCache implementation repository was positively identified from the retained paper links; dependency links are not claimed as author code.

## 3. MP17-01: publish physical Top-K metadata once per eligible index group

### Existing behavior and concrete delta

At the pinned source:

- `attention.py:314–358` derives the latest KV-source and index-source independently. Consumers share the most recently published logical Top-K buffer.
- `nvidia/flash_mla_mega_attn.py:305–323` calls `compute_global_topk_indices_and_lens` on every compressed decode consumer.
- `common/ops/cache_utils.py:824–910` already fuses **page-table lookup, valid-entry count and padding-length masking**. There is no missing three-way fusion to invent.
- The helper preserves the order and multiplicity of nonnegative indices, emits `-1` for invalid entries, and leaves mapped slot contents for padding rows while making their lengths zero.
- `nvidia/flashmla.py:125–136` and Mega `:258–265` obtain compressed-cache metadata through the KV-source prefix. SWA metadata remains layer-specific.
- `sparse_swa.py:600–625` derives row-to-request mapping from common metadata and derives validity from that layer's slot mapping. Therefore identical Top-K and compressed-cache pointers alone **do not prove** equal outputs.

The model topology gives index groups 2–7, 8–13, 14–19, 20–23, 24–27, 28–31, 32–35 and 36–39. KV source 20 is shared through layer 39, but **index metadata must refresh at 24, 28, 32 and 36**. Reusing source20's selection through all twenty consumers is incorrect.

For a conditional full backbone traversal where every compressed layer executes Mega decode with equivalent metadata in its group, the repeated helper sites number 38; one publication per index group would number 8. This is **topology arithmetic, not an observed call count**. Mixed prefill/decode, partial traversals, backend fallback, replay and per-rank activity change exposure.

### Proposed bounded adapter

Unconditionally publish mapped indices and lengths at each eligible index-group entry into graph-static resources. Consumers use them only until that group finishes. Every execution republishes, including executions with identical tensor addresses. Isolate resource ownership across ubatches/lanes/streams; next publication must follow all previous readers. Unsupported partial traversal, metadata or backend uses the original helper.

Required equality contract includes Top-K contents/order, row partition, request map, physical page table, compressed page size and validity. Source20 cache sharing alone is insufficient. The design must establish equivalence statically from actual builder/dataflow or cheaply from already available host facts; adding per-layer GPU comparisons/synchronization can consume the whole potential gain. A Python "filled" flag retained across graph replay is invalid.

This is not AT03's prefill BF16 materialization reuse, AT02's cross-query KV load sharing, PJ01's output-column projection reduction or TR01's input-row trimming. It does relate to canonical H200 R1:

`hypothesis:42e6a9af04fe7bd2d3b8ad717ece4296d1ba0496c9df39728fddd89672105388`

That prior fuses selection with physical mapping. MP17-01 removes repeated consumer mapping after an unchanged selection. Its H200 baseline `baseline:a399927...` must not be rewritten as c455. Record **one target-scoped child with derived-from/compared-to lineage, same mechanism family, no novelty claim**. Later comparisons need native, reuse-only, eligible selector-fused-only and combined controls; their savings cannot simply be added.

### CPU evidence and falsifiers

`mapping_contract.py/json` transcribes the integer mapping semantics, without importing Triton/Torch. It demonstrates six failures of stale reuse: changed selection at a new index source, request reorder, changed physical page table at the same address, changed per-layer validity, changed compressed page size, and duplicate collapse. A separate alias example shows republication mutating data still referenced by an earlier reader.

The 500 equal-input cases establish only consistency of the supplied pure model. Comparing the same model with equal inputs is **not independent implementation validation**. The useful evidence is the changed-input counterexamples and source requirements. No actual graph, metadata equality, cache generation or compiled reader contract was executed.

The first fixture invocation failed because the raw config nests parameters under `text_config`; the corrected fixture reads that exact path and completed. This was a fixture error, not a target failure.

### ROI and evaluation

There is no measured mapping bottleneck. Thirty fewer outputs would remove 61,560 bytes per decode row of mapped-index/count **writes only**, under the conditional 38→8 model. This is not total HBM savings: input reads, table lookups, attention reads, allocator behavior and graph execution remain. Graph replay may make launch savings small.

Fastest next step is source/dataflow closure and saved-metadata comparison, not a serving patch. Fail the scope if a consumer can enter without publication, metadata differs without a cheap repair, or a reader can outlive/reuse the buffer. When GPU work is separately authorized, first compare actual metadata bytes under padding, changed tables, partial groups, mixed requests and graph replay. Then use existing Mooncake and agent-75 evaluations, with the identical workload, accepted-token progress and SLA guards. Measure exposed target-round time, eligible mappings and unprofiled request ITL/TTFT/goodput. No bespoke evaluator is currently justified.

Status remains **deferred, low priority, no numerical gain forecast**.

## 4. Independent triangulation and other selected papers

### FlashInfer #5118: relevant design precedent, not direct serving evidence

The retained local opening record for [FlashInfer #5118](https://github.com/flashinfer-ai/flashinfer/pull/5118) already describes an owned candidate-metadata snapshot, explicit republication, ordered readers and cache-address-width checks. It concerns candidate **index scoring**, not attention's final Top-K mapping. It usefully challenges any claim that this lifetime design is new. Its prepared-arm timings exclude publication and use different head-reduction precision recipes from pinned DeepGEMM. No current PR status, head code or serving portability was established in this bounded round. Do not transfer its microseconds to MP17-01.

Other FTS hits: #62170 targets V3.2/GLM fused-Q weight output; #62172 selector BF16 input changes have model/dispatch conditions; #30923 eliminates unused indexer cache allocations in GLM. Native V4.1 already owns index state only at configured source layers. These opening records are leads/context, not newly qualified proposals.

### AttnFuse: the claimed fusion gap already closes on our selected source route

[AttnFuse](https://arxiv.org/html/2609.13612) makes pre-matmul RoPE expressible in a DSL. Its H100 fast path is causal MHA/GQA, D64/128, FP16/BF16; FP8 is future work. It reports long-context Hopper cases where pre-rotation beats fusion. The full Llama training integration did not execute fused RoPE because the HF layer had already applied it (§6.5).

Pinned `flash_mla_mega_attn.py` already calls `fused_norm_rope_attn_rope_cast_decode/fwd`, consumes paged quantized H512 caches and emits quantized output. This rejects “add RoPE/attention/output-cast fusion” as an absent component on the selected Mega source path. It does not prove that path is active on the live node or that no kernel tuning remains. Do not transfer the RTX3090 headline or replace the existing kernel with this DSL on that basis.

The retained full-text URL is **unversioned**; observed body hash is in the dossier/manifest. No publication-version pin is invented.

### MLIPS: exact-producer language does not mean exact consumer selection

[MLIPS v1](https://arxiv.org/html/2610.27438v1), October, shares wider candidate pools while each consumer scores its own candidates. The paper explicitly identifies trained V4.1 pools as related prior work; its experiment is V4-Flash on GB300 TP4, not this V4.1 checkpoint. Consumers cannot recover omitted keys. Persistent reuse omits newly relevant old keys and newly appended keys unless handled; its reported quality deltas are single runs.

Its exploratory Top-G prefill pool is not a ready exact-execution component: Appendix E explicitly notes that pool membership can depend on future queries even if future key positions are masked. Simply retaining fresh scores does not remove that dependence. Broader query working-set sharing is already AT02; no new ID is warranted for the same direction. Approximate pool policies could be evaluated under a separately scoped quality budget, but they do not satisfy this round's unchanged selected-support constraint.

## 5. Honest yield and retained state

- 33 returned paper records / 31 explicit identities; three full-text reads.
- One target-scoped deferred refinement proposal, one existing mechanism family.
- Three selected direct-transfer stories screened out or narrowed; prior hypotheses were recalled instead of regenerated.
- Zero implementation, GPU tests, benchmark wins or service-qualified ideas.
- Isolated research state contains records, revisions and query receipts; snapshot is deferred and unpublished. Parent owns later reviewed retention.

The decision-changing work was full-text applicability checks, the exact native fused call site, the independently changing index/KV source boundaries and semantic stale-mapping counterexamples. Repeating broad fusion queries or copying paper speedups would not strengthen this proposal.
