# Independent compact recall review

## Verdict

**No blocker found in the reviewed narrow change.** Compact literal/source recall fixes the output-size and typed-decision visibility problem without claiming semantic novelty detection or changing hypothesis qualification. Source hashes of the reviewed implementation are recorded in `read_only_probe.json`. No repository files were edited by this reviewer.

CLI retains legacy full-card output by default and adds explicit `--compact`; MCP defaults to compact and supports `compact=False` for the old wrapper/output. The full `hypothesis_show` dossier remains available. Offset/source filters require compact mode, limits are checked, exact source matches sort before other literal matches, and source IDs include typed claims attached after proposal creation.

The implementation correctly includes modern `review.rationale`, `reopen_when` and `decision_id`, not only legacy `assessment.reasons`. This matters: the old baseline-ranked `recall()` helper would have omitted those typed-decision reasons. The new method does not reuse that helper or inherit its unknown-baseline ranking behavior.

## Actual read-only field replay

`read_only_probe.py` uses the current methods on a canonical SQLite connection with `mode=ro`, `query_only=ON` and a read transaction. It instantiates the object with `__new__` and assigns that connection; it never invokes the migration constructor or canonical writer lock. Canonical `total_changes` is zero.

| Query, limit 5 | Compact serialized characters | Legacy serialized characters | M02 on first compact page |
|---|---:|---:|---|
| `HPC` | 1,510 | 4,052 | Yes |
| `indexer` | 6,213 | 33,637 | No |
| `sparse` | 6,325 | 32,251 | No |
| `2609.08450` | 1,510 | 4,052 | Yes |

The original round24 prior-recall artifact is **101,072 characters**. That original was a custom read-only recall, not demonstrated MCP use; this field replay must not rewrite its provenance.

Using the real M02's exact linked source ID with query `indexer` and limit one brings **M02 first**, exposes `status=rejected`, the K512 unsampled-dispatch reason, the existing sampled implementation, and its reopening condition. The rationale is explicitly marked truncated and the full decision ID is retained.

Paginating `sparse` with five entries returns **26 unique matches across six pages**, including old M02, with no duplicates in this read snapshot. The absent-literal control returns zero. An initial diagnostic assertion incorrectly expected the literal `indexer` to match M02's `sparse-index` wording; the test was corrected to `sparse`. This illustrates the documented lexical limitation rather than a semantic search guarantee.

## Tests run

```sh
PYTHONPATH=ideation .venv/bin/python /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/review/recall-surface/read_only_probe.py
.venv/bin/python -m pytest ideation/tests/test_chat_memory.py ideation/tests/test_mcp_research.py ideation/tests/test_research_flow.py -q
```

**45 tests passed in 1.31 seconds.** Included coverage: old rejection pagination beyond a short first page, source-first behavior, later-linked evidence, modern typed rationale/reopening information and no changes from the compact method itself. Real M02 replay separately verifies the production data shape.

## Remaining limits, not blockers to this change

- The result is bounded by per-field caps and page size, **not a fixed global character budget**. Use a small page when inspecting broad queries; limit 100 can still be large.
- Exact source IDs do not unify arXiv abstract/fulltext/DOI aliases. No match is not proof of novelty or lack of prior rejection.
- Pagination is stable within the diagnostic snapshot. Separate calls while concurrent records are appended may shift offset pages; no persistent snapshot cursor is promised.
- Selection is distinct from test outcome. The compact result explicitly instructs callers to open the dossier for scoped outcomes, complete reasons and exact baseline.
- The shared `recall_cards` helper still uses the preexisting ledger constructor and normal CLI machinery. The new pure-read method is verified read-only; this audit does not claim the entire CLI has become a migration-free read-only service.
