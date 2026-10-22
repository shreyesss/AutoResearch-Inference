# Round62 — kernel selection constrained by actual arithmetic and backend reachability

## Decision

**Zero new hypothesis; zero implementation or service qualification.** Retain two recent papers as components for the existing kernel-tuning family: static candidate features and reference-arithmetic admission. Neither establishes an absent, reachable high-value runtime policy on the pinned Flash1017 path. The concrete PR examined does not enter that path. No GPU, native package, model, serving, canonical, cloud or Git operation was performed.

Baseline: planned `deepseek-ai/DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`, `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, TP1/DP4/EP4 native DSpark5, temperature1/top_p1. This is not live deployment attestation.

## Prior recall changed the question

Fresh readonly canonical hypothesis backup and normal isolated compact recall (`prior-01.json`, `prior-02.json`) cover the complete inventory; `prior-M01.json` includes current linked refinements and refuting claims. Standalone round54 BF16 tuning and round56 expert-tail reports were also inspected.

- M01 already proposes selecting MegaMoE tiles from layer/rank routing distributions. N03 covers compute/communication resource allocation. Historical H1/H2 cover shape-aware GEMM backend and resource selection. Generic online kernel routing would repeat these.
- Round54 retains FI6360 cold-chain BF16 tactic measurement as an evaluator control; default CUDA `linear_backend=auto` remains `F.linear`, not FI auto.
- Graph bucket/padded-row work already has its own family.
- The M01 arithmetic correction remains binding: for fixed expert rows and legal BLOCK_M divisible by16, the inspected summed MMA token extent is `16*ceil(n/16)`, independent of BLOCK_M. No reduced padded-MAC claim is revived here. Remaining task/staging/occupancy effects require evidence.

The narrowed question became: **Can candidate selection use additional static features while refusing arithmetic-changing choices, and is there a concrete missing target route?**

## Adaptive online search, preserved failures and read depth

Both online searches were dated August1 inclusive–October23 exclusive2026 using actual `expand` and `paper-search` in isolated state.

1. LLM plus kernel selection/autotuning/**tactic** returned20 hits, mostly language-agent security/social tactics. LLM was insufficient to disambiguate the final Boolean branch. GPU Goldmines was relevant; a prompting-for-HPC optimization paper was adjacent rather than a runtime policy.
2. Revised query required **GPU/CUDA and inference/attention/GEMM outside every alternative**, removed generic tactic and allowed non-LLM numerical operator papers. It returned9 hits. Two fulltexts were selected: hardware-aware CUTLASS selection and bitwise-equivalence admission. Stop after these and the exact PR screen resolved the target decision.

There are29 hit references and28 unique papers. All returned abstracts/dispositions are in `paper-dispositions.json`; fulltext read depth is explicit. This query repair follows the already-existing discovery skill's ambiguous-branch instruction. It is **not a new tool capability, measured recall improvement or hypothesis-quality gain**. Fewer irrelevant results alone cannot prove better coverage.

Readonly retained-source lookup found no match for the two selected arXiv IDs in its bounded text query; two version-pinned fulltext GETs were then made through `investigate`. Local PR search preserved total/page diagnostics: `kernel selection`1957/15, `batch invariant`244/15, `split heuristic`132/15. These are partial pages, not corpus-wide absence proofs.

## Selected paper components

### Hardware-Aware Features for CUTLASS Kernel Selection — arXiv2609.35587v1

[Paper](https://arxiv.org/abs/2609.35587v1), retained exact provider text in `2609.35587.txt` and source revision export.

The useful component is representing a candidate by induced hardware behavior: output tile counts, final-wave efficiency, shared-memory/register residency bounds, pipeline fill, TMA/compute balance and cluster fit. These derive from shapes, layouts, dtype, candidate geometry and hardware properties; serving need not read new GPU counters for every selection. The paper learns their interactions rather than assuming a single analytical ranking.

Important limits from fulltext: approximately4.9million measured CUTLASS candidates; GH200 SM90a/CUDA13.1 training/evaluation; dense GEMM, selected precision/epilogue transfer with finetuning; fixed rasterization/swizzle/split-K during comparison. It does not supply an execution-free guaranteed B200 mixed FP4/FP8 persistent-MegaMoE selector. Static feature availability is not a trained performance model or an exposed-time prediction. The hardware features could improve an existing M01 diagnostic/model later, but this is supporting evidence for that family, not another intervention.

### Taming Bitwise Behavior in GPU Kernels with Tensor Core — arXiv2609.11356v1

[Paper](https://arxiv.org/abs/2609.11356v1), retained exact text in `2609.11356.txt`.

The separable component is **pruning the candidate set by arithmetic equivalence to a chosen reference before timing/ranking**. Section6 describes symbolic assembly traversal over addresses and arithmetic/dependency nodes; rounding, reduction grouping and loops contribute to signatures. Unmodeled syntax stays opaque and distinguishes candidates conservatively. The Triton autotuner uses a pruning predicate; it can select a supplied compiled reference rather than silently blessing whichever candidate appears first.

This avoids the false choice between unrestricted faster tactics and one permanently fixed tactic. A different physical layout/schedule may preserve the same arithmetic graph. Conversely, equal dtype, quantization label and mathematical operation do not establish equal results. The paper explicitly notes FP8 MMA lowering/promotion cadence can differ, so BF16 instruction-equivalence reasoning cannot be generalized to our FP4/FP8 paths.

**What is not established:** no checker implementation was installed, compiled or run; no pinned target PTX/SASS artifact or exact compiler lowering was available here; no proof covers MegaMoE routing, scale conversion, shared-expert fusion, dispatch/combine order or FlashMLA softmax. The fulltext's checker claims are author evidence, not our certification. A numerical-tolerance test is not an exact-output gate, and selecting a new balanced-tree reference would itself change the baseline unless separately authorized. Opaque/unsupported cases must remain unsupported, not interpreted as equivalent.

## Exact target source check

| Route | Pinned evidence | Decision |
|---|---|---|
| MegaMoE | `get_block_m(num_tokens)` calls DeepGEMM with EP world size, expert count, symmetric-buffer max tokens, current local tokens, top-k and MMA type | Shape-based dispatch already exists. Additional routing-histogram selection is prior M01, not new. Actual histogram availability without synchronization remains a separate concern. |
| CUDA unquantized linear | `dispatch_unquantized_gemm` maps only explicitly named FI backend; default auto returns default linear | Paper candidate ranking does not activate a new backend by itself. Round54 already isolates activation versus ranking. |
| FlashMLA Mega decode | `_forward_decode_mega` calls `_flashmla_C.fused_norm_rope_attn_rope_cast_decode`; source explicitly has no batch-size split-KV fallback | A generic attention threshold is not an omitted default. Source comments report GB300 TP/head comparisons; do not treat them as our B200 measurements. |
| Ordinary FlashMLA decode | Same-type layer scheduler metadata shared per step; first call plans, subsequent calls skip | Do not propose per-layer planner memoization already present. |
| Quantized target | Retained config is dynamic FP8/group32 UE8M0 with routed expert FP4; text heads64 | Dense BF16 paper is not automatic coverage of actual quantization/reduction semantics. |

No installed-image dependency revision, tactic trace or exposed time was recovered here. Assertions describe pinned source and retained model config only.

## PR triangulation: FlashInfer2836 is a useful negative transfer

[FI2836](https://github.com/flashinfer-ai/flashinfer/pull/2836), merged observed head `PerkzZheng/flashinfer@e2b581945b3f32f0d6f16d80f2c31c04802566d3`; all3 changed-file patches retained. Created March2026: this is a known implementation follow-up outside the recent-paper window, not a recent paper hit.

The actual diff separates sparse MLA selection in the **TRTLLM-gen** runner. It changes64-head KeepsMmaAb selection, adds batch-aware128-head1CTA/2CTA choice, and halves <=32-head tile width for low occupancy. It also bounds reselection to four passes, preserves updated reduction mode across passes, and updates required cubin artifacts/checksum. These details matter more than the opening phrase “dynamic selection.”

Our examined Mega attention path calls FlashMLA, not this TRTLLM-gen runner. Furthermore, the donor's batch-dependent head-splitting arms apply to <=32 or128 heads. With planned TP1/64 heads, its selected KeepsMmaAb tile remains64 across tested batches; the donor64-head change is a static choice, not new load dependence. The donor also changes head/cluster/reduction organization: copying a threshold while ignoring artifacts and arithmetic is not justified.

The PR is not rejected paper-wide. It is excluded as a direct target implementation, and retained as a concrete illustration of selection state, artifact and numerical-admission requirements.

## Bounded CPU falsifiers

`admission_probe.py/json` is a **manual transcription of named donor branch conditions**, backed by exact-string checks against the pinned diff, not executed C++/CUDA. It evaluates40 illustrative head/batch/SM-count combinations. The64-head result is constant; the128-head negative control changes as intended. The SM counts are illustrative and are not observed hardware properties.

A stdlib binary32 example checks `(2^24 + 1) + (-2^24) = 0` versus `2^24 + (1 + (-2^24)) = 1`. This falsifies “same mathematical sum and dtype implies identical arithmetic,” not any actual target tactic. No production checker, native equivalence, inference output or speed was tested.

The original scalar fixture used a grouping that did not differ; its assertion failed, and `admission_probe.attempt1.py` is preserved. The corrected positive/negative diagnostic is scoped as above. This failure did not become a target-runtime result.

## What would justify reopening

For an **existing** tuning investigation, first retain the actual selected module/backend/kernel/compiler and processed operand/scale layouts, graph replay policy, reference output contract and compatible compiled candidates. Partition only where a sound supported checker can establish the reference arithmetic; otherwise use a separately authorized differential/native validation gate and preserve unsupported status. Then rank admitted candidates using source-appropriate static features and target measurements. Cache keys need code/compiler/architecture/dtype/layout/epilogue/rounding identity, not just M/N/K; a graph capture also fixes which implementation executes, so a host policy cannot change it merely by changing a dictionary entry.

The potential service bound remains exposed eligible fraction `f` times actual component reduction `r`, minus selection/capture/extra-storage overhead and interference. **f and r are unknown.** No claim follows from a CUTLASS ranking regret or a donor's throughput table. Standard agent-p75 and Mooncake can evaluate eventual service ITL/TTFT/tails/goodput; internal tactic/numerical traces are necessary to explain it, not a reason to invent a new serving workload now.

Stop this lane: no distinct reachable high-materiality policy survived source/prior checks. Retain numerical-admission and feature-design components for M01/round54 without changing their existing selection state. No new card and no status promotion.

## Operational notes and durability

Initial commands incorrectly supplied `--defer-snapshot` to init (now explicitly unsupported), then expand correctly reported uninitialized state; paper-search was initially given a nonexistent `--query` option. Corrected init and positional query succeeded. A display helper expected `results` instead of the actual `hits`; complete readonly search JSON had already been saved. The provider's fulltext body was already extracted text; an unnecessary HTML-parser pass dropped some math syntax. Those derived attempts are preserved, and authoritative `.txt` files now exactly equal retained source bodies. No source text was silently substituted.

Source documents/revisions/edges, commands, all hits and their decisions, source pins, PR diffs, prior recall and diagnostics are exported. Mutable isolated databases/caches are excluded from the manifest. Local deferred state is not a newly published S3 snapshot.
