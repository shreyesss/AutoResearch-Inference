# Publication diagnostics and chunk reuse

`storage.push()` checks/uploads each distinct chunk hash once per invocation. It still reads and validates every file's ordered chunks, including duplicate references and per-file hashes. Each invocation checks remote existence anew; there is no persistent assumption that remote objects still exist. Snapshot selection, manifest format, writer lock, expected-parent lineage checks and conditional HEAD publication are unchanged.

Successful push receipts include `diagnostics`. An unsuccessful push attaches the same numeric partial measurements to the original exception's `publication_diagnostics` attribute. Exception type/cause remain unchanged; higher-level error reporting may expose only its existing failure summary. No new durable failure log is implied.

## Fields

| Field | Meaning |
|---|---|
| `total_seconds` | Monotonic wall time of this push invocation. Excludes snapshot construction and caller lock wait. |
| `phase_seconds.local_manifest` | Read/validate local manifest and expected parent. |
| `phase_seconds.remote_head_read` | Initial remote HEAD-pointer read. |
| `phase_seconds.local_chunk_validation` | Local compressed-object reads, decompression, chunk checks and ordered file-hash updates. Repeated file references are still validated. |
| `phase_seconds.immutable_chunk_transfer` | Remote existence checks, conflict reconciliation and any immutable chunk writes. Includes local SDK work; not a pure network timer. |
| `phase_seconds.immutable_manifest_transfer` | Check/write the immutable manifest. |
| `phase_seconds.head_compare_and_swap` | Read remote HEAD and conditionally advance it using the original expected parent. |
| `phase_seconds.exact_publication_recovery_validation` | Existing crash-recovery branch: validate exact remote manifest and all local/remote payloads. No new publication writes. |
| `counts.chunk_occurrences / unique_chunks` | Manifest references versus distinct content hashes. |
| `counts.chunk_transfer_checks / duplicate_transfer_checks_skipped` | Actual immutable-transfer operations issued versus repeated references skipped. |
| `counts.chunk_objects_written` | Confirmed new immutable chunk writes reported by the transport; same meaning as existing `objects_written`. |
| `counts.compressed_chunk_bytes_written` | Compressed payload bytes for those confirmed new immutable chunk writes. Excludes manifest, HEAD, retries, protocol overhead and billing. Not an estimate from differences with the parent manifest. |
| `counts.files_verified` | Completed file checksum validations. Exact-publication recovery validates both local and remote files, so it counts both passes. |
| `s3_requests` | Per-push SDK operation counters/timers for S3Transport; `null` for other transports. |

S3 counters distinguish GET/HEAD/PUT calls, successful responses and failed calls. Missing-object404 responses therefore count as failed SDK calls even when publication succeeds. These are logical SDK invocations, not HTTP wire attempts. GET call timing stops when the SDK returns its streaming body; encompassing publication phases include body reads. Reported SDK `RetryAttempts` are summed only when numeric metadata exists, with a separate `responses_with_retry_metadata` count. An absent retry field means unavailable, not zero. No bucket, object key, request headers, credentials, response body or exception text is recorded. Context-local counters isolate concurrent pushes sharing one transport.

Confirmed-write counters are not a complete account of physical writes or billing. A conditional PUT may commit remotely, lose its response, then be reconciled as an already-existing identical object after a retry conflicts. That path returns no confirmed new write, so object/byte counters can undercount what this invocation physically wrote. This ambiguity does not bypass object verification or conditional HEAD publication.

Phase fields exist only for phases entered. Timers include Python/local work within that phase; total also includes orchestration and final per-file checks outside named phases. A receipt alone does not measure writer-lock wait or prove S3 latency dominates.

## Scope and verification

Offline fake-client tests cover one chunk HEAD per unique hash, missing-object PUT counts and payload bytes, controlled-clock phase attribution, failure before publication, conditional-HEAD races, validation of a corrupted duplicate file, exact-publication retry, missing/reported retry metadata, and concurrent counter isolation. Existing storage tests cover restore and lineage recovery.

The measured local manifest from the investigation had1556 chunk occurrences and1500 distinct hashes. Deduplication removes56 redundant transfer checks for that manifest (3.6% of chunk checks). No live speedup is claimed. Publication remains inside the existing writer lock; safely moving uploads outside it requires a separate reviewed generation/lineage protocol.
