# AV-off k5 timing — evaluator builder report

The fixed reader returns **`inconclusive_trace_adequacy`**. The workload fidelity checks pass, but the required timing inventory is incomplete. This report describes extraction evidence; the independent designer owns the final qualification and the orchestrator owns the user report.

## Completed workload and controls

- Exactly 986 profiling records and 986 raw HTTP200 records, with zero errors/cancellations and no duplicate request IDs or stable keys ; 55 warmup requests also completed without errors.
- Final aggregate is complete. Profiling replay p99 is 4.6538368ms and degraded=0. The console 107615ms warning exactly matches warmup p99=107614.99131904ms; it does not describe the profiling cohort.
- The metrics `profile_complete` relay timed out 30seconds after all 986 request records were processed. The server-metrics Parquet export subsequently completed at 21:27:22.471 with 3,105,464rows. This is a retained export/control delay, not a request failure; complete endpoint coverage is not inferred from the row count.
- Client exit 1 corresponds to ordinary completed-but-SLO-ineligible diagnostic output. No comparison to the full 4004-request screen is valid.
- Exact profiling start is 1792531285900046323ns; the live NOTICE anchor was 46323ns earlier. All four backend start dispatches meet the predeclared ±1second bound; cross-backend skew was 1.950ms and 0.387ms. Both episodes and all stop calls returned 200.

## Trace identity and parser provenance

All 16 collected traces were retained and hash checked, alongside both complete backend logs. CPU scope PID, distributed rank, local CUDA device ID and trace clock metadata bind each trace to the externally attested worker/container/GPU and its unique90s or210s episode. Before/after host PIDs, process start ticks, container IDs and source hashes match. Root archived the drained run and subsequently confirmed cleanup.

The original reader included Kineto mirrored `gpu_user_annotation` events as CPU parents. The frozen first-actual-trace reproduction correctly records its failure: mixed PIDs 0/1514 and insufficient joined cycles. The original 38a0bb45… source/output are preserved. The independently approved v2 reader 37f9cf8e… changes exactly two filters to require CPU `user_annotation` for scope/native parents. Ten CPU tests pass, including mirrored-track and GPU-only negative cases. V2 ran once over all 16 traces; no runtime source, workload, threshold, synchronization or capture changed.

## Measured cells and adequacy

Each percentage below is the sum of attributed interval unions divided by the sum of finite, nonoverlapping same-device target-to-next-target cycle spans. These are descriptive measurements, not exposed latency or removable compute. Draft execution is included in draft proposal; it is not added twice. Unattributed chronological flags remain unresolved even when their clipped occupied fraction is small.

| Offset | Replica / DP | Complete decode cycles | Target occupied | Draft occupied | Idle without observed GPU activity | Parser issue |
|---|---|---:|---:|---:|---:|---|
| 90s | 0 / 0 | 19 | 86.77% | 6.99% | 4.27% | none |
| 90s | 0 / 1 | 19 | 86.74% | 7.01% | 4.29% | none |
| 90s | 0 / 2 | 19 | 86.83% | 6.82% | 4.30% | none |
| 90s | 0 / 3 | 19 | 86.64% | 6.97% | 4.40% | none |
| 90s | 1 / 0 | 16 | 96.05% | 2.05% | 1.46% | chronology |
| 90s | 1 / 1 | 19 | 80.19% | 8.17% | 8.90% | none |
| 90s | 1 / 2 | 4 | 39.56% | 0.43% | 59.98% | <10 cycles; chronology |
| 90s | 1 / 3 | 19 | 80.09% | 8.13% | 9.03% | chronology |
| 210s | 0 / 0 | 17 | 97.07% | 1.83% | 0.83% | none |
| 210s | 0 / 1 | 15 | 90.53% | 5.92% | 2.38% | none |
| 210s | 0 / 2 | 15 | 90.27% | 5.78% | 2.62% | none |
| 210s | 0 / 3 | 18 | 97.13% | 1.81% | 0.81% | none |
| 210s | 1 / 0 | 19 | 87.58% | 6.46% | 4.15% | chronology |
| 210s | 1 / 1 | 19 | 87.60% | 6.49% | 4.18% | none |
| 210s | 1 / 2 | 19 | 87.60% | 6.46% | 4.23% | none |
| 210s | 1 / 3 | 19 | 88.00% | 6.41% | 3.83% | chronology |

Only 15/16 cells meet the minimum ten complete decode cycles; 11/16 have no parser adequacy issue. At 90s replica 1/DP2 has eight native execute annotations, 26 target/proposal scopes and only four complete eligible decode cycles. Nineteen target spans cannot be joined to exactly one native/draft range, two are mixed/no-generation, and the final boundary span is excluded. Extra scopes are retained, never promoted to real decode samples. The pinned `execute_dummy_batch()` path bypasses the native worker annotation; that is a possible source explanation for unjoined spans, not proof that each particular excluded span was dummy work.

Five cells contain GPU activities whose recorded end precedes the uniquely correlated CPU launch: 53, 406, 43 events for 90s replica 1/DP0,2,3, and 91,54 for 210s replica 1/DP0,3. No clock correction or tolerance was introduced. Missing required sample coverage alone blocks full qualification. All raw target fractions exceed 20%, but that does not satisfy the contract while required timing adequacy fails.

Target ownership includes collective execution/waiting. The independent reviewer identified large target-owned NCCL all-gather activities in the second replica0 episode; the percentages must not be described as pure verifier computation or an AV speedup prediction. Exposed service savings remain unknown.

## Perturbation context and limits

The four predeclared inactive brackets remain fixed. Each has20 telemetry loop samples; their request-start cohorts contain 72, 70, 69, 58 requests respectively. The 110–130s bracket overlaps replica 1 first-episode stop/export control until 113.651051s and is marked contaminated. The 60–80s, 180–200s and 230–250s brackets have no control-interval overlap. Different traffic/cache states prevent treating these brackets as an unbiased profiler-overhead experiment. The scoped capture durations vary considerably across ranks, and no synchronization or ordinal-based cross-rank alignment is inferred.

The structured profiler log audit found no CUPTI/Kineto/drop/truncation warning or backend error, consistent with independent review. This does not prove zero profiler perturbation. Source/worker warnings, full logs, unresolved chronology and all partial/excluded spans remain preserved. No repeated traffic or added capture is recommended by this builder report.

## Evidence

- `fidelity-builder.json`, `phase-final.json`: phase/raw/aggregate accounting and timing reconciliation.
- `trace-inventory-builder.json`, `trace-manifest.json`: all raw hashes, workers, devices and episode bindings.
- `trace-summary-v1-first-trace.json`, `trace-summary-v2.json`, `evaluator-v2-build.json`: immutable extraction outputs and correction provenance.
- `timing-table.json`, `timing-table.csv`: per-cell unions, denominators, exclusions and problems.
- `inactive-profile-bracket-context.json`, `profiler-log-audit-builder.json`: preserved perturbation context and structured log audit.
- Root `collection.json`, `drain.json`, `cleanup.json`, `final-integrity.json`: collection, strict drain, clean node and original-environment integrity.
