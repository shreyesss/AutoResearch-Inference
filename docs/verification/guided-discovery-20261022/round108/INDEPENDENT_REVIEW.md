# Independent review — round108 historical cache exposure

## Verdict

The central conclusion is supported: these historical endpoint summaries do not establish round105's costly eviction/preemption/restoration premise and cannot qualify the current d464 deployment. Two bounded reporting corrections are required in an additive note; the frozen author packet is unchanged.

1. The run-manifest dates are **15 on October 17 and six on October 18, 2026**, not uniformly October18. A score's creation time or duration was not inferred beyond its associated run manifest.
2. `readback.json` reports `runtime_image_present=5` per workload because the author predicate accepts an empty string as present. In fact **15 selected_image values are empty strings and six are null; zero are nonempty image identifiers**. This strengthens the missing-runtime-attestation caveat and does not reverse the scientific disposition.

## Independently checked

Read all 21 score copies and 21 manifest copies. Verified the supplied author manifest SHA `d5912528771af5d026d547ce00588642bf7bf724e3a400ec5a48d7fbe501c86b`, all 46 author-file hashes, and all 42 copied-file hashes against the bounded declared original paths. The declared source tree contains 21 score files and two additional unscored manifests; those two cannot be counted as completed scored runs.

Each of the three workloads has seven scores and six with cache-hit reporting: **18 of 21 overall**. This means reporting is available, not that all 18 have complete coverage. Seventeen have full request coverage; the public median 2x run has 4003/4004 reported requests (0.9997502497502497). The selected public cache-heavy example has full coverage. My initial overstrict assertion equating availability with full coverage failed; the retained correction checks the actual per-row reported/request ratio instead. This was a reviewer error, not an author science failure.

For `20261018-080958`, copied source index18 is `bitlane-public-2x`, production Mooncake cache-heavy: 4053 attempted requests, 10,142,720 cached prompt tokens / 33,375,484 prompt tokens = **0.3038973157662672**, full reporting coverage. The manifest has null selected_image, dirty benchmark checkout `724cee8d6b9208addbca149e29a9f87fae8c5820`, tokenizer `DeepSeek-V4.1-Flash@2cba9e42aa026125f3ed06c6d98c1db82f7ca027`, and the public endpoint model alias. Those are accounting/benchmark identifiers, not a source pin for a running vLLM server or proof of target Flash-1017 weights.

Independently walked nested metric keys, not only top-level metrics, for the bounded eviction/preemption/recomputation/allocation-failure/restored key patterns. None appeared. This does not prove such events were zero, that arbitrary differently named counters do not exist, or that richer raw/server artifacts are unavailable elsewhere. It confirms that these summaries do not supply causal restoration attribution.

## Interpretation limits

Cached prompt-token share is not an eviction rate or a count of recoverable misses. Cold or unique tokens, routing, prefix identity, policy and backend eligibility can all affect the aggregate. Unmatched extrema across endpoint runs do not identify a cache-protection effect on ITL. The chosen example's complementary 69.61% therefore is not a restoration budget or opportunity estimate.

All retained environment objects are empty. The `code_sha256` manifest entries and executable command identify the load-generator/analysis code; their git revision cannot be repurposed as a server code pin. Every retained tokenizer revision differs from the frozen Flash-1017 target revision. That mismatch does not independently identify actual model weights behind a public alias; it makes current-target attestation weaker, not stronger. No legacy run was relabeled as d464.

The author correctly leaves round105 parked and seeks an attributed, pinned server-side eviction/preemption event before a runtime comparison. Existing Mooncake/agent-p75 service benchmarks remain suitable for eventual service outcomes, with an attribution diagnostic added only if needed and separately authorized. No tenant benchmark, current runtime measurement, quality revalidation, or cloud read was performed in this review.

## Reproducibility and scope

Executed only `python3 review/round108-agent/check.py`: stdlib JSON/hash/count/ratio checks over existing files. It writes reviewer-owned outputs. `checks.json` retains row-level evidence, date/image corrections and bounded original inventory; `initial-check-failure.json` preserves the reviewer availability/coverage mistake. This is not an independent replay of AIPerf normalization or the historical benchmark itself.
