# Fresh probe-off B startup: host-only progress check

Observed 20 October 2026, 19:09:45–19:10:15 UTC. Root launched B at 19:07:55, host launcher PID 344726. No Docker/container operation, GPU workload, request, runtime mutation, or source/evaluator edit was performed by this review.

[backend-B-screen.log](backend-B-screen.log) lines 467/470 report both leaders loading the model from scratch at 19:09:12–13, approximately 77 seconds after launch. Fresh A reached the same milestone approximately 74 seconds after launch. No fatal/error milestone was found in the checked B log; coordinator waiting messages alone do not indicate failure.

At 19:09:45, all eight workers were runnable with 44–46 CPU seconds accumulated during 59 seconds of process lifetime. A 20-second `/proc` sample from 19:09:55 to 19:10:15 confirms active host-memory population:

| Host worker PIDs | Additional CPU seconds per worker | Additional minor faults | Additional RSS per worker | Ending RSS per worker |
|---|---:|---:|---:|---:|
|348853,348854,348859,348861|16.02–16.11|5.657 million|21.581 GiB|67.08–67.09 GiB|
|348880,348881,348882,348883|15.88–15.96|5.488 million|20.934 GiB|67.83–67.84 GiB|

All eight remained runnable; two sampled wait channels were `folio_wait_bit_common`. No major faults occurred in the interval. Shared mappings mean these RSS values must not be summed as distinct physical memory. Memory pressure averages were zero, `MemAvailable=2271948068kB` (~2.12 TiB), and I/O pressure avg10 was 16.32%. These observations support ongoing initialization, with no evidence of an actual stall or memory exhaustion at this point. They do not measure checkpoint bytes or prove future readiness.

Fresh A reference: launch 18:20:07; model-loading start 18:21:21; first weight completion 18:29:14–15; full model completion 18:33:17 (~716 s reported loading); first capture completion 18:36:14; root reports approximately 18 minutes to complete startup. B's early milestone and allocation rate are consistent with that sequence. Root retains later health, source, capture and service attestations; these historical durations are not timeout thresholds.
