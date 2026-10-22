# Local search diagnostics verified against an observed research mistake

Round55 used `kind=pull_request` and saw no PRs. Its corrected `kind=pr` searches worked, but one result list was capped at20. The prior help/skill change explained this; this change makes it observable in the tool response.

## Implemented

Optional `researchctl search --explain`, `pr-search --explain`, legacy CLI `search --explain`, and MCP `search_local(explain=True)` return hits plus total_matches, next_offset, applied filters, the effective alias-expanded lexical FTS expression, and kinds/counts in the selected repository/ID scope. Warnings distinguish a kind absent from that scope, an empty scope, and a page offset beyond the matches. The tool does not rewrite `pull_request` to `pr`, relax date/repository filters, or judge relevance. Defaults keep their previous result shapes and ranking.

Hits and diagnostic counts are read within one SQLite savepoint, including a caller's existing transaction. Separate calls/pages can see subsequent imports. Source-scope counts cover current retained records, not all upstream PRs, revisions, semantic recall or archive completeness. This optional mode adds count queries; default search does not incur that work.

## Actual replay

Six production Store.search calls used canonical mode=ro inside one outer read transaction. Each explained hit list was asserted equal to ordinary search under identical arguments. Current corpus may contain later records than original round55; this is not a frozen original-result benchmark.

| Query, match=all | Wrong kind result | Correct pr matches | Page1 / next offset |
|---|---|---:|---|
| engram prefetch | 0 + actionable warning |16|16 / none|
| engram speculative | 0 + actionable warning |30|20 /20|
| engram lookahead | 0 + actionable warning |1|1 / none|

The additional page was then fetched and retained. It exposes10 more opening records, not10 new ideas. A bounded opening-section triage found hardware-specific indexer/Hopper/AMD changes, loading/log changes, mHC/metadata optimization bundles, SWA replay and specialized DSpark. The last is already the C025 family, explicitly documented in rounds25/39. Other records have not received a new full-diff compatibility audit here and are not counted as implementation candidates. No extra accepted hypothesis or inference gain is claimed. The diagnostic improved visibility of a filter error and a truncated result set in an actual use case; it does not establish improved semantic retrieval quality.

## Verification

Three new CPU tests cover wrong-kind versus genuinely empty lexical search, custom kinds, repository scope, exact date-filtered pagination, alias expression, default-hit equivalence, caller transaction rollback, and real CLI/MCP result contracts. Full research suite:364passed and29subtests; bootstrap dry-run and discovery-skill validation passed.

Independent review additionally inserted a record from another connection during hit decoding and verified hit/count/scope consistency in the first snapshot, then visibility on the next call. It checked nested/same-name savepoints, exception paths and malformed literal kinds. Review manifest: `e5b5af6c0bbcc69b4794cae71386caafd592f9d500c332cd37e8fefa7dc563e8`.

No provider, model, GPU, serving, canonical write or cloud operation was needed for the replay. CLI/MCP tests mutated only isolated fixtures. Local mode=ro reads can use SQLite shared-memory bookkeeping; they are not a guarantee of zero filesystem activity. This tool change does not alter the active backfill or publication process.
