# Independent native002 outcome: valid baseline, metrics-readiness stop

A002 native collection is valid under the frozen reader: all eight receipts pass exact original-sampler before/after numerical oracles, capture/source/stream/restoration checks, all four intended executed capacities and960ordered samples each. The candidate never started. This remains a controlled padded-native baseline, not useful-output/service timing.

All ten initial actual requests passed the independent singleton-token oracle, HTTP200, expected17/19/23/29/31output lengths, usage and active k5 evidence. The first post-request scrape records router5+5 requests and zero in-flight, rank0 running/waiting0 in both replicas, and all40 terminal-reason counters with expected five length completions on each rank0 and zeros elsewhere. Running/waiting gauges are absent only for the six never-used ranks1–3. The old driver failed immediately at this scrape; no cancellation/EOS/recovery/natural-stop fixture followed. Therefore lifecycle remains incomplete, and no all-eight-engine drain observation is claimed.

Pinned-source diagnosis is concrete: vLLM creates mostrecent gauge labels but only sets them on per-engine scheduler stats; Prometheus initializes their timestamps to0 and its accumulator emits only when the timestamp is greater than its initial0. Untouched gauges therefore remain absent. Counters have different construction/aggregation behavior, so the earlier terminal-counter source check did not establish gauge availability. I independently reran the CPU reproduction against the exact extracted accumulator (`prometheus_client/multiprocess.py` SHA256 `9114faeb79deedbbdd266180187f9effbe3dcac627e4c95a68f1b2eeec696da7`): zero timestamps emit no series, setting rank0 emits only rank0, setting all four emits allfour. This reproduces the missing-series mechanism; it is not an invented service drain receipt.

This was another readiness/preflight gap in the evaluator protocol, including my review. It is not a numerical failure, observed busy queue or candidate rejection. Do not reinterpret absent samples as zero or silently mark002passed. Explicit six-rank priming and typed bounded telemetry readiness are prospectively specified in `C25_NATIVE_CONTINUATION_003_CONTRACT.md`, preserving the original concurrent multirow fixture. A separately named B-only continuation against hash-frozen A002 is justified before anyB output; its narrower lineage and candidate-only lifecycle qualification must remain explicit.

The execution receipt SHA256 is `e04559db766356bbee461348cd0f220b9e43a54519d4beddd93c76c56679455f`; closed-log attestation is `b9e0a60510720345999b27de627c8544dc844a68f4f335e66f5cc69aa7850454`. Wall allocation was1088.757488seconds, **2.419461allocated GPU-hours**. All frozen inputs remained unchanged; final GPU-process and running-container lists are empty, and watchdog disarmed after verified idle. This cost and the original campaign deadline remain in force.

The previously declared descriptive A001-to-A002 comparison shows draft-span changes from−0.180% to+0.729% across the eight cells, while target-forward changes range−4.828% to+0.434%. They are startup/context drift evidence, not a reason to select or pool baselines. A002 is the fixed comparator for the prospective continuation.

## Frozen baseline native receipts

- Replica0 rank0: `c9dd1fcaa914122f6504f3f349ff51ecd5cfd2274fb56556e99aa22ae5b54901`.
- Replica0 rank1: `9a6d1bcba6cfb1f68cf08274ddba95726825dd078b1fe75f5a9b2caa5fb12a2e`.
- Replica0 rank2: `edcdb06d3a46239f5eefd287ab562b41cf357a42eb64d74a5b236cb9368b89af`.
- Replica0 rank3: `9c0d7780dd99891d430351a8f483d254e8e449124b4846ce4623c9c1f5c07754`.
- Replica1 rank0: `54a4bd7c9baa9191c7cf49f9b675244741e7f1724dc349270286f157ec3c2e2a`.
- Replica1 rank1: `6764c63511bee24a1de5d1fcf9b4e97863fc6aedbf1e98eb03f3f5eb21c56378`.
- Replica1 rank2: `edcd676a7f2bae218dd088d6f791e396a7666a4545c9dbe0407b11272f160388`.
- Replica1 rank3: `6ab5b200e5b165b7c57fbf0e240e7c82b0f767b04ac5e13d7c26aa06f8cef250`.
