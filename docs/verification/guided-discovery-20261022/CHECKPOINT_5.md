# Guided discovery — checkpoint5

22 October2026. Active CPU/source loop; no GPU queries, models, experiments or serving changes. All performance claims below are source reports or conditional reasoning, not our serving results.

## A negative branch retained in full

The lossless-cache branch used two recent-paper searches, then deliberately followed one older named citation after reading the newer papers. Seventeen papers were screened and three mechanisms read in full. It produced three concrete interventions, preserved even though none is implementation-qualified:

| Card | Intervention examined | Decision and decisive evidence |
|---|---|---|
| LC01 | Direct D-Quant fixed-record entropy codec while preserving current resident KV bytes | Rejected as scoped: the published fixed-size guarantee uses controlled value drift. Dropping that step requires overflow/fallback storage and a different sparse reader. This does not reject lossy research generally. |
| LC02 | Direct AlignPred exact resident-cache restoration port | Rejected as scoped: residual quantization is error-controlled, and persistent restoration differs from the current resident packed-cache path. Retain it for a future actual restore workload. |
| LC03 | Direct SplitZip lossless compression of resident FP8 rows | Deferred: paper E4M3 results expand storage; released code has whole-buffer decoding and dynamic allocation. Actual target byte entropy, indexed-read cost and memory pressure are unknown. |

The integer model reconstructed all65,536 possible16-bit words with escapes. That establishes a limited bit-decomposition property, not GPU codec correctness or useful target compression. Executing the donor's size-accounting property on synthetic528-byte objects gave both compression and expansion:396 vs1964 bytes. Existing fixed-size cache allocations would not automatically release memory after merely compressing their contents.

**Useful next evidence:** an already-existing, correctly identified Flash-1017 cache dump could support a CPU entropy/payload/random-access diagnostic. No new GPU capture is requested. Broad future lossless methods remain an open question; the rejected direct ports do not prove impossibility.

[Mechanisms and evaluator mapping](round13-lossless-cache/REPORT.md) · [Independent review](round13-lossless-cache/INDEPENDENT_REVIEW.md)

## Yield without excluding failures

Through round14: **29 screened intervention cards:2 accepted bounded CPU plans,20 deferred,6 rejected,1 duplicate;0 service-qualified improvements.** Round13 is one explored mechanism family with three distinct proposed ports, not three independently successful research branches. Its17 source screens are a separate denominator. A deferred card can have a real source gap and a useful future experiment; it is not an implemented or measured optimization.

The strongest concrete source gaps from earlier rounds remain PJ01's discarded DSpark context-Q outputs, AT03's repeated compressed-KV materialization, RD01's physical expert-weight placement and EG01's representation conversion. Their runtime eligibility and expected service value remain separate unresolved questions.

## Deployment and persistence checks

A bounded read-only Docker metadata check succeeded on bitlane-b1 and found only node-exporter among running containers. That leaves no running vLLM container revision to attest through this check. It says nothing about bare-metal processes, GPU activity or other nodes. No GPU probe was performed. [Exact receipt and scope](deployment-metadata-check/REPORT.md).

Canonical imports through round14 have completed. Independent read-only checks verified **140 archived file hashes, 17 exact source quotations, 47 paper revision/query references and four inconclusive CPU results** for rounds12–14. PJ01 and TR01 remain deferred; LC01/LC02 remain rejected as scoped and LC03 deferred. [Readback receipt](canonical-round12-14-readback.json).

S3 snapshot `e05b413d4ff55f30bbe532094151622e32733ad698f696aecfa3739a1b607acc` successfully published the earlier database state and selected files through rounds5–9 and round11. It excludes rounds12–14. The default archive policy omits some raw source/replay file extensions; a separate completeness audit is underway. Publication does not yet prove every replay script can be restored. [Receipt and explicit scope](publication-checkpoint5-11.json).

The query-domain field study is being imported through the standard corpus-import command, including its exact receipts and review as source records; that command's completion/publication is not claimed yet. No VM restoration was checked. [Persistence status](STATE.md).

## Context-row direction: useful source gap, weak objective exposure

TR01 is a deferred, low-priority selective port of upstream vLLM #60320. Pinned c455 prepares DSpark context projections for rows that cannot be read by the finite-window draft. The initial adaptation preserves the captured graph prefix and full hidden-state combination, so it cannot inherit the donor's component timing.

The standard agent-p75 workload changes the priority: a single conditional warm 2048-row span drops only1915 rows, below the donor's2048 aggregate-drop threshold. Two such prefills in one eligible batch may cross it. Ordinary small decode spans do not. Source defaults can make the draft cache groups non-prefix-cacheable while retaining global prefix caching, but actual effective runtime groups remain unattested. Never turn prefix caching off just to activate this change.

The donor's reported TTFT confidence intervals all include zero despite large context-path savings. This is counterevidence against presenting the change as a likely long-output ITL win. Its useful next step is a bounded compatibility/exposure check, not another invented percentage.

[Full mechanism and evaluation](round14-context-rows/REPORT.md) · [Workload threshold and packing costs](round14-context-rows/WORKLOAD_REFINEMENT.md) · [Independent workload review](round14-context-rows/WORKLOAD_REVIEW.md).

PJ01 column removal and TR01 row removal share the projection denominator: compare baseline, columns only, rows only and both where eligible. Do not add their arithmetic savings. Round14 contributes one direction; its workload refinement adds no extra hypothesis.

## Continuing questions

A new paper-led branch targets sparse-attention/indexer data movement, with separate adversarial review against prior work and pinned code. The bounded search-method check reduced off-domain abstract hits from6/8 to0/8 under independently applied criteria, while yielding no deployment-qualified idea. The discovery skill now includes ambiguity-aware Boolean anchoring; an isolated forward planning test produced valid queries without network calls. [Field check and limits](query-domain-audit/REPORT.md). Round15 science remains separate from this checkpoint count until frozen.

## Verification of this checkpoint

The discovery skill passed its syntax validator in an isolated environment. The independent forward check exercised actual `expand` planning, not online retrieval. Repository gate: **267 tests and11 subtests passed**; bootstrap dry run passed. These are research-tool checks. No serving code changed and no GPU experiment ran.
