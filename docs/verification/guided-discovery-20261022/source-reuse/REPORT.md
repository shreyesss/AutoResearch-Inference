# Selected source reuse: audit and repair

## Observed failure and scope

The parent observed two identical full-text downloads in round38 after those papers were read in round19. This audit made no network requests. Read-only inspection found `fulltext:2609.04244` (68,871 characters) and `fulltext:2610.00671` (58,378 characters), each with two retained content revisions. These are **unversioned** full-text records; they establish available historical evidence, not the latest arXiv revision. The independent readback is `readonly-lookup.json`.

The MF19 linked evidence bundle references both files, but `HypothesisMemory.recall_index` matches cards, decisions and claim-linked source IDs, not arbitrary linked-investigation artifact metadata. A source-library lookup is therefore necessary before treating a recall miss as a new discovery.

`Sources(store)` constructs `Cache(store.path.parent)`. `Sources.fetch` calls the HTTP-cache/request path without first inspecting an existing full-text document. `deep_dive.investigate` calls that fetch path even when text is retained. Independent study roots consequently have separate HTTP caches. The repair deliberately does not add automatic freshness assumptions or a shared cache.

## Existing APIs and minimal extension

Existing APIs already provide `Store.get`, `Store.revisions`, FTS `Store.search`, `Store(..., readonly=True)`, `evidence.canonical`, CLI `show --history/--revision-hash`, and MCP `source_show`. Existing whole-corpus import was too broad for a two-source reread because it also imports collection cursors.

The extension adds repeated `import-corpus --source-id EXACT_ID` and MCP `import_sources(source_corpus, source_ids)`. It imports only selected SQLite documents, all their historical revisions and incident provenance edges; it does not recursively import other endpoint documents or collection checkpoints. It preserves a newer destination projection and keeps incoming older revisions available. No-filter import retains its existing whole-corpus behavior. JSONL selection is explicitly rejected; unfiltered JSONL import is unchanged.

All requested IDs are validated within the same read-only source transaction before destination data writes. The normal command journal can still record a failed invocation. Imports hold the existing destination writer lock and use its normal checkpoint/deferred-checkpoint flow; no canonical state was changed in this audit.

## Real replay

`replay.py` used the repaired public `invoke` command in a fresh isolated state with socket connection creation denied. It imported both actual retained full texts, read their histories, and repeated the same import:

- 2 documents, 4 retained revisions; original retrieval timestamps and body hashes preserved.
- Retry: 0 new revisions, 0 imported checkpoints.
- 0 socket connection calls; no HTTP cache directory created.
- No S3 publication or VM synchronization; the isolated state is marked pending checkpoint.

See `replay-receipt.json`. This is a real retained-source tool replay, not an online provider test. Original unversioned evidence remains unversioned.

## Verification

- Focused source-import/MCP/foundation tests: **33 passed, 8 subtests passed**.
- Full research suite: **311 passed, 25 subtests passed**.
- `scripts/bootstrap-node.sh --dry-run`: exit 0, no changes.
- `git diff --check`: clean.
- Discovery skill validation: passed using the existing round23 tokenizer-loader virtual environment. The first attempt with the repository environment failed because PyYAML is absent; no dependency was installed.

Tests cover selected history and incident edges, excluding unrelated documents and cursors, source file hash unchanged, idempotent data replay, newer destination preservation, rejection of a missing selection before data writes, JSONL compatibility and MCP argument forwarding/empty-selection rejection.

## Limits that remain explicit

This does not extend compact hypothesis recall to all linked investigation contents. It adds an economical source-level reuse path and skill instruction to use it. Importing retained text does not seed HTTP responses. Calling `investigate` after importing can still issue HTTP requests; use `show`/`source_show` for the offline reread. A zero-HTTP investigation budget prevents requests but does not silently replace its fetch stage with a source lookup.

Selected-source import does not import hypothesis dispositions, raw binary artifacts, cache databases, credentials or S3 lineage. Incident edges can reference unresolved endpoints; select those document IDs explicitly when their content is required. Reuse is not evidence of freshness, scientific novelty, mechanism applicability or performance gain.

## Independent review correction

The scheduling reviewer found that a selected target A could import an old derived B→A edge from an **unselected** source B even when destination B was newer and had removed that edge. The initial implementation compared only selected document projections. This is fixed: derived edge evidence is compared against its destination projection even when unselected, with cached comparisons. Regression covers both `links_to` and `child_of`; historical `discovered_by` provenance is retained. Reviewer reproduction is under `review/source-import-agent/incident_edge_probe.py/json`. The final full-suite count above includes the new regression. `manifest.v1.json` preserves the pre-review code receipt.
