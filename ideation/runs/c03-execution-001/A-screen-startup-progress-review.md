# Fresh probe-off A startup: read-only progress check

Observed 20 October 2026, 18:22:37–18:23:10 UTC. Root launched this arm at 18:20:07. This review used host `ps`, `/proc`, and existing log files only: no Docker/container operation, generation request, GPU workload, runtime mutation, or source/evaluator edit.

[backend-A-screen.log](backend-A-screen.log) records both leaders loading the model from scratch at 18:21:21 (lines 465/473). At 18:22:46, four ranks of one replica report a 94.42 GiB shared Engram table offloaded to pinned host memory (lines 523–526). No completed checkpoint-weight, full-model, or capture milestone is expected this early solely because the coordinators log “Waiting for 4 local”. No fatal startup error was found in the checked log.

At 18:22:37, all eight workers had accumulated approximately 78–81 CPU seconds during 100–101 seconds of process lifetime and were mostly runnable. A 20-second sample, 18:22:50→18:23:10, measured:

| Worker group | Additional CPU seconds per worker | Additional minor faults per worker | Additional RSS per worker | Ending RSS per worker |
|---|---:|---:|---:|---:|
| 309548,309551,309553,309556 |14.72–15.16|5.44 million|20.751 GiB|117.34–117.35 GiB|
| 309581,309582,309585,309586 |16.03–16.51|6.72 million|25.631 GiB|127.04–127.05 GiB|

All workers were runnable at the ending sample; one concurrently sampled wait channel was `folio_wait_bit_common`. No major faults occurred during this interval. The two inspected leaders had no checkpoint blob mmap yet, so these deltas show active host-memory initialization/population rather than proving checkpoint-file read progress. Shared mappings mean per-process RSS must not be summed as distinct physical memory.

Memory pressure averages were zero; `MemAvailable=2143439844kB` (~2.00 TiB). I/O pressure avg10 was 14.76%, indicating storage wait elsewhere in the system/current initialization. The observed CPU, allocation and log milestone progression provides no evidence of a stalled load or memory exhaustion.

Reference timings: diagnostic B started 17:27:17, reached full-model completion 17:40:19 and capture completion 17:43:15. Initial diagnostic A reached full-model completion 16:26:27 and capture completion 16:29:22 after its approximately 16:05 start. Thus the present arm's first 3 minutes are within the earlier initialization period. Those total durations are planning references only; root retains health/source/capture attestations and any intervention decision.
