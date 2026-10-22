# Independent optional search explanation review

Verdict: no blocker in inspected patch. The optional surface makes the observed wrong-kind/empty-page failure diagnosable without relaxing filters. It does not establish better retrieval relevance, recall, ranking or upstream completeness.

## API and behavior

`Store.search(explain=False)` retains the list result and the same lexical expansion, predicates, rank/order, ID tie break, limit clamp and offset. `explain=True` wraps the identical hits with matching count, applied query/filters, page continuation, kind counts and warnings. Repository source-scope counts intentionally ignore query/date/state/kind filters, so they describe available kinds in the repository rather than matches. An empty query match in a populated, correctly typed corpus gets no misleading ingestion warning. Unknown kinds remain literal, including pull_request, uppercase, whitespace and SQL-like strings; no aliases or automatic retries are introduced. Source completeness is explicitly disclaimed. Counts may cost additional local scans; no performance claim.

Foundation search/pr-search forwards the flag, pr-search still fixes kind=pr. Legacy corpus CLI forwards parsed arguments to Store. MCP defaults to its existing {hits: list} envelope and returns the richer object only when requested. Existing test executes real foundation and MCP handlers and checks parity. The retained-corpus absence test concerns read-only Store: absence raises and does not create a file; this does not claim every existing CLI entrypoint refuses to initialize an empty store.

## Transaction safety actually checked

The SAVEPOINT covers hit rows, matching count and source-kind counts. An independently executed temporary SQLite probe committed a second document through another connection during first-hit decoding: the first response consistently showed one hit/count/scope record; the next call saw two. It preserved an existing read transaction and a caller savepoint with the same name. Pending writes remained rollbackable. A deliberate decode exception released the tool savepoint without committing the caller’s pending update. Missing read-only corpus was not created. Invalid offsets rejected; clamped limits and past-end pages reported honestly.

These are local SQLite transaction/API checks, not production contention benchmarking. No canonical database, network or GPU calls were made. The optional diagnostics read current records, not historical revisions; separate page calls can change during ingestion.

## Verification

Executed the retained independent probe once and the three focused author tests: 3 passed. Inspected all four changed implementation paths and tests; source hashes are retained. No edits made to production files. No broad test rerun or quality-gain inference.
