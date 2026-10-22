# Retention 19/20/22 — review before canonical import

## Scope

Default command creates a new isolated state seeded from a read-only SQLite backup of canonical hypothesis memory. It imports **only** this packet's research corpus/evidence and runs local snapshot/restore checks. It does not upload to S3 or modify canonical state. Existing unrelated canonical artifacts/corpus are not copied, so this isolated snapshot validates the newly selected bundle, not recovery of every historical test in the copied memory.

```
/Users/shreyas/workspace/AutoResearch-Inference/.venv/bin/python import_packet.py
```

Explicit apply requires `--apply --state-dir PATH`; canonical additionally requires `--allow-canonical-import`. Parent review is required before using that option. `--defer-checkpoint` records pending snapshot work, never publishes. No provider/GPU/serving/model action occurs.

## Identities and decisions

MF19 is replayed through existing ResearchFlow APIs in original order: six exact claims, proposal, initial defer screen, CPU diagnostic plan, deferred decision, revised advance-diagnostic screen. Every resulting ID must equal the original isolated typed ID. Its baseline/card/brief are unchanged. Target gain stays null and service unqualified.

S01 **keeps its existing accepted-for-bounded-CPU selection** and byte-identical original card/baseline. Rounds20/22 append an investigation, source consultations and scoped inconclusive CPU results. Inconclusive means these diagnostics do not establish serving efficacy; positive and negative finite CPU observations remain in full artifacts. No new S01 hypothesis and no S01 selection review/decision is issued.

Both hypotheses receive a portable evidence-bundle graph link with state-relative paths/hashes. This adds a usable projection without rewriting immutable original absolute paths or archival documents.

## Retention and exclusions

The source manifest explicitly selects reviewed UTF-8 evidence. Safe neutral archive filenames retain the original filename/path in `artifact-map.json`; this avoids confusing public source names containing tokenizer vocabulary with credentials. No environment files or secrets are selected. Original source bytes are never executed by the retention tool.

The existing `retain_artifacts` API stores each selected file as a verified `research/artifacts/<sha256>.txt` projection plus index mapping. This preserves .py/.rs/.cuh/.log/.toml/.lock and tokenizer-named sources that default snapshot filters otherwise omit. `snapshot-exclusions.json` lists every original archive path excluded by the default snapshot and its retained-text coverage. Snapshot and restore use the default selection with no extra inclusion bypass.

Compiled wheel/shared library, full venv, toolchain/cargo caches and binary source tar remain **local and unretained**. Exact repository commit/build configuration, binary hashes, build receipts, selected source and generated input/results are retained. Future native execution requires rebuilding/restoring a compatible pinned native package and toolchain; the evidence snapshot is not an ARM binary deployment package. Original script paths may need rebasing using artifact-map; corpus bodies and state-relative artifact references remain directly inspectable after relocation.

## Failure and retry behavior

Pinned packet and every source hash are checked before importing; exact S01 identity, baseline, original node hash and accepted status are checked before Store/ResearchFlow/journal mutations and again under the writer lock. Existing archive files and prepared packet must match; never overwrite conflicting bytes. The final completion receipt is written only after successful readback.

Research corpus and memory are separate databases; this is not a global rollback transaction. Failure after verified artifact retention or a subset of typed records can leave an append-only partial import. Retry can reuse matching copies/IDs; no completed test may receive conflicting results. A completed matching receipt makes retry a no-op after rechecking prior/source/archive hashes and artifact resolution. Corrupt/mismatched records fail closed for review, not silent repair. The retention helper itself can leave verified orphan blobs on interrupted writes; its existing retry protocol applies.

## Validation

`isolated-readback.json` records actual counts and exact IDs. `isolated-validation.json` records no-op retry, default local snapshot ID, skipped originals and every restored artifact's resolution method. `negative-controls.json` records bounded preflight corruption/missing-prior checks. Initial development run failed on an SQL spacing typo before import; corrected run succeeded. All checks are local CPU/read-only with respect to the serving deployment. No claim that new artifacts were covered by the older117-file repair.
