# Round 9 independent review: shared-host Engram MXFP8 staging

Verdict: retain a distinct, source-grounded adaptation candidate; defer service qualification and GPU execution. Exact target numeric equivalence, resolved live route, and exposed conversion cost remain unverified. No GPU, CUDA/model import, availability check, or serving mutation was executed for this review.

## What the candidate actually removes

Pinned `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, `common/engram.py` lookup kernel lines650–723 already reads FP8 values and scale bytes directly from the table, including shared pinned host memory through UVA. Its BF16 branch materializes dequantized rows on the GPU. The WKV FlashInfer MXFP8 linear path then requantizes those rows before GEMM. A compatible direct FP8/scales input could remove that intermediate materialization and main-stream requantization.

**It does not reduce shared-host table PCIe/UVA bytes.** The 48% smaller collective payload claimed by DP/TP-sharded donor work is absent from this local TP1/table-dp1 route. Nor is a universal HBM-byte reduction justified: F8_128x4 scales pad to 128 rows. At one token, width6144 gives6144 value bytes plus24576 padded scale bytes versus12288 BF16 staging bytes, before counting the old quantizer's own output and reads. This is component accounting, not a latency model. Credit only exposed saved work; asynchronous lookup overlap and two actual Engram layers constrain the denominator.

## Existing implementation and donor selection

`EngramBatch.create` lines1443–1456 explicitly excludes `table.dp_size==1`. Shared-host embedding construction resets table dp_size to1. Removing that guard alone is invalid: `_stage` still chooses peer exchange or all-to-all and uses group token slots. The existing DP batch is not a drop-in local implementation.

The exact donor is public vLLM PR58766, closed/unmerged/draft, head `5030d5dd66884830e5b20149218ca27e9864901b`. Its unsharded branch directly writes persistent FP8 values and F8_128x4 scales; its sharded branch packs scales into rows. Reuse the unsharded mechanism selectively, preserving current fork prefetch and batch branches. PR body reports139 passed on GB300, a real CuTe WKV comparison, and removed host-path main-stream requant time1.5us atT1/1.6us atT128. These are donor reports, not our measurements; full model evaluation was pending. A merge-conflict bot comment does not establish a correctness failure, and closed/unmerged does not establish deployment readiness.

PR59923 covers DP-sharded batching, which our pin already has. It supports the ABI concept but not a missing shared-host implementation or transfer-byte benefit. PR58766 is the closer source. No new algorithmic novelty claim is needed.

## Exact eligibility gates

1. Resolve runtime `dp_shared_memory`, effective Engram table dp_size, TP, WKV kernel class, and model/image pin. Config default sharing is conditional on CPU offload, no THP, DP>1, no elastic EP. `can_share_engram_tables`876–906 can fall back after co-location or `/dev/shm` capacity checks. Planned DP4 alone proves neither live sharing nor this missing path.
2. Preserve `can_fuse_query_quant`: exact FlashInfer CuTe-DSL/CUTLASS MXFP8 classes accept this F8_128x4 scale ABI. A quantization key alone does not identify layout. Keep BF16 fallback for unsupported WKV, including SM90 Marlin. Include block32, head/width alignment, LoRA and actual TP/SP constraints in the adapter; do not inherit donor topology support without reconciling current code.
3. Keep values contiguous, scale padding freshly zeroed for each active128-row tile, correct head offsets, masked/out-of-vocab zero rows, and orig BF16 metadata. Test changing token counts across graph replays, especially130→1→129; stable allocation addresses alone do not protect stale padding.
4. Preserve per-layer prefetch event ordering. Current model stages all eligible layers before decoder entry; layers share a prefetch stream, and each layer waits its own event. A new all-layer synchronization can erase overlap. Both values and scales must be ready before the same event is recorded/awaited; each layer needs independent persistent storage.

## Numeric contract: narrower than the donor prose

The donor real CuTe test uses token counts1/130, output width256, random weights and moderate table scales120..133. It is substantive component evidence, but not all checkpoint values, full25600-output WKV, all backends, or complete model equality. Do not expand its bit-identical claim beyond that coverage.

Our SM100 `mxfp8_utils.py187–211` dispatches to **FlashInfer cute-dsl quantization**. The subsequent torch fallback formula is not proof of target behavior. FP8 times powers of two is BF16-exact only within the representable range and under matching exceptional-value semantics. Small scales can lose FP8 low values to BF16 underflow; large scales can overflow. The native lookup decodes scale byte0 by float32 exponent-bit construction, yielding zero, whereas a simple `2**(byte-127)` reference would yield2^-127. Include zero/255 scale and FP8 NaN handling, but do not claim such values exist in the checkpoint. A CPU toy boundary counterexample is a proof that the blanket assertion needs a domain, not evidence that this actual model fails.

Fastest next non-GPU discriminator: inspect an existing checkpoint's Engram table/scale metadata and, if locally available, scan scale bytes/exceptional value occupancy without uploading or loading onto CUDA. Establish the representable input domain, then inspect the pinned FlashInfer quantizer source/ABI. If these files are unavailable, retain unknown numeric eligibility. Later authorized component differential tests must compare actual target lookup→requant→WKV with direct staging using actual weight shapes and both selected backends; model-level output equality remains a separate gate.

## Prior-memory overlap and relevance

Prior A01 (`hypothesis:36794075a7034c3f1ff100e73c1d8436a4606397c8e07766ed5388ef64b16646`) moves WKV GEMM earlier to overlap attention and fences at its consumer. This candidate removes representation conversion while leaving WKV scheduling unchanged. They are distinct interventions and can be tested independently; do not double-count combined savings. The raw lookup already has prefetch, so a proposal merely adding asynchronous lookup would duplicate existing code.

Target model evidence identifies Engram in two backbone layers, not every layer or every DSpark draft step. A decode token-count/round trace is needed before translating per-invocation savings into ITL. Donor microseconds and DP-sharded <1% TPOT reports do not fix our gain. Unknown ROI permits a bounded diagnostic, not a service-win claim or blanket rejection.

## Falsifiers and decision-changing checks

| Check | Decision changed by failure |
|---|---|
| Resolved route already selects raw quantized input | Reject missing-mechanism claim for that deployment |
| Shared mode falls back to DP-sharded batch already optimized | Re-scope or reject applicability; do not patch inactive branch |
| WKV backend lacks exact QA/scale ABI | Keep BF16 fallback; no forced reinterpretation |
| Exact checkpoint scale/value domain violates BF16-roundtrip identity | Require explicit numerical compatibility treatment; no blanket bit equality |
| Prefix/padding/invalid-ID sequence differential fails | Fix packing before any performance trial |
| Prefetch event or stable-storage lifecycle differs after adaptation | Repair ordering/resource lifetime; no throughput interpretation |
| Conversion is hidden or saved critical-path time below objective | Deprioritize; report bound rather than donor-speedup transfer |

These source checks already changed the candidate: shared conversion removal, not collective/PCIe reduction; selective PR58766 reuse, not whole EngramBatch enablement; conditional numeric gate, not global exactness assertion. No GPU performance or correctness proof has been produced here.

## Final worker-card inspection

Reviewed `round9-engram/candidates.json` after publication. EG01 incorporates the narrowed mechanism, exact donor, CPU-only inconclusive scope, shared-host traffic correction, non-additive A01 relationship, and existing endpoint evaluators. No blocking factual correction is required for retention as **deferred**. The remaining CPU numeric fixture is not a substitute for the checkpoint/FlashInfer checks above.

EG02 is a lower-priority, deferred **discovery lead**, not an implementation-ready hypothesis. STAPLE's inference cache is a selectively reusable mechanism independent of its training recipe, but a token-indexed inverse map cannot be transplanted into layer/head-specific n-gram tables. Offline request/token hashes should preserve request timing/order, table/layer/head identity and model revision; a global repeated-token ratio is insufficient. A software-cache hit curve alone cannot establish marginal hardware-cache misses or saved PCIe traffic. A capacity sensitivity analysis can bound opportunity, while actual device-cache/coherency/overlap measurements remain unauthorized and unperformed. No absence-of-prior-memory claim was established beyond the bounded index reviewed here. Retain as low-confidence evidence gathering, with no predicted service win.
