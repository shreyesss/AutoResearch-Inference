# Round37 — resident selected-KV work elimination

**Outcome: zero new hypotheses; zero implementation or service qualification.** Four bounded online searches returned36 rows /33 explicit paper identities across three successful OpenAlex requests; the arXiv request failed with429. Two selected fulltexts were read. This round found useful exclusions and reusable components, but no demonstrated missing exact component worth a new implementation proposal on the planned Flash1017/c455 resident B200 path.

No GPU, backend/model import, build, serving change, timing invention or canonical-state mutation occurred. The139-card compact recall is retained. MP17, AT02/AT03, M02, NQ33 and earlier lossless-cache directions are not regenerated as new ideas. Root34's separate Top-K work was not reclassified as this round's discovery.

## Starting from the implementation

Pinned `nvidia/flash_mla_mega_attn.py:_forward_decode_mega` directly passes quantized paged SWA and compressed caches, physical slot indices and lengths to `fused_norm_rope_attn_rope_cast_decode`. Records are528B FP8 (512 value bytes +16 inline scale bytes), or288B for the optional compressed FP4 cache. This planned lane uses native FP8 KV; optional formats do not establish actual configuration.

`_decode_compressed_kv_and_topk` already calls a helper fusing local-to-physical slot conversion, lengths and validity handling. Reusing that publication across index-sharing layers is MP17, not a new gather idea. Decode does not first materialize a complete selected BF16 tensor in HBM. Prefill does have a different combined BF16 gather path; AT03 already studies source20 materialization reuse. Cross-query shared loads/intersections are AT02. Generic indexed gather-free attention, cached mappings, or query grouping therefore needs a specific delta beyond these existing components.

The task objective is long-output ITL with separate guards. Being on a repeated decode path establishes possible exposure, not a measured bottleneck. Neither total context length nor top512 is a byte-traffic measurement; compressed context, source/consumer layer, selected-set overlap and GPU cache behavior intervene.

## Search adaptation

1. **Selected KV/cache/locality query, OpenAlex:** returned SPIN, AVSG-adjacent offload work, HiSparse, QUILT and other directions. SPIN was selected for fulltext because it explicitly claims indexer work removal and handles speculative verification.
2. **Quantized sparse layout query, arXiv:** HTTP429, with retained status and exact unrelaxed query. It is not an empty-literature result. No retry storm or hidden semantic widening.
3. **Quantized attention memory layout, OpenAlex:** mostly changed-value quantization and known D-Quant. Those titles were not counted as evidence of a target-compatible layout transformation.
4. **Cache-aware physical layout, OpenAlex:** agent-authored adaptive plan was validated through `expand --plan`. This brought AVSG, selected for fulltext because its exact selected-token reuse could potentially remove repeated traffic. Tessera's exact physical mask mapping remains abstract-level background, not a read-and-qualified implementation.

The paper ledger labels each record's read depth; most returned titles were not promoted or deeply screened. Fulltexts were fetched through unversioned arXiv HTML endpoints and retained by content hash. They are not revision-number-pinned author code. No auto-selected README was fetched and no author repository pin was inferred from unrelated links.

## Screen37-A: SPIN — substantial work reduction, different correctness contract

[SPIN,2610.09025](https://arxiv.org/abs/2610.09025) maintains vertical and diagonal EMA score statistics, predicts block importance, scores only selected blocks, then runs original Top-K inside those blocks. It max-pools predictions by block and reserves a fraction for random exploration. The source explicitly says skipped blocks receive no score updates and may become important while excluded. Exploration mitigates this; it is not a certificate that omitted blocks cannot contain current Top-K tokens.

A minimal logical falsifier of exact transfer is one omitted block whose current score rises above every selected block while its old EMA remains low. Capacity for K entries within the retained blocks does not make their Top-K equal to the full current domain. No synthetic execution is needed to manufacture this result: the paper itself measures misses, including nonzero mean/p99 misses and quality tradeoffs.

The serving headline uses DeepSeek-V4 Flash,507K cached context +5K new tokens,96 concurrent requests and16K outputs. That does not forecast our exact model or current indexer work at agent-p75/Mooncake contexts. The paper's MTP ablation uses draft length3, row-local mask union and prefix-valid EMA updates; neither matched acceptance averages nor task scores establish identical target execution. V4.1 DSpark5 and layer/candidate sharing need separate analysis.

**Selective reuse:** prefix-valid state updates and per-row mask-union ownership are useful design cautions for a future predictive prefetcher. If all current scores and selections are retained, prediction can merely prefetch/reorder work; it no longer removes the indexer work responsible for SPIN's gain. If scores are skipped, a formal bound/exact recovery or an explicitly approved approximation/quality policy is needed. No such target-compatible mechanism was established here. AT01 already covers certified partial-head score pruning; M02/Root34 already cover threshold prediction plus exact selection recovery.

**Disposition:** reject direct transfer under the unchanged-support contract; preserve the approximation research lead without declaring it universally useless. Do not open another hypothesis just because the paper reports a sizable ITL result.

## Screen37-B: AVSG — exact reuse saves an offload transfer our path does not perform

[AVSG,2609.37538](https://arxiv.org/abs/2609.37538) is an exact post-selection gather operator for **host-offloaded** DSA on Ascend NPU. Its concrete components are vectorized full-ID hash matching, hit lifetime refresh, miss-slot reservation, balanced miss transfers and shared reservations across MTP tokens. Full32-bit identity comparison prevents a fingerprint-only false hit; the fingerprint is not a complete cache key.

The reported39% TPOT reduction is against the same offload layout without HBM-buffer reuse. The relevant work removed is repeated **H2D copying** of selected entries. The pinned target reader instead receives the original resident device caches directly; its selected IDs already address resident rows. Introducing another HBM copy/cache layer cannot claim those absent H2D savings.

A narrower resident adaptation might pack a persistent selected working set or retain dequantized rows. That would introduce matching, slot/lifetime state, copy misses and another representation. Cache-hit entries still need to be read by attention, and native GPU caches may already provide incidental reuse. Exact safe keys would require request/address-space identity, typed SWA versus compressed storage, layer/source group, block-table/reuse lifecycle and valid row limits. No actual selected-index trace, resident-cache miss cost or dequantization exposure establishes that this extra layer beats the native direct reader. Prefill materialization reuse and shared-query execution are already AT03 and AT02; the paper does not independently validate a new resident decode version.

**Disposition:** reject direct H2D-reuse transfer for this resident path. Retain the exact hash/slot-reservation component for an explicitly offloaded baseline or demonstrated resident packing bottleneck; neither exists in this round's evidence. This is not a rejection of AVSG's reported offload result.

## PR triangulation and exact target comparison

Four bounded read-only whole-corpus FTS queries (12results each, no date filter) were retained, then replayed through actual `pr-search` on an isolated subset. The second tool read is not independent or exhaustive corpus evidence. No exact AVSG entry appeared in this bounded retained search. A `SPIN indexer` hit can concern a GPU spin-loop rather than this paper; matching tokens alone is not corroboration.

- **FlashInfer6616**, retained opening-record revision updatedOctober18: describes inline528B FP8 /288B FP4 formats replacing footer-scale pages on SM120. Its body warns equal-size layouts can silently decode incorrectly and reports calibrated cold-L2 component improvements. The exact c455 Mega wrapper already documents and passes native inline records. Therefore this format migration is not a missing B200 component. The PR's source head and GPU claims were not independently reproduced or code-audited here; they are reported body evidence, while the target absence check uses pinned source. Do not import its SM120 calibrated percentages.
- **FlashInfer5022**, retained body: removes unused GLM NoPE RoPE reservation from656→528B rows. Our native record is already528B and its format differs. Its masked-slot-zero/NaN warning is useful correctness evidence, not a new byte saving here.
- **SGLang34583**, retained body: MiniMax-M3 IndexCache skips indexers at a configured layer cadence. It explicitly calls the reuse an approximation. Native V4.1 already has architecturally defined index-source sharing. Broader ad hoc cadence is a quality change, not redundant computation proven by cross-layer correlation.
- **DeepGEMM459**, retained body: accepts16-byte instead of512-byte page alignment and reuses warmed workspace for graph capture under serialized launch assumptions. This is an integration/layout compatibility change, explicitly no kernel algorithm change. It does not establish fewer selected KV bytes or reduced resident decode work. The cited4352-byte footer page is an index-cache integration example, not our inline main KV ABI. No new capacity-pressure or live mismatch is asserted; no donor head audit was required to make an implementation proposal because none is being advanced.

All local PR records and corpus revisions are preserved. Opening-record content hashes are not Git head pins. The target source files are pinned to c455 with hashes in source-manifest.json.

## Decision and stop/reopen rule

No new identity. Preserve the three concrete scoped exclusions: SPIN direct exact-support transfer, AVSG direct resident-path transfer, and re-porting already-present inline-layout/gather-free execution. No source-only screen is labelled a failed target experiment.

The next evidence needed to justify a resident adaptation is a **retained exact-baseline selected-index/consumer profile** showing which source groups and rounds reuse the same typed KV rows, actual cache/read/dequantization exposure, and whether a missing copy/materialization exists. Without it, packing/dequantization-cache additions may increase traffic and ownership complexity. Do not run a GPU to obtain that record during this CPU-only campaign. If such a record later exists, compare the proposed residual against AT02/AT03/MP17 first and reuse their identity when appropriate. A separately approved approximate-attention objective could reopen SPIN with explicit quality evaluation, but endpoint speed tests alone would be insufficient.

## Tool usefulness and limits

The adaptive searches found different mechanisms; fulltext changed decisions by revealing SPIN's omission/miss contract and AVSG's specific H2D denominator. Local PR data exposed already-present format changes and misleading cross-architecture gains. Pinned source established direct resident reads and existing mapping/gather structure. These checks were more decisive than another synthetic cache-hit simulation. **No new CPU performance or correctness diagnostic was executed**, because the transfer premise already failed at source/contract level.

One429 search failure is retained unchanged. The first broad prior print matched `COMP` when looking for `MP` and truncated output; the complete compact JSON is retained, and relevant exact identities and earlier reports were read separately. No claim is based on the omitted console text. Provider billing is not measured; bounded calls are not a zero-cost assertion. State remains isolated and requires reviewed retention/publication later.
