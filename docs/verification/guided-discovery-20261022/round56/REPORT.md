# Round56 — expert tails: source contradiction before a port

## Result

Zero new implementation candidates. The exact donor tail-split scheme addresses a different cluster layout. More importantly, target source already reduces the tensor instruction row extent to the live row count rounded to16. A coarse BLOCK_M-padding arithmetic forecast would overstate removable compute. This refines how to assess existing M01, without claiming that all tail overhead is absent or changing its historical decision.

Target source is DeepGEMM a7a927731b109fdfec770df7c2a5be5d7e2216b5 used by the pinned c455 Flash1017 source plan, not a new live attestation. No GPU, native kernel, model, timing experiment or serving change occurred.

## Adaptive search and reuse

Two agent-authored expanded arXiv queries used August1–October22 submission dates. The first combined wave/tile quantization with MoE load balancing and returned five papers. It overemphasized placement/offload, so the second explicitly requested GPU grouped GEMM/matrix-multiply padding, partial tiles or irregular shapes. It returned three papers. All eight abstracts were inspected; they are eight distinct explicit arXiv identities, not eight read fulltexts or eight hypotheses.

The analytical overlap paper2609.07536v1 was already retained. Its57,325-character fulltext and two PR opening records were imported through selected-source reuse; no repeat fulltext download was needed. I read the workload/residency/decision-variable sections, not every figure. Its exact communication-CTA choice is already the source of prior N03. The source-read here adds a target comparison rather than another novel candidate.

Production Store FTS queries covered wave quantization, tail split, expert tail, communication CTA and exact paper identity. Bounded campaign report lookup had no literal tail-split match; that is not semantic absence. Typed recall scanned143 cards for each phrase; the104 tail matches were fully paginated in one readonly transaction and stable per-query inventory hash. Selected M01, N03 and MF19 full cards were read. Initial console output was truncated and the first tail page incomplete; complete receipts and the subsequent selected read correct that limitation.

## Donor mechanism and decisive target mismatch

FI5374 head a192faac9154ae9ef87b4db121a0577f62e2b48e TUNING describes an SM90 scheme where a two-CTA token cluster encounters an odd number of CTA token tiles. The second CTA otherwise has no tokens. Pair tasks instead reuse the valid token tile across adjacent weight tiles, adjusting weight fetches and completion counts. The author reports H200 gains and donor correctness checks. Those are source claims, not reproduced target measurements. [Pinned donor](https://github.com/inocsin/flashinfer/blob/a192faac9154ae9ef87b4db121a0577f62e2b48e/flashinfer/moe_ep/kernel_src/sm90/pull_style_cutedsl_megakernel/TUNING.md)

The target is not two independent full M tiles with one orphan CTA. Its SM100 implementation explicitly swaps A/B and uses2-CTA MMA. The two CTA ranks select adjacent weight-N blocks (`n_cluster_idx * 2 + rank`), while the nonleader token load starts at half the dynamically aligned valid M. They cooperate on the same task's effective token dimension. [Pinned implementation](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/impls/sm100_fp8_fp4_mega_moe.cuh)

The scheduler derives `valid_m = min(remaining expert rows, BLOCK_M)` and `get_umma_aligned_valid_m()` returns `align(valid_m,16)`. The MMA warp calls `update_instr_desc_with_umma_n` on every task using that value. An additional exact-pin code-only investigation fetched mma/sm100.cuh: both descriptor overloads assign n_dim_ = umma_n >> 3. Consequently the final task's token extent in the instruction is already shortened, rounded to16. A proposal that merely reduces it from BLOCK_M to the live aligned rows duplicates existing behavior. [Pinned scheduler](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/scheduler/mega_moe.cuh)

This is a narrow source result. The fixed TMA buffers/copy dimensions, scale layout, task/weight work, ring storage and masked epilogue still have costs. It is not proof that the kernel has no padding, that M01 cannot improve tactic choice, or that dynamic instruction sizes achieve proportional speed. No synthetic alignment arithmetic was presented as an experiment on the kernel.

## What changes for existing ideas

- M01: keep the actual routed histogram/tactic question, but separate task count and fixed staging from tensor-instruction work. Counting `ceil(n_e/BLOCK_M)*BLOCK_M` as executed useful-plus-padded matrix rows is unsupported by this inspected MMA path. Any ROI model must use the actual per-task aligned live extent and still account for data movement, weight reuse, occupancy and exposure. We do not retroactively edit the frozen card or manufacture a replacement percentage.
- N03: the retained paper changes a COMET A100 communication-CTA count while holding selected kernels/readiness fixed. Our target has specialized warps and a coupled persistent2-CTA schedule. An SM allocation port requires a newly specified legal resource parameter and forward progress; the paper's reported gains are not target evidence.
- MF19/MonoMoE: the second search retrieves a previously audited quantized megakernel; its producer-output fusion has an existing scoped proposal. A new retrieval is not an additional implementation win.

## Abstract dispositions

1. TopoEP2609.35481: training expert replication/rerouting solver; not the missing tail-cluster operation.
2. EasyBalance2608.07964: cross-layer execution strategy, different dependency/semantic question; abstract alone cannot establish exact target compatibility. Not promoted or globally rejected.
3. InplaceKVCache2609.14507: CPU/GPU long-context offload layout; unrelated to expert tail utilization and already a separate cache-space question.
4. Zepp2610.11158: communication/routing with recent round52 selective dedup evidence; no new fulltext read here.
5. Analytical resource management2609.07536: retained fulltext reused and selected scope read; existing N03 family, COMET A100 variable differs from target.
6. TEMPO2608.13057: makespan-aware replicated-expert dispatch across memory/compute regimes. Its128-row profile and thresholds cannot override actual target instruction geometry or attest exposed padding. No fulltext claim in this pass.
7. MonoMoE2609.04244: already audited, including an earlier source-reading correction. No new port qualification.
8. FuTransformer2610.23796: dense Hopper FP8/INT4 block; separable direct-layout/fusion ideas exist, but changed quantization/weight-gain folding and different operator path cannot be counted as exact current target tail fixes. Abstract-level screen only; not a blanket rejection of every component.

## Stop / reopen condition and evaluation

The donor's motivating orphan-M-cluster event is not established in this target; stop direct port planning. An alternative tail optimization must first identify a concrete instruction/load/task operation still wasted in the actual source. Then use already-retained exact physical expert counts and selected task geometry to establish eligibility. Missing representative counts remain unknown; arbitrary uniform/Zipf histograms cannot estimate target benefit.

If an actual new schedule is later justified, hold source checkpoint, quantization, routing and tactic constant; validate same expert outputs/accumulation contract and ring/completion counts before timing. Existing agent75/Mooncake can judge ITL and tail guards. Only add internal task/transfer timing to distinguish saved masked arithmetic from hidden or unchanged staging. No new workload or GPU test is justified by this closed direct-port premise.

## Accounting

Two online queries, eight distinct abstract identities, one reused fulltext with selected passages read, three reused exact source files plus one newly fetched exact descriptor helper, five bounded FTS queries and paginated typed recall. Zero new formal cards, zero accepted implementations, zero target timing results. New useful outcome: explicit target tail-extent evidence that constrains existing ROI reasoning. Isolated source records and receipts are retained; canonical/S3 import is not claimed here.
