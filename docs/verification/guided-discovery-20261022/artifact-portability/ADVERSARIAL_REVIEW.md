# Independent artifact-retention review

Read the complete current resolver/retainer, narrow CLI integration and targeted tests. Independently ran `pytest ideation/tests/test_artifact_retention.py -q`: **9 passed,12 subtests passed**. No canonical application or cloud publication by reviewer.

No blocking correctness issue found for the explicit reviewed-manifest, single-writer-lock contract. Sources are constrained to research/records, hashed and size-checked before mutation, UTF-8 bytes preserved, key-like paths/material excluded, and source/blob/index symlinks rejected in retention. Hardlink creation does not overwrite an existing blob; exact retries preserve mappings; orphan blobs from a failed index append can be adopted if identical.

Resolver falls back only when the original is absent. An existing directory, dangling symlink, size mismatch or hash mismatch is reported rather than hidden by the retained copy. Retained mapping, bytecount and digest are rechecked, with no source execution or global filename search. Historical references remain untouched.

Limits are correctly narrower than a secure filesystem transaction: writer lock does not defend against arbitrary external processes racing parent paths; JSONL append can tear and then fails closed; no all-or-nothing multi-file transaction or power-loss durability proof. Exact byte hashes and explicit reviewed selection do not constitute a general credential scanner. Existing-original resolver symlink behavior predates the fallback; the new retained path itself rejects symlinks. Unsupported >16MiB/binary selections are explicitly skipped rather than claimed retained.
