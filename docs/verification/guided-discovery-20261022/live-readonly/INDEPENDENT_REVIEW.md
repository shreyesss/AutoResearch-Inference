# Independent review: live read-only WAL visibility and report recall

**Verdict: no blocker in the reviewed scope.** Verified author manifest `13460cceff8f74ad944c76c59eec70c45aea73dfbb32abc51ed934a69b67e9a9`, all10 contained files, and current code/test/doc/skill copies against those bytes. This includes the retained pre-fix failing receipt; I did not rerun the old implementation.

## Source and contract

`Store(readonly=True)` now uses SQLite `mode=ro`, allowing the live reader to see committed WAL data. It returns before schema setup/migrations and still rejects writes. `immutable=True` is explicit and requires readonly=True; it is appropriate only for a sealed, unchanged source. An incorrect caller can still mislabel a live file immutable: the option is a contract, not a seal detector.

The two changed foundation callers pass immutable only for the existing replica branch. Ordinary canonical CLI access retains its existing normal Store and writer lock. I inspected replica.sync and storage._sqlite_backup: the snapshot path backs up SQLite and changes the destination to DELETE journal mode; replicas are restored into versioned directories and marked with checksums. The patch does not add new trust to a caller-controlled replica marker beyond existing behavior, and does not make ongoing mutable databases safe for immutable reads.

Read-only database access need not mean zero filesystem bookkeeping: WAL readers may use SQLite shared-memory/locks. Documentation says this explicitly. No provider or source ranking behavior changes.

The discovery-skill addition checks declared campaign reports as well as cards, uses bounded report-directory search if an exact report has not been indexed, retains provenance and permits reopening changed premises. It explicitly does not require scientific novelty. This addresses a documented coverage gap; neither this prose review nor the development example validates a general improvement in hypothesis quality.

## Independent checks actually executed

```
PYTHONPATH=ideation .venv/bin/python -m pytest ideation/tests/test_store_readonly.py -q
PYTHONPATH=ideation .venv/bin/python <review-dir>/replay.py
```

-**3 focused tests passed in0.01s.** Real SQLite WAL writer remains open after committing; live readonly get/FTS/revisions see the new row and DELETE fails. Sealed immutable read creates/changes no sidecars. Invalid immutable/missing readonly paths do not initialize state.
-A reviewer-owned temporary fixture exercised both actual foundation replica callers: `invoke --replica search` and `invoke --replica status`, with a corpus sealed by the real SQLite backup helper. Search returned the expected document; status selected the intended replica; all replica file hashes and names remained unchanged.
-All10 author packet hashes and current source copies matched. The full361-test receipt and bootstrap output were verified as artifacts, not independently rerun.

The extra fixture updates only its disposable node journal, never canonical state. No cloud/network/provider, model/native, GPU or serving action occurred. No source edits were made by this review. This is finite library/caller correctness evidence, not a production snapshot-isolation guarantee or a performance benchmark.
