# Round71 — distinguish request-average ITL from streaming gaps

**Completed: pinned source audit, CPU semantic probe and independently reviewed normalizer correction. No serving experiment or measured improvement.** This round strengthens evaluation of the retained hypotheses rather than adding another inference optimization card. The frozen long-output ITL objective is unchanged.

## Exact evidence boundary

The public AIPerf v0.13.0 tag resolves to `794f8bb75f8582f22e412d7e650fc71ca2a3d21a`. GitHub tag/tree receipts and exact files are retained in this packet. Source reads use the normal `researchctl investigate` tool with this commit in an isolated state. The local adapter was inspected at AutoResearch-Inference `513ab3a0de7b1c4735abcd225edff31348c9e0a8`; copies preserve its pre-change state. This is not attestation of a running evaluator or the semantics of arbitrary older AIPerf versions.

## What each metric actually measures

`InterTokenLatencyMetric._parse_record` computes one ratio per request: `(request latency - TTFT) / decode token count`. With no usable first-content count, decode token count is OSL minus one. With valid first-content count, it is OSL minus that count. OSL is output plus reasoning tokens; server completion tokens include reasoning once. A nonpositive count or a count leaving fewer than one decode token triggers the upstream warning and legacy denominator. Requests with OSL below two have no ITL value.

The first-chunk adjustment has an explicit configuration gate: `inference_result_parser._compute_server_token_counts` supplies it only when `endpoint.per_chunk_usage` is enabled. Volunteered usage without that option must not silently change the metric. Moreover, the helper walks to the first parsed response with both data and usage, which is not necessarily the literal first content response if usage starts late. Reproduce the pinned evaluator semantics and disclose this limitation; do not reconstruct a denominator from the observed ITL itself.

`InterChunkLatencyMetric._parse_record` instead produces adjacent gaps between content-bearing response timestamps. Usage-only/end packets are excluded by the parsed content-response list. A zero gap is allowed; fewer than two content responses has no ICL. A content chunk can contain several tokens, so ICL is not an internal model token-generation timestamp.

The local normalizer's `tpot_p99_ms` is a percentile over completed eligible requests' individual mean ITL values. It does not describe the slowest individual streamed token/chunk gaps. Pooled gap percentiles also weight requests differently: requests with more content responses contribute more samples. The upstream ITL metric is marked as including failed requests in its percentile population, while the local normalizer selects completed records; this audit has not certified all upstream aggregation paths. Valid comparison cells must preserve the existing request-accounting/failure gates.

## Executed semantic control

`metric_probe.py` extracts the unchanged pinned metric method bodies and executes them with scalar record stand-ins, without importing AIPerf, Torch, a model or a GPU backend.

| Synthetic content arrival times (ms) | Mean request ITL | Largest content gap |
| --- | ---: | ---: |
| 0,10,20,30,40 | 10 ms | 10 ms |
| 0,1,2,3,40 | 10 ms | 37 ms |

These requests have identical OSL, TTFT and final time. Thus identical request-average ITL, including its cross-request percentiles, cannot by itself certify absence of within-request streaming stalls. This is a semantic counterexample, not evidence of any actual server stall.

A second fixture uses OSL10 and50ms of post-first-token duration: missing first-count produces50/9ms; a valid first chunk of5 produces10ms. An inconsistent first count10 falls back to50/9ms with a warning. The one-content-chunk ICL case raises the pinned no-value exception. Probe output records no forbidden modules loaded.

## Concrete local adapter issue

The adapter launches with `--per-chunk-usage`, but its pre-change validation always compares native ITL with `(latency-TTFT)/(completion-1)`. Therefore a valid first-chunk-adjusted ITL can be rejected as `token_counting_mismatch`. This is a source-backed potential false invalidation; no historical result has yet been shown affected.

Metric JSONL exports do not include the internal TokenCounts object. The raw exporter retains the wire request and responses, so reconstruction needs the exact endpoint parser and opt-in contract. The implemented correction is restricted to the supported chat export path, retaining existing validation and a documented legacy fallback. Missing, malformed and unsupported evidence must not be silently treated as proof of corrected semantics. No change is being made to the serving objective or qualification thresholds.

## Consequence for hypothesis evaluation

Continue to use the frozen request-average ITL objective and its separate existing guards. When a proposed optimization specifically claims smoother delivery or fewer stalls, retain content-gap evidence as an additional diagnostic and state its sample population. Any promotion gate based on ICL must be explicitly designed and frozen later; this report does not silently add one. Chunk-boundary changes can affect client observations even with the same model progress, so keep raw stream packets and evaluator version/configuration in the reproducibility record.

## Operational limits

An initial init command incorrectly supplied `--defer-snapshot`; it failed before discovery and the corrected isolated init is retained. An initial source-reader used a nonexistent Store `.conn` attribute; `.db` was then used. These were invocation errors, not provider outages. No paper query, model call, Serper search, serving request or GPU operation was needed for this metric audit. The final verification below records the implemented scope and limits.

## Implemented correction and independent verification

The exported `input_config.endpoint.per_chunk_usage` is authoritative when present. Otherwise the wire option is an explicitly bounded compatibility assumption for this adapter; absent opt-in preserves legacy behavior. The supported raw chat parser reproduces the first-data-plus-usage rule, including prose, reasoning and tool text. It rejects unsupported exported endpoint/counting modes and malformed evidence. It preserves the pinned missing-count/out-of-range fallback. Consistent integer server counts are required; reasoning greater than completion or disagreement with an exported OSL is ineligible. This avoids silently applying completion=OSL to an inconsistent export.

Every eligible normalized row now records the first count, denominator and evidence source. The metric's value is never used to solve for its own denominator. Existing functional/accounting/measurement gates remain; mismatched metrics can remain visible diagnostically in an ineligible cell, so cell validity is still required before any promotion decision.

A before-fix exported-data fixture reproduced `measurement_failed/token_counting_mismatch` for valid bundled first content. After correction, the bounded normalizer regression passed19 tests and39 subtests, with7 executable/model/saved-export cases deliberately deselected. Independent review ran all15 new ITL tests successfully. It also found a malformed-config admission bug in an intermediate patch; explicit presence/type checks and negative fixtures repair it. Both original and reviewer observations are preserved.

The broader adapter attempt did not pass: the author's run had4 missing-executable failures and one unavailable saved-hardware-export skip. The reviewer used a different unittest selection and saw4 errors and2 failures for the same missing AIPerf prerequisite. Neither run executed or installed AIPerf. Research-layer verification passed365 tests and29 subtests; bootstrap dry-run, critic-skill validation and diff check passed. No frozen historical result was rewritten or rerun.

The packet retrieved15 exact upstream files in7 normal investigate calls, with15 logical cache misses and no dossier errors. Separate cached GitHub tag/tree lookups established the revision and paths. Three pre-change local code copies are retained. These are source fetches, not paper discovery yield or an exact transport-request count.

The critic skill now requires auditing evaluator formula, opt-in flags, sample population and missing-value behavior before a metric supports a mechanism or promotion claim. Independent source/skill review supports that instruction; no demonstrated general research-yield increase is claimed.
