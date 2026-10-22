# Round 43 — exact existing sparsity inside resident MegaMoE

**Decision: no implementation-qualified intervention. Three concrete screens are preserved: two rejected as scoped and one deferred to a cheap checkpoint-byte diagnostic.** This is not evidence that exact sparse execution cannot help. No GPU, model, backend or native library was imported or executed; no serving configuration, canonical state, weights or source repository was changed.

## Why this lane

CURRENT/checkpoint 13 and all 141 compact hypothesis projections were read before search. Both recall pages shared inventory hash `e4b1696042533edc10fc7d6a1121a19041799ef72c8dd7364513be8b191c90c7`. The selected question was whether existing exact zeros permit removal of expert arithmetic or weight movement while retaining the frozen target function. This differs from the existing histogram tile selector M01, physical weight placement RD01, packet layout WP38 and producer quantization MF19.

Source baseline: vLLM `c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, target checkpoint `1bae0e1088993b9b82de08f59de5be5a34e42170`; planned two TP1/DP4/EP4 B200 groups. This is a frozen source plan, not a current runtime attestation. The exact checkpoint config says expert dtype FP4. The inspected c455 MXFP4 MegaMoE route uses routed MXFP4, shared MXFP8 and dynamically quantized MXFP8 activations, with UE8M0 scales per 32 values. Eligibility for that route is conditional on actual backend selection.

## Discovery accounting and adaptive decisions

| Stage | Actual outcome | Decision |
|---|---|---|
| arXiv anchored zero-skipping query, Aug 1–Oct 23 | HTTP 429; no successful result coverage | Switch provider, keep failure receipt |
| OpenAlex activation-sparsity query | 10 hits | Read Celty and ByteCross full text |
| Retained source lookup | Existing abstracts/query references, no retained full text found | Fetch only selected full texts |
| Celty explicit repository investigation | Exact commit README; implementation forthcoming | Do not pretend a software port is available |
| OpenAlex quantization-induced sparsity follow-up | 10 hits, one repeated Celty identity | Inspect UnionSparse's representation component |
| Selected import + UnionSparse full text | Existing arXiv abstract reused; pinned v1 full text fetched | Evaluate exact existing-zero adaptation |
| Read-only canonical PR searches | Bounded opening-record results; four selected records imported | Actual `pr-search` replay over the four-record subset |
| Exact target header verification | One pinned DeepGEMM header fetched; equals earlier local bytes | Close target arithmetic provenance |

Totals: **3 search attempts, 2 successful queries, 20 hit references, 19 unique paper identities, 3 full texts, 4 selected PR opening records, 2 exact code records.** The small isolated corpus export contains 29 current source records, 33 immutable revisions and 224 edges. Twenty paper records include OpenAlex/arXiv aliases for UnionSparse; they are not twenty independent papers. The failed arXiv attempt is not counted as an empty literature search.

All 19 paper dispositions are in `paper-dispositions.json`; search bodies and dates remain in receipts and `source-export.json`. Celty and ByteCross were retrieved through unversioned HTML URLs; their receipt says `version_pinned:false`, even where the HTML identifies a revision. UnionSparse's fetched URL explicitly pins v1. Publication metadata is provider evidence, not independently verified editorial chronology.

The first offline expansion call omitted the required mechanism field and failed; the invalid input is retained. The repaired expansion was run subsequently. No successful expansion is fabricated for the failed call. Command journals preserve the actual ordering.

## What the papers actually contribute

### Celty: software zero-aware execution is a genuine separable component

[Celty](https://arxiv.org/html/2608.01536) includes a software SMEM implementation as well as a proposed custom architecture. Its software scheme broadcasts a scalar activation across a warp and skips the associated weight column when zero; RLC-CSC encodes sparse FP16 weights. The inspected regime is single-column matrix-vector execution, A5000, and induced weight plus activation sparsity. Software results are conditional on matrix size and sparsity; the large architectural headline is not an off-the-shelf B200 software result.

This component is not rejected merely because the paper also proposes hardware. However, its current direct port would replace a fused distributed FP4/FP8 resident MoE with a different precision, sparse representation and execution path. The paper's induced thresholds/pruning do not establish the exact-zero distribution of our frozen checkpoint. Its reported quality changes cannot be called exact target preservation. The pinned [public repository](https://github.com/RuokaiYin/Celty/tree/05415f9ec9baff308d622824a6e8097416b6892c) README says implementation is forthcoming; no kernel implementation was inspected.

**ZS43-01: reject the direct resident replacement as scoped.** Fine-grained exact-zero reuse remains an open component, conditional on evidence and an actual compatible implementation.

### ByteCross: retain its evaluation discipline

[ByteCross](https://arxiv.org/html/2609.33889) combines induced activation sparsity with sparse KV policies in FP16 batch-one execution. The important transferable component here is its matched baseline and byte/overhead accounting: an apparent 6.92× KV-policy speedup against masked attention becomes about 1.29× against the stronger split-K attention baseline in its 128K comparison. Those numbers describe the paper's comparison, not our target.

Our existing Mega sparse reader is already sparse and the MoE is already fused. Any future zero-skipping result must compare against that implementation, preserve routing/quantization/selected KV policy and separate detection, metadata, staging and decode cost. A theorem about fewer bytes is insufficient. No new ByteCross policy is proposed in this round.

### UnionSparse: reuse the codec question, not the INT4 kernel

[UnionSparse v1](https://arxiv.org/html/2608.09291v1) encodes four area-aligned weight values with one union-occupancy bit (the illustrated 2×2 area partition); these are not necessarily four adjacent packed nibbles. If any value is nonzero, all four values are retained; inactive groups omit the payload. Its reported implementation is W4A4 INT4 and targets Jetson with sparse/pruned weights. Its register-fragment decode path does not directly feed the target's mixed FP8 × MXFP4 TCGEN05/TMA path.

A narrower component can still be considered: encode **existing** exact-zero MXFP4 groups while preserving original value codes and scales, then reconstruct an existing consumer-compatible tile. Initial work need not prune, retrain or reorder rows. Row reordering from the paper is deliberately excluded from the initial diagnostic because it interacts with gate/up pairing, scale groups and output restoration.

**ZS43-03: defer representation adaptation to a CPU scan of exact available packed weights.** This does not require a GPU and should precede kernel work. No such weight bytes were inspected here.

## Target contract: why element zeros do not justify a tile skip

The pinned target source in `sources/target-mega-moe.cuh` already fuses BF16 rounding, gated activation, routing-weight multiplication, per-32 scale determination, FP8 conversion and intermediate stores in the L1 epilogue (roughly lines 1080–1225). The inspected scale helper floors the FP8 scale exponent at 105. For ordinary non-floor groups, a maximum remains nonzero after normalization. Quantization can create many zeros without producing an entirely zero group or K tile.

The executed scalar fixture constructs a 128-value row with **124 zeros (96.875%)**, yet each group of 32 has one nonzero and the K128 operand cannot be skipped. This is a mathematical counterexample to a density inference, not an observed target tensor. Entire CTA/paired-CTA eligibility is stricter still: the skip predicate must cover the actual live operand rows and consumers. Existing unrouted padding is not new sparsity to claim.

The MMA loop's accumulator-enable expression depends on literal loop positions. If the first MMA is skipped without replacing that initialization contract, the next instruction can accumulate into stale TMEM. The abstract fixture yields 105 instead of 6 from prior accumulator 99 and products `[0,6]`. This demonstrates a **repairable integration obligation**, not a proof that selective execution is impossible.

More materially, the activation/scale TMA producer and separate weight producer continue through every K block. Predicating only the MMA does not remove their loads or any claimed HBM/TMA traffic. Full/empty barrier progression and last-block completion must remain valid. A repaired coordinated producer/consumer design would need an exact zero certificate early enough to suppress useful work, first-active/all-zero initialization, unchanged accumulation semantics for surviving work and finite/signed-zero admission. None is implemented or timed.

**ZS43-02: reject the naive MMA-only branch as scoped.** Preserve the repaired protocol as an open question; the unknown frequency of truly eligible target tiles is the first exposure gate.

## Exact CPU checks executed

Command: `python3 contract_probe.py` (standard library only).

- Replicated the inspected FP32 bit-expression for scale selection and used a mathematical finite E4M3 round-nearest-even code table. Tiny floor-limited groups can become all-zero; ordinary normalized maxima remain nonzero in the selected cases. This is not compiled GPU equivalence, exhaustive numeric admission, or a claim about target weights.
- Executed the 96.875%-zero row and stale-accumulator counterexamples described above.
- Computed ideal four-value bitmap cost: one bit plus 16 bits for each active group. With all-zero group fraction `f`, ideal ratio is `1.0625 - f`; payload savings require `f > 1/16` before offsets/scales/alignment/staging/decode. An independent element-zero model is only an illustration, not a histogram estimator.
- Same 50% scalar zero density gives **18 bits or 34 bits**, versus 32 dense bits, depending on grouping. Joint correlation matters.
- Recorded that numeric `+0/-0` equality does not prove preservation of packed FP4 code bits or target arithmetic when zeros are omitted. Finite-input and output-equivalence policy must be explicit.

The fixture is intentionally not a timing benchmark, native correctness test or ROI estimate.

## PR triangulation and contrary evidence

Only opening bodies were read; no diff/review completeness is claimed.

- [FlashInfer #6371](https://github.com/flashinfer-ai/flashinfer/pull/6371) skips structurally zero triangular GDN prefill subtiles on SM120, preserving surviving K order. It demonstrates a different known-zero domain; it does not prove input-dependent SwiGLU tile zeros on B200.
- [FlashInfer #5031](https://github.com/flashinfer-ai/flashinfer/pull/5031) addresses all-zero-row scale failures in a different NVFP4 fast-math/ReLU2 path. Its zero rows are not evidence of target SwiGLU density or this FP8 helper failing.
- [FlashInfer #4805](https://github.com/flashinfer-ai/flashinfer/pull/4805) shows a faulty fuzz launch can produce misleading all-zero outputs. Retain independent quantization/reference checks, not a sparsity claim.
- [SGLang #32385](https://github.com/sgl-project/sglang/pull/32385) concerns scale padding in another quantization path. Uninitialized or padded zeros must not be counted as useful active weight/activation sparsity.

## Cheapest next evidence and future evaluator coverage

First, if exact checkpoint shards are already locally available, scan packed routed weight bytes on CPU without loading a model: distinguish true E2M1 zero codes and signed-zero bit preservation; calculate joint four-value zero groups under a specified area-aligned codec mapping and the **actual** kernel layout, scale overhead, offsets/alignment, per-layer/expert distribution and extra conversion residency. Stop the codec lane if total represented bytes cannot improve even before decode overhead. Do not substitute random independent zeros or dense BF16 values for this evidence.

For activation skipping, packed weight bytes cannot establish dynamic activation tile exposure. A future authorized trace would need actual live rows, per-group scales/zeros, the paired-CTA operand domain and detection latency. This round authorizes no such capture.

If a representation later survives, CPU round-trip of codes/scales and deterministic metadata cases come first. Native finite/signed-zero/padding/shared-expert/EPLB and graph tests are additional gates, not completed work. A controlled future comparison must include original MegaMoE, codec decode without skipping, and coordinated skipping only after numerical qualification. Existing Mooncake and agent-75 workloads cover end-to-end latency/throughput once the path is exercised; they do not prove exact arithmetic or compression safety. Pruning/thresholding would require a separate explicitly authorized quality contract and quality evaluator, not only these latency tests.

Primary long-output ITL/TTFT/tail improvement remains **unknown**. No target exposure fraction or cost forecast was invented.

## Tool usefulness and retention

The new explicit code-only investigation interface successfully fetched the pinned Celty README without inventing a paper dependency, and then fetched one exact target header. Selected-source import reused UnionSparse's existing abstract. These are field-use observations, not controlled evidence that a skill improves research quality. The failed expansion and arXiv 429 remain visible; raw source lookup avoids claiming refresh for old records.

`screened-interventions.json` preserves all three concrete scope decisions; `paper-dispositions.json` retains every hit; `source-export.json` retains source revisions/edges; command journals and source hashes preserve provenance. No new canonical hypothesis or decision was written by this worker. Root owns subsequent production retention and will decide whether scoped screens need formal identities. Zero implementation-qualified yield is not zero screened work.
