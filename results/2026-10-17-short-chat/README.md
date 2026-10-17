# Real short-chat vertical slice, 17 October 2026

Protocol: `fresh-server-cell-v1`; pinned model `Qwen/Qwen3.8-27B@1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`; vLLM 0.28.0 image digest `sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14`; AIPerf 0.13.0; one RTX PRO 6000 Blackwell (`GPU-9bb5b2a6-b234-55f6-6462-e030fcadfa83`). Each cell used a fresh server, three disjoint warmup requests and a 60-second dispatch schedule. All four timed cells completed with zero failures, zero server queue and <1 ms dispatch-lag p99.

| Load | Configuration | Completed | Output tokens/s | TTFT p99 ms | TPOT p99 ms/token | MTP acceptance |
|---|---|---:|---:|---:|---:|---:|
| 2.56 requests/s | B0 `cfg-8d0de585f89598b2160f` | 154/154 | 556.196 | 209.039 | 56.026 | — |
| 2.56 requests/s | MTP1 `cfg-917d6ef745e36c2567c3` | 154/154 | 591.410 | 220.330 | 35.263 | 81.0% |
| 3.2 requests/s | B0 `cfg-8d0de585f89598b2160f` | 192/192 | 688.933 | 223.958 | 63.820 | — |
| 3.2 requests/s | MTP1 `cfg-917d6ef745e36c2567c3` | 192/192 | 738.478 | 232.627 | 39.293 | 82.1% |

B0 resolved serving settings: `max_num_seqs=512`, `max_num_batched_tokens=8192`, `gpu_memory_utilization=0.92`, prefix caching on, chunked prefill on, MTP off. MTP1 changed only `mtp_draft_tokens=1`. At 2.56 requests/s its output tokens/s rose 6.33%, TPOT p99 fell 37.06%, and TTFT p99 rose 11.29 ms. At 3.2 requests/s those changes were +7.19%, −38.44% and +8.67 ms. Both points remain on each exact-load Pareto frontier because of the TTFT tradeoff.

These are one paired window per load. The [pilot plan](../../configs/pilot-plan.json) requires another B0/MTP1 repeat on each load and two cap64 inactive-axis control repeats before the sensitivity effect can qualify. The representative mixed/session/semantic suite and tail precision gate are also open. Autonomous real search remains blocked. The raw AIPerf exports, request records, Docker logs, GPU samples, schema-valid cell results, SQLite ledger and qualification report are retained locally under `.artifacts/vertical-slice-v3/`; this Git snapshot tracks the small result table and graphs.

Files: [points.csv](points.csv), [B0 load curve](b0-load-curve.svg), [Pareto at 2.56 requests/s](pareto-001.svg), [Pareto at 3.2 requests/s](pareto-002.svg).
