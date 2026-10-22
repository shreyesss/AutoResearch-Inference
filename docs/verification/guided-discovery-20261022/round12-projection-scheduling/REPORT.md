# Round12 — DSpark context projections: remove the output that is discarded

**Disposition:** one new, source-grounded direction (PJ01), **deferred implementation**. Completed CPU layout/control diagnostics are inconclusive for numerical compatibility and performance. No GPU/model/CUDA/runtime changes, no deployment probes and no canonical writes.

## What changed the decision

Paper-first search did not directly yield a new target-compatible projection technique. A local PR search identified [SGLang31986](https://github.com/sgl-project/sglang/pull/31986), which stacks DSpark per-layer context-KV projections. That donor explicitly falls back for quantized weights. Reading the exact target source revealed a narrower opportunity: preserve three layers and their context caches, but stop computing the query columns that context preparation immediately discards. This is selective reuse of the donor's shared-context observation, not a direct port or a paper-result performance prediction.

The frozen target is `DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`; source is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, planned SM100 TP1/DP4/EP4 groups. The live image and selected quantized linear backend are **not attested** here.

## PJ01 mechanism, line by line

[DSpark context precompute](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/nvidia/dspark.py)165–195 loops over three distinct draft layers. Each receives the same projected target hidden input `main_x`, calls its own `attn.fused_wqa_wkv(main_x)`, keeps only output columns after `q_lora_rank`, applies that layer's KV norm, then inserts context KV with that layer's positions/slot mapping. It still projects/normalizes when a slot mapping is None; only insertion is skipped. Profiling/workspace behavior must remain intact.

The [merged linear construction](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/attention.py) uses replicated `disable_tp=True`, input5120 and output partitions Q1280+KV512. Context preparation discards Q1280; actual query attention still needs those columns. **Keep the original full merged module/parameters for query forward.** Build a compatible KV-only view/adapter solely for context preparation.

[Proposer control flow](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/v1/worker/gpu/spec_decode/dflash/speculator.py) matters: eager mode prepares current target hidden rows. FULL graph prepares a captured prefix, and extra target rows are handled in an eager tail before replay. These ranges partition the work; they do not each reprocess the entire context. Padding can execute projection but suppress cache writes via PAD_SLOT_ID. This is not historical-context recomputation and cannot be multiplied by draft depth5.

### Why the quantized slice may be feasible

Checkpoint linear scales are native [32,32] UE8M0; the model's quant selector routes compatible linear layers through ModelOpt MXFP8. Preprocessing expands scale rows and chooses a backend. Only two exact processed layouts were audited:

| Backend | Processed weight | KV view | Scale region |
|---|---|---|---|
| FlashInfer CUTLASS | contiguous [1792,5120] | output rows1280:1792 | F8_128x4, row start1280 aligned128 |
| FlashInfer CuTe | [5120,1792], strides(1,5120) | output columns1280:1792 | same scale layout |

The weight region begins at element6553600. Scale columns=160, byte offset204800, region81920 bytes. All81920 exact source offset equations agree with a rebased512-row scale view. This is integer address algebra, **not a tensor/GEMM execution**. Other backends, shuffled formats, bias/LoRA or altered geometry need their own contract or baseline fallback. Bind views after final preprocessing and rebind after reload/parameter replacement.

Output-width changes can change the GEMM tactic and rounding. Equal algebra/selected weight bytes does not prove equal KV bytes or downstream proposals/confidence. That remains an explicit correctness gate.

### Keep three arms separate

1. **Initial intervention:** three per-layer KV-only projections; original input quantization, norm, RoPE and cache insertion unchanged.
2. Optional later arm: share one quantized `main_x` only if actual activation ABI, scaling algorithm, dtype and shape match every consumer.
3. Optional later arm: stack three distinct KV projections and batch norm/insertion. Preserve different weights/norms/slot maps. The donor's dense-only fallback makes this a larger adaptation.

These are arms of **one direction**, not three discoveries. Slice-only first isolates removed dead-column work from launch fusion and quantizer reuse.

## What can and cannot be estimated without GPUs

Per context row, three projections nominally use27,525,120 MACs; retaining only KV requires7,864,320. Thus **71.43% of nominal projection output arithmetic** is discarded today. This is not71.43% of context-update time, round time, ITL, or measured HBM traffic. Cache reuse, tactics and overlap determine realized savings.

Let `f` be the measured exposed round-time share in these projections, `r` the realized component-duration reduction, and `h` added overhead normalized to baseline round time. Under that decomposition, total reduction is `f*r-h`. All three are unknown. Perfect removal cannot save more than `f`; the arithmetic fraction is not a measured `r`. Accepted progress must remain comparable. Smaller GEMMs could lose efficiency; target verification, communication, norm or cache insertion could dominate. No numeric ROI forecast is justified.

## CPU evidence and independent review

Run from this folder: `python3 context_projection_audit.py`.

-81920 exact integer scale-offset equalities; misaligned row1279 negative produces81280 mismatches.
-Extracted actual native context method executed with shape/provenance stubs for all mappings, middle-None and all-None:3 projection/norm calls retained, insertion counts3/2/0; shared input and distinct layer identities retained.
-Expected CuTe/CUTLASS metadata inferred from source; no real tensors constructed.

[Independent review](INDEPENDENT_REVIEW.md) confirms distinctness, layout plausibility and limitations. Its related address checks are independent review, not an extra set of runtime/numerical samples. No quantized numeric parity, actual KV writes, loader lifecycle, GPU timing or service result is established.

## Prior and existing-code rejection checks

Prior `RUNTIME-R2-03-revision1` (`hypothesis:61bf4139c462a5dd161f32e0143cb065d2785f1231b8cde38e93c0585425ff85`) attempted to omit unused query/Markov work during unfinished prefill and encountered confidence/state dependencies. PJ01 retains context preparation and removes only its discarded outputs on eligible iterations. It does not remove query sampling, RNG advancement, confidence scheduling or collectives.

Generic alternatives were not promoted:

- Native attention already overlaps fused input projection with compressor/indexer branches and overlaps preparation/cache work on auxiliary streams. Generic parallel projection is already present.
- Query normalization/quantization already has PDL dependency operations; WO-A fusion and SM100 mega-attention already exist. Generic PDL/fusion would relabel existing work.
- [SiFAR](https://arxiv.org/html/2607.08973v1) improves TP all-reduce dependencies/redundant pulls. TP1 attention has no corresponding TP collective; EP all-to-all is not an interchangeable target.
- [NUMA characterization](https://arxiv.org/html/2607.28824v1) gives operand locality categories, not a callable source-compatible dense projection patch. Prior RD01 addresses related MoE localization. Retain as background, not an additional hypothesis.
- FlashInfer5982 early standalone MXFP8 quantizer PDL launch needs the installed FlashInfer revision/path; native fused norm/quant already has PDL. Donor model/hardware timing is not transferred. FlashInfer6322 is a dependency-order correctness caution, not a speedup proposal.
- SGLang17688 indexer overlap is source/model-specific and overlaps capabilities already present here. SGLang33265's packed loader axes warn against generic slicing; it does not establish that our MXFP8 loader is broken.

## Evaluation design and stopping rules

**Remaining CPU/source gate:** attest immutable deployment manifest/backend and exact prepared weight/scale geometry; specify lifecycle rebinding and fallback; retain PAD, None mapping, graph/eager partition and different-layer fixtures. Missing actual compatible route keeps implementation deferred.

**Later, only when GPU work is authorized:** compare original full projection's KV slice against KV-only output on exact weights/backend and representative decode/prefill/padded row counts. Compare post-norm/RoPE and inserted per-layer KV, draft proposals, confidence and acceptance—not final target output alone. Declare numeric tolerances against baseline and keep query modules intact. Exercise graph/eager paths and reload lifecycle. Time quantization, projection, norm and insertion separately, then paired serving runs.

Existing **agent-p75 and Mooncake** can exercise native DSpark context updates. Reuse them for service evaluation with fixed traces/image/config and paired repeated runs; track objective ITL/goodput and separate TTFT/E2E/tail/errors. A new endpoint workload is not justified by this mechanism. The additional evaluation is **component attribution and draft-cache correctness instrumentation**. Do not inherit a numerical SLA or promotion threshold from unrelated experiments.

Stop if route/layout is unsupported, correctness/acceptance regresses, or exposed savings/service gain is absent. A fused/stacked arm cannot rescue an incorrect KV-only baseline by obscuring its effect.

## Search yield and tool learning

Three paper queries returned24 provider documents/24 paper identities, all retained with exact revisions, query links and individual dispositions. Two were read in full;22 received abstract-level triage only. Local PR title query returned180 records; five selected opening bodies retained for focused triage, donor31986 API/head code/test also read. This is not a claim that all180 PRs were audited. One deferred hypothesis, zero qualified implementations, zero measured wins.

Query2 exposed automatic arXiv relaxation from eight requested terms to the first three, dropping the mechanism. Query3 was agent-authored and still too broad in its OR branch; that noise is our query-design failure too. The implementation worker repaired the hidden truncation/fallback and replayed the original strict cache response with0HTTP calls; see [tool replay](../../arxiv-mechanism-preservation-20261022.md). Original receipts remain unchanged. No further broad queries were needed once the quantized source path was the decision-changing question.

`paper-retention.json` contains all24 original Store documents/revisions and original edges. `discovery-command-journal.json` preserves command metadata. `RETENTION_PACKET.json` requests searchable retention; these files are not evidence that canonical import or S3 publication has happened.
