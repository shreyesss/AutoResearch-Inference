# Checkpoint 26 — smaller interventions and honest evaluator semantics

**Reviewed checkpoint.** The guided discovery loop remains active. No GPU/native model execution, serving change or measured performance improvement is claimed.

## Where the strongest next experiments stand

| Direction | Change to the pinned implementation | Why it remains useful | Unresolved gate |
| --- | --- | --- | --- |
| PJ01 | Compute only the consumed KV columns of the three DSpark context projections | Exact source shows unused Q output; existing warmup/capture route can be reused | Actual prepared tensor layout, external backend workspace, numeric and graph correctness |
| CF59 | Overlap unchanged context preparation with sampling | Independent work exists in the source DAG | Preserve early output release, streams, scratch ownership and exposed overlap |
| AV68 | Skip two metadata publications overwritten in the same adaptive-verification step | Narrow source change; no new cross-step cache or buffer-pool protocol | Effective AV activation, native metadata equivalence and exposed host/transfer cost |
| HM65 | Refresh static sampling metadata only when dirty | Five unchanged arrays are republished in clean steps | Actual writer/invalidation coverage and existing reader lifetime |
| CR64 | Compare compressed-KV cache eviction hints | A narrow tuning arm with unchanged attention support | Workload cache interference and actual compiled instructions |

This ordering reflects implementation readiness and clarity of the falsifier, not predicted percentage gain. All service value remains unmeasured. PJ01's nominal projection MAC reduction does not imply the same decode-speed reduction. AV68's smaller contract than HM65 does not imply a larger benefit.

## AV68: source-driven continuation

The general cumulative-logit device allocation and query-start copy are replaced by the existing adaptive reallocator before their device contents are consumed. Guard their publication only when the AV manager exists and scheduled drafts are nonempty, including the zero-selected-budget case. Preserve CPU metadata, complete query-capacity padding and all no-draft paths. The reallocator already writes the same persistent query buffer.

Fourteen paired source-extracted scalar/vector controls preserve downstream metadata; two deliberately unconditional-elision variants fail. They do not execute the native selector or validate streams/CUDA graphs. Logical omitted bytes are `4*(N+1)+4*(R+1)` per eligible step; exposed time and eligible frequency are unknown. This advances a component parked in round65, not a second independent discovery of that component.

[Mechanism and falsifiers](round68/REPORT.md), [independent review](round68/INDEPENDENT_REVIEW.md).

## Recent-paper exploration that did not become new cards

**mKernel:** the paper's adaptive role-controller idea belongs to the existing N03 family. The inspected released BF16 MoE implementations use fixed role ranges. Our pinned MegaMoE has warp-specific register allocations, scheduler consumers and barrier participants. A scalar SM-allocation knob is not a safe port. The follow-up found that completed primary CTAs call a reducer helper but every applicable current branch excludes them; the tiny-chunk recycling condition is unreachable. Target epilogue-to-combine reuse already exists. Dispatch-to-combine still needs task ownership, scratch and cleanup/barrier contracts. Three focused source reads settled this without another generic paper. [Follow-up](round72/REPORT.md), [root review](round72/INDEPENDENT_REVIEW.md). [Author investigation](round69/REPORT.md), [independent review](round69/INDEPENDENT_REVIEW.md).

**EqiForge / mHC:** residual-to-next-normalization fusion is already present. PR62745's single-pass tuning band is specifically H4096 and does not directly apply to our H5120 target. Its separate NaN reciprocal-RMS guard could avoid remaining Sinkhorn iterations, but the donor's padding symptom is not established here. It remains a conditional lead, with finite-row iterations and all output/synchronization contracts preserved. [Investigation](round70/REPORT.md), [independent review](round70/INDEPENDENT_REVIEW.md).

Neither a large paper headline nor a matching model-family keyword qualified these as improvements. These rounds returned21 paper records across three dated queries and selected two fulltexts; this is returned-record count, not a deduplicated cross-provider denominator. Round68 reused existing source without a new online query. One previously parked direction was formalized; zero implementations or service wins were qualified.

## Evaluator correction verified on CPU

Pinned AIPerf ITL is a request-average ratio. Its p99 across requests does not certify the p99 of within-request streaming gaps. A CPU counterexample preserves request ITL at10ms while the largest gap changes from10ms to37ms. Streaming chunks may contain several tokens, and gap pooling weights requests differently.

The adapter requests per-chunk usage but previously validated every ITL using `completion_tokens - 1`. Pinned AIPerf can subtract the valid first-content count instead, gated by its per-chunk configuration. A CPU export fixture reproduces false `token_counting_mismatch`; the correction reconstructs the supported export contract rather than inferring counts from ITL. The frozen objective and thresholds remain unchanged. No historical serving result is yet shown affected.

[Metric audit](round71/REPORT.md), [independent code review](round71/INDEPENDENT_REVIEW.md). The exported configuration flag is authoritative; raw wire options are a bounded fallback. Normalized rows record the count, denominator and evidence source. Unsupported/malformed evidence and inconsistent server counts remain ineligible. Independent review caught and repaired a malformed-config admission gap.

Verification:19 bounded normalizer tests and39 subtests passed; independent reviewer ran15 new ITL tests successfully. The broader adapter suite could not pass because this environment lacks the AIPerf executable and one saved hardware export. No native evaluator was installed or run. The required research gate passed365 tests and29 subtests; bootstrap dry-run, skill validation and diff check passed. [Exact commands and limits](round71/implementation-receipt.json), [root gates](round71/root-verification.json).

The critic skill now asks for metric formula, opt-in flags, granularity and population before using an evaluation claim. This is an evidence-driven instruction change, not a claimed measured increase in future discovery quality.

## Retention

Independent root review verified the67/68 isolated default restore:108 artifacts and29 source revisions, exact deferred AV68 card, and four background claims for the original PJ01. The fixture's shortened PJ01 history is not a replacement for canonical history. The guarded normal-tool replay is queued after the existing sole writer chain. This is isolated durability evidence, not completed canonical/S3/VM synchronization.

At06:42:15UTC, local job receipts still showed937 successful GitHub pages and a last completed batch at06:10:58UTC. Latest local research snapshot remained `b57a565991adf4b30ebef05e660799bba01b25b8868f529405aa59191f842752`; last completed published lineage was `f82df0e3c9dc0b01534b03f6915f2b1f1e000e888e1ee4de0b4d0b2d63da356d` at06:05:49UTC. These differ; newer work is not claimed uploaded. [Observation](retention-26/publication-observation.json), [delivery hashes](source-copy-manifest-26.json).
