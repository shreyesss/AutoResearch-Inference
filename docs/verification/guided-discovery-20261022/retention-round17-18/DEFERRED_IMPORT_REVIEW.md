# Independent review: deferred corpus import

Reviewed the current three-file patch in `foundation.py`, `test_interactive_research.py` and `CHAT_RESEARCH_WORKFLOW.md`. No repository edits were made by this reviewer.

**No blocker found in the narrow reviewed scope.** The CLI now admits explicit `--defer-snapshot import-corpus`; corpus import still runs inside the existing writer lock and transaction-preserving merge. Its checkpoint uses `_research_snapshot`, so defer writes a pending checkpoint marker without snapshot/publication, while the ordinary path still snapshots. Passing `publish=not args.local_only` also correctly prevents configured automatic publication for local-only imports.

Inspected unchanged `_import_corpus` transaction/rollback and source read-only handling, historical revision/edge preservation and newer-target selection. The patch does not alter merge semantics. Refresh/backfill and experiment commands remain excluded from deferral. Documentation distinguishes a successful local merge from recoverable checkpoint/publication and explicitly does not promise to preempt a publisher holding the lock.

Commands actually run from the repository:

- `PYTHONPATH=ideation .venv/bin/python -m pytest -q ideation/tests/test_interactive_research.py`: 7 passed.
- `PYTHONPATH=ideation .venv/bin/python -m pytest -q ideation/tests/test_foundation.py ideation/tests/test_interactive_research.py`: **24 passed, 8 subtests passed**.
- `git diff --check`: passed.

The new tests execute deferred import with `_snapshot` prohibited, inspect retained command/pending state, then perform actual local snapshot/restore and check revisions/discovery edge. The configured local-remote test verifies local-only does not publish and the default import still publishes. These are local fixture tests; no S3, canonical corpus or provider calls were made. They do not establish publication durability before the final checkpoint or add scheduling preemption.

Reviewed file SHA256:

- foundation.py: `727f9084b16a9fdafc4f19ea8374b279463ea5e641224c8999d48ab93eaf337e`
- test_interactive_research.py: `f43933012d37624e8e669dea5d1ab13af00c94ea13ed162284ef8d95260e38ff`
- CHAT_RESEARCH_WORKFLOW.md: `be764e5eb73756b3bb63540803929ab6c131dfa773247e4b84e84f227c3e42e4`
