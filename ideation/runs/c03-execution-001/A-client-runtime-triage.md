# Diagnostic A client/runtime triage

Run: `/home/ubuntu/Deepseek_serve-c03/results/h200/vllm/c03/production/mooncake-median/c03-A-exposure-median-0p5x/20261020-163428`. Read-only diagnosis; no runtime, package, evaluator, or scoring changes.

The 16:57:22 console warning is a warmup metric, not a profiling replay failure. Splitting all 4,056 exported rows by `metadata.phase_kind` and reconstructing the analyzer formula produces:

| Phase | Rows | p50 (ms) | p90 (ms) | p99 (ms) | Max (ms) |
|---|---:|---:|---:|---:|---:|
| warmup | 52 | 45556.494154 | 93644.838530 | 104095.508444 | 104203.467087 |
| profiling | 4004 | 2.040059 | 2.865399 | 5.861525 | 12.160918 |

The warmup values round exactly to the warning (45,556 / 93,645 / 104,096 ms; `console.log:1548`). Final `score.json` reports profiling p99 **5.86175488 ms**, `replay_degraded=0`. The tiny difference from reconstruction is below one microsecond; the reconstruction uses exported request-start metadata whereas the metric uses the internal record timestamp. This does not alter the real latency/SLO failures or the separate evaluator gate.

Warmup explicitly uses `concurrency_burst` (`artifacts/logs/aiperf.log:1509`) and sends 52 requests in 120 seconds. The client copies the original turn timestamp into `scheduled_send_ms` without excluding warmup (`workers/inference_client.py:271`). The metric forms actual-minus-scheduled timestamps (`metrics/types/replay_sched_lag_metrics.py:100`), the analyzer anchors to the least-late record (`metrics/replay_sched_lag_analyzer.py:77`), and the accumulator invokes it for masked export summaries (`metrics/accumulator.py:695`). Its once-per-run warning omits the phase (`metrics/accumulator.py:512`). Profiling itself uses phase-relative trace scheduling (`timing/strategies/fixed_schedule.py:67`).

Reconstruction: join `conversation_id=session_NNNNNN` to trace row N; for each phase separately compute `offset_ns = request_start_ns - int(trace[N].timestamp * 1e6)`, then `lag_ms = (offset_ns - min(offset_ns)) / 1e6`; take NumPy linear percentiles. The trace span is 1,196.942 seconds, matching profiling send completion (1,196.943 seconds after phase start). Full paths, input hashes, percentiles, and source hashes are in `A-client-runtime-triage.json`.

The server-metrics timeout was a 30-second command timeout during export, not a stalled replay. At 16:58:23–16:59:45 the server-metrics process consumed about 78 CPU seconds over 82 wall seconds; Parquet grew from 6.9 MB to 28 MB; main/workers mostly waited in `ep_poll`, and memory/I/O pressure were zero. A finished 11,548,835 Parquet rows 168.277 seconds after requests completed, then wrote status at 211.900 seconds. Historical corrected baseline 145417 also emitted the timeout and completed 11,574,757 rows after 173.199 seconds, status after 223.646 seconds. Source `server_metrics/manager.py:840` awaits stream exporter finalization before the summary export at line 856. No intervention was needed.

Pinned AIPerf: **0.13.0**, existing `.venv-aiperf` Python 3.12. Source SHA-256 values:

- `timing/strategies/fixed_schedule.py`: `7b22e0b68f245044e1e71e4e72dbad433e18b99c9d4aa3c7ebe37c6eb32b6159`
- `workers/inference_client.py`: `fe64c6ced0383376297474f54e29151795330174c55e652b193b502b7a08f647`
- `metrics/types/replay_sched_lag_metrics.py`: `977309635059195e0cf282529b303513c312c6c382b106ddb749b30cde3b3305`
- `metrics/replay_sched_lag_analyzer.py`: `21fdabef5b5a206cc8a17eb7af57b7ef501abdeb3dfdeff7ed1d00d1ea028857`
- `metrics/accumulator.py`: `84207cd087a01d0f82466222269f4e544fa1ee53035fa6990e792b3585585a7d`
- `server_metrics/manager.py`: `56f6bd495ce1d163c26cfe7a1910f8f44429edebb89c2da38791b4e6a402906d`
