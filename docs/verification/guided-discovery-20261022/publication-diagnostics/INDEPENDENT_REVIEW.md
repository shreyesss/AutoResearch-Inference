# Independent publication diagnostics review

**Verdict: no blocking data-integrity or concurrency defect found in the reviewed patch.** This is bounded source review plus two offline probes, not cloud validation or a claim about every interruption point.

Read the entire changed storage path, local/S3 transport and manifest/chunk helpers, all seven new publication-diagnostics tests, and `ideation/docs/PUBLICATION_DIAGNOSTICS.md`. Compared the storage diff against Git's current base. Did not repeat the full test suite, use credentials, contact S3, change canonical state or modify storage code.

## Integrity and concurrency

* Deduplication happens only after each occurrence's local chunk size/hash validation and ordered file-hash update. Thus a repeated content ID cannot hide a corrupt later file or conflicting chunk length. The checked set is per invocation; no persistent remote-existence assumption is introduced.
* Manifest validation and expected-parent checks precede transfers. Immutable manifest transfer still follows complete file validation; HEAD still uses the original conditional compare-and-swap. Failed operations may leave unreferenced immutable chunks, as before, but do not manufacture successful publication.
* Exact-publication recovery continues verifying the exact remote manifest and both complete local/remote file sets. It does not claim fresh uploads.
* Each push installs a fresh ContextVar dictionary and resets its token in finally. Shared-transport thread calls are isolated; the existing test deliberately interleaves two namespaces. Nested synchronous push contexts restore the parent token by construction. This does not promise context isolation for arbitrary unrelated transport operations deliberately executed inside the same active push context.
* Exception type/cause remain intact on normal built-in/provider exception paths. Diagnostics contain numeric fields and static scope labels rather than response bodies, keys or exception text.

## Independent additional probes actually executed

`probe.py`, using only the offline FakeS3 fixture and temporary local archives:

1. Structurally valid manifest references the same chunk twice but changes the second declared size. It rejects with `Chunk checksum/size mismatch`, leaves HEAD unpublished and resets request accounting. Deduplication did not skip the second validation.
2. GET returns a streaming body whose read raises. The original exception type is preserved, the body closes, the ContextVar resets, and no objects are published. `get_succeeded=1` is correct under the documented **SDK response returned** meaning; it does not mean body consumption or checksum verification succeeded.

Two probes passed. No boto3 session, network, cloud mutation or GPU call occurred.

## Counter semantics correction

One documentation limitation was clarified with root authorization: conditional PUT success can be ambiguous after response loss and a conflicting retry. Identical-object reconciliation returns false, so object/byte counters measure **confirmed new immutable writes**, not all physical commits or billing. Only this wording was changed; code and existing counter behavior were preserved.

Other limits are explicit: GET SDK time excludes streaming body reads; encompassing phases include them; retry totals are available only where response metadata exists; per-file checksum completion is outside some named phases; total excludes caller writer-lock wait and snapshot construction. The patch keeps publication inside the existing writer lock. It does not establish why the production lock was held or quantify live S3 speedup.

## Scope not changed

Trust in existing immutable-object metadata, individual SQLite backup consistency, external deletion of published blobs, process termination, external path races and broader multi-store transaction behavior are pre-existing transport/storage assumptions, not resolved by instrumentation. No claim of general transactional or billing accuracy is made.
