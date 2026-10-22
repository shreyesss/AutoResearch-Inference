# Round93 — exact host Engram row layout after analogical retrieval

## Result

One concrete **low-priority deferred component**, not an implementation-qualified improvement: store each frozen FP8 Engram row beside its original UE8M0 scale bytes in host backing storage, preserving exact bytes and output order. The source delta is real, but a cheap address falsifier rejects the proposed shortcut explanation that this automatically saves memory-transfer bytes. Its remaining motivation is conditional page-translation locality, not compression or reduced projection work. No new typed hypothesis was created; disposition awaits independent review. No GPU/native/model import, build, benchmark, serving change, canonical write, or cloud operation occurred.

Target: Flash1017 checkpoint1bae0e1088993b9b82de08f59de5be5a34e42170; callgideon/vllm c4557869393db4d75c483d92edd02a5125500883; planned B200 TP1/DP4/EP4, frozen weights. This is source-plan evidence, not actual active allocation/page-size or latency attestation.

## Prior and adaptive search

Full compact recall covered153 cards with a stable matching inventory hash. Complementary report search covered Engram, embedding+batch, NUMA, and CXL. Existing EG02 hot-row caching/dedup, EG01 packed output staging, A01 WKV lookahead, ER73 modulus, EM75 request mapping and exact-size registration are distinct or duplicate mechanisms, not missing basics to rediscover. The actual lookup already has 16-row persistent tiles, optional table-order sort above36,864 rows on the SM100 family, a background half-SM grid, and lookup prefetch/events. None is proposed anew.

One July–October OpenAlex query returned ten mainly neighboring vector-search/RAG/architecture papers. One narrower August–October arXiv query returned twelve references, including a directly relevant n-gram paper. Provider receipts retain publication intervals, dates and identity mappings; duplicates across providers are counted once by explicit IDs. The selected paper was previously abstract-only in round60, so reading its versioned full text is new evidence, not a new title discovery.

Normal `investigate` fetched **N-Gram Memories at Two Bits: Quantizing Lookup Tables in Large Language Models, 2610.21810v3**. Read its representation, related work, and AppendixG layout/tier evaluation; selected passages elsewhere establish table shape and post-training scope. We did not read every benchmark table or claim to reproduce the paper. Its TF-Engram and CXL citations were checked against retained metadata; no additional fulltext was fetched because an SSD/new-hardware placement package would not resolve this narrow layout question.

Read-only PR search found Mooncake#4507, then selected import and normal `pr-search` replayed the isolated subset. Its Store gather proposal is inspected at body level only, not implementation-qualified or claimed absent everywhere. A title/body match was not treated as target reachability.

## What transfers from the paper

[CP v3](https://arxiv.org/html/2610.21810v3) uses independent fixed-size row records containing trellis symbols and a BF16 row scale. AppendixG compares row records against tile-window decoding; it explicitly separates computed sector counts from measured bandwidth and finds no consistent HBM decode advantage. The transferable idea is to evaluate the complete independently requested row and its metadata together. The published comparison does **not** establish that co-locating native FP8 bytes and native scales improves this target.

The full CP codec is post-training compression without neural retraining; it must not be rejected merely as a trainer. It nevertheless reconstructs different row values and changes model outputs. Its quality/storage results do not qualify the exact-output layout arm. We retain it as a separate conditional lossy direction requiring numerical/task admission, not a part of this proposal. No codebook fitting or table conversion was executed. Its H200/reference-code measurements and capacity-driven workload changes are not B200/c455 ITL evidence.

## Exact pinned operation and proposed delta

`common/engram.py::DPSharedEngramStorage` allocates values first and scales afterward. Private/THP allocation follows the same logical planes. The word `_packed` in this code means one allocation containing two planes, **not interleaved per-row records**. The retained target config has head dimension256 and quantization group32: each row requires256 FP8 bytes and8 original UE8M0 bytes. Two Engram layers each use24 hash heads. Runtime executed/padded row counts are not inferred from this static multiplicity.

`_engram_lookup_kernel` loads `weight + local*DIM + cols` and `scales + local*(DIM/QUANT_BLOCK) + scale_cols` within the same kernel, then writes BF16 or packed output. Thus this change removes no kernel launch, conversion or lookup row. Its first useful consumer is those UVA host loads; downstream WKV and existing output staging remain unchanged.

Proposed representation:264-byte host records, FP8 values at offset0 and unchanged scale bytes at offset256. Both parameter views would use row stride264; the lookup must accept separate physical row strides rather than hardcode256 and8. Shared allocation/loader/reload ownership must be updated coherently. The pinned `csrc/cuda_view.cu` uses original sizes and strides for already pinned tensors and retains their owner, so strided UVA views have a source-level path. The unpinned fallback first makes the tensor contiguous and copies it; that would defeat this representation unless explicitly excluded or adapted. No claim is made that an untested view is accepted by all loading/registration code.

Exact bytes, logical row/head mapping, original scale interpretation, BF16 rounding, invalid/dead/padded-row zeroing, sorted-destination permutation, two-layer stream events, sharding and output layout must remain intact. Preserve current shared-storage identity, registration lifetime and captured addresses; changing layout after capture requires rebuilding those objects. Avoid a temporary second full table at steady state; if conversion is post-load, peak host allocation and reload handling need explicit accounting. No row compression or new arithmetic is part of this arm.

## CPU/source falsifier: narrower benefit than it first appears

`layout_control.py` uses integer addresses, not hardware counters:

- Assumptions: page-aligned base,32-byte sectors,4KiB pages, isolated cold rows, separate nonoverlapping value/scale planes.
- Across the512-row alignment period, both layouts touch **nine unique32-byte sectors per isolated row**. Co-location does not imply fewer sector bytes or PCIe transactions.
- Per-row distinct virtual pages average2 for the separate planes and1.0625 for264-byte records. This is an address-footprint result, **not measured TLB misses**; actual page size, translation caches, NUMA placement and load coalescing are unknown.
- For512 consecutive rows, unioned page counts are **33 in both layouts**. Summing independent-row counts would exaggerate a batch benefit. Existing sorting and page reuse can eliminate the proposed advantage.
- Eight byte-copy controls preserve exact256-byte value payloads and8-byte scales; leaving the original hardcoded row stride produces a negative control. This tests byte/address logic only, not PyTorch loader, UVA, Triton codegen, numerical runtime parity or performance.

The remaining hypothesis is therefore narrow: if native small random host lookups have exposed translation cost from separate value/scale pages, co-location could reduce it without changing outputs. Scale pages may already be cached; page walks may overlap; misalignment or changed memory instructions may regress. Huge pages, sorted large batches or a different active host path could remove relevance. No exact-target access/translation trace was found in prior retained applicability reports; no new claim of global absence is made.

## Neighboring Store pipeline and other exclusions

[Mooncake#4507](https://github.com/kvcache-ai/Mooncake/pull/4507) proposes CPU-owner gather into two registered512KiB staging buffers, then ordinary Transfer Engine WRITEs, selected for many small source ranges with contiguous destinations. This is a useful bulk-transfer component, but the target does not call Store `get_into_ranges`: hashes are produced on GPU and the native lookup directly reads registered host memory. A direct Store toggle is ineligible. A separate CPU-packing design would need current hashes on CPU, ownership/lifetime and extra staging/transfer scheduling; no such overhead-free path is established. Its prefill-oriented thresholds and lack of performance results in the RFC cannot justify a decode claim. No full diff or code read is claimed.

FlowTT needs TT-core computation reuse absent from this frozen embedding representation; its abstract is retained, not a whole-paper impossibility claim. COUNT changes memory contents/architecture. Chimera's candidate filtering and CPU scoring do not return the exact arbitrary requested Engram rows. RAG pipelines and GPU architecture proposals do not establish an operator change here. All returned references remain in dispositions.

## Rubric and smallest next decision

- **Relevance:** native host lookup is directly affected if that route is active; exact allocation, page size, numerical branch and exposed time remain unknown.
- **Distinctness:** host backing-row co-location differs from EG01's output staging and EG02's repeated-row reuse. It is not a new cache or projection algorithm.
- **Evidence:** pinned two-plane address expressions and strides establish absence; paper supports independent-row layout as a design question, not the gain.
- **Cost/risk:** changes a very large shared allocation and loader/kernel interface for uncertain translation savings. Priority is below narrower established whole-work-removal ideas.
- **Disposition:** retain low-priority deferred component; reject automatic byte/bandwidth gain and direct compressed-codec/Store transfer claims.

Fastest remaining check is an already-existing exact-profile allocation/access record showing the active host path, page size, row distribution and exposed lookup/translation cost. Without it, do not manufacture a Zipf hit rate or numerical ROI. When native testing is separately authorized, validate original versus interleaved byte/numerical outputs under masks, reload, sorted/unsorted paths and graph replay before a matched lookup comparison. Compare complete lookup time including address changes and maintain the same stream policy. Existing Mooncake and agent-p75 serve latency/throughput evaluation; shared prompt prefixes are not proof of actual row locality. Only a small component attribution measurement is additionally needed to test the translation mechanism; no new service harness is proposed.
