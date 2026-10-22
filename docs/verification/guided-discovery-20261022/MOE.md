# MoE, sparse indexer and KV discovery — first audited checkpoint

Date: 2026-10-22. **CPU and source research only. Zero GPU, inference, model-loading or serving changes.**

## Outcome and yield

Four distinct interventions reached code-grounded cards. One advances to a bounded source/CPU diagnostic; two are deferred or require revision; one direct port is rejected. **Zero implementation-qualified or performance-validated wins.** This is a hypothesis-quality checkpoint, not an inference improvement claim. Components of the same intervention were not counted as independent ideas.

| ID | Intervention | Disposition | What changed after scrutiny |
|---|---|---|---|
| M01 | Actual-distribution-conditioned MegaMoE GEMM tile choice at fixed SM allocation | Advance to bounded source/CPU diagnostic | Mean token count loses information, but legal tile/layout options and actual profitable distributions remain unknown |
| M02 | HPC-Ops sampled TopK direct replacement | Reject direct port | Author K512 path is unsampled; target already contains sampled exact selection; target exposure and tie semantics differ |
| M03 | Candidate producer skips ranking when every candidate block fits | Revise/defer semantics | An executed CPU counterexample invalidates unconditional enumeration; finite-block membership must be preserved |
| M04 | HiSparse / adaptive residency for V4.1 | Reject flag; defer integration | Pinned layout explicitly unsupported. New October V4.1-specific paper improves architectural guidance, but its 500K-context capacity regime does not establish benefit here |

The four-card denominator is the set examined deeply enough to propose a target intervention. Additional papers screened below were search leads, not hidden accepted hypotheses. Every gain estimate is unknown. The deployment pin is planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, two DEP4 groups; current live runtime was not verified. Source pin is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`.

## M01 — choose a GEMM tile from routing distribution, without changing SM partition

**Problem.** The pinned MegaMoE wrapper asks DeepGEMM for `block_m` using token count, expert count, top-k and rank count. Default-pinned DeepGEMM estimates mean assignments per expert and adds a square-root margin. It cannot distinguish two distributions with identical total assignments. Padding and repeated expert-weight tiles can differ substantially at the same batch shape.

**Paper-to-system synthesis.** [DA-MoE](https://arxiv.org/html/2607.23099v1) selects fused-MoE tactics from routing histograms. Its reported tests use B200, FlashInfer/TRTLLM and different models/quantization; its improvements are full MoE-graph measurements, not request-level serving improvements. Its approximately 14 microsecond selector/control overhead is a warning against per-step selection unless necessary. Reuse the distribution-conditioned tactic idea inside existing MegaMoE; first seek a stable fixed tactic per layer and batch bucket. Preserve weights, selected experts, numerical format, communication policy and SM allocation. A dynamic GPU-side choice is a later option only if it beats a strong fixed control.

**Existing implementation check.** `deep_gemm_mega_moe.py` exposes no actual-histogram-conditioned block-M selector. The CMake default dependency is `vllm-project/DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`; a `DEEPGEMM_SRC_DIR` override means this does not prove which binary a deployed image uses. The DeepGEMM API accepts optional cumulative local expert receive statistics, but the inspected vLLM wrapper does not wire them. Its `capture_fn(topk_ids)` precedes EPLB remapping; these are logical router IDs, not physical rank-local receive histograms.

**Executed cheap discriminator.** `da_cpu_discriminator.py` uses pure Python and the pinned heuristic. EP4, E384, top6, 128 tokens per rank gives mean eight assignments per expert and chooses block16 for both synthetic cases:

| Synthetic local histogram; 768 assignments total | block16: tile count / padded rows | block64: tile count / padded rows |
|---|---:|---:|
| 96 experts × 8 tokens | 96 / 1536 | 96 / 6144 |
| 16 experts × 48; 80 empty | 48 / 768 | 16 / 1024 |

These are conflicting work proxies. They establish that count alone loses information; **they do not establish which tile is faster, that either histogram occurred, or that block64 is a legal replacement under the present layouts.**

**PR triangulation and counterevidence.** [FlashInfer #4106](https://github.com/flashinfer-ai/flashinfer/pull/4106) implements the paper's mechanism, but its environment flag reaches TRTLLM wrappers, not MegaMoE. [#5194](https://github.com/flashinfer-ai/flashinfer/pull/5194) supplies a newer PrimsTS implementation with single-body versus conditional-switch modes; several B200 DeepSeek-V4-Pro/MXFP4 cells are neutral or slower, and full-model parity remains unfinished. [DeepGEMM #381](https://github.com/deepseek-ai/DeepGEMM/pull/381) changes wave size, not GEMM tile. It is calibrated to EP8/E256/top8 and one large skewed regime; its approximately 1.27% result in that cell is not a target estimate. Broader policies regressed. These results make a best-fixed-tactic control mandatory.

**Prior distinction.** Existing shape-bucket backend selection and N03 SM/CTA compute/communication partition are related but different interventions. M01 holds backend and SM policy fixed and tests whether *the same shape with a different distribution* warrants a different legal GEMM tile.

**Next CPU/source gate.** Trace whether block-M can be overridden coherently through scale layout, symmetric buffer allocation, ring divisibility and forward dispatch. Use retained physical histograms only; if none exist, record unknown exposure. Never add a host synchronization to every round merely to obtain a histogram. No implementation or GPU execution is authorized by this card.

**Future evaluation, only after authorization.** Reuse agent-p75/AIPerf and Mooncake with frozen request tokens, arrivals, prefix mix and decode settings. Add separate bounded routing/tactic instrumentation because the load generators cannot tell whether the intended mechanism executed. Compare current heuristic, best fixed layer/bucket tactic and any dynamic variant including selector cost. Require expert/weight identity, per-layer numerical checks, full-output checks and graph/layout lifetime checks. Report the task's frozen primary metric plus TTFT, ITL/TPOT, E2E, goodput, tails and errors. Reject if legal alternatives are unavailable, actual distributions do not change the best tactic, or total cost regresses.

## M02 — why the tempting exact TopK replacement did not survive

[HPC-Ops](https://arxiv.org/html/2609.08450v1) uses sampled bounds plus full-row certification/refinement. Pinned author code `f39028d9f5ab77f71906fbf929d1b611859ab6b7` explicitly disables sampling for K512. Its measured H20/Hy4 K2048 very-long-row regime differs from this model's token K512. The target's `csrc/sampled_topk.cuh` already implements a sampled exact path with fallback. A generic “add sampled TopK” proposal is therefore redundant.

Candidate-producer K2048 is a distinct operation and may justify future long-row comparison, but its rows are block-score/compressed positions, not automatically the raw prompt length. Exact score rank also does not guarantee identical boundary-tie KV membership. Preserve NaN/inf, causal masks and tie contracts before claiming target equivalence. Existing E06 already covered selector qualification: no new acceptance for merely naming another library.

## M03 — a smaller source-derived idea, then a real falsifier

Candidate producer layer20 uses block size8 and a 2048-block budget. When every eligible block fits, ranking appears unnecessary. Eligibility is `ceil((min(end,width)-start)/8) <= 2048` in actual compressed/request-local or packed-row coordinates, with DSpark row-repeat handling. It is not simply a raw-context cutoff. Producer tokenTop512 still runs and must remain.

**The unconditional shortcut is false.** The fallback removes blocks whose maximum is minus infinity. A valid all-minus-infinity block excluded at the producer can have finite scores at a later consumer. Enumeration would reintroduce that block. The independent reviewer executed this pure CPU counterexample in `../review/candidate_bypass_counterexample.json`. It is a legal arithmetic counterexample, not evidence that the target produces such inputs.

The sparse consumer sorts candidate IDs before expansion, so the reviewer's initial permutation-only objection was withdrawn for that branch. Membership, newest-block pinning, NaNs, clamped bounds and backend-specific short-row behavior still matter. DeepSelect may already skip ranking when all candidates fit; only block reduction may remain. Next gate is a proved finite-score invariant or cheap membership-preserving algorithm. If neither exists, reject this shortcut. Its single-layer scope may make service impact negligible even if valid.

Future correctness checks must include producer-to-consumer differences, not just candidate set size. Existing short-context benchmarks can expose eligible cases; add eligibility/component counters rather than invent another load generator.

## M04 — real long-context reference, unsupported current flag

The pinned V4.1 attention creates a `model_version="deepseek_v4"` MLA specification; `v1/hisparse/layout.py` explicitly rejects that model version. Generic HiSparse support elsewhere in the tree does not make this deployment supported. [SGLang #44684](https://github.com/sgl-project/sglang/pull/44684) is useful compatibility work but concerns a different V4-Flash path; its reported accuracy check is not speed evidence for V4.1 here.

An adaptive online query then found [Adaptive DHiSparse, October 9](https://arxiv.org/html/2610.13708v1), explicitly studying V4.1 Flash. Its relevant design separates physical KV sources, preserves per-query selections while deduplicating speculative retrieval, and bounds temporary staging. Its measurements use B300, SGLang, separated prefill/decode and 500K prepared-prefix contexts. This is a valuable integration reference, but it does not establish an improvement in the current shorter-context DEP4 workload. No standalone implementation revision was identified in inspected paper links. First establish retained-trace evidence of KV-capacity admission pressure; otherwise defer. A long-context capacity experiment is justified only if existing Mooncake/agent-p75 traffic does not expose that regime, and must be labeled as an expanded workload scope.

Revision note: M04 was first recorded against generic HiSparse. The later online query added the October source and refined the integration reference; its deferred status did not change.

## Additional leads retained, not accepted

| Source | Screen result and reason |
|---|---|
| MISA 2605.07363 | Primary source is approximate head-selection/reranking, despite a tempting secondary exactness description. Earlier foundation; no exact-target direct port |
| MiniMax MSA 2606.13392 | Kernel scheduling component could be reused without training; block-GQA to compressed sparse MLA mapping needs a concrete integration and cost case. Deferred, not rejected solely for model training |
| RelayMoE 2610.07333 | Ring/recompute addresses training buffer pressure. No demonstrated corresponding resident-inference buffer bottleneck; inference component remains possible but unqualified |
| MonoMoE 2609.04244 | H200 FP8/TP persistent MoE at tiny batches differs from MXFP4/EP MegaMoE; large backend rewrite lacks target evidence |
| CoMoE 2610.09424 | Consumer-GPU host-mediated communication regime differs from present NVLink deployment |
| MoX 2607.20220 | Direct-connect topology/hardware premise; not a current software patch |
| Weave 2609.21483 | Existing N03 overlap/SM-partition memory; duplicate generic mechanism |
| OrderMoE 2607.17154 | Approximate expert substitution does not satisfy unchanged target semantics |
| Mira 2609.38090 | Single-GPU expert-offload regime, not demonstrated weight-resident target bottleneck |
| TopoCompress 2609.26061 | Approximate compression/edge topology changes the premise |
| Topology/congestion search hit 2609.37828 | Simulated larger fabric and fixed prefill; insufficient target mechanism |
| Astral / GenomeOcean search hits | New network infrastructure or browser inference; outside current software/hardware scope |
| SAC 2606.19746 | CXL memory hardware premise not established here |

## What the tools actually did

Three real `researchctl paper-search` calls ran with an isolated initialized state, `--local-only --defer-snapshot`, date window June1–October22 and saved receipts. OpenAlex broad MoE search found DA-MoE. A narrow arXiv query found HPC-Ops. A later HiSparse query found the more recent exact-model Adaptive DHiSparse paper. This was adaptive refinement, not one deterministic pass. These three receipts show no provider error; no claim is made about other sessions' reliability.

Primary full text, pinned source and four PR refreshes were then read. Readonly SQLite FTS searches retained opening records; their LIMIT12 result sets were bounded and not BM25-ranked, so absence is not proof of exhaustive coverage. All source hashes and raw receipts are retained. CPU work consists of the synthetic tile discriminator and the independent sentinel counterexample. The paper-search results are cached in isolated local state; canonical state and S3 publication are parent responsibilities, not completed here.

The command ledger is `tool-use.json`; deep cards are `candidates.json`; source manifests and raw sources are under `sources/`. No PR or paper benchmark was reproduced.

## Second iteration addendum

`M01_FIXED_TABLE_AUDIT.md` resolves the next API question: common buffer allocation covers multiple tiles; a fixed layer/bucket table is a coherent future integration, but requires a single explicit choice shared by scale packing and compute launch. The current API has no override. This ordinary kernel is Blackwell-only, not H200. No readiness promotion or extra hypothesis count follows.
