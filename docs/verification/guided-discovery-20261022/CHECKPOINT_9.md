# Checkpoint 9 — recovering prior decisions before drafting

## Scientific yield

**34 reviewed intervention cards: 2 accepted for bounded CPU investigation, 24 deferred, 7 rejected, 1 duplicate. Zero implementation or service qualifications.** Diagnostic selection is 2/34 (5.9%), not an estimated success rate. Round23 refines S01; round24 revisits an already-rejected M02 and adds zero identities. Round25's source fast-path closure is not counted as a new card. No cumulative unique-paper count is claimed across overlapping searches.

### Output usage bookkeeping: real residual, weak standard-workload case

[Round21](round21/REPORT.md) finds a repeated tuple conversion before the existing incremental reasoning counter. The ready counter ignores history; the false-ready path requires it. [Independent review](round21/INDEPENDENT_REVIEW.md) checks the source and recomputes all six saved CPU medians. The saved standard-length synthetic case saves approximately 0.100 ms over a 1,024-token stream with five-token chunks. This does not justify a material ITL claim. OH21-01 is low-priority deferred; reopen on demonstrated frontend pressure or a substantially longer output regime. Generic incremental detokenization/delta parsing already exists.

### Tokenizer loader: a suspected mismatch is resolved, version admission stays open

[Round23](round23/REPORT.md) actually loads the exact cached target tokenizer through Transformers 5.16.1/tokenizers 0.23.2, one combination allowed by pinned vLLM requirements. No model/backend accelerator imports or network attempts occurred during materialization. All 1,283 effective added-token entries match raw JSON because the loader resolves sidecar flags through the raw map. Seven bounded ID checks agree. A split_special_tokens=True control changes IDs and demonstrates that file hashes alone do not capture runtime semantics.

[Independent loader review](round23/INDEPENDENT_REVIEW.md) verifies29 artifact hashes, installed/source pins, all added rows and normalized model data. Earlier native/segmentation evidence used tokenizers 0.22.2. It remains valid for that fixture and does not certify the declared 0.23.2 dependency or live settings. S01 remains the same accepted bounded CPU investigation. No serving admission or ITL improvement is claimed.

### Sample-guided top-k: recovered prior rejection, no new yield

[Round24](round24/REPORT.md) triangulates the recent paper and pinned donor. The donor disables sampling for K=512, our planned indexer setting; the target also already contains a sampled path. More importantly, this is existing rejected M02. The [inspection miss](round24/RECALL_MISS.md) was concrete: its record sat at character 95,014 in a 101,072-character recall receipt, outside a manually printed 20,000-character prefix. Independent review agrees that this is a duplicate/source-pin refresh, not fresh hypothesis yield.

## Tool improvement based on that failure

CLI compact recall now scans all cards and latest decisions, includes later-linked source IDs, exposes literal-match counts and pagination, and prioritizes exact source identity matches. MCP uses compact output by default; full legacy output remains selectable. Latest typed decision rationale and reopening conditions are shown, including in the separate ranked recall used by the bounded reasoning pipeline. Neither interface claims semantic deduplication or scientific qualification.

Tests cover an old rejection behind 25 newer long cards, complete pagination, exact-source priority, later-linked counterevidence, latest typed rationale/reopening and no read-time ledger mutations. An in-process MCP roundtrip also checks the actual typed rejection and legacy full-output mode. Full research suite: **286 tests + 25 subtests passed**. Bootstrap dry-run and discovery-skill validation passed. [Independent real-record review](recall/INDEPENDENT_REVIEW.md) found M02 with its rejection/reopening conditions using both literal HPC and exact linked-source queries. Complete pagination recovered26 unique sparse-related matches. The literal HPC result was1,510 characters versus4,052 legacy; the original101,072-character receipt was custom SQL recall, not a direct MCP response. A subsequent additive inventory_hash exposes changes in matching projections across pages; it does not provide snapshot isolation.

## Persistence: separate completed checks from queued imports

- Rounds15,16,17–18 canonical imports completed. [Independent readback](canonical15-18/REPORT.md) verifies exact source revisions, quotes, graph links, current search entries and statuses. Original failed query receipts remain in revision history even where a later retry succeeded.
- Local repaired snapshot `7af36f9c79421c8efd870a052d1d1f7a59213824020ff50bb76fff19cf780974` was actually restored and verified 302/304 audited historical references; PNG and hidden .gitignore remain explicitly excluded. This is local restore, not S3 download or VM recovery.
- Verified S3 published lineage is `3b13134326534348b1ad050b5e50f4e63bf4007b789ef0fb1c15c8ce19c4d02d`, published 02:37:24 UTC. It includes round15 and the historical 117-reference retention map; it predates round16/17–18 imports. Later local snapshots are not publication evidence.
- An additional 48 reviewed text-reference retention request for15–18 is queued. Its first request failed closed because the explicit reviewed flag was missing; the revised request preserves identical selections/hashes. Four original filenames remain excluded by the path policy; no blanket raw-file completeness is claimed.
- For19/20/22, root independently verified all173 references in an actual isolated default snapshot restore and all11 MF19 typed identities; original S01 node/baseline and accepted status are unchanged. Native wheels, toolchains and venvs are excluded. Root-reviewed canonical import is queued, not yet completion. Scripts may require path rebasing; this is an evidence archive, not a turnkey native package.
- Round21/23/24 evidence is external local research plus selected Git reports. Its next canonical retention packet is being prepared. No VM restore is claimed.

GPU experiments, model launches, serving changes and training remain zero. Tool-triggered model calls are zero in these recorded probes; host-agent reasoning cost is unmetered, not zero.
