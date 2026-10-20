# Diagnostic B startup progress: read-only check

Observed 20 October 2026, 17:35:57–17:36:45 UTC. Both existing experiment containers remain in their initial load. This review issued no generation requests, GPU work, service commands, source edits, or environment changes.

At 17:36:21 and17:36:22, [backend-b-diagnostic.log](backend-b-diagnostic.log) lines 3573/3580 recorded the first `Loading weights took` milestone for both leaders (277.94 s and 269.14 s). At 17:36:24, both leaders logged loading the next 48-shard checkpoint. Thus the repeated coordinator “Waiting for 4 local” log line is not evidence of a stall.

Host worker PIDs: 268718–268721 and 268739, 268740, 268741, 268748. At 17:35:57 they alternated between runnable state and `folio_wait_bit_common`, with 4m11s–6m21s accumulated CPU and approximately 258–449 GiB RSS. The larger temporary RSS dropped after the first stage completed.

A 20.003-second `/proc` sample, 17:36:25→17:36:45, measured:

| PID | Additional CPU seconds | Additional minor/major faults | Ending RSS GiB |
|---|---:|---:|---:|
| 268718 |16.05|3324 /5|191.29|
| 268719 |16.06|3355 /2|191.31|
| 268720 |16.03|3393 /9|191.34|
| 268721 |16.45|3380 /6|191.31|
| 268739 |16.06|3362 /1|191.35|
| 268740 |16.05|3363 /1|191.35|
| 268741 |16.45|3407 /5|191.31|
| 268748 |16.42|3323 /8|191.32|

All main threads happened to be in `futex_wait_queue` at the end of the interval. Process CPU includes other threads and may include synchronization work; CPU alone does not prove checkpoint bytes advanced. The new completed-weight milestone is the stronger progress evidence. Both leaders still mapped nine Hugging Face blob files. Kernel-accounted `read_bytes` changed by less than 0.001 GiB during this interval; mmap/storage caching means that counter is not a complete checkpoint progress meter.

Memory pressure averages were zero; `MemAvailable=1979313460kB` (~1.84 TiB). I/O pressure `avg10=11.26%` indicates storage wait during the current phase, with no observed memory-exhaustion condition. No fatal startup traceback or error was found in the B log checked through 17:36:44.

Reference A milestones from [backend-a-exposure.log](backend-a-exposure.log): first weight completion 16:23:02–03 (lines 3679/3684); full model completion 16:26:27 (line 3837 onward, ~1181 s loading); first capture completion 16:29:22 (lines 5878/5879). B's first milestone has arrived sooner relative to its 17:27:17 start. If the remaining phases resemble A, model/capture progress around 17:40–43 is a planning estimate only. It is neither a readiness claim nor a timeout threshold. Root remains responsible for continued health/progress observation and any intervention.
