# Guided discovery — checkpoint 4

22 October 2026. CPU/source research continues against `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883` and the retained Flash-1017 model metadata. This source plan is not a live deployment attestation. No GPU experiments or serving changes were performed.

## A new concrete DSpark source gap: PJ01

Context preparation currently computes Q1280+KV512 for each of three draft layers, then discards Q1280. The first proposed arm keeps all three context updates, input quantization, per-layer norm/RoPE/slot mapping and full query modules, but uses only the KV output rows on a verified compatible processed-weight backend. Stacking layers is optional and separate.

Independent review confirmed this differs from the earlier proposal to skip draft-query work during unfinished prefill. It preserves that work and removes only immediately discarded context-projection outputs. Source-derived scale indexing checked81,920 coordinates for the exact aligned CuTe/CUTLASS layouts; actual tensor layout, numeric behavior and runtime backend remain unverified.

**71.43% of this projection's nominal output arithmetic is discarded. This is not a71.43% latency forecast.** The exposed component share, smaller-GEMM efficiency and added overhead are unknown. This is a particularly direct source gap to investigate; implementation remains deferred until route/layout attestation and correctness design. Standard agent-p75/Mooncake remain the eventual service tests, with added draft-cache/component instrumentation.

[Mechanism, pins and experiment design](round12-projection-scheduling/REPORT.md) · [Independent review](round12-projection-scheduling/INDEPENDENT_REVIEW.md)

## New component recovered from a previously closed PR

**EG01: remove shared-host Engram conversion before WKV.** The running-plan route uses one shared host table. The merged packed distributed-exchange implementation does not handle this route. Closed PR58766 contains a separate unsharded component: write packed FP8 values and scales directly into the existing WKV input representation instead of materializing BF16 and quantizing it again.

This is a concrete missing component, with modest prior evidence for materiality. It leaves host-memory traffic unchanged. At one token, padded scale output increases GPU stores. There are only two target Engram layers and no draft Engram in the audited construction; multiplying a per-layer saving by40 layers or five draft positions would be wrong. Donor GB300 timings are not a B200 service forecast. **Keep the proposal deferred pending numeric, consumer, lifetime and exposure evidence.**

[Source-grounded proposal](round9-engram/REPORT.md) · [Independent review](round9-engram/INDEPENDENT_REVIEW.md)

### Adversarial tests changed the proposed adapter

The donor predates the pinned fork's sorted-ID lookup and inline/background branch selection. CPU byte simulations caught three intentionally broken ports:

1. Padded scales not refreshed after a large-to-small call.
2. Values restored by sorted destination while scales use the iteration row.
3. Invalid IDs skipped, leaving stale values/scales.

The repair requires matching value/scale destination identity, writing the full returned padded scale view, and zero-writing invalid rows. Source-extracted Python control flow also shows that both inline and background lookups must receive the scale buffer; a local one-token request can take the inline route because the decision uses the maximum token count across DP ranks.

**28 simulated sequence cases,49,152 scale-coordinate comparisons and four source-extracted orchestration cases passed.** These establish bounded layout/control-flow properties. They do not execute CUDA, the real quantizer, checkpoint values, GEMM or concurrent stream lifetimes. No serving optimization is validated.

[Detailed adversarial report](round11-engram-lifetime/REPORT.md)

## Another lead deliberately remains low priority

**EG02: software caching/deduplication of hot Engram rows.** STAPLE's inference-memory component is potentially reusable independently of its training system. However, token-indexed caching is not the same as n-gram/head/layer-indexed Engram lookup. Existing hardware caching may already remove most benefit. Without actual residual miss and exposed-time evidence, this remains a weak discovery lead rather than an accepted experiment.

## Historical benchmarks do not supply the missing ROI denominator

The bounded retained-artifact audit found no compatible measured MegaMoE/gather/Engram exposure for Flash-1017 at c455. Older B200 R7b matches the two DEP4-group topology but differs in model/source and supplies aggregate timings. The genuine H200 C25 sampler saving belongs to another component and cannot estimate B200 MoE or KV benefit. The H200 verification trace itself reports instrumentation limitations. The entire S3 archive was not audited, so this is a scoped evidence gap, not a claim that no evidence exists anywhere.

[Compatibility matrix and scope](round10-exposure-audit/REPORT.md)

## Yield and current selection

Through round12: **25 considered directions:2 accepted bounded CPU plans,18 deferred,4 rejected,1 duplicate;0 service-qualified improvements.** The25 includes EG02's weaker discovery lead. Rounds6/7/11 refine existing identities; round8 evaluates research methods; round10 audits historical exposure. None increases the hypothesis denominator.

PJ01 offers a newly isolated, direct code-delta diagnostic. Existing priorities remain RD01 physical expert-weight localization, M01 workload-informed MegaMoE tiles, and AT03 compressed-KV materialization reuse. EG01 is a narrower, auditable conversion-removal opportunity, with counterevidence against a large ITL claim. Ranking these as confirmed wins would overstate the evidence.

## Tool behavior and persistence

Round12 observed an automatic arXiv fallback lose the requested mechanism by retrying only the first three words. The old receipt disclosed the attempted queries; the problem was the automatic relaxation itself. The implemented repair preserves all submitted content terms and lets the agent explicitly choose a different query when results are empty. A replay using the original cached response retained all eight terms and returned zero hits in one attempt, instead of eight off-topic fallback hits in two attempts. It made zero provider HTTP requests. This verifies query fidelity, not improved recall. See [field replay](../arxiv-mechanism-preservation-20261022.md).

Research tests pass at267 with11 subtests after the repair; bootstrap dry-run also passes. Earlier artifact-portability, local-coverage errors and optional citation controls are already implemented. See [tool evidence](TOOL_IMPROVEMENTS.md).

S3 publication through rounds2–4 is verified by manifest `3bf6db32a1a516433190ae8966cfb5ceda475539792b682b1128c40443f33489`. Canonical imports through round9 have now completed and independent readback verified152 artifact hashes plus28 paper-revision/search references. Their S3 coverage remains pending; round10 and round12 retain external reports and diagnostics. Round11 has also been appended to the same EG01 identity:6 claims,2 inconclusive CPU records and12 independently checked artifact hashes. Its cloud coverage is likewise pending. Reports in Git, canonical memory, S3 publication and VM restore are separate facts; [STATE.md](STATE.md) tracks them.
