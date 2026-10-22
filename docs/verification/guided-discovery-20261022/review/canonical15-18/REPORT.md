# Independent canonical readback: rounds 15–18

## Scope and method

This is a read-only verification of completed canonical imports. `readback.py` opens both databases with SQLite `mode=ro`, sets `query_only`, and takes read transactions. It does not construct `ResearchFlow` or a `Store`, invoke migrations, restart importers, or write canonical state. New audit files are outside canonical state. No network, GPU, model, or serving calls occur.

The script checks the canonical retained receipt against the external importer receipt, every archived artifact's SHA-256 and byte count, prepared source records against immutable `document_revisions`, current documents against their FTS entries and bounded MATCH probes, exact claim quotes and locators against the specific revision body, hypothesis-to-claim graph relations, baseline content addressing and brief binding, latest selection status, scoped CPU test events, and complete discovery receipts and `discovered_by` revision edges. It also inspects append-only trigger definitions without attempting a canonical write.

## Round 15: verified

| Item | Independently checked |
|---|---:|
| Archived artifacts | 73 |
| Source revision records and current FTS consistency | 83 |
| Exact source-revision claims | 6 |
| Online query receipts / discovered-by edges | 3 / 24 |
| Hypotheses / CPU result events | 2 / 4 |

- **AT02** remains the existing identity, **deferred**. The QUILT/cross-token sharing work is appended refinement evidence. The immutable node bytes match the preserved isolated validation snapshot.
- **CMR01** is the new **deferred** identity. Its CPU artifact and event preserve **2 worse greedy proxy cases out of 200**, along with request-boundary, rank-shape, and adaptive-budget counterexamples. A balanced proxy does not establish shorter distributed execution.
- Both retain the content-addressed planned Flash-1017 baseline: checkpoint `1bae0e1088993b9b82de08f59de5be5a34e42170`, vLLM `c4557869393db4d75c483d92edd02a5125500883`, 8 B200, two planned TP1/DP4/EP4 groups. This is source-plan identity, **not a live deployment assertion**.
- All four new CPU test outcomes remain **inconclusive** for target implementation/service claims. The 1,000 set-identity tests and independent float64 algebra tests are not FP8/BF16 kernel or runtime validation. The synthetic counterexamples remain retained; nothing is promoted to a measured serving win.

## Pending imports

At the initial audit, round 16 and rounds 17–18 external canonical receipts were not yet present. Root's existing import processes are left untouched. Their independent readback will be added only after the completed receipts exist. `readback.json` is the machine-readable status for each cohort.

## Limits

This verifies retained evidence and its stated scope; it does not rerun the CPU experiments. Existing-node comparisons use preserved isolated validation snapshots, baseline hashes and append-only constraints; no independent canonical pre-import filesystem image was captured for this audit. Source quote integrity does not automatically establish the interpretation of a paper or a performance claim. Current FTS records may legitimately have a later revision than the one cited; those two checks are deliberately separate.

The canonical imports used deferred checkpointing. This audit makes **no S3 completeness or recoverable snapshot claim**.

## Reproduce

From `/Users/shreyas/workspace/AutoResearch-Inference`:

```sh
PYTHONPATH=ideation .venv/bin/python /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/review/canonical15-18/readback.py
```

This only replaces external `readback.json`; canonical state is read-only.
