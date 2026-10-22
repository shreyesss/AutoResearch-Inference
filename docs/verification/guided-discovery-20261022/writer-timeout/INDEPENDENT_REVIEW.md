# Independent writer timeout review

**Verdict: no blocker in the reviewed v3 scope.** This is an optional acquisition timeout; it does not authorize concurrent writers or terminate work after acquisition.

## Exact revision and review history

Initial v2 manifest: `fb63f8dc7a2b73fb115b0c3c1b85275e9834868ac3949f6f1be92a4ba19a424e` (9 files verified). The author identified and repaired a late-retry issue before this review concluded: v2 could sleep past the deadline and attempt acquisition again. This review does not approve v2.

Final v3 manifest: `5072b769f1e0437e1050fe8d624b2611d8e8350858f84cf82421ce0094a58002` (8 files verified). The four current repository code/test/doc files match their frozen v3 copies byte for byte. See checks.json for individual hashes. No frozen author artifact was changed.

## Source findings

- Default `timeout=None` retains the original blocking `flock(LOCK_EX)`. CLI parser default and MCP default both remain None.
- A finite timeout uses `LOCK_EX|LOCK_NB`; zero permits exactly the first attempt. The v3 pre-retry monotonic check rejects retries after the budget expires. This is an acquisition policy, not a hard real-time scheduling guarantee.
- Only EAGAIN/EWOULDBLOCK is classified as contention. Other OS failures propagate to existing sanitized transport errors; they are not called `writer_busy`.
- Validation rejects boolean, invalid, negative and nonfinite values with a fixed message. Arbitrary input/provider exception text is not disclosed.
- The budget is measured with monotonic time and stops governing execution once acquisition succeeds. The existing finally block releases an acquired lock even when command execution raises.
- `journal.start` and `_execute` are inside the acquired lock. Failed acquisition invokes neither. Environment loading can occur before acquisition for existing applicable commands; creating the state directory and lock file is possible. The documentation correctly does not promise zero filesystem activity on a previously absent directory.
- CLI and MCP expose the same typed busy condition. MCP configuration applies the budget per call. No transport bypasses locking and no publisher behavior is altered.

## Independent execution

Executed from the repository with its existing venv:

```
PYTHONPATH=ideation .venv/bin/python -m pytest ideation/tests/test_writer_timeout.py -q
PYTHONPATH=ideation .venv/bin/python <review-dir>/review_checks.py
```

**13 tests passed in 1.44s.** These include real separate-process CLI contention, successful release for default and finite waits, real in-process MCP Client calls against the server, zero-budget free acquisition, error release, deadline regression, static invalid-value errors, secret sentinels, and hashes of the entire isolated initialized state before/after failed acquisition. The tests directly assert no journal start or command execution on failed acquisition. MCP provider calls are mocked and asserted absent.

Two additional reviewer controls confirm that successful zero-budget acquisition does not inspect the clock during command execution, and EINTR propagates as a non-contention failure. These are narrow control-flow checks, not latency benchmarks.

No canonical state, live publisher, cloud endpoint, GPU, model/backend, or native engine was used. The author's full-suite receipt was hash-verified, not independently rerun. This review supports the optional timeout's bounded behavior; it makes no throughput, research-quality, or live-operation claim.
