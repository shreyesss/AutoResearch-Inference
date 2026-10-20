# Independent short-operation probe prelaunch review

Accepted for the distinct one-device allocation in
`C24_SHORT_OPERATION_PROBE.md`, after the C25 allocation has released its
resources. No runtime result is implied; old probe/reader/result files remain
unchanged. Root alone controls launch, timeout, telemetry and cleanup.

Reviewed the new builder script, explicit-association parser and nine CPU
negative-control fixtures. The script asserts the exact implicated physical
GPU-6 UUID, uses one nondefault current stream, ordinary FP32 vector add/copy,
preallocated buffers/events, capture/warmup outside profiling, and one continuous
recording. It implements all 1,536 scheduled operations across 0/20/40-second
epochs, with per-iteration end-event completion to avoid queue masking. Finite
inputs and exact output values are checked against the CPU add/copy oracle.
The extra pre-capture eager warmup is allowed; it is recorded and lies outside
the measured windows. No synchronization change to serving is implied.

The parser enforces inventory, explicit unique launch association, CPU-only
annotation containment, no conflicting external IDs, consistent device/stream,
positive and consistent per-operation eager/graph activity multiplicity, and
the fixed receipt schedule. It retains signed chronology offsets, categories,
durations and missing graph-node metadata. Missing metadata prevents a complete
graph-node-accounting claim; it is not inferred from names or ordinal position.
Actual console/profiler warnings and final runtime identity still require
post-run review. The parser applies no clock shift or timing tolerance.

| Accepted file | SHA256 |
| --- | --- |
| `tooling/short_operation_probe.py` | `63b0e430522c005288484a2fe877b867ad75a482c8afd8fbe5afdea4174f6d1f` |
| `tooling/parse_short_operation_probe.py` | `86acd5995862340b412fd9c3a2bbac91d9c3e069b8619f3cbd93edd3e75a6ece` |
| `tooling/audit_saved_trace.py` | `c1c8101089a3c3c8c7bba59aa39b9374c3fe5dcb6f0cb100656425e72339b8b0` |
| `tooling/test_short_operation_probe.py` | `bf754f53ecbdfdb6e124b38f6eaf1c8b5e12a2bc27a36c6c3bbad2be33c5e062` |

Approved in-container command:

```text
python3 /work/tooling/short_operation_probe.py --output /out/probe
```

Use the versioned root runner with the exact GPU-6 UUID, pinned image, `/work`
read-only and unique writable `/out`; no model mount/network/install. Cap five
minutes and 0.083334 visible-GPU hours. One allocation, no automatic repeat,
timestamp correction or model recapture. Root must bind this completed review
and exact accepted source hashes in the execution receipt.
