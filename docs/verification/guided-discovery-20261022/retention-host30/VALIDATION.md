# HS30 isolated retention validation

Status: ready for parent review; canonical application not performed.

- One new deferred direction, two alternatives in the same card. Isolated hypothesis count **138 → 139**.
- Exact reused planned baseline: `baseline:d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279` (Flash-1017, c455786, B200, TP1/DP4/EP4). No historical DP8/model substitution.
- Hypothesis: `hypothesis:74a743094d0a39de5eeedbbd14282681bb17d593df59680ec5d7bc114c2f43f5`.
- Six exact-revision claims; two **inconclusive** CPU results. Current code's existing duplicate-insertion checks and precomputed-hash lookup are retained as counterevidence. No performance estimate or implementation promotion.
- 51 searchable source documents/revisions: 19 existing PR/issue results, 21 title-level paper identities, four queries, five exact code documents, one paper fulltext and one abstract page. All 19 local retrieval edges retained. No assertion that all title-only papers were read.
- Failed arXiv receipt stays failed. Original first complete web response is not locally recoverable; title triage and second complete response are retained with that limitation.
- 65 frozen artifacts, including original study, root review, correction and preparation/import instructions.

## Executed checks

1. Default local snapshot and actual restore at a different root; all 65 artifact digests resolved (35 direct, 30 content-addressed text fallback).
2. Both reviewed standard-library AST probes replayed from restored bytes and reproduced their saved JSON exactly. This is source-fixture reproducibility, not production allocator/runtime verification.
3. All 51 restored source IDs have exact document revisions and FTS rows. An isolated newer current query document remained current while the original failed revision was retained.
4. Complete retry did not change hypothesis/node/event/test counts.
5. Injected interruption after typed retention resumed with the same typed counts.
6. A conflicting existing artifact was refused before memory writes.

The partial-retry test covers one meaningful typed-stage interruption, not every possible crash boundary. Command journals can append entries on retries; corpus, archive and memory stores are not one transaction. Source objects, claims and prior node payloads are checked before mutation and under the writer lock. Counts are read under that lock. No cloud calls, GPU calls, canonical mutations or runtime patches occurred.

## Apply only after review

```sh
/Users/shreyas/workspace/AutoResearch-Inference/.venv/bin/python /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/retention-host30/import_packet.py --apply --allow-canonical-import --state-dir /Users/shreyas/.local/share/inference-autoresearch --defer-checkpoint --output /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/retention-host30/canonical-readback.json
```

`--defer-checkpoint` only marks pending checkpoint publication. It does not upload or create a snapshot.
