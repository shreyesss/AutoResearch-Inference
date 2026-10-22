# Guided discovery — checkpoint 7

22 October 2026. Active guided research continues; no GPU queries, experiments,
profiling, model loads or serving changes.

## Yield

Through frozen round17: **32 screened intervention cards: 2 accepted bounded CPU
investigations, 22 deferred, 7 rejected, 1 duplicate. Zero implementation-qualified
or service-qualified improvements.** The extra card is a target-scoped child of
an earlier mapping hypothesis, not a newly discovered mechanism family.
Rounds18 and20 strengthen existing S01 and add no hypothesis identity. Round19
is still under review and excluded from this denominator.

Round17 returned 33 paper rows / 31 explicit identities, read three full texts,
and narrowed one useful component. These are per-round counts, not cumulative
unique paper counts. Failed searches and abstract-only screens remain distinct
from full-text investigation.

## 1. Recent papers changed the proposed mechanism

UlaCache's capacity/transfer headline does not match fully resident TP1/DP4.
Its own DP mode avoids the selected-copy buffer, and batch-one comparisons
against GPU-resident SGLang are negative. The reusable component is **access-plan
reuse across layers sharing sparse selection**.

MP17-01 asks whether physical Top-K mappings can be published once per eligible
index group. The pinned target already fuses mapping, counts and padding masks;
we are not proposing that fusion again. Conditional full-backbone arithmetic
gives 38 mapping calls versus eight publications, but those are not observed
calls or measured latency savings. Index groups refresh independently of KV
groups. Buffer lifetime, partial traversal, graph replay and final metadata
bindings determine correctness. It remains deferred and low priority.

Source follow-up found a useful cheap guard: actual attention-group members
receive the same metadata object. Bounded replay can replace the first layer's
entry, so eligibility must inspect the **final forward-context bindings**, not
assume original group membership. No live configured bindings were inspected.

AttnFuse did not establish a missing fusion on our selected source path. MLIPS
fresh scoring did not establish exact selection after candidate omission. The
full-text counterevidence and selective synthesis are in the
[round17 report](round17-attention-fusion/REPORT.md) and
[metadata addendum](round17-attention-fusion/source-closure/ADDENDUM.md).

## 2. S01 now has actual native CPU evidence

The pinned TokTier source was built in an isolated ARM/macOS environment, with
locked Rust dependencies. The exact Flash-1017 tokenizer was used. The original
artifact admission gate remains closed; this was an explicit diagnostic adapter.

- 2,818 complete repaired token-ID and offset comparisons matched HF.
- 2,813 cases used the Python splice path, backed by the real native encoder.
- Of 3,423 suffix attempts, 1,809 used Gigatoken and 1,614 used its intentional
  added-token HF fallback. Window retries explain the larger denominator.
- 2,710 separate full native encodes matched HF; many special-token cases used
  the embedded reference. This is not 2,818 independent serving workloads.

This removes the native-build blocker and replaces the earlier HF suffix proxy.
It does not test the native Rust session store, certify a Linux deployment,
establish session identity/lifecycle correctness, or demonstrate TTFT improvement.
Renderer rewrites still require full fallback. An independent corrupt-prior
negative shows that trusted cached-prefix integrity is a real precondition.

See the [native report](round20-native-tokenizer/REPORT.md) and
[independent splice review](review/round18/REVIEW.md). Bounded CPU timing is the
next diagnostic; no timing or service win is claimed at this checkpoint.

## 3. A promising donor was narrowed by dispatch counterevidence

vLLM #57977 can let MegaMHC emit FP8/scales directly into MegaMoE's staging
buffers, retaining BF16 for the router. This is absent from the pinned caller.
However, eligible FULL graphs with 1–16 captured query rows take an existing
overlap path that returns before the proposed producer. TP1 does not by itself
disable that path. Initial scope therefore covers only already-MegaMHC shapes;
disabling overlap is a separate intervention, not a free part of this proposal.

Independent CPU formula checks found equal scale exponents for all 32,640 finite
nonnegative BF16 amax patterns and equal shared-scale row mappings for 28,672
pairs. These are source transcriptions, not compiled kernel parity or performance
tests. Actual exposure, buffer ownership, numerical conversion and measured
benefit remain unresolved. [Review](review/round19/NUMERICAL_REVIEW.md).

## 4. Tool improvement and persistence

Repeated isolated-corpus imports were each triggering a bulk checkpoint and
publication under the writer lock. Added explicit
`--defer-snapshot import-corpus` so reviewed imports can join an interactive
batch, retaining source revisions, discovery edges and command receipts before
one final checkpoint. Default imports still checkpoint immediately;
`--local-only` now reliably prevents publication. This does not preempt a
publisher already holding the lock or promise durability before the checkpoint.

Research suite: **283 tests and 25 subtests passed**; bootstrap dry run and
whitespace check passed. Independent review ran 24 tests and eight subtests,
including real local snapshot/restore and configured-remote controls.
[Review](retention-round17-18/DEFERRED_IMPORT_REVIEW.md).

Canonical round15 import and the explicit 117-reference historical artifact
retention completed. Round16, the HTTP-diagnostic corpus import and round17–18
retention are queued/running; independent readback is in progress. A new local
restore audit is also pending. No repaired S3/VM restore is claimed.

Verified publication advanced to `b3e4baaeb9c14a19aa46f46aaccbfe796dbaf3aa62d7406ec98208c11c7e884d`
for the query-domain import. Its snapshot predates the round15/117-reference
writes and does not prove their backup. A later local snapshot is not yet proof
of publication. Native build binaries remain local and are not covered by the
text-artifact retention policy. Source-copy hashes are in
`checkpoint7-source-manifest.json`.
