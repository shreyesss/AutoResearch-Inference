# Round70 — mHC/Sinkhorn execution: selective evidence, zero new hypotheses

**Disposition: zero new hypotheses, implementations or service qualifications.** Retain a conditional NaN-RMS Sinkhorn fast-exit lead from PR62745, but do not promote it without evidence that the exact target produces this symptom. Preserve existing fixed iteration counts on ordinary rows. No GPU/native/model execution or runtime change.

Target remains planned Flash1017/c455, H5120, hc_mult4, B200 TP1/DP4/EP4 and native DSpark5. This is source planning, not deployment attestation.

## Adaptive search and prior controls

Complete canonical compact recall and prior reports were read before searching. MF19 changes the mHC→MoE quantized handoff; round29 adapts its small-row overlap path; NQ33 partitions Q/KV normalization scale padding; R3/H200-COMP-003 tunes SM90 fused post/pre configuration; R4/H200-COMP-004 ports existing coefficient-stream overlap; round58 parks first-draft broadcast coefficient specialization. None supplies a reason to reduce trained Sinkhorn iterations. Current source already uses delayed pre-mix and separates coefficient statistics from input readiness for eligible small FULL-graph rows.

One explicit arXiv query restricted to September1–October22 returned7 papers. Fulltext was selected for **EqiForge, arXiv2609.12330v1**; all other hits were screened at abstract depth. Five bounded local source/PR searches then found concrete mHC implementations. Exact PR62745 metadata, all two file patches and one pinned full source were retrieved. Existing source identities were reused through normal selected import. Every hit/read depth is retained; bounded FTS lists are not exhaustive GitHub coverage.

The first expand invocation omitted required `--question`; it failed before discovery, and the corrected invocation is retained. Initial guessed source/report paths also failed and were resolved using `rg --files`. These are tool-use mistakes, not source absence or provider failures.

## Paper component: cross-boundary residual/normalization fusion

[EqiForge §7.3 / Figure9](https://arxiv.org/html/2609.12330v1) combines a residual update with the next connection's normalization, reusing the intermediate inside the kernel. The reported mHC5.84× is a whole-layer comparison against torch.compile on its `(16,512,1K)` case; it is not a measurement of Flash1017/B200/c455. Figure9 explicitly retains SK20. Section4 says its algebraic rules assume real arithmetic and that floating implementations can differ through reassociation/precision.

The source target already implements the separable component:

- `mhc_fused_post_pre_delayed_tilelang` documents and implements the previous post mapping folded into the next pre-norm GEMM within its fused range, avoiding another global read.
- The selected Mega-mHC route fuses the shifted post/pre work through DeepGEMM.
- The small-row FULL-graph overlap route intentionally runs coefficient statistics on another stream while making normalized layer input available earlier. Its delayed pre-mix differs from a generic whole-layer mHC example.

Therefore generic residual→next-normalization fusion is **already represented**, not a new candidate. The compiler paper remains useful evidence for selecting a component rather than adopting an entire compiler. It does not certify target numerical equivalence or make a runtime implementation missing merely because its headline is large.

## Actual PR62745: split its two changes

Observed PR is merged, head **CentML/vllm@a75389bd5bd2766ecfa552defa31071322d59332**. Both patches and pinned `tilelang_kernels.py` are retained. The target c455 file lacks these exact changes.

### A. H4096 single-pass configuration — ineligible direct port

The new shape band chooses `(tile_n=2, n_splits=16, threads=256)` at up to4 tokens only when `hidden_size == n_splits*n_thr`, i.e.4096, with the CUDA SM100+ support check. Target H5120 does not satisfy that predicate. Source tests explicitly preserve H5120 configurations. Relaxing the shape gate is a new tuning experiment, not activating the tested donor optimization. Existing R3 and related configuration work already cover the broader family. No new hypothesis is retained.

### B. NaN-RMS Sinkhorn short circuit — conditional source-absent lead

In `mhc_pre_big_fuse_with_norm_tilelang`, the donor wraps the remaining `sinkhorn_repeat-1` iterations with:

```
if rms[0] >= 0.0:
    ... existing row and column normalization loop ...
```

This is specifically a **NaN-sensitive RMS predicate**, not an explicit blanket `isfinite` check: positive infinity and zero pass. The initial softmax/normalization and output stores remain. The source comment explains that NaN RMS makes the mixed logits/results NaN already, so repeated IEEE divisions on that row are unnecessary for its intended padded-output use.

The donor's observed cause is GLM-5.3-Flash layer0 KDA: a null-slot early return leaves stale output storage and later padding rows become nonfinite. Flash1017's inspected attention/runtime route is different. Graph padding by itself does not prove NaN RMS in our target; source absence of the guard does not prove profitable exposure. The donor's ~89call count, microseconds and server gain are not transferred.

The guard is potentially usable without reducing iterations for valid finite rows or retraining. However, it must be admitted only with the actual intended numerical/output contract. Equal NaN classification is not independently established bitwise NaN-payload parity; no native IEEE or TileLang lowering test was executed here. A live-row nonfinite issue should remain observable rather than be described as harmless padding automatically. The actual target stats/input split and compiler lowering also need validation.

**Park, reopen only if an existing exact-pin trace or later authorized instrumentation shows NaN RMS on discarded rows and exposes the repeated normalization cost.** The fastest useful next action is that symptom/consumer audit, not a toy scalar timing or another generic Sinkhorn paper. If such rows are absent, this optimization does nothing.

## Other PR openings: selective possibilities without invented code validation

- **FlashInfer#6202:** author reports a two-lane, fixed20-iteration Sinkhorn chain replacing a16-lane chain inside CAKE's H5120 persistent Mega-mHC programs. This preserves the intended algorithm and is conceptually relevant. But the inspected target dispatch invokes DeepGEMM `mega_mhc` or TileLang, not the described FlashInfer CAKE entry point. Its donor timing is mixed for T1/64/65 and strongest in its27-split T200 class. Only the retained opening body was read, not the generated implementation diff; no claim that the same lane optimization is absent from the current DeepGEMM kernel, or that switching backend is valid. Keep as an unqualified component reference.
- **FlashInfer#6790:** the opening describes H4096 cluster-based normalization plus a division-free Sinkhorn representation. Splitting weighted-sum work across CTAs is separable in principle. The published support envelope and coefficients are not H5120/current delayed-pre-mix ABI, and the target already overlaps coefficient and input work. Replacing divisions/reduction order introduces numerical questions beyond exact power-of-two rescaling. Only opening-body screening occurred; no whole-PR rejection or target performance claim.
- **Depth Memory:** proposes a new LDM architecture with regression/memory streams. Its abstract's hardware-aware implementation does not establish a fixed-checkpoint mHC component; not selected for fulltext in this bounded lane. Training-paper components are allowed, but must be shown applicable rather than borrowed from the headline.

## Exact target dispatch constrains exposed value

In `nvidia/model.py`, the overlap stream is disabled for PIECEWISE, shapes outside1..16, and noncapturing execution. In eligible FULL captures, `mhc_pre_delayed_overlap` launches input work first for n<=8, then coefficient GEMM and `split_mode="stats"` on a side stream; larger eligible shapes enqueue the statistics before input work. The split stats kernel runs the Sinkhorn loop. Elsewhere, shifted post/pre selects Mega-mHC when supported, or fused TileLang. Engram injection imposes a real boundary between post and pre and cannot be fused away by analogy.

Thus shortening Sinkhorn only helps if that selected path has remaining exposed coefficient work at its join. It may be hidden by the next input/sublayer work. No valid per-layer or per-decode saving can be inferred by multiplying a donor microbenchmark by target layers. If exposed eligible normalization time is E and the guarded replacement cost is E', step headroom is at most positive E−E' over actual eligible calls; both are unknown.

## Evaluation mapping and honest yield

No new CPU numeric fixture was manufactured. This round's useful falsifiers are source gates: exactH4096 predicate excludes the launch band; existing post/pre fusion removes the generic compiler novelty; current backend/overlap dispatch blocks naive transfer; donor KDA padding cause does not establish target NaN exposure. This is sufficient to park without a new card.

If the NaN lead reopens, test original/revised exact selected kernel with finite and nonfinite inputs, output masks/consumers, all returned coefficients/pre-mix, eager/FULL and PDL/lifetime behavior. Preserve existing abort/diagnostic behavior. Only then use paired agent-p75/Mooncake with the frozen long-output ITL objective and separate tails; add internal symptom counters/timeline to attribute an effect. No GPU task is authorized by this report.

Yield: **1 dated query,7 paper identities,1 selected fulltext;5 local source/PR searches;1 actual two-file PR diff and1 pinned donor file;0 new hypothesis identities or service wins.** This is an adaptive source-based stop, not evidence that the research domain lacks other useful work. All exact revisions, query receipts, original provider documents, quotes, prior comparisons and read-depth dispositions remain available for retention.
