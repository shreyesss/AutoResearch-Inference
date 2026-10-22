# Round 15 — exact sparse execution, selective component reuse

Status: CPU/source research only. **No GPU, model, serving, availability helper, or canonical writer operations.** The target is the planned Flash-1017 revision and vLLM `c4557869393db4d75c483d92edd02a5125500883`, not an attestation of a live deployment.

## Outcome

- **One new deferred hypothesis:** capacity-preserving, context-work-aware permutation of eligible uniform-decode request bundles before the existing microbatch split. It has an actual source difference but unresolved activation, adaptive-verification, metadata and critical-path gates. It is not ready for implementation.
- **One refinement of existing AT02:** QUILT's exact set decomposition and cascaded sharing, with final private-tail clipping disabled. A recent FlashInfer union/mask PR supplies a concrete metadata donor. Do not count this as another cross-query-sharing hypothesis.
- **Two transfers not qualified:** WaveAlign count ordering lacks demonstrated work variation in the target saturated reader; JSSA's MLA gather-free execution is already the kind of path our target uses.
- **Zero implementation-qualified or service-qualified improvements.** This round improves the specificity and falsification of the portfolio; it does not establish a speedup.

## How discovery actually ran

The host agent authored two plans; `researchctl expand --plan` validated and retained them. It did not invent the queries. Two initial online requests (arXiv and OpenAlex, June 1–October 22) returned 16 rows. After finding a fixed-count applicability problem, one explicitly authored arXiv follow-up searched gather/coalescing/irregular sparse execution and returned eight rows. **24 result rows, 21 canonical papers**, including provider mirrors and repeated discoveries. Four papers received pinned full-text reads: WaveAlign, the KARAT/PNM scheduling paper, QUILT and JSSA. `paper-dispositions.json` preserves every paper screen and depth.

Three bounded FTS queries read the entire local corpus through SQLite `mode=ro` inside one read transaction; they returned 39 distinct PR bodies. Those exact records were copied into this isolated state. Three actual `researchctl pr-search` calls then replayed inspection over that **39-record subset**, not a second full-corpus search. Exact QUILT/WaveAlign/JSSA name search returned zero PRs. Mechanism terms found relevant union/mask and sparse-kernel work. Coverage and selected IDs are in `pr-source-query-receipt.json`; bounded top-20 retrieval is not exhaustive negative evidence.

FlashInfer #6421 head/base metadata and file list were fetched and saved; three files at head `dffe440df5ab858d8f37279faf811c565218466a` were read through the actual pinned-code tool. Full PR hydration subsequently failed with a sanitized `RuntimeError`; the three pinned-file reads succeeded. The retained opening body plus current PR head/file metadata are evidence; missing hydrated discussions are not silently treated as read.

Operational mistakes retained: initialization with `--defer-snapshot` was rejected and corrected; the first expand therefore had uninitialized state. A code investigation with `deep-count=0` returned `no_selected_sources`, so it was retried at one. A source-copy script initially used a wrong cache-utils path and was corrected to `common/ops/cache_utils.py`. None of these errors involved GPU execution or provider-query broadening.

## A. QUILT component: refine AT02, not a new idea count

[QUILT, 2610.11134v1](https://arxiv.org/html/2610.11134v1) concatenates and sorts neighboring unique Top-K lists, detects common entries by adjacent comparisons, then separates shared and private segments. Cascaded intersections expose sharing at different group sizes. A small shared tail may be pushed into private work while preserving support. The paper explicitly identifies **final private-tail pruning as the approximate step**; omit it.

This is useful selective reuse from a paper whose complete benchmark recipe is unsuitable for our exact-execution lane. Its evaluation is Ascend 910C, Top-2048 GLM/DeepSeek-3.2, and an optimized CANN baseline. The report's large TTFT/kernel reductions cannot be carried to B200, Top-512, or our fused backend.

### What remains to improve here

Our `flash_mla_mega_attn.py` prefill already gathers and dequantizes compressed KV plus SWA into a combined BF16 buffer before attention. QUILT's repeated per-query dequantization explanation therefore does **not** describe that stage of our baseline. The remaining possible gain is sharing selected **BF16 reader loads / on-chip use** across neighboring queries; it needs actual overlap and kernel-cost evidence. AT03's across-layer materialization reuse is a different operation, and must not be credited twice.

AT02 already proposes bounded query grouping and KV reuse with original masks. QUILT adds a concrete exact intersection/private-tail algorithm and a cascaded granularity option. Preserve it as an AT02 refinement.

### Concrete donor and limits

[FlashInfer #6421](https://github.com/flashinfer-ai/flashinfer/pull/6421), at the pinned head above, provides `group_union_masks`: a per-request group union in cache-slot order and per-query bitmask. It is a reusable metadata implementation option, not a replacement H512 Mega-attention kernel. Its PAGE=64, Top-K multiple-of-512, shared-memory bitmap/domain limits, equal consecutive grouping and valid-union mask-length contract need adapters. Our combined 512+128 support is not directly that API's 512-aligned list; treating compressed and SWA as separate typed contributions is necessary. #6363 is the preceding stack version, not independent corroboration.

[FlashInfer #6339](https://github.com/flashinfer-ai/flashinfer/pull/6339) supplies another concrete SM100 union kernel, but its BF16 H128, 16:1 GQA and selected64-token-block contract differs from H512 MLA. Its own zero-overlap cases regress. It is useful design evidence, not a direct port.

### Correctness and fastest falsification

1. Keep request identity, physical buffer/source identity and occurrence identity. Equal integer token IDs across compressed and SWA caches are not equal attention contributions. Never deduplicate repeated meaningful occurrences merely because their bytes match.
2. Exclude padding before the unique-list SCSD algorithm. Respect per-row valid lengths and causal masks; retain the private remainder exactly.
3. If separate attention partitions are merged, merge unnormalized numerators using their partition functions/log-sum-exp. Averaging normalized outputs is wrong. Apply the attention sink once.
4. Reordering/partitioning changes floating-point accumulation; exact set support is not bitwise target-token equality. Later device and model differential checks remain mandatory.

Executed `scsd_contract.py`: 1,000 random unique-list cases, five boundary cases, and request/pool alias, repeated-padding and lossy-tail counterexamples. Independent `review/round15/softmax_contract.py` tests the real-valued partition algebra and falsifies naïve merges. These are **algorithm-contract CPU checks, not tests of a GPU implementation**.

Next useful input is existing saved selected-index traces, if any, for same-request neighboring prefill queries. Measure typed overlap, union/tail lengths and existing BF16 reader exposure. If unavailable, retain the hypothesis without guessing either. Do not run a model merely to obtain them during this CPU-only task.

Future evaluation: unchanged agent-75 and Mooncake TTFT/throughput first, broken down by prefill length/cache-hit class. Their service metrics need separate kernel support/mask and token-output equality checks. A long-output ITL win is not implied by this prefill-only component.

## B. WaveAlign: preserve its condition, decline the unconditional transfer

[WaveAlign, 2609.34814v1](https://arxiv.org/html/2609.34814v1) has two components: query similarity grouping (already AT02 territory) and descending selected-block-count order within waves. The second component is more specific than generic locality. It requires row-work variation and useful shared working sets; the paper itself skips unprofitable sparse/short/already-local cases.

Target decode already consumes physical slots directly. Its configured fused kernel uses Blackwell cluster launch control to obtain subsequent jobs, rather than the paper's simple fixed row-to-SM wave picture. Decode work count reserves full SWA width and adds the actual compressed Top-K length. Saturated 512+128 rows consequently have equal counts; different context lengths alone do not prove reader imbalance. Short/invalid rows may differ, so this is not a universal impossibility claim.

The CPU fixture verifies that equal-count stable sorting is identity and varying-count sorting can change order. This only falsifies the unconditional premise. Before a new sorting intervention, require actual per-job count distribution and the current CLC scheduling behavior; do not infer it from raw prompt lengths. No standalone implementation candidate is promoted.

## C. JSSA: good partial component, already represented in the target

[JSSA, 2610.19026v1](https://arxiv.org/html/2610.19026v1) separates learned/scored selection from a gather-free indexed reader. Its new per-KV-head GQA reader is concrete, but the paper explicitly says the MLA branch uses FlashMLA sparse attention. Our `flash_mla_mega_attn.py:305–364` already passes quantized paged caches and physical slot IDs into the fused reader; `cache_utils.py:824–910` prepares mapped indices/counts. No extra gather elimination is established here. Reject the direct MLA gather-free port as redundant. Do not reject the paper's GQA contribution globally.

## D. New deferred hypothesis: context-work-aware microbatch composition

[KARAT/PNM paper, 2608.03555v1](https://arxiv.org/html/2608.03555v1), §CMR, repartitions requests by aggregate context length while leaving KV resident on the same device. Its hardware architecture is not ours. Its **request-composition algorithm** can be examined independently; the paper's throughput/TDP gains are not our forecast.

### Actual missing mechanism and relevant work

Pinned V2 `gpu/ubatch_utils.py:49–65` splits by DP-padded scheduled-token count. Producer/pre-candidate indexers still evaluate context-dependent logits, while optionally sparse consumers use a bounded candidate domain. Thus equal query-token counts need not imply equal indexer work. Compressed context, compression ratio, dense/sparse layer role and per-request query count matter; raw context is only an initial feature, not a latency model. Core sparse attention saturated at Top-512 has a different cost regime.

Proposed scope: **only when microbatching is already enabled and an eligible uniform-decode batch exists**, permute complete request bundles before derived batch metadata, using a capacity-constrained context-work partition. Keep identical scheduled-token capacity and existing split points on every rank. Retain original composition if the work proxy does not improve. Do not activate DBO or disable adaptive verification to manufacture eligibility.

### Why the simple paper algorithm is not directly safe

- `parallel.py` defaults `enable_dbo=False`; `use_ubatching` can also arise from `ubatch_size>1`. `maybe_build_ubatch_runner` requires DP>1. Exact planned launch activation is unknown.
- `gpu/ubatch_utils.py:399–426` assumes all ranks have equal token count in each microbatch for expert all-to-all. Arbitrary independent context-balanced split points violate that contract.
- Uniform per-request Q does not imply midpoint alignment: three Q=6 requests split at token9, through a request. Require aligned boundaries and actual complete bundles, including padding handling.
- Adaptive verification compacts and reallocates draft budgets on GPU (`model_runner.py:1418–1451`). CPU upper-bound bundle sizes do not prove final sizes. Initial scope excludes this active branch unless a no-sync correct mapping is demonstrated; do not alter the baseline to turn it off.
- Reordering must occur before `idx_mapping`, block tables, slot mapping, draft/logit positions and outputs derive from request order, preserving decode/short-extend/prefill classification. Permuting hidden states alone is incorrect.
- Aggregate local proxy reduction does not prove reduction of the distributed all-rank critical path. Changed per-microbatch expert routing and numerical batch behavior need their own checks.

### CPU discriminator actually executed

`cmr_contract.py` AST-extracts the actual pure NumPy slice helper without importing vLLM/Torch. It tests 200 synthetic equal-Q request partitions and synthetic inverse bundle maps. It demonstrates two concrete failures: arbitrary rank-local split counts `[6,18]` versus `[12,12]`, and odd uniform request count straddling a midpoint. Capacity-constrained greedy composition worsened the proxy in **2/200 cases**, so unconditional greedy replacement is not justified. Retaining the original when proxy-worse is necessary but not proof of benefit.

A labelled positive control `[16384,16384,1024,1024]` changes the maximum context-sum proxy from32768 to17408 while keeping equal query-token capacity. **Those are synthetic work counts, not measured latency, speedup, or a target traffic distribution.**

### Decision and next gate

**Deferred, not implementation-ready.** Cheapest next step: reconstruct the exact launch's DBO/adaptive flags and already-retained per-request metadata, then determine whether any eligible uniform complete-bundle regime occurs at all. If DBO is off or all eligible batches are absent, this scoped proposal has zero exposure. If eligible, build a CPU replay of the actual full metadata permutation/inverse mapping and collective schedule before any device implementation.

Future evaluator mapping: unchanged agent-75/Mooncake for ITL/TPOT and TTFT tail guards, accepted tokens, failures and goodput; stratify mixed-context versus uniform-context cases and compare unchanged DBO baseline. Existing traffic can test the effect only if it actually produces eligible varying-context microbatches. If it does not, a synthetic mixed-context replay is a mechanism diagnostic, not evidence of production value. Source-derived proxy must be checked against component exposure in a later authorized run; no numeric ROI is asserted now.

## Remaining screens and limits

The 21-paper and 39-PR ledgers distinguish full-text/body/code reads from title/abstract triage. PNM hardware, altered sparse support, SSD-only cache paths, diffusion temporal approximation and unsupported quantized reader formats are not transplanted. [SGLang #41461](https://github.com/sgl-project/sglang/pull/41461) adds Q/probability FP8 quantization and targets H20/H256, so its delayed widening is not an exact arithmetic port; its own 8K TTFT result is effectively flat. CAKE #5997 uses a different V4 NVFP4 ABI and shows H64/H128 regressions in its own tables; its promotional summary is not sufficient evidence.

All unresolved exposure remains unknown. Older unsuffixed Flash/B200 or H200 artifacts do not supply current Flash-1017/c455 component timing. No source result, CPU work proxy, or set identity is a measured service improvement.

## E. Follow-up: native speculative verification is a distinct exposure question for AT02

A source audit requested after the first review extends the same AT02 component question to neighboring verification-token rows; it does not add a new hypothesis identity.

The target does **not** establish identical selections for a two-token CED group. `attention.py:313–318` describes ratio-2 as compressed KV topology and cross-layer source reuse. `forward_q` at1503–1528 projects every `qr` row and applies that row's position. `sparse_attn_indexer.py:793–935` packs actual decode rows as `(B,next_n,...)`, uses per-row context lengths for native speculation, scores them, and writes per-row Top-K. `row_repeat` broadcasts visibility bounds in a layout case; it is not a broadcast of Q scores or selected token sets. Short-context all-candidate fill is a separate branch and can produce equal sets when compressed lengths coincide; it does not prove equality in long-context Top-K selection.

The configured FlashMLA fused core maps `s_q_idx=cta_x_idx/CLUSTER_SIZE`, loads Q from `params.q + s_q_idx*stride`, and accesses that row's indices. Its existing shared loading is across **heads of one token** (and the CTAs cooperating on that row), not explicit common-segment decomposition across neighboring token rows. L2 may already supply incidental reuse; absence of explicit sharing does not mean all repeated loads reach HBM.

Consequently a bounded query-pair common/private decomposition could target **same-request native verification rows**, preserving each query's typed support, causality, sink and normalization. Actual overlap is unknown; the runtime `next_n`/valid verification count is not assumed to be a fixed five. Mixed requests, adaptive verification and partial bundles require explicit mapping. Initial exploration can share only compressed-cache common entries and retain each query's SWA occurrences privately, avoiding unsafe cross-pool deduplication.

This decode arm has a stricter break-even question than long-prefill: sorting/intersection, metadata and mask construction, query/head packing or transposition, padded common/private tile tails, extra synchronization and per-query normalization may cost more than the avoided selected loads/dequantization. Do not reuse QUILT's NPU hidden-vector-slack assumption or #6339's head128/16:1 tile win as a B200 H512 fact. Exact support still requires later numeric/token differential verification after reordered accumulation. Existing saved per-row index traces and configured kernel shape are the cheapest evidence to examine first; none was produced by a new GPU run here.

If this arm later becomes eligible, agent-75/Mooncake can measure ITL/TPOT and goodput with unchanged native speculation, acceptance and TTFT tail guards; a separate correctness comparator and per-round timing/overlap evidence would explain causality. Neither the paper's TTFT gain nor this source audit forecasts that decode benefit.
