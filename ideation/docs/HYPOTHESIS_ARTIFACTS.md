# Portable hypothesis test artifacts

Hypothesis test results and experiment-registry artifacts use separate ledgers. This page covers `HypothesisMemory` / `hypothesis.get`; it does not change the experiment registry.

## New results

When `test_result` receives a file inside the research state root, its immutable artifact record uses a relative locator:

```json
{
  "path": "research/records/run/artifacts/result.json",
  "path_base": "state",
  "sha256": "<content digest>",
  "bytes": 123
}
```

`hypothesis.get` adds a **read-time** `resolved_artifacts` list. A verified entry contains `state_relative_path`, `resolved_local_file`, `resolution_method`, and `resolution_status: "verified"`. Both file size and SHA-256 must match. The projection is not written into historical events, and it does not validate a scientific conclusion.

Keep files in the state directory and include them in a checkpoint. The locator alone does not copy a file, publish to S3, or guarantee snapshot inclusion. Files outside state remain absolute external references and are reported as `external_not_retained` by the portable resolver.

## Existing absolute references

Historical events are never rewritten. An absolute reference already under the current state root can resolve there. After relocation, an absolute path with exactly one `research/records/` suffix can resolve to that same suffix under the new state root, **only after hash and size verification**. There is no basename matching or whole-filesystem search. Ambiguous suffixes, `..`, unsupported path bases, symlink escapes, missing files and hash mismatches do not return a resolved filename.

Retrying a completed result after relocation with the same verified file, verdict, scope and note returns the original event. It does not append a second outcome or change its historical actor/path. Different evidence or verdict still requires a repeat test.

## Verification

`ideation/tests/test_hypothesis_artifacts.py` runs actual local snapshot/restore for both new and legacy records, deletes the original location, and checks immutable-event identity and retry behavior. It also checks missing/corrupt files, traversal, symlink escape, ambiguous paths, external references and same-content files at a different locator. This is CPU state-portability verification; no serving behavior is tested.

## Retain reviewed source and replay files

Default snapshots omit Python/C++/HTML files even when a historical artifact
reference points to them. Retain selected UTF-8 evidence before checkpointing:

```json
{
  "reviewed": true,
  "provenance": "Reviewed source/replay artifacts from pinned run manifest",
  "artifacts": [
    {
      "path": "research/records/example/diagnostic.py",
      "sha256": "REPLACE_WITH_ACTUAL_64_HEX_SHA256",
      "bytes": 1234
    }
  ]
}
```

```bash
researchctl --defer-snapshot hypothesis retain-artifacts --manifest selection.json
researchctl snapshot --namespace research
```

This command uses the existing writer lock and command journal. It verifies all
selected source hashes/sizes and existing copies before writes, then retains the
original bytes unchanged in `research/artifacts/<sha256>.txt`, with an append-only
`index.jsonl` mapping. It never imports or executes the source. Selection must be
explicitly reviewed, state-relative, and confined to `research/records/`; symlinks,
traversal, credential/key paths and private-key material are rejected. Global snapshot exclusions remain unchanged. This explicitly reviewed path/hash
selection permits the whole filename word segments `tokenizer` and `tokenization`
(e.g. `cpu_tokenizer_audit.py`, `tokenizer.json`); other `token` names such as
`token.txt` and `access_token.json` remain rejected. This narrow allowance is not
permission inferred from provider text or a general credential-name bypass.

Limits: 16 MiB per text file, 64 MiB per selected batch, 1,000 selected entries,
1 MiB input manifest and 16 MiB mapping index. Binary/non-UTF-8 and oversized
files return explicit unsupported statuses; check these before claiming complete
recovery. This is not general secret detection: review the selected provenance
and contents before authorizing retention.

After restore, artifact reads consult the mapping **only if the original file is
missing**, require the exact original relative path and hash, and verify retained
size/hash. An existing corrupt original remains corrupt; a retained copy cannot
mask that failure. The returned file has a `.txt` name. No old path is recreated
and no old command is run automatically. Historical events/manifests remain
unchanged. Exact retries add no mappings; interrupted copy-before-index writes
can leave verified orphan blobs which retries adopt. A torn/conflicting index
fails closed and requires explicit recovery; multiple files and their mappings
are not a transactional database.

`--defer-snapshot` retains local bytes and marks a pending checkpoint. It does not
publish S3 or create a recovery snapshot. A later normal snapshot includes the
text copies/index; old snapshots remain incomplete for previously omitted files.

If retention fails after a partial copy, the command still attempts the standard
checkpoint (or deferred marker). If that checkpoint/publication also fails, the
checkpoint error preserves the original exception as its cause and exposes only
its type as `mutation_error_type`; neither failure is presented as success.
