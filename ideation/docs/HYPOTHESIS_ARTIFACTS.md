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
