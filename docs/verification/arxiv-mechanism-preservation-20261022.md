# arXiv query fidelity: verified repair

22 October 2026. The old arXiv search truncated ordinary queries to ten content
terms, then automatically retried their first three terms after zero hits. The repair
preserves every content term/quoted phrase and executes one query; explicit field
expressions and requested dates remain intact. Receipts expose the exact query,
result count/cache status or sanitized failure. Empty results ask the host to
choose its next action explicitly. No new constraint schema was added.

## Actual field replay

Query: `LLM inference fine grained kernel scheduling layout transformation`,
arXiv, `after=2026-06-01`, exclusive `before=2026-10-23`, limit 8.

| | Before | Repaired |
|---|---|---|
| Strict query | 8 terms, 0 hits | Same 8 terms and dates, 0 hits |
| Automatic fallback | `LLM inference fine`, 8 hits | None |
| Attempts | 2 | 1 |
| Replay network requests | Original requests not repeated | 0; original strict response was a cache hit |

The replay ran the actual `researchctl` executable against a new isolated state
with copies of the original two cached responses. Original state was read-only;
there was no refresh, GPU work, canonical mutation or publication. This verifies
faithful retrieval, **not improved paper recall or a new online search**. The next
query remains an agent decision; semantic `must_keep` constraints still need
agent review.

Evidence: external batch
`guided-discovery-20261022-001/tool-arxiv-repair/` contains `REPORT.md`, original
`before.json`, actual `after.json`, both original response XML files, `replay.py`
and `replay-receipt.json` with commands/cache keys/response and code hashes. It is
under `~/.local/share/autoresearch-reviews/`. The repair was uncommitted during
replay; use the file hashes, not HEAD alone, to identify executed code.

## Verification

```text
.venv/bin/python -m pytest ideation/tests -q
# 267 passed, 11 subtests passed
scripts/bootstrap-node.sh --dry-run
# passed, no changes
```

Regression tests cover mechanism terms beyond the old caps, phrases/field
expressions, dates, cached absence, errors without silent broadening, rejected
stopword-only input and the saved CLI receipt. The new CLI test initially used
`result.json`; it was corrected to the existing `search.json` before the passing
full suite. Workflow and MCP descriptions document the same behavior.
