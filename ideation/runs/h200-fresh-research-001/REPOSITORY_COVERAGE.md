# Repository acquisition and decisions

All 13 original CSV repositories received URL/title indexing and fresh discovery attempts. Selected sources were then opened on demand. Supplemental repositories are explicit additions. Counts below measure available snapshots, not equal-depth review or exhaustive search.

| Repository | Original CSV URLs | Primary pages | Patch snapshots | Decision/use |
|---|---:|---:|---:|---|
| `SemiAnalysisAI/InferenceX` | 294 | 5 | 0 | #2963/#3077/#3099 and related H200 recipes give workload/configuration comparators. TP4 recipes differ from current TP1/DP4/EP4; preserve cost, topology and benchmark definitions. |
| `deepseek-ai/DeepEP` | 188 | 3 | 2 | #693 direct-NVLink triple buffering is a conditional backend/kernel comparison (H14); current AG/RS is inactive for this kernel. Preserve newer adapter/API compatibility concerns. |
| `deepseek-ai/DeepGEMM` | 179 | 11 | 10 | #448 correctness, #452 prefill epilogue, #350 narrow-K and #303 negative report; also inspect MegaMoE relatives. Narrow K<=256 groups4 paths do not establish our H5120 expert eligibility. Closed slowdown reports do not settle other shapes. |
| `deepseek-ai/DeepJIT` | 29 | 3 | 0 | #12/#14 startup/JIT concurrency ideas are a cold-start objective. No active DeepJIT steady-state serving path was established; do not spend warm-service budget here. |
| `deepseek-ai/DeepSelect` | 25 | 2 | 0 | #14 SM90 implementation/build and integration via vLLM #59204. Python application succeeds; native FP32/stride/build remains a gate (H07/H13). |
| `deepseek-ai/DeepSpec` | 87 | 6 | 4 | #30/#31/#48 provide sampling-distribution/correctness context. Use for G01 test design, not as evidence of a direct serving speedup. |
| `deepseek-ai/Engram` | 4 | 1 | 0 | #27 is a demo extension, not evidence for the installed vLLM storage branch. Follow implementation into vLLM #59849/#59923/#62359; logs rule out the private-path card. |
| `deepseek-ai/FlashMLA` | 60 | 4 | 4 | #200/#216 older layouts and #213 planner shared-memory lead; no broad H200 port inferred from old V3.2 kernels. Existing vLLM plan sharing is the stronger immediate experiment. |
| `deepseek-ai/TileKernels` | 40 | 3 | 0 | #18 mHC prototype and related kernel discussions are useful history. Use the already fused installed vLLM implementation as comparator; old prototype availability is not an end-to-end improvement. |
| `deepseek-ai/deepseek-recipe` | 25 | 4 | 0 | #11/#15/#24/#25 contribute tool/text encoding and semantic invariants. Treat as G04 quality constraints, not kernel speed claims. |
| `flashinfer-ai/flashinfer` | 272 | 7 | 1 | #6343/#6517 native FP4 SM90 MegaMoE, cleanup and weight conversion are concrete H12 leads. Benchmark geometry differs; EP4 is unchanged by new H200 push buckets. #62603 in vLLM concerns block-FP8 integration. |
| `sgl-project/sglang` | 0 | 15 | 10 | Added beyond original CSV: 3 bounded API searches plus focused pages. #41251 bundle, #39664 mHC, #40860 candidate scorer, #41561 mapping fusion, #41659 metadata, #40417 near-parity and #43065 sequence-parallel paths. Preserve layout/topology and benchmark confounds. |
| `vllm-project/FlashMLA` | 0 | 1 | 1 | #26 fork-level implementation context; dependency availability is not installed dispatch. Keep upstream/fork identities distinct. |
| `vllm-project/humming` | 0 | 1 | 0 | #38 is primary negative evidence: grouped-scale synchronization and weight-preprocessing memory tradeoffs on Hopper. It argues for per-token/BF16 controls and total memory accounting. |
| `vllm-project/recipes` | 120 | 3 | 0 | #1005 H200 setup is a comparator; #1017 revision changes are a separate baseline arm. Recipe convenience does not justify a silent model/image update. |
| `vllm-project/vllm` | 4209 | 39 | 37 | 39 focused pages cover all five mechanism lanes. Prioritize H01–H08; reject small-head TP4/8 transfer and private Engram branch on TP1/shared storage. Patch and installed-source checks are selective, not all 4,209 original PRs. |

## Depth and limitations

- **URL/title only:** all 5,532 original rows and 74 supplemental leads; this layer is not quotation evidence.
- **Opening record:** historical corpus and initial live feed. Fresh fetch time does not imply all discussions were read.
- **Primary page:** 108 selected HTML/text captures, retaining visible opening text, comments and some review discussion. Pagination and hidden replies are not complete.
- **Patch:** 69 downloaded patch snapshots. HTTP 429 failures remain in receipts; unavailable patches are not treated as inspected code.
- **Installed source:** exact read-only snapshots and hashes; no GPU dispatch or correctness measurement follows from text alone.
- **Model source use:** each evidence/proposal/critic input is archived. Critic context explicitly lists omitted extra retrieval IDs after its size fix.

The initial feed refresh was four-day bounded discovery, not full history; final checkpoints completed that pass. Serper searches with empty-result errors (including some small repos) remain recorded. Those repositories still have CSV leads and selected primary reads. OpenAlex returned empty edge lists for two initial citation-expansion attempts; the full-text backward/forward path in [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) supplies an explicit alternative.

See [primary receipts](primary-manifest.json), [coverage JSON](repository-coverage.json), [URL index](source-index.jsonl), [supplemental leads](supplemental-source-index.csv), and [discovery artifacts](discovery/).
