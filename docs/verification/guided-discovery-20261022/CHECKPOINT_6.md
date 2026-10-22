# Guided discovery — checkpoint 6

22 October 2026. CPU/source research continues. No GPU queries, profiling, experiments, model loads or serving changes.

## Yield and scientific status

Through frozen round16: **31 screened intervention cards: 2 accepted bounded CPU investigations, 21 deferred, 7 rejected, 1 duplicate. Zero implementation-qualified or service-qualified improvements.** AT02's new mechanism detail is a refinement of its existing identity, not another success. Counts describe authored and reviewed research; canonical retention and publication are tracked separately below.

Round15 screened 21 unique papers from 24 returned rows, read four fulltexts and triangulated 39 distinct retained PR opening records. Round16 screened 21 unique papers from 22 successful-query hits, read one fulltext and rejected one concrete transfer. These per-round paper counts can overlap; they are not additive unique-corpus counts. Failed searches are not evidence of absence.

## Selective synthesis that survived review

### AT02: preserve QUILT's useful exact component

QUILT decomposes neighboring sparse-attention selections into common and private entries. Keep the decomposition; omit its final approximate tail clipping. Our prefill already materializes BF16 KV, so repeated per-query dequantization is not the missing baseline operation. The remaining proposal is explicit reuse of reader loads across queries. A FlashInfer PR supplies union/mask metadata code, with substantial H512 MLA, cache-pool and grouping differences.

The same question may apply to native speculative-verification rows. Pinned source selects separately per query row and the configured reader explicitly shares across heads within a token, not common segments across tokens. Actual overlap and incremental benefit beyond L2 reuse are unknown. Compression ratio 2 does not prove two queries select identical tokens.

CPU tests checked exact set partitioning and real-valued attention merging, and exposed aliasing, padding, multiplicity and sink mistakes. They did not test reordered low-precision arithmetic or target tokens. Sorting, metadata, tile tails and synchronization can erase savings. **Still deferred.** Next useful evidence is an existing exact-target selected-index trace; no GPU capture was launched.

### CMR01: balance context work without changing collective shapes

A PNM paper's request-composition idea is separable from its hardware. Pinned vLLM splits microbatches by padded query-token count; indexer work can also depend on context. An eligible request-bundle permutation could improve balance while keeping identical DP split capacities.

The gates matter: microbatching must already be enabled, boundaries must align with complete requests, and adaptive verification can invalidate CPU-side bundle assumptions. Every cache/slot/draft/logit/output mapping must remain coherent. A greedy proxy worsened 2 of 200 synthetic cases; retaining baseline when worse is necessary but does not prove a service benefit. **New, deferred, not implementation-ready.** First reconstruct eligibility from existing launch/metadata artifacts; do not disable baseline features to manufacture exposure.

[Full mechanism, source pins and evaluator mapping](round15-indexer-search/REPORT.md)

## A paper rejected after reading its limitation

RT16-01 examined SiFAR's speculative synchronization removal. Its own fulltext permits a stale payload followed by a current valid flag unless an additional GPU-progress assumption holds. A symbolic CPU interleaving retains that failure mechanism; it is not a device reproduction. Moreover, repeated TP all-reduce is not the main planned TP1/DP4/EP4 exposure, and the inspected custom mHC path requires TP4 without EP. Embedding groups are a separate unresolved case.

The direct transfer is rejected. A future rigorously ordered dual-buffer component is not ruled out, but no absent applicable operation was established here. [Evidence and scope](round16-runtime-scout/REPORT.md).

## Research-tool improvements measured against failures

1. Failed paper searches now retain safe numeric HTTP status, allowing agents to distinguish 400/401/429/5xx. Authenticated URLs, headers and error messages remain excluded. Four injected provider failures tested this boundary. There is no automatic query relaxation or retry.
2. One explicit unchanged-query retry succeeded with eight papers and led to October21 UlaCache. Earlier HTTP failures remain unknown-status failures; success does not explain their cause. Fulltext follow-up is active, not counted as a qualified idea. [Receipt and all eight dispositions](paper-http-diagnostics/REPORT.md).
3. A real snapshot restore exposed missing raw source/replay files: 185/304 audited references recovered, 119 omitted by default archive filters. Added explicit reviewed path/hash retention through content-addressed text copies, preserving historical events. Independent review found a conflicting-duplicate manifest bug, which was fixed before application. The scoped selection covers 117 references; PNG and `.gitignore` remain explicit exclusions. Test fixtures exercise actual snapshot/restore and refuse to hide corrupt originals. [Audit and implementation](artifact-portability/REPORT.md).

## Persistence scope at this checkpoint

Round15 importer passed isolated and independent checks: 73 archived files, six exact source claims, 24 paper revision references, four inconclusive CPU diagnostics; exactly one new identity plus AT02 refinement. Canonical application is queued under the writer lock. Round16 retention preparation is ongoing. Selected-artifact retention is also queued; no completed canonical repair, new S3 publication, or VM restoration is claimed yet.

Last verified S3 publication remains `e05b413…`; `b97f51c…` exists locally but publication is not yet verified. The query-domain corpus import/publication is still running. None of these operations was restarted or allowed to adopt remote lineage silently. [Current state](STATE.md).

## Next adaptive actions

- Independently inspect UlaCache's reusable components against resident DP storage and already-fused index mapping; reject headline transfer if baseline differs.
- Exercise accepted S01's actual CPU tokenizer repair path where dependencies permit, beyond previous registry comparisons and naïve-append counterexamples.
- Continue source-grounded attention/indexer work, stopping each branch when evidence resolves it. Unknown ROI remains unknown; no quota of accepted ideas.

## Code verification

Research suite: **281 tests and 25 subtests passed**. Bootstrap dry run and whitespace check passed. This verifies research-tool behavior, not GPU serving or hypothesis efficacy.
