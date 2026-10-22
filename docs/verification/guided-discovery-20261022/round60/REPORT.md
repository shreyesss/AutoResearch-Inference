# Round60 — microscale reuse and exact low-bit execution screens

## Result and scope

**No new implementation-qualified hypothesis.** Two recent-paper searches returned16 distinct identities; four fulltexts were retrieved and selected mechanism/limitation sections read. Four concrete component transfers were screened below: one already implemented, two rejected as direct transfers, one deferred component option without a target benefit premise. The initial repeated-scale-conversion premise was also closed as an unsupported per-decode claim. These are retained negative findings, not zero research activity and not a proof that low-bit kernels cannot improve.

Target source plan: DeepSeek-V4.1-Flash-1017/config revision1bae0e, callgideon/vllm c455786 and DeepGEMM a7a927, planned B200 TP1/DP4/EP4. No live deployment, checkpoint tensor census, GPU measurement, native import/build, serving modification, canonical write or cloud action occurred. Model config identifies routed FP4 experts and block32x32 FP8 dense weights; do not treat the latter as the routed expert scale shape.

## Search and adaptation

First recalled143 cards across two compact pages with a stable inventory hash and searched retained reports. Twenty-three broad card matches and eleven reports were screening aids, not23 independent mechanisms. Relevant priors are M01 tactic selection, RD01 physical locality, WP38 weight packets/cache policy, MF19 pre-FFN producer quantization, OP36 output handoff, PJ01/context reuse, LC resident compression and round43 exact-zero sparsity.

1. OpenAlex, August1–October23 exclusive: `GPU microscaling matrix multiplication scale factors inference`, eight results. Initial question: is a repeated scale representation/conversion operation avoidable on the actual decode path? The native source instead shows packed per-row group32 scales and load-time packing. Most results change precision or hardware. Selected MicroQonv, MpFA and Vortex for component-level reading.
2. Adapted to `GPU lookup table low bit matrix multiplication LLM inference`, same dates/eight results, because Vortex described precomputed products but required a different accelerator. FluxBin offered an actual GPU scale-fused lookup mechanism, so its fulltext was selected. The question became whether that algebra can preserve native arbitrary group32 scales without its new quantization algorithm.

The second query was explicitly authored after the first source findings; it was not an automatic semantic relaxation. `expand-1.json` is the only executed expansion-plan receipt. Four arXiv HTML bodies are retained by hash/revision; URLs were unversioned, so this packet does not claim version-pinned paper retrieval. No automatic cited-repository candidate was treated as the authors' implementation. Retained-source lookup avoided assuming a prior abstract was a fulltext; all four selected fulltexts were absent from that bounded canonical lookup.

Three bounded canonical read-only PR searches returned44 references (44 distinct IDs), copied into isolated state for an actual `pr-search` replay. This is a selected inspection subset, not a refreshed full PR corpus. Only three relevant bodies were read in depth: vLLM#62759, SGLang#39296 and DeepGEMM#404. Other returned PRs remain title/body search leads, not audited patches. #404's cache hint is already adjacent to WP38; no new cache-policy card is counted.

## S60-A — quantize before duplicating activations: already present

MicroQonv2609.28358 moves quantization before convolution's im2col expansion. Its useful general component is to avoid repeatedly quantizing the same numerical input after replication. Its paper also explicitly explains that changing the grouping of quantization blocks can change quantized values; the transformation is not automatically bitwise neutral.

The target already calls `prepare_megamoe_inputs` once before `fp8_fp4_mega_moe`. In `prepare_megamoe.py`192–242, `_quantize_fp8_groups` produces FP8 and packed scales once per token/group; the same `packed_scale` is written to the shared expert's required layout while resident. Native dispatch subsequently pulls prepared rows. This is a source call/dataflow observation, not an executed invocation-count trace.

Thus “quantize once before expert duplication” adds no new component here. Removing repeated remote input pulls is the separate round52 D52 intervention; producer-output fusion is MF19; repeated context projection preparation is round48/PJ01. No renaming. SGLang#39296 provides a corroborating older external integration description, but its K128 scale/block and model differ; the target's own source is decisive.

## S60-B — FluxBin scale-fused LUT: direct factorization rejected, repair remains open

FluxBin2608.15602 Eq11 folds column factors into input and row factors after binary matvec because its learned/PTQ reconstruction has explicit row×column factors per binary basis. This is a training-free PTQ scheme, **not** unchanged pretrained weights. Its CUDA/A100 lookup kernel is a real algorithmic component, not a custom-hardware-only dismissal.

Target `deep_gemm_mega_moe.py` allocates packed scales per output row and K32 group. `_pack_scale` can repeat smaller checkpoint scale grids at **load time**; it does not establish rank-one separability across rows and K groups. Runtime native MMA reads group scales directly. We did not inspect actual checkpoint scale values and do not claim their rank or repetition statistics.

The executed standard-Python `contract_probe.py` uses exact rational arithmetic and legal finite power-of-two scales `[[1,2],[4,16]]`. Its determinant8 disproves a single row×column factorization; matching the first row/column would substitute8 for16. With one FP4 code1 in each of two K32 groups, reference outputs are `[3,20]`, while that transplant gives `[3,12]`. A separable `[[1,2],[4,8]]` positive control succeeds. This falsifies a **format-only guarantee**, not FluxBin's own algorithm or any measured target tensor. Multiple bases, group-dependent lookup tables, a proven restricted scale grid, or a different exact representation could repair the premise, with new memory/work costs. No performance experiment or native rounding equivalence is claimed.

The first useful consumer would be routed L1/L2 MMA, but source never materializes all FP4 weights as BF16 per decode. A dequantization-removal benefit measured against W4A16/A100 cannot be attributed to this B200 native FP8×FP4 consumer. vLLM#62759's body describes Rubin SM107 LUT-B and dequantizing emulation elsewhere, different codebook quantization and unexercised EP. We did not audit its diff and do not use the body as target absence proof. It provides no ready exact native B200 adapter.

## S60-C — Vortex product-table reuse: direct transfer rejected

Vortex2609.12208's multiply-first flow computes a table of activation/codebook products and reuses it through lookup/accumulation. That is a meaningful component to inspect separately from sparsity. Its VQ weight representation, learned codebooks and lookup/vector-processing accelerator differ from native scalar MXFP4 and GPU Tensor Cores. Its own text identifies lookup/accumulation balance and poor GPU VQ efficiency as constraints.

Re-expressing arbitrary scalar FP4/group scales in an exact GPU lookup representation is not supplied by this paper. The paper's contextual sparsity and KV VQ are additional numerical changes, not required to understand its product reuse. We reject the direct frozen-target port, not all future exact GPU LUT work. Source-only dimensional or bit counts do not establish a faster path than current native MMA.

## S60-D — MpFA scale/accumulator lifetime overlay: deferred component option

MpFA2609.33135's useful selective component is TMEM lifetime reuse, separate from its QK4PV8 quantization and rank-one smoothing. It borrows columns of the other query stage's score storage while those scores/probabilities are dead; copies must precede their MMA and overwrites must follow the last consumers. The paper's fixed probability scaling/reverse traversal changes finite-precision behavior and is not transferred here.

Target native MegaMoE does allocate separate scale columns after two accumulator stages (`mega_moe.cuh`180,232–237). It copies SFA/SFB to TMEM at898–909 then issues block-scaled MMA. However, the other accumulator stage may still be read by epilogue (`tmem_full`, output loads and `tmem_empty` release at987–1025), while the current stage is the MMA destination. Moving scale copies into those columns without additional lifetime proof can overwrite live values. Waiting for the other stage could repair safety but reduce intended overlap. Unused tail columns are not guaranteed across all tasks and static allocation cannot simply shrink when one task is short.

This would remove allocated capacity, not the scale copies or GEMMs. No evidence here shows TMEM capacity limits active persistent-kernel residency, and no exposure/timing trace supports an ITL gain. We retain the source-backed option and exact lifetime gate, without a new typed hypothesis or another synthetic schedule claiming native proof. If revisited, first establish a useful allocation/residency threshold on actual eligible shapes and a complete producer/consumer lifetime design; otherwise stop before a GPU test.

## Rubric, evaluation and stopping decision

- Mechanism/source relevance: direct decode path identified for S60-A/B/D; no absent useful A delta; B violates an unproved factorization premise; D has a new capacity option but no demonstrated consumer benefit.
- Numerical admission: no unchanged-weight claim follows from “training-free.” Exact scale-factor counterexample is meaningful but not target evidence. Full native output/tie/rounding tests would be required after any repaired design.
- ROI: unknown. No conversion-time or component-exposure measurements; no weight bytes→ITL forecast, no paper speedup import. Capacity reduction is not a latency reduction.
- Benchmark relevance: Mooncake/agent-p75 exercise native MoE when that source plan is active, but cannot establish scalar representation correctness or isolate TMEM hazards. Any future admitted arm needs exact component differentials and alternating steady-state serving A/B with frozen long-output ITL plus TTFT/E2E/tail guards. No such run is authorized or launched.
- Cheapest next decision: source/actual tensor representation evidence for a specific repaired factorization, or actual resource constraints for the TMEM option. More broad microscaling search is unlikely to resolve either; this branch stops.

## Tool usefulness and limits

Discovery found a GPU LUT alternative after the custom-hardware Vortex mismatch. Fulltext reading separated inference components from whole-method format changes. Source inspection falsified the tempting duplicate-quantization premise. Compact recall plus report search prevented recycling MF19/WP38/round52. PR search found a native-vs-emulation hardware boundary and an already-integrated shared-scale path. No controlled improvement in research-skill quality is established.

Failed operator reads are retained in tool-use.json: guessed package paths for Store/model/config were wrong and corrected with bounded `rg --files`; several console searches truncated and were followed by bounded source reads. Saved documents remain complete; truncated output is not full review coverage. Source export contains retained current bodies/revisions/edges and journal. All state is isolated/local; no new recovery snapshot, S3 sync, canonical retention or production qualification is claimed.
