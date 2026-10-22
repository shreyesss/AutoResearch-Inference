# Additive correction: exact predecessor and yield

This note supersedes the new-intervention interpretation in the frozen author report; it does not modify that report or its manifest.

The independent reviewer identified an exact predecessor, not merely a related EG02 card:

- `engram-projected-cache-preflight/REPORT.md`, SHA256 `7bf0f5707d8111d978b5a78a2ff5198dff82c5043e09129f5a75799f42863271`.
- `engram-projected-cache-preflight/online-followup/ADDENDUM.md`, SHA256 `877fef3a6a183d10011212714438ad9103acf2361ab0ff5be866aa4db79fff27`.

Both already describe caching the complete pre-gate WKV result with the ordered24-head key,50KiB output, miss-compaction/numerical conditions and the missing representative execution trace. Round51 contributes a newly selected dependency/amortization paper, **zero new interventions**, and zero resolved service-exposure or native-correctness gates. No new card or status change was made.

The review also makes storage ownership, per-request adapter eligibility, hit-path output materialization and the active local-table/EngramBatch branch explicit. A cache entry cannot alias recycled workspace, and private hits cannot independently suppress collective participation. These remain integration requirements, not validated implementation.

Initial retrieval diagnosis found the earlier reports missing from searchable source documents/revisions. The reviewer then noticed that its read-only helper used SQLite immutable mode, inappropriate for a live WAL database, and requested a WAL-aware recheck. Treat the initial absence conclusion as provisional until the additive live-read receipt resolves it. Root reproduced the separate WAL visibility defect in an isolated regression test and is correcting the library default while preserving explicit immutable replica reads.

The useful next step remains locating representative exact-target execution evidence; a repeated capacity calculation or another generic cache paper does not advance this intervention. Preserve both old reports and this correction in searchable source memory, with analysis provenance distinct from primary evidence.
