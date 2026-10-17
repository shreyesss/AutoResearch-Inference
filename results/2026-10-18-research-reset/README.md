# Adaptive-load and BLIS feasibility checkpoint

Date: 18 October 2026 (Asia/Kolkata). This is an integration/research checkpoint, **not** a serving-capacity or improvement result.

| Check | Executed result | Interpretation |
| --- | --- | --- |
| AIPerf 0.13 adaptive load on pinned B0 vLLM/Qwen | Two 12-request synthetic-chat trials, 12/12 completed each; sampled configured rates 2.0996 and 2.0384 requests/s; selected second by 134.26 versus 58.99 output tokens/s | Native search loop and `search_history.json` work. The first trial was distorted: 0.230 completed requests/s and 27.1 s median TTFT, versus 0.524 and 0.137 s in the second. No warmup/repeats/SLA; **no capacity conclusion**. |
| BLIS CPU trace replay | Built BLIS and replayed all 307 recorded OPS4 B0 chat requests as TraceV2 in about 0.06 s | Trace handoff works. BLIS has no calibrated Qwen3.8-27B/RTX PRO 6000 coefficients, so surrogate Llama/H200 numbers are **not predictive**. |
| Evaluator cost audit | Existing OPS4 candidate: 2744 s total, about 1350 s server startup, 1181 s benchmark, 202 s warmup | A one-task coarse screen could reject clear failures in about 13 minutes; a longer statistically useful stream will still be costly. No such gate is active yet. |
| Mixed-task matched repeat | Fresh-server confirm B0 and 4096 candidate, 36/36 clean requests each, both valid/normal | Same-input direction repeated; see table below. This is run-to-run evidence for the frozen stream, not unseen-content or p99-SLA confirmation. |

| Mixed task | B0 screen → 4096 screen | B0 confirm → 4096 confirm |
| --- | ---: | ---: |
| Output tokens/s, higher better | 55.079 → 55.118 | 55.076 → 55.124 |
| TTFT p99 ms, lower better | 9029.83 → 8492.59 | 9003.89 → 8442.10 |
| TPOT p99 ms/token, lower better | 64.839 → 63.488 | 64.896 → 63.440 |
| Queue peak / drain | 1 / 23.58 s → 1 / 23.31 s | 1 / 23.60 s → 1 / 23.27 s |

The p99 TTFT movement is concentrated in a specific tail request: document-shape request index 33 improved by 1596 ms in the screen and 1609 ms in the confirm repeat. The slowest document request (index 34) stayed near 9.2 seconds under both configurations. Per-shape median changes are much smaller; inspect [`paired-mixed.json`](paired-mixed.json) before generalizing the aggregate p99. Its analyzer checks exact request IDs, token counts and frozen timestamps across all four cells. The confirm B0 and candidate cells took 763 s and 792 s respectively, including startup. Optional AIPerf GPU telemetry dropped during both; request accounting and server metrics were present.

Machine-readable AIPerf planner output: [`aiperf-search-history.json`](aiperf-search-history.json). Full per-trial exports and logs: `.artifacts/aiperf-adaptive-ops4-spike/` (local, ignored by Git). BLIS build, converted trace and replay log: `.artifacts/blis-spike/` (local, ignored by Git). The temporary B0 container was stopped after the smoke.

The compact confirm cell results, controller validity checks and timings are tracked under `b0-confirm/` and `candidate-confirm/`. Full confirm exports are local under `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/qwen38-27b-ops4-v1/eval-7661c59086214c2199f361afe445da30/` and `eval-2b9e68ea7031497dbeb85a8e0a151da3/`. Both evaluator-managed model servers were stopped after their cells.
The eight compact machine-readable artifacts have SHA-256 entries in [`ARTIFACTS.json`](ARTIFACTS.json).

Research and proposed next steps: [`AIPERF_ADAPTIVE_FINDINGS.md`](../../infra/AIPERF_ADAPTIVE_FINDINGS.md), [`BLISS_SPIKE.md`](../../infra/BLISS_SPIKE.md), [`OPS4_EVALUATION_REDESIGN.md`](../../infra/OPS4_EVALUATION_REDESIGN.md), and [`SEARCH_SPACE_EXPANSION.md`](../../infra/SEARCH_SPACE_EXPANSION.md). The next real checkpoint is a versioned development-stream B0 repeat and a validated one-task gate, followed by a sealed unseen test stream. The current OPS4 candidate remains unconfirmed.
