# Checkpoint34 — two narrowed components and cheaper opportunity screening

Discovery continues on pinned Flash1017/c455 source, with no GPU/native execution.
This batch retained **two low-readiness components and one evaluation refinement**.
Neither component is an implementation-qualified improvement. No new typed
hypothesis, accepted implementation or measured service win is counted here.

## Boundary-only index-K: real discarded work, small affected surface

The target projects every latent row through a512→128 matrix before a cache
writer discards invalid slots and non-compression-boundary positions. Computing
only useful rows could remove work, but source/configuration inspection narrows
the opportunity to ratio-2 owning layers **2,8,14**. It does not affect every
model layer, every indexer or the much larger compressor projection.

A direct every-other-row slice is wrong for ragged requests and differing start
positions. The original latent also feeds main-cache insertion, so it cannot be
compacted in place. A K-only packing/map must retain original positions and slots,
avoid extracting dynamic counts to the host, and actually reduce the native GEMM
shape. One-token requests can require the same padded capacity as before. Small-M
minimum tiles, unchanged weight reads, packing and existing overlap can erase the
benefit.

The recent-paper query mostly revisited known selection families. The new
component came from source inspection; it is not credited to a paper that did
not propose it. The selected FlashInfer training-indexer PR has different key
format and rounding requirements and is not a drop-in native replacement.

**Next useful check:** a concrete fixed-capacity packing or producer layout that
preserves both consumers and removes executed work. An optional producer-fusion
arm is being inspected separately; no serving patch is claimed.

[Mechanism and scoped evaluation](round92/REPORT.md) ·
[Independent review](round92/INDEPENDENT_REVIEW.md)

## Engram row co-location: reject the easy bandwidth story

The native host allocation places all FP8 values before all scale bytes. Each
selected row needs256 value bytes and8 original UE8M0 bytes. Interleaving each
row's unchanged payload and scales is source-distinct from output staging or
hot-row caching, but does not automatically reduce transfer traffic.

Under the documented address model, separate planes and264-byte records both
touch nine unique32-byte sectors per isolated row. Interleaving also misaligns
most value loads; the independent review finds a larger average sum of the two
load-instruction address footprints. Neither number is a hardware transaction
count. The remaining possible advantage is page-translation locality, which
scale-page reuse, huge pages, sorted batches and overlap may eliminate. For512
consecutive rows, both layouts touch the same33-page union in the model.

The recent N-Gram Memories paper supplies a useful row-locality question, but its
compressed trellis layout and quality results do not establish a native FP8
co-location win. Its codec is post-training compression, not neural retraining;
adopting its altered values would still need a separate quality contract.

**Disposition:** low-priority component. Loader strides, pinned UVA ownership,
registration/reload/capture lifetime and exact output ordering need explicit
integration. Establish exposed translation cost before paying that complexity.

[Source analysis and controls](round93/REPORT.md) ·
[Independent alignment review](round93/INDEPENDENT_REVIEW.md)

## Incomplete metrics can still give useful bounds

Round91 showed that scheduler acceptance metrics do not generally identify FV86's
actual full-admission passes under AV. Round94 adds a useful qualification.

Let accepted drafts be a, hidden admitted drafts m, and valid scheduled drafts s.
When the exact source/count mapping gives `a <= m <= s`, and the native eligible
branch is established, `a=s` forces a complete pass. In particular, accepted5
under the five-draft ceiling identifies a complete five-draft event. The native
placeholder stop also establishes validity for that proven event; do not demand
a redundant new validity counter.

| Existing observation | Removable interior-row bound |
|---|---|
| Paired a,s; verified eligibility | Lower: `max(a-1,0)` if a=s, otherwise0; upper: `max(a-1,0)` |
| Fixed-five accepted histogram H | Lower: `4*H_5`; upper: `sum(max(j-1,0)*H_j)` |
| Only N verification observations and A accepted drafts | Relaxed lower: `4*max(0,A-4N)`; upper: `A-ceil(A/5)` |
| Eligibility unknown | Positive lower bound is unavailable |

N counts compatible **verification observations**, not requests. Counter resets,
worker/time populations, grammar adjustment, bonus conventions and rounded means
must be handled correctly. Extra AV constraints may tighten these relaxed bounds.
Source constraints alone do not establish that a concrete run retained such data.

The CPU enumerator checked21 single pairs,9,261 observation triples and175,616
hidden assignments, plus54 aggregate cases. Independent review checked the
algebra and source boundary. No actual workload frequency was invented.

Use these bounds when they can decide whether additional observation is worth
collecting. Even exact removable-row counts do not identify exposed stage time,
flag overhead, HBM traffic or ITL. The calculation remains a small retained
script, rather than another general command without a real input artifact.

[Derivation and CPU control](round94/REPORT.md) ·
[Independent source/algebra review](round94/INDEPENDENT_REVIEW.md)

## Yield, state and continued work

- Round92: one dated query/ten paper identities; one retained selective fulltext
  reread; one PR hydrated with two selected patches read; one parked component.
- Round93: two queries/20 distinct paper identities; one newly fetched versioned
  fulltext; one body-level neighboring PR screen; one low-priority component.
- Round94: no provider call; one existing-counter evaluation refinement.

These are per-lane counts, not globally unique corpus coverage or a success-rate
claim. Independent reviews checked the quoted sources and narrowed the proposed
benefits. No performance gain is inferred from arithmetic or self-scoring.

Git delivery and canonical/S3 retention remain separate. Read-only process
inspection found81 waiting in `flock`, behind the existing backfill process's
publication interval. Network waiting/activity was observed; a fresh upload
completion was not. The controller is not executing retention slowly, and its
presence alone is not forward progress. No lock was forcibly released and no
competing writer was started. [Diagnosis](retention-34/CONTROLLER_WAIT.md).

Recent operator-fusion literature and the index-K producer arm remain active
research branches. A separate fixed-case test is examining whether a proposed
critic-skill paragraph improves counter-based decisions; no improvement claim or
skill change is made before its results.

[Frozen source packets and exact copies](source-copy-manifest-34.json)
