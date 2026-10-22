# Live read-only corpus visibility correction

## Observed issue and bounded fix

While reviewing the missed projected-Engram preflight, the reviewer noticed that `Store(readonly=True)` always set SQLite `immutable=1`. That mode can ignore a live database's committed WAL. This was a separate audit defect; it did not establish that the missing-report diagnosis was false. A subsequent WAL-aware canonical check still found those two reports unindexed.

An isolated regression reproduced the library defect: initialize a corpus, checkpoint its schema, disable automatic WAL checkpointing, commit a report with FTS/revision rows, keep the writer open, then read with `Store(readonly=True)`. Before the change, `get` returned None for that committed report. `before.txt` preserves the actual failed test.

The default read-only constructor now uses `mode=ro`, which observes committed WAL and rejects writes. An explicit `immutable=True` option requires `readonly=True` and is used by the existing two frozen-replica callers in `foundation.py`. Ordinary CLI canonical search continues to use its normal Store under the writer lock. No writer lock, source ranking, query syntax, schema, publication or hypothesis policy changed.

Read-only means no database writes, not no filesystem bookkeeping. SQLite may use shared-memory and lock state for a live WAL reader. Immutable access is for a sealed, unchanged, checkpointed source only; callers must not label a changing corpus immutable.

## Verification actually executed

- Before fix: one isolated WAL visibility regression failed at missing committed report.
- After fix: three focused tests passed. The live reader sees the document, FTS hit and immutable source revision, and rejects DELETE. A frozen replica reads without creating/changing sidecar file contents and rejects writes. Invalid immutable mode and missing read-only path do not initialize a database/directory.
- Full required research suite: **361 tests and29 subtests passed**. Bootstrap dry run and diff check passed.
- No canonical DB mutation, provider call, GPU or native serving execution by these tests. This is source-library visibility correctness, not a retrieval-quality or service-performance benchmark.

The related discovery skill now requests report recall in addition to formal-card recall before counting a campaign-new intervention, distinguishes missing ingestion from ranking, and scopes filesystem fallback to declared campaign reports. It does not require scientific novelty or force every search through a fixed sequence. Its actual development-case repair is documented separately by the adversary's before/after ingestion receipts; no general hypothesis-quality claim follows.

Skill validation initially lacked PyYAML in the project and system interpreters. The bundled quick validator then passed using a cached PyYAML package installed only under `/tmp/autoresearch-skill-validator-deps`; project dependencies were not changed.

Independent review is pending at author freeze. Exact code/test/doc/skill copies and hashes identify this revision.
