# Preserve selected historical source-revision identities

An actual retention audit found one old paper revision whose hash included retrieval_query metadata; the current formula excludes it. The historical revision and its original bytes remain valid. An isolated regression then showed a tool bug: claim(record with explicit old revision) loaded the correct old row but replaced its key with a recomputed fingerprint that was absent from the revision table. That created an unresolvable source reference.

## Change

`ResearchFlow.claim` now selects the actual stored immutable revision key for explicit selection and for the latest source. It reads and verifies the quotation against that row. Missing revisions fail before writing a claim; the operation does not silently invent a modern identity or migrate the source.

Dossier review alerts compare current and pinned source contents using the current semantic fingerprint. Changing only the hash formula therefore does not masquerade as a scientific source update. Actual changed body/metadata still triggers review. Original claim and revision records remain immutable.

This change does not repair prior malformed claims, migrate the corpus, or alter `changes()`'s identity-based observed-revision feed. Older source rows without any retained immutable revision must be refreshed/imported before claims can reference them. It does not affect the current EM75/PC76 claim IDs because those new claims use ordinary current revisions.

## Verification

The new historical-metadata regression failed before the change. It now verifies exact selected-key resolution, default latest-legacy selection, idempotent claim identity, unchanged historical encoded bytes, missing-key no-write failure and real-content versus hash-format alerts.

36 focused research-flow tests passed. The required CPU research suite passed385 tests and29 subtests; bootstrap dry-run and diff check passed. An independent reviewer reran36 focused tests and five separate isolated controls, including a historical-only quote, substantive metadata change and explicit old revision after the latest source row is absent. Reviewed source hashes match the current files.

No network, canonical-state migration, GPU/native backend or serving performance test was part of verification. This fixes provenance reliability, not hypothesis quality or inference performance.
