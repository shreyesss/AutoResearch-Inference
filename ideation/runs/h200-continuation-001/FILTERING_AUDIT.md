# How the sources were filtered, and what this scan establishes

The earlier work was a relevant, bounded research pass. It was **not a
comprehensive semantic review of all PRs/issues** and did not measure retrieval
recall. We should judge coverage by explicit topics, repository/date scope,
acquisition depth and missed-source audits, rather than by download count.

## Earlier selection

1. The supplied CSV contained 5,532 URL/title identities across 13 repositories.
   The B200 audit applied conservative rules to titles and catalog fields:
   hardware/model exclusions, inherited negative labels, release-membership
   checks and family assignments. Selected primary reviews overrode rules.
   `auto` rows remained deferred. These were not 5,532 independent semantic reviews.
2. The fresh H200 pass reopened the original catalog without inheriting B200
   applicability filters. Its local search used nine query families across those
   repositories: hardware, model, attention, speculation, communication, host,
   scheduler, fusion and negative evidence. Each query returned at most 35 hits.
   Common terms and ranking could hide relevant older or differently named work.
3. Live opening-feed discovery covered a four-day window, with page caps. Broader
   web queries emphasized Hopper/performance/DeepSeek. Source packets were then
   hand-selected for four mechanism lanes. SGLang was supplemental, not an equal
   historical corpus; DeepInfer was absent from that original repository set.
4. The completed pass retained 108 selected pages and 69 patches across 16
   repositories. Its visible HTML discussion was not an exhaustive review/reply
   archive. A complete disposition ledger meant every input had a recorded
   disposition, not that every changed implementation had been inspected.

Evidence: [original triage code](../pr-evaluation-audit-001/scripts/build_audit.py),
[fresh discovery code](../h200-fresh-research-001/scripts/discover.py),
[packet selection](../h200-fresh-research-001/scripts/prepare_lanes.py),
[original repository coverage](../h200-fresh-research-001/REPOSITORY_COVERAGE.md).

## This pass

The acquisition scope is public openings updated since **13 October 2026 UTC**
for 16 repositories, plus an all-state opening enumeration for the newly released
DeepInfer repository. A first collection and an explicit cursor-resume pass
retrieved/refreshed **2,202 opening records** across 17 repositories. These are
not 2,202 unique additions to the pre-existing corpus.

| Repository | Openings retrieved/refreshed | Reached end of requested feed? |
| --- | ---: | --- |
| DeepInfer | 95 | Yes, all-state endpoint at capture time; all returned records were PRs |
| vLLM | 600 | No; continuation cursor retained |
| SGLang | 500 | No; continuation cursor retained |
| InferenceX | 400 | No; continuation cursor retained |
| FlashInfer | 400 | No; continuation cursor retained |
| DeepEP | 19 | Yes, bounded update interval |
| DeepGEMM | 17 | Yes, bounded update interval |
| DeepJIT / DeepSelect / DeepSpec / Engram | 6 / 1 / 1 / 1 | Yes, bounded update interval |
| DeepSeek FlashMLA / TileKernels | 3 / 3 | Yes, bounded update interval |
| deepseek-recipe / vLLM recipes | 43 / 78 | Yes, bounded update interval |
| Humming / vLLM FlashMLA | 30 / 5 | Yes, bounded update interval |

The full local ledger scans **8,908 distinct identities** without a per-query
result cap, using titles and available opening bodies. **1,122 remain title-only**.
Fourteen overlapping topics cover speculation, graph shapes, attention/indexers,
MoE compute, mHC/fusion, communication, host memory, scheduling, cache/routing,
load balancing, correctness, evaluation, quantization and compatibility/releases.
Matching a topic does not prove relevance or implementation eligibility.

A deterministic 40-entry sample from the first scan's 627 unmatched records
exposed real vocabulary omissions: RoPE initialization, FP8 cache quantization,
paged-MQA out-of-bounds handling, bank conflicts and release bundles. Eight leads
were explicitly reopened for source or correctness inspection. The expanded
queries retain 525 unmatched entries in the final, larger corpus; **none are
automatically excluded**. This sample guided query repair, so it is not an
independent recall estimate or evidence of exhaustive coverage.

Close acquisition retained 28 selected opening/page records and 26 proposed
patches, including 14 DeepInfer PRs. Other DeepInfer openings remain explicitly
review-deferred in the [95-row ledger](DEEPINFER_DISPOSITIONS.csv). Focused
evidence extraction uses 20 sources plus a three-source update for the new C24
verdict, CPU probe and fused-sampler gates; paper full texts and installed-code
excerpts are included. Selected-source review remains a smaller set than discovery.

## Remaining gaps and continuation

- Finish the four capped feeds only if the next research question benefits from
  more of their interval. The exact opaque next URLs and prior receipt revisions
  are saved. A bounded resume advances rather than restarting those feeds.
- Inspect deeper bodies/diffs for title-only and unmatched candidates when they
  can change a decision. Generic release and correctness titles need special care.
- Follow DeepInfer's referenced fork issues where necessary. Its endpoint returned
  PRs; that does not imply there are no relevant issue discussions elsewhere.
- Full comments, reviews and every historical patch remain outside this pass.
- Before claiming retrieval recall, build a separately labeled, held-out topic
  set. Before claiming research superiority, prospectively compare equal-budget
  portfolios against a baseline selector, preserving all failed/inconclusive work.

Reproducible artifacts: [feed receipts](discovery/feed-coverage.json),
[compressed opening snapshots](sources/feed-openings.jsonl.gz) with
[hash/count manifest](sources/feed-openings-manifest.json),
[topic ledger](discovery/topic-ledger.csv),
[topic matrix and patterns](discovery/topic-coverage.json),
[missed-source audit](discovery/unmatched-sample-review.json),
[primary manifest](sources/primary-manifest.json), and [collector](scripts/collect.py).
`collect` reuses saved receipts; `resume` makes one bounded increment and archives
the previous receipt; `scan` reruns local discovery without network calls.
