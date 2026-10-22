# Guided discovery checkpoint17

The discovery loop remains CPU/source-only. No GPU experiment, model launch, serving change, training or measured inference improvement is reported here. This checkpoint packages completed work; it does not create a new hypothesis or promote an implementation.

## Round50: useful components, inactive-path caveat

[Author report](round50/REPORT.md) and [independent review](round50/INDEPENDENT_REVIEW.md) retain two distinct components from FlashInfer#6429:

| Component | Exact proposed delta | Why it remains deferred |
|---|---|---|
| P50-01: sparse metadata→logits launch overlap | Release the native metadata grid early, enable the consumer's programmatic launch, and preserve its existing wait before metadata access. | The pinned sparse-indexer flag defaults off. No active-route, producer-tail, graph-edge or useful-overlap evidence is attested. Metadata schedules are reused, so savings cannot be multiplied across all consumers. |
| P50-02: paged key-data cache hint | Compare a fixed evict-first hint with the native hint while preserving addresses, predicates, scale loads and graph shape. | Key reuse and interference are unknown. The donor's constructor-time mean-context policy is not a portable performance rule; its host `.item()` is not proposed as a per-step policy. |

The source's warning about the sparse path below roughly32K contexts is upstream guidance, not a new benchmark. Enabling it simply to obtain a small potential PDL saving on the8K workload changes the baseline and is unjustified. The dense-path follow-up also stopped: its metadata release already exists and its producer placement differs from the donor's inline pair.

Evidence scope:27 donor file entries retained, selected pinned target/donor/DeepJIT files read, official PDL documentation retained, and seven inert host-policy cases plus a mutation control. The independent reviewer verified all75 frozen author files and read the critical dependency chain; no CUDA execution or sanitizer reproduction occurred. No extra paper query was run solely to decorate a source audit. Next useful evidence is actual route exposure, not more synthetic examples or a donor-percentage forecast.

## Writer timeout: verified tool responsiveness

[Timeout v3 report](writer-timeout/REPORT.md) and [independent review](writer-timeout/INDEPENDENT_REVIEW.md) cover the observed local-search stall behind a publisher holding the shared writer lock.

`researchctl --lock-timeout 2 ...` and the equivalent MCP startup setting bound acquisition wait. Omission preserves indefinite blocking; zero tries once. A busy attempt returns static `writer_busy` before starting the command or journal. Only documented contention errno values are treated as busy. The option does not shorten publication, bypass locks, limit command runtime after acquisition or change existing queued jobs.

- Required suite:358 tests and29 subtests passed; bootstrap dry run and diff check passed.
- Thirteen focused tests include actual CLI/MCP calls, a separate-process lock holder, unchanged initialized-state hashes on failed acquisition, default blocking, release-before-deadline success, secret-negative controls and a pre-retry deadline check.
- Independent review reran all13 focused tests and additional acquisition-only clock/error controls. No live canonical timeout smoke or publisher manipulation was performed.
- Root/lock-file creation can precede acquisition; the claim is no journal/command mutation on failure, not literally zero filesystem effects.

## Canonical local retention closed out

The earlier waiting packages have now completed production import/retention through the normal writer lock:

| Retained scope | Verified canonical local coverage |
|---|---|
| Round41 |59 artifact references /22 immutable source revisions|
| Rounds43–44 |96 artifact references /68 immutable source revisions|
| Rounds46–49 |162 artifact references /129 immutable source revisions|
| QH45 |33 source documents /34 exact content revisions /101 artifact references, backed by91 unique retained text blobs|

The first three rows are source-only operations with no hypothesis selection changes: [chain closeout](canonical-retention17/CHAIN_CLOSEOUT.md). Counts are packet-specific and may overlap; do not sum them into a unique-corpus total.

[QH45 closeout](canonical-retention17/QH45_CLOSEOUT.md) verifies its exact baseline and latest independent **deferred** decision, all13 expected typed identities and two evidence-link operations. It preserves an already generated direction, not an additional idea count. Five preexisting OpenAlex revisions keep their earlier `fetched_at`; their content and other fields match. No CPU evaluation command was executed merely because its evaluation plan was registered.

**These are verified local retention results.** Commands used `--local-only --defer-snapshot`; this checkpoint does not verify a subsequent snapshot, remote S3 HEAD/object coverage or restored VM. Independent isolated restore tests in older packets remain isolated evidence. Do not equate canonical presence, delivery copies or pending publication with a new S3 durability guarantee.

## Accepted diagnostics are not accepted implementations

The existing [accepted-diagnostic re-audit](ACCEPTED_DIAGNOSTICS_REAUDIT.md), preserved unchanged, distinguishes two historical CPU-investigation selections from current implementation readiness. S01 is parked pending exact service exposure/admission; DA01 is parked pending physical-receive evidence. Three historical accepted decision records concern two hypothesis IDs. Neither count establishes a service improvement.

[Copy manifest](source-copy-manifest-17.json) records the18 delivered files and original hashes. [Source verification](source-verification-17.json) records six checked frozen manifests plus the unchanged re-audit hash. Original author reports, independent reviews and operational closeouts remain separate. No database, credential, model weight or large paper fulltext was copied into Git.
