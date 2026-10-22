# Round 33 — normalization and packed-scale scheduling

Status: one new **deferred** source-level candidate, NQ33-01. No implementation or GPU experiment. No service improvement forecast. Target is the planned Flash-1017 / c455 source baseline, not a live attestation.

## Discovery and adaptation

Read compact recall across all five stable pages (138 cards), including MF19 FFN quantization staging, PJ01 dead draft Q projection, AT03 cache gather reuse and the round30 reduction/barrier negative result. One explicit online OpenAlex query returned 12 paper identities; one selected ComFuse full text was fetched. No hidden semantic broadening or second paper query was needed: the remaining questions became exact target dispatch and memory layout, then GPU exposure, rather than another literature search.

ComFuse (arXiv 2608.03537) describes hierarchical reduction scheduling, intermediate bypass and epilogue overlap. Its selectively useful component is separating producer/reduction/output-layout work when scheduling a fused operator. It does **not** propose the exact padding transformation below, certify our MXFP8 ABI, or establish a target speedup. Its full text was fetched through the unversioned HTML endpoint and retained by content hash; do not claim a paper-version-pinned code implementation. A whole compiler/GEMM adoption is rejected as scoped. The target already fuses Q/KV RMSNorm and Q quantization and shares the quantized Q between both projections; that generic fusion is already present.

Three initial corpus FTS queries plus three targeted source-name/layout queries triangulated PRs. These are bounded searches over the retained local corpus, followed by isolated `pr-search` inspection receipts for the initial subset; they do not constitute live exhaustive GitHub coverage. All records and search limits are retained. PR5520 and6207 show launch geometry is a real optimization dimension, but their group search/SM107/batched TMA mechanisms and timing cannot be transferred. PR62632's TP2 eager Q padding is not our TP1 small-decode scale padding. PR157's stale packed scale bytes and PR6607's scale stride issue are correctness warnings, not matching consumer proof. SGLang44933's compound TP4 chain is not adopted: our TP1 layout lacks its all-reduce route, and inverse-RoPE/output-quant fusion is already present in the target. No exact prior implementation of this proposed padding partition was found in the bounded searches.

## NQ33-01: coalesce scale-padding work inside the existing fused Q/KV launch

### Exact source mechanism

`vllm/models/deepseek_v41/common/ops/query_quant.py` at c455 launches `(ceil(tokens/128)*128, 2)` for fused Q/KV RMSNorm + Q MXFP8. Its Q branch computes real rows; padded Q rows only write zero scales. Padded KV rows perform no normalization. All CTAs execute the PDL wait/release code before the branch. Q1280, KV512 yields 40 scale groups and 5120 scale bytes per128-row tile. For a tensor with1–16 rows, the launch has256 CTAs:2n real Q/KV workers,128−n padding-zero workers,128−n empty KV workers. This is a launch-count observation, **not a GPU latency estimate**; empty CTAs may be cheap.

The planned checkpoint has [32,32] UE8M0 FP8 weights. `DeepseekV4FP8Config.get_quant_method` maps the linear layers to ModelOpt MXFP8 dynamic input; CUDA kernel preference starts with FlashInfer CuTe then CUTLASS. The ordinary main wq_b and indexer wq_b dimensions satisfy their static shape guards on B200. The fused path nevertheless requires both loaded kernels to be those exact classes and the expected quant key. Missing dependencies, disabled kernels, --linear-backend overrides or skipped quantization can remove exposure. We did not instantiate them or attest any live selection.

First useful consumers: main `_wq_b_proj` in `project_query_and_cache_kv`, then indexer `_wq_b_proj`; both accept the shared `QuantizedActivation` and pass its exact scale buffer to `mm_mxfp8`. Faster producer completion could shorten their dependency path. Existing preparation/compression overlap means a shorter producer does not imply the same reduction in the whole layer or serving ITL.

### Proposed minimal change, not implemented

For small captured tensor shapes, retain the exact Q and KV live-row bodies, numerical rounding, output types/shapes and F8_128x4 scale allocation. Flatten the CTA grid into2n real-row workers and a small set of contiguous512-byte scale tiles. Padding workers derive the physical byte's row from the swizzle and store zero only where row>=n. Live workers continue writing every group column they own, including padded group columns. For Q1280 this illustrative scheme has2n+10 CTAs:12 atn1,42 atn16. One kernel launch remains. Large shapes keep the original path; at128 real rows the illustration has266 CTAs versus256, so unconditional adoption would be unjustified.

The proposed partition does not skip any padding bytes or shrink scale allocation. It preserves the input tensor row count rather than confusing it with the number of active service requests. CUDA-graph bucket padding may itself appear as rows in `qr.shape`; activation traces are needed to know actual n. The new grid must remain graph-static for each captured shape, and retain PDL wait/release semantics. Fewer CTAs may reduce scheduling instructions, but grouped stores, register allocation, SIMD masking or changed scheduling can erase or reverse that benefit. A byte-write proof is not a PDL or compiled-kernel proof.

### CPU diagnostic actually run

`python3 padding_contract.py`:128 integer-layout cases over16 token counts and8 group widths. It checks address uniqueness, full allocated-scale coverage, disjoint live and padding writes, and byte equality against the source-derived row/group store model with nonzero synthetic live scales. All128 pass. A naive contiguous live-prefix zeroing strategy fails88 cases because the scale layout interleaves rows and groups. At the planned n1/Q1280,5080 of5120 scale bytes are padding; atn16,4480 bytes. This is only a few KiB, not an HBM-bandwidth bottleneck claim.

The diagnostic copies symbolic live values. It does not execute RMSNorm, UE8M0 conversion, FP8 cast, Triton lowering, CUDA graphs, PDL, model inference or timing. Preserving live code is a patch requirement, not independently established numerical parity.

### Fastest next falsifiers and evaluator mapping

1. Read a future existing deployment launch manifest/log to establish exact two consumer classes, QR tensor-shape histogram and call counts. If this branch is not used, reject for that baseline without running a benchmark. No current trace was found or collected.
2. Future isolated device kernel differential: original/revised Q, KV and every scale byte for real shapes1–16 and boundaries0/17/127/128/129, strided Q/KV views, nonfinite/subnormal values, caller allocation sentinels, eager/graph and PDL on/off. Unchanged normalization expression and BF16 round-trip are mandatory. These cases test the replacement, not model quality by proxy.
3. Future paired CUDA graph timings include the two actual GEMM consumers, not only the producer, to catch PDL and scale hazards. Abort if the candidate does not beat the original; no parameter search can be assumed to help.
4. Existing Mooncake and agent-75 workloads remain the serving evaluation. Their ITL/decode-throughput and separate TTFT/tail guards can detect an end-to-end benefit if enough eligible calls occur. They cannot diagnose a scale/PDL race alone; the kernel differential is the specific added correctness test. Freeze workload, shapes, graph and model pins, and alternate A/B. No custom serving benchmark is currently justified.

Primary long-output ITL relevance is conditional on repeated exposed decode calls and critical-path cost. No CPU timing or CTA count provides an ROI percentage. Candidate stays deferred pending exposure and device correctness/performance work, which was not authorized in this CPU-only campaign.

## Honest yield and tool usefulness

One online query,12 returned paper identities,1 fulltext; six bounded local FTS queries, three actual subset-tool inspection receipts. Three concrete mechanism branches: whole ComFuse adoption rejected as scoped; generic Q/KV norm+quant fusion rejected as already present; NQ33-01 layout-preserving padding scheduling deferred. Zero implementation-qualified or measured service wins. Source and PR screens are retained separately from formal intervention identities.

The paper tool found a useful scheduling lens, and local PR search exposed real layout/zero-padding counterexamples. The decisive work was source dispatch and address analysis. More paper calls would not resolve missing active-kernel or GPU-latency evidence. One standard-library SQLite export attempt failed to open the URI; repeating with repository Python and Path.as_uri succeeded. This was an operational export retry, not a provider failure or added source hit.
