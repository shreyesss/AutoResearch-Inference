# Optional writer wait timeout implemented; no canonical smoke

- CLI `--lock-timeout SECONDS`, MCP startup flag and `create_server(lock_timeout=...)` now accept finite nonnegative seconds. Omitted remains blocking flock; zero makes one attempt. Acquisition only is bounded, not execution after acquisition. Monotonic elapsed-time retries sleep at most50ms.
- Only EAGAIN/EWOULDBLOCK are contention. Permission failures are not reclassified. `writer_busy` has static actionable wording and appears before journal.start/_execute. Existing canonical queued45 and publisher were not interrupted, reconfigured or probed with the new option.
- Invalid CLI values use a static argparse type error, avoiding raw invalid-float echo. Direct MCP startup validation rejects bool, negative, NaN and infinity. Provider/OS failure messages remain sanitized and do not become writer_busy.
- On contention in an initialized isolated state, actual CLI and actual MCP calls left all file-content hashes unchanged. Lock directory/file creation and filesystem metadata are explicitly excluded from a blanket zero-filesystem-effect claim. No provider call/command execution or journal entry occurs on failed acquisition.

## Verification

`test_writer_timeout.py`:13 tests passed. Includes separate-process flock holder, actual CLI timeout0/0.05, actual MCP contention then successful release, default blocking until release, explicit3-second acquisition success after release, free zero-budget acquisition, exception-unlock, invalid-value state-absence and secret-negative controls, plus EACCES/EBADF/ENOENT propagation. MCP provider mock was never called; no canonical/cloud calls occurred.

Full required research suite:358 tests and29 subtests passed. Bootstrap dry run and git diff --check passed. Frozen v1 design remains unchanged. Source copies and hashes in this v3 folder identify the reviewed implementation; no commit made. Benefit is prompt tool feedback under lock contention, not faster publication, concurrent local search, research quality or GPU throughput.

## v3 finite deadline refinement

A retry now checks elapsed budget before attempting acquisition again, preserving the initial zero-budget attempt. A deterministic clock control proves the lock cannot be acquired after the budget elapsed during sleep. v2 code/report remain preserved. Full suite and bootstrap were rerun for this concrete correction.
