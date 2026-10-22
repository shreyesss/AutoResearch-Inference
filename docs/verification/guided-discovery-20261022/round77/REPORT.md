# Round77 — normalization intermediates and cross-SM reduction

**Outcome: zero new formal hypotheses. Two concrete transfer screens are retained below; neither establishes an implementation-ready improvement.** This round advances a repeatedly abstract-only paper screen to its full text and pinned released code, then tests its proposed saving against the exact target. No GPU, native/model import, compilation, serving change, canonical mutation, or performance experiment occurred.

Target remains planned Flash1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, B200 TP1/DP4/EP4, baseline d464. Source configuration is not live deployment attestation.

## Retrieval and adaptive decisions

Recalled all 147 compact cards over two pages with one stable inventory hash, then searched retained report text for normalization, RMSNorm, Sinkhorn and intermediate fusion. The normalization search had 23 matches; the second page was read rather than interpreting the first 8 as complete. Selected 29 related cards for closer mechanism comparison. NQ33, MF19, OP36, PJ01 and rounds 29/33/36/48/58 already cover padding, quantized handoff, discarded projection work and first-entry specializations. This is bounded literal/manual recall, not a semantic novelty certificate.

One dated **OpenAlex** query, `GPU inference normalization kernel fusion`, September 1 through October 22 inclusive, returned 8 identities. The provider completed without errors. A retained expansion plan explains why a different provider was useful after many arXiv-led rounds. Every abstract disposition is retained.

The useful lead was [Taming Dynamism on GPUs: Cross-SM Kernel Fusion via SM Cooperation and Just-in-Time Reduction](https://doi.org/10.1145/3830418.3843857), OpenAlex W7214714509, September 2026. Earlier rounds 33/36 had screened its abstract without establishing a transferable component. Exact source-library lookup found those records and a **citation hit in BOOST**, not the selected paper's full text. I caught that identity distinction before scientific attribution; the wrongly descriptive temporary filename was corrected and the retrieval note remains. AttnFuse was already retained and screened in earlier work; merely importing its available body is not counted as a new full-text read.

The normal `investigate` tool attempted the explicit OA ACM PDF, recorded HTTP failure and `read_depth=not_retrieved`, and kept only abstract evidence. An exact-title web search found the authors' university publication page, whose matching title links to [the author PDF](https://ipads.sjtu.edu.cn/zh/publications/sosp26-he.pdf). The web reader timed out; one explicit `Sources.fetch(expected_pdf=True)` succeeded with real PDF extraction and caching. This fallback is separately recorded, not disguised as a successful original investigation. The PDF title/authors match the selected publication.

The selected paper names `he-jingkai/tilelang.dataflow`. Repository discovery needed four logical reads; my initial three-call budget exhausted before README. The explicit retry used cached metadata and one additional miss. Pinned commit: `b839d789054a818500f3cfc57f0af891710a3e43`. An untruncated 1,561-entry tree plus the actual RMSNorm file resolve what was released. No repository code was imported or executed.

## What the paper supplies—and the release does not

Meld uses cross-SM communication and staged partial/reduce/partial execution. For RMSNorm, it partitions a wide row, retains each input partition on chip, combines partial squared sums, then normalizes the retained values. This avoids an intermediate-memory round trip in its compared staged implementation. Table 4 uses RMSNorm widths 32K–80K on H100/GB200. This establishes a selective systems method; it does not establish target speed or a full-checkpoint numerical contract.

The inspected release has dataflow examples for MLA and fused MoE. Its `examples/norm/rms_norm.py` is **not** the paper's distributed RMSNorm implementation: both functions launch a grid over row blocks, not column partitions cooperating across SMs. One loads a whole row into local/shared storage; the function named `rms_norm_splitk` loops over column chunks in the same block and rereads them in reverse. They use FP32 values, epsilon 1e-12 and no learned gamma. The ordinary example must not be advertised as a ready Meld cross-SM adapter. A filename/tree search alone would have been insufficient; the code body is retained.

This finding is scoped to the pinned release and files inspected. It does not prove the paper's implementation never existed or that cross-SM normalization cannot help smaller dimensions.

## Exact target comparison

### Q/KV normalization: the retained-input saving is already present

`attention.py:789+` splits the merged projection into Q1280 and KV512 and invokes a fused Q/KV RMS normalization. Eligible FlashInfer MXFP8 consumers additionally share one normalized-and-quantized Q representation. Eligibility is per layer/backend, not an assertion that the planned deployment reaches every branch.

In `common/ops/query_quant.py`, `_norm_row` loads each row's values once, computes its squared-sum reduction, and returns the normalized values directly to quantization. It preserves the BF16 normalization boundary before group32 quantization and F8_128x4 scale stores. It does not materialize an unnormalized RMS intermediate and then reload that intermediate for a second stage.

The non-quantized fallback `models/common/ops/fused_qk_rmsnorm.py` likewise loads a row once, reduces and writes the normalized result in the same kernel. It already pipelines the independent gamma load ahead of its PDL wait. Therefore the donor's specific avoidance of a staged RMSNorm input reread is absent on both inspected target branches. Neither this observation nor the smaller widths proves the baseline is optimal; cross-SM parallelism would be a different, unqualified scheduling experiment.

The preceding GEMM still produces Q/KV in a separate buffer. Fusing that producer with the norm could be a separate operation, but the selected RMSNorm method and released example do not implement the target quantized GEMM epilogue or its cross-tile reduction. I do not turn that remaining buffer into a supported proposal by analogy. Such work would need an actual producer/consumer ABI, reduction ownership, BF16 rounding and compiled-resource design; no claim of a ready adapter is made.

### mHC: distinguish its two reductions and existing shared intermediate

The delayed overlap path consumes 4×5120 residual values for its coefficient/statistics calculation; the normalized collapsed input has width 5120. It is not simply a standalone 20K RMSNorm call. `tf32_hc_prenorm_gemm` produces the FC and partial square sums; the epilogue consumes those statistics for its coefficients. Replacing the whole path with a row-normalization library would lose its coefficient, gating and stream contract.

More decisively, `mhc_pre_big_fuse_with_norm_tilelang` already stashes the weighted-collapse output in shared memory. In the delayed `save_pre_mix=True` arm, squared sums use the BF16-rounded values; in the other arm they use FP32 `ol` before the BF16 shared store. Its second pass reads that shared intermediate and applies normalization/gamma before the final output store. The hypothesized HBM intermediate round trip is therefore not present in this inspected implementation. Its shared-memory accesses, reduction order and overlap cost are not certified optimal. A new cross-SM repartition would require a separate implementation and could delay the small-row input/coefficients schedule; it is not the same saving illustrated by the paper.

This conclusion is about that source path, not every mHC backend. The standalone source evidence does not identify the active native path or its frequency. Existing MF19/round29 quantization handoff concerns a subsequent different pass and remains a separate proposal.

## PR triangulation and dispositions

Four bounded full-corpus read-only searches inspected `RMSNorm fusion`, `cross SM norm`, `Meld` and `QKV norm`. They returned 358, 21, 0 and 193 matches respectively; only the top 7 per nonempty query were materialized. This is partial inspection, not complete PR coverage. Three selected opening records were imported into isolated state and replayed through actual `pr-search`; that replay covers only those 3 records.

- DeepGEMM#387 has the title “fused qkv norm a2a” but an empty retained body. It is a locator, not implementation evidence or proof the target lacks a feature. No claim is based on its absent diff.
- FlashInfer#5952 describes a different BF16 QK/RoPE/cache interface and 128-dimensional heads. The current target already has its own fused preparation paths; body-level benchmark numbers do not qualify a port or establish a new missing operation.
- FlashInfer#5540 concerns an eight-peer fused norm/combine interface. Planned target TP1 is not that collective contract. No whole-system speed is transferred.

**Screen77-A: direct released RMSNorm substitution — rejected as scoped.** The inspected file is not the advertised cross-SM implementation and omits the target learned gamma, epsilon, dtype and quantization boundary contract. This rejects a direct substitution, not the mathematical class of distributed normalization.

**Screen77-B: retain the paper's on-chip partial/reduce/partial component — deferred, low priority.** Its central reread-removal premise is already addressed in the inspected Q/KV and mHC paths. Cross-SM scheduling or fusion with the preceding GEMM would require a newly specified mechanism and native code evidence. No target exposure or material benefit is demonstrated. Keep this component available if a real wide staged-reduction path is later identified; do not create a fresh hypothesis just for this paper match.

## Yield, tool usefulness and stopping rule

One new dated provider query; 8 abstract identities; 1 selected paper advanced to full-text sections and 2 pinned repository files; 3 selected PR opening-record replays. Two concrete intervention screens, 0 new typed hypotheses, 0 implementation or service promotions. Existing cached fulltexts and a citation hit are counted separately. No CPU toy cases or timing were needed to decide whether the target source already retains its norm input.

The useful tool behavior was explicit failure/read-depth reporting, selected-source reuse, and accurate provider query retention. Two failures required agent adaptation: publisher access failed, and the repository-read budget was too small. A literal fulltext citation hit was an agent identity-selection hazard, not a broken source record. No new tool patch is justified by these observations. Source/receipts remain local and deferred; no new snapshot, S3 or VM synchronization is claimed.

Stop this lane here. A broader search is not justified until there is a specific staged target operation or new implementation whose missing data movement can be tested against the pinned source. Standard Mooncake/agent-p75 objectives remain unchanged; no scalar traffic count is converted to ITL gain.
