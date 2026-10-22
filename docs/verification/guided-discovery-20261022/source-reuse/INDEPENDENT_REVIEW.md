# Selected-source import independent review

## Verdict

**No remaining blocker for the stated local SQLite selected-source import after the incident-edge correction.** I read the real foundation importer, Store revision/index/edge behavior, MCP wrapper, CLI parser, selected tests, and actual retained-source replay script/receipt. I made no canonical writes or provider/cloud requests. Author owns code edits.

## Found, reproduced and fixed

The initial implementation filtered incident edges by selected source/destination/evidence IDs, but only tracked freshness for selected documents. Source old B linked selected A; destination newer B removed that link. Importing only A preserved B's newer body but resurrected old B→A as an active `links_to` edge. `incident_edge_probe.py/json` preserves that independent counterexample.

Author fixed derived incident-edge admission by comparing source/destination evidence documents even when the evidence ID is unselected, caching results. Historical `discovered_by` provenance remains importable. I read the correction and reran the exact independent reproducer as `incident_edge_probe_after.py/json`: no stale edge, one historical-derived edge skipped, newer body unchanged. The original receipt is preserved. Author regression additionally covers `child_of` and provenance preservation.

## Verified properties

- SQLite source uses URI `mode=ro` and a read transaction. The source is not opened through writable Store. Source state/records are not modified by the importer; this does not claim absence of SQLite sidecar/locking activity on every filesystem.
- Selected IDs are bounded to 1..100 nonempty strings, deduplicated and bound as SQL values. SQL text contains only fixed fragments and generated `?` placeholders; quotes/operators in IDs cannot inject clauses.
- All selected IDs must be found before destination `BEGIN IMMEDIATE` or corpus writes. A mixed present/missing selection fails as a whole. This promise concerns corpus writes, not the enclosing command's normal journal/lock bookkeeping.
- Document/revision/edge writes share one destination transaction; exceptions roll back that corpus transaction. Store.put does not commit internally. Publication/checkpoint failure after the corpus commit remains the existing separate lifecycle, not an atomic cloud transaction.
- A strictly newer destination current record is preserved, while incoming original content-hash revision receipts and historical revisions are retained. FTS updates flow through Store.put when current documents are imported. Equal-date behavior follows the pre-existing merge policy; no new conflict-resolution algorithm is claimed.
- Selected imports exclude checkpoints entirely. They do not copy credentials, HTTP caches, refresh cursors or unrelated documents. Incident edge endpoints can remain unresolved, explicitly stated on CLI/MCP/receipt. Derived edges incompatible with known newer evidence are now skipped.
- Selected JSONL input is explicitly rejected; omission of the selector retains whole-file legacy import. This is not a silent fallback to importing all records.
- MCP exposes a separate `import_sources(source_corpus, source_ids)` tool and builds structured argument arrays. It does not call investigate/online discovery. Default server mode is local-only; a server configured to publish may still publish its normal checkpoint. “No network refresh” should not be read as forbidding an explicitly enabled S3 publication.
- Exact retained source inspection via `source_show` is the appropriate next action. `investigate` can perform retrieval separately and is not made offline by import.

## Independent verification performed

1. Executed the isolated incident-edge counterexample before and after the fix. Temporary local databases only.
2. Read actual `tool-source-reuse/replay-receipt.json` and its replay.py. Independently opened the isolated replay DB read-only using the repository Python and verified both document bodies/hashes, current revisions, both sets of retained revisions, original fetched timestamps, exactly two documents and zero checkpoints. See `receipt_readback.json`.
3. Ran only the focused tests for selected-source import plus the new MCP tool surface: **6 passed**, 0.42 seconds. Did not repeat the broad suite.
4. Author replay patched **socket.create_connection**, with zero calls and no HTTP-cache directory. That is bounded instrumentation, not a general socket/syscall audit. Combined with source inspection it supports no provider refresh in this execution. It does not establish paper freshness: the retained full texts are unversioned observations.

The initial attempt to read the isolated DB with the shell's system python failed with SQLite “unable to open database file”; rerunning through the repository .venv Python succeeded. No source/corpus changes were made to work around it.

## Limits

No concurrent-writer stress test, process-crash injection, cloud publication test or general malformed-database fuzzing was performed. Legacy revision collisions use INSERT OR IGNORE as before. A successful same-content retry can still record another command receipt and reapply an equivalent current projection; it is record-idempotent, not a guarantee of zero filesystem writes. Source paths are explicit local inputs authorized by the caller; this change does not sandbox all paths.
