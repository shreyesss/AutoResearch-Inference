# Code-only investigation repair

Observed failure: `round41-graph-padding/code-investigate.json` returned `no_selected_sources` with an explicit pinned code file and deep-count zero. The CLI skipped deep_dive; deep_dive and MCP also required a stored source ID. Original failure receipt is unchanged.

## Change

Explicit pinned files, brief code_sources and explicit repositories now work without paper IDs. Selection validation is shared and runs before run feed refresh; no paper/code relationship is invented by explicit selection. Budget/cache behavior remains shared and offline sets the HTTP budget to zero. Empty or failed-only reads retain receipts, return no_usable_sources/no_usable_evidence, disable model calls and do not enter typed reasoned-packet retention. A nonblank body is a minimum input criterion, not a semantic qualification. No input remains no_selected_sources at CLI/MCP; direct deep_dive rejects absent selection.

## Verification

Actual CLI handler and actual MCP→CLI→deep_dive tests exercise the path, not just argument forwarding. Focused tests: 52 passed plus 15 subtests. Full suite: 319 passed plus 29 subtests. Bootstrap dry-run and git diff check passed. No live network/model/GPU calls, canonical writes or publication. _import_corpus source is byte-for-byte unchanged from HEAD.

The first added-test run failed because repeated calls reused an immutable dossier output directory; tests were corrected to use separate outputs. Production immutability was preserved. This repair does not fix provider errors or make failed reads successful. Root owns any actual retained round41 cache rerun and its separate receipt.
