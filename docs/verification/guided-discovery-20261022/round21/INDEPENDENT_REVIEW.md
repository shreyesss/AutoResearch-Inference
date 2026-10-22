# Independent round21 review

Disposition supported: OH21-01 remains low-priority deferred, not an implementation or service win.

I read the actual pinned serving call, ParserEngineReasoningAdapter and ParserEngine methods alongside the extraction script. The ready counter genuinely does not inspect history. Its false-ready branch requires history and must remain available. The synthetic Poison object is a useful dependency check; the mocked fallback is a counterexample to universally passing empty history, not a full parser correctness test. A capability method returning readiness plus counter would preserve this distinction; merely removing tuple conversion globally remains unqualified for other parser implementations.

Exposure requires all source guards together: a parser, `_include_reasoning_tokens_details`, continuous usage, and valid streaming counter. A saved `--per-chunk-usage` flag alone proves none of the remaining guards. Full-ID accumulation must not be removed without accounting for the false-ready/final usage consumers.

I independently recomputed all six saved paired medians and tuple-copy counts. The seven alternating repetitions share synthetic traces and mocked counter state. They estimate marginal tuple bookkeeping, not HTTP/parser throughput, request latency, contention or a deployment confidence interval. The approximately 0.100 ms whole-stream saving at 1,024 tokens/five-token chunks supports low priority; the longer quadratic examples motivate conditional reopening, not a forecast for current workloads.

No new source modification, parser execution, benchmark rerun or GPU action. Existing DecodeStream and delta parser are correctly acknowledged; the Muse donor is not a DeepSeek direct port. Timing/counter evidence remains scoped CPU investigation.
