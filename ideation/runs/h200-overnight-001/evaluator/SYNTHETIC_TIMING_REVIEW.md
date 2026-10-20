# Synthetic timing probe: independent prelaunch review

Accepted for the one bounded allocation in `SYNTHETIC_TIMING_PROBE.md`.
No runtime outcome is implied. Root retains runtime, timeout and cleanup control.

Reviewed the evaluator builder's script, explicit-association parser, common
read-only helpers and nine CPU fixture tests. The script uses one explicitly
current nondefault stream, which is required for graph capture; initializes
timing events outside profiling; performs the fixed initial and per-mode
warmups; records six episodes of exactly 64 operations; synchronizes only after
each episode's queued work; preserves finite-value/checksum evidence and raw
traces; and fails on missing/nonfinite execution. The eight-multiplication
graph contains independent multiplications ordered on the same stream, not
data-dependent mathematical chaining. These are prospective clarifications of
the implementation, not changes after observing a trace.

The parser requires unique correlation records, CPU-only annotation parents,
consistent device/stream and no conflicting external IDs. It retains graph/node
IDs and requires every single-multiplication graph iteration to have consistent
positive kernel multiplicity, with exactly eightfold multiplicity in the
eight-multiplication graph. This added prelaunch cross-mode invariant detects a
missing graph node without kernel-name attribution. Missing emitted graph/node
identity remains inconclusive. It reports signed chronology offsets unchanged;
there is no numerical clock correction. Its structural pass still requires root
to review actual profiler logs for warnings and runtime identity.

CPU negative controls reject duplicated/removed launch records, GPU annotation
mirrors, conflicting external IDs and missing graph activity; a known negative
chronology example is retained as a diagnostic rather than shifted. These tests
do not prove actual CUDA trace completeness. All old timing artifacts and their
inconclusive verdict remain immutable.

| Accepted file | SHA256 |
| --- | --- |
| `tooling/synthetic_timing_probe.py` | `71228a89395f4e2218f92a8e8e27f0a016dbdc4c34edc7341787779f9c57f7e9` |
| `tooling/parse_synthetic_timing_probe.py` | `4dd05e99469c6127aa5f5af4a6ca014a3f56b86d31673bcdd805a4a022786954` |
| `tooling/audit_saved_trace.py` | `c1c8101089a3c3c8c7bba59aa39b9374c3fe5dcb6f0cb100656425e72339b8b0` |
| `tooling/test_synthetic_timing_probe.py` | `0638460427a21aff9dc985e4e0402ce79fef3e1572023c76b252962a99499a4a` |

Approved in-container command:

```text
python3 /work/tooling/synthetic_timing_probe.py --output /out/probe
```

Use the root runner's `/work` read-only mount and `/out` unique writable mount,
without `/model`, network or package changes. Maximum 15 minutes, one physical
GPU 0, 0.25 visible-GPU hours. The exact script/helper/contract/review hashes and
GPU UUID must enter the root receipt. Parse retained evidence only after finite
completion; no automatic rerun or model-service capture is released.
