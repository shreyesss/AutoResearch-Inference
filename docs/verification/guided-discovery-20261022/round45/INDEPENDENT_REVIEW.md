# Independent QH45 review — separate quantized DSpark output head

Reviewer: guided_adversary. Reviewed frozen round45 report, selected primary-paper passages, pinned loader/config/head/sampler source and stdlib diagnostic. Supplementary source copied here is pinned online/fp8.py. No GPU, native tensor import, provider query, target checkpoint tensor inspection, code patch or canonical mutation.

## Verdict and relative priority

**Retain QH45 as deferred, source-supported integration work; no implementation/service qualification.** This is a real missing DSpark integration of an existing helper, rather than a new quantization kernel or duplicate of C025/PJ01. It affects an entire vocabulary projection across draft rows and has a concrete existing implementation to reuse, so it deserves a bounded backend/exposure gate. Weight count alone cannot rank it above measured bottlenecks or establish an ITL win. Do not start another sequence of synthetic probability fixtures after the current contract illustration.

The source audit shows DSpark's config rejection and its direct target-head alias, while EAGLE/MTP already calls the derived-copy helper. This establishes the gap at c455, not absence of every later branch or uncommitted deployment patch. No novelty requirement is needed.

## Two important arm clarifications

1. **The FP8 helper is W8A8 PTPC, not weight-only W8.** `Fp8PtpcOnlineLinearMethod` uses per-output-channel weight scales and dynamic per-token activation scales. It rejects MarlinFP8 because that kernel is W8A16. The proposed arm leaves the DSpark backbone tensor values unchanged, but quantizes the normalized input to this output-head GEMM internally. The NVFP4 helper is separately W4A16. HyCo's W8 PTQ result is a rationale for examining a precision/acceptance tradeoff, not validation of this exact head, activation treatment or backend.
2. **A batch-invariant fallback can invalidate the intended execution.** `online/fp8.py:449–465` dequantizes the full copied weight to the input dtype and calls `torch.nn.functional.linear` when `VLLM_BATCH_INVARIANT` is enabled and the chosen FP8 kernel is not batch invariant (for ordinary tensor input). That adds a full dense-weight materialization and does not execute the intended FP8 GEMM. Admission must identify the selected backend and this mode, not merely accept a config string. Do not claim the narrower FP8 residency/traffic model for that fallback.

## Proposal-cache and verifier audit

Native DSpark computes all configured draft-position base logits, then adds the parent-conditioned Markov bias at each step. `_sample_logits` routes the resulting logits to Gumbel sampling with the persistent draft-logit cache. The Gumbel source explicitly caches pre-temperature logits and applies matching temperature semantics in the consumer; it does not cache the original target-head output independently. Thus replacing only the head naturally feeds the changed proposal into the same sampling/cache boundary.

This is positive source evidence for a feasible integration, not a correctness proof of native block verification. The exact-rational two-token fixture correctly demonstrates why stale q breaks standard single-step rejection sampling. It does not exercise five-step block rejection, EOS, masked/padded rows, watermarking, top-k support, mixed temperatures, capture or floating-point probability behavior. Same-seed token disagreement is neither proof of a distribution error nor a sufficient stochastic correctness test. Target greedy equality and stochastic verification need their appropriate distinct controls.

The top-k drafting path already truncates/scatters the actual biased proposal; do not combine vocabulary reduction or a new sampler with the first precision arm. Keep the target head object/weights and target logits path unchanged. Treat generic q-caching statements as a requirement to confirm against the exact enabled native branch.

## Copy and reload lifecycle

The helper requires an unquantized FP16/BF16, bias-free source head. Its per-channel converter allocates new FP8 output and replaces the new module's weight; it does not quantize the aliased target storage in place. It records the source in a weak-key registry and provides in-place refresh to preserve captured tensor pointers. The V2 runner's `reset_lora_state` refreshes derived draft heads after target-weight changes via `get_draft_model`. This is useful existing plumbing.

Nevertheless, presence of these utilities is not evidence that a new DSpark loader branch invokes them at every required reload/capture boundary. The test must check original target object/data unchanged, derived module registration, stable tensor layout after refresh and peak conversion residency. An unguarded mutation of the shared target head is a different, invalid experiment.

## Memory, acceptance and service relevance

The reported661,913,600 weights and per-rank logical capacity arithmetic are correct for the stated full TP1 shape. The original target head remains resident; adding an FP8 copy consumes roughly662MB before backend/workspace/temporary costs. Copies are per rank, not a single amortized node allocation. These bytes are capacity, not saved HBM traffic, and could reduce KV admission.

HyCo's98.8% top-1 agreement is not our acceptance rate and not a guarantee of whole-round progress. Source confidence prediction also deserves explicit observation: parent-conditioned sampled tokens change, while a trained confidence head's calibration may no longer match the new proposal. Rebuilding latency cost curves does not itself recalibrate acceptance predictions. Keep confidence weights fixed for the initial arm and report prediction/acceptance/budget behavior rather than introducing retraining.

The `G_new/G_old > T_new/T_old` condition is useful for conditional average progress per round. It is not a direct proof of long-output ITL or its tails under streaming, batching and admission changes. PJ01, C025 and QH45 savings cannot be added: they share the round denominator and can move its critical path.

## Bounded next gate and stop rule

Before any authorized GPU experiment, check the retained deployment config/image for: exact active native DSpark route, eligible source-head dtype/layout, selected PTPC kernel, batch-invariant mode, existing equivalent patch, graph/reload integration, and already-recorded head shape/timing plus memory headroom. This is an evidence request, not a fabricated missing-cost estimate. If no retained timing/exposure records exist, keep the card parked pending one explicitly authorized head/complete-round measurement; do not generate more toy acceptance cases.

The later first arm should be separate FP8 PTPC head versus the same target/native chain baseline, with full vocabulary and unchanged Markov sampler/verifier. Require native correctness before economic timing; retain acceptance/progress, exposed full-round time, actual kernel, memory/KV changes and adaptive behavior. Keep standard Mooncake and agent-p75 for service confirmation; the extra bounded numerical/native-verifier test is necessary because those traffic workloads do not prove sampling correctness. No ROI or implementation readiness is awarded now.
