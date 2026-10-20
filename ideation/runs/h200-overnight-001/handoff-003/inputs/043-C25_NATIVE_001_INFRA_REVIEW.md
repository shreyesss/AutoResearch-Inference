# Native allocation 001: valid baseline observations, infrastructure stop

Independent review, 2026-10-20 UTC. Allocation `native-pair-001` is **incomplete due to a root runtime-identity failure after baseline native collection and before traffic**. It is not a candidate correctness/performance rejection. No candidate was launched, and no lifecycle acceptance or A/B improvement claim is available.

All eight A rank receipts passed the frozen reader's native checks: exact original-sampler cache/token oracles before and after collection, finite active cache writes, inactive-row preservation, counters, source/graph/stream identity, restored persistent state and 960 ordered samples each. I independently checked the pinned physical UUID for each rank, common run identity and installed FP32 Gumbel mode. Each rank witnessed 37 captured draft graphs. Actual target/draft token and request capacities were 6/5 (1/1 rows), 12/10 (2/2), 24/20 (4/4), and 36/35 (6/7); all intended draft capacities were covered. The five-logical-request cell correctly had six actual valid state rows and one padded draft row. These are retained controlled padded-native baseline observations, not accepted-token/service timing.

Native collection took approximately 19.8–20.0 seconds per rank. Startup reached native/API readiness at23:12:12UTC, then the controller reported `PermissionError(13, Permission denied)` while collecting runtime identity before traffic. The code path attempts host `/proc/<root-owned container init PID>/exe` resolution from the ubuntu controller. A CPU-only reproduction is required to establish the exact failing read before a repaired allocation is released. No `controlled-traffic.json` exists, B was not started, and the raw receipt is not relabeled a completed A arm.

The final execution receipt SHA256 is `d25678db677ab202f09d40cf772aa992d7f710c249c90651c6cfd74974ee0f61`; closed-log attestation SHA256 is `9a816945da060b8581557b2050bdd8d86a4af902c2c1a3ddb4b9b8bc163e75af`. Allocation wall time was1151.492seconds, **2.558871 allocated GPU-hours**. All bound inputs were unchanged at exit. Docker removal attempts reported zombie-init errors; those errors remain retained. Final observations show no GPU processes or running containers, and the watchdog disarmed only after that verified idle state.

A separately named fresh A/B pair is scientifically reasonable after an independently reviewed infrastructure-only identity repair, with the same frozen treatment/oracle/workload/statistic. It must retain001 and its cost, and use the original absolute85/90-minute work/hard-deadline envelope rather than restart the budget. Container-local PID1 exe/argv/start ticks read by `docker exec`, linked to docker-inspect host PID and readable host start ticks, can replace the inaccessible host executable read. This document records the diagnosis/recovery rationale; concrete repaired source and CPU proof still require acceptance before launch. Two full service attempts remain.

## Retained native receipt hashes

- Replica 0, rank 0: `afa8bdcc93026c65436b28626a0f8c91e7efb9a3c87b528b08f1a7eb858308c5` (960 samples).
- Replica 0, rank 1: `09b46a9044f7b44ef9482a72e5c1c4d6470ab4ac2dfaf14e1393685319a49128` (960 samples).
- Replica 0, rank 2: `bcf77aafbed3720d5acad1c938d3434db0025962386f05a11bdd9d6ef7b60297` (960 samples).
- Replica 0, rank 3: `2fcc3c46637192b89520991d502da19b91530d88fb7c2da68dada0b57c9368bc` (960 samples).
- Replica 1, rank 0: `ba06075d4a26111f0bd219d12f72c3a7ecebaf12567332e8c2ed694b602a9215` (960 samples).
- Replica 1, rank 1: `793273f6bbba42006469cb0a5039123d922951528bafdf15fa3d241ca3e07133` (960 samples).
- Replica 1, rank 2: `6f892ff55397016552632fb10f416b0a43e63f4daef574e9407cc5801bc13849` (960 samples).
- Replica 1, rank 3: `49d73214c2dce91d040baab56f3928b3393e4312970e05e07c0ca25cb5f5c277` (960 samples).
