# Independent round15 sparse-attention review

Status: no new service-qualified hypothesis. QUILT's exact component is a refinement of AT02, not a new identity. WaveAlign count-sorting has a concrete target-exposure objection; JSSA gather-free selected reads overlap existing decode behavior. No GPU, model, CUDA, provider or serving calls by reviewer.

## QUILT selective reuse

The retained fulltext explicitly separates exact shared-tail pushdown from approximate final private-tail clipping (§3.4). Disable clipping; retain every original support occurrence. Four-way then pairwise intersections offer a concrete implementation option for AT02's already-recorded query grouping and shared KV loads. This is more specific evidence, not another independent performance direction. Target prefill already dequantizes/gathers full compressed/SWA representations before attention, so the paper's eliminated per-query dequantization is not a target saving in that path. Remaining possible saving is BF16 selected-load reuse; decode has a different quantized direct reader and higher integration scope. No target overlap statistics or profitable group size is known.

Key correctness obligations:

1. Equality keys must include request/cache identity and typed address space. Compressed and layer-local SWA copies of one logical token may differ in representation and must retain their distinct attention contributions. Cross-query loads may be shared; per-query multiplicity must not collapse.
2. Q/K scores remain query-specific. A shared KV tile does not mean shared attention weights.
3. Shared/private partition outputs must merge using their maxima and partition functions, not averaging normalized outputs. Attention sink contributes once per query/head, not once per subpartition.
4. Preserve token position, validity, output permutation, causal masks and padding. A changed reduction order still requires target numerical/correctness tests; mathematical exact support does not establish byte equality.
5. Sorting, intersections, scatter/packing, metadata allocation and extra launches are costs. No generic benefit is inferred from lower logical load counts.

`softmax_contract.py/json`: 1,000 synthetic scalar float64 partition cases agree within 1.12e-15. Four negative controls falsify cross-cache aliasing, dropping duplicate occurrences, unweighted output averaging, and repeated sink inclusion. This validates equations only, not target tensor layouts or GPU execution. Worker set tests separately cover typed keys/padding/clipping.

## WaveAlign: mechanism exposure before a new card

The paper's second stage sorts rows by the number of accessed KV blocks within waves; it assumes meaningful uneven row work. Current indexer selects at most512 entries, rather than work proportional to full context length. `cache_utils.py:824–910` counts actual valid TopK indices and zeros lengths for padding tokens while fusing physical-slot mapping.

The pinned Mega kernel has stronger contrary evidence: `_make_outer_loop_args` in the selected dependency `core_attn/kernel.cuh:452–477` computes decode loop blocks from `ceil((params.topk + extra_topk_length)/B_TOPK)` when compressed KV exists. The SWA portion reserves its full configured width even if its live count is shorter. Full512 compressed rows therefore have equal loop counts at configured SWA128. Longer historical context alone does not produce longer selected-reader work. Short/padded/partly populated rows can differ; absence of all target imbalance is not proven.

The same kernel uses Blackwell CLC response-based next-job selection (`:500–513`), so naïve row-to-SM fixed-wave reasoning does not describe the complete current scheduler. The separate FlashMLA path also already constructs and reuses a per-layer-type tile schedule (`flashmla.py:225–258`; `sparse_swa.py:911–945`). These are not proof arbitrary sorting cannot help cache locality; they invalidate a blanket missing-load-balancing diagnosis. First establish varying actual loop counts and retained original support with admissible reorder overhead. The paper's similarity grouping overlaps AT02.

## JSSA / gather-free scope

`flash_mla_mega_attn.py:305–364` already passes the two quantized paged caches and physical selected slots directly into fused decode. No separate dense BF16 gather in this decode path should be invented. `cache_utils.py:824–910` already fuses mapping, valid count and padding masking. Prefill still materializes BF16, but replacing it is the prior direct-candidate reader/gather family, not a new hypothesis merely because another paper uses gather-free terminology.

## Decision

Retain QUILT exact cascaded intersections as new evidence/implementation option under AT02 with clipping disabled and the above falsifiers. Keep AT02 deferred; do not forecast ITL or throughput. Record WaveAlign sorting and JSSA direct-reader dispositions explicitly, including possible narrower follow-up if actual work distribution or prefills show a distinct unmet gap. No target live backend attestation was performed.
