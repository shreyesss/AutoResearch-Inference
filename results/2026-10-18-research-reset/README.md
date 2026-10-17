# Adaptive-load and BLIS feasibility checkpoint

Date: 18 October 2026 (Asia/Kolkata). This is an integration/research checkpoint, **not** a serving-capacity or improvement result.

| Check | Executed result | Interpretation |
| --- | --- | --- |
| AIPerf 0.13 adaptive load on pinned B0 vLLM/Qwen | Two 12-request synthetic-chat trials, 12/12 completed each; sampled configured rates 2.0996 and 2.0384 requests/s; selected second by 134.26 versus 58.99 output tokens/s | Native search loop and `search_history.json` work. The first trial was distorted: 0.230 completed requests/s and 27.1 s median TTFT, versus 0.524 and 0.137 s in the second. No warmup/repeats/SLA; **no capacity conclusion**. |
| BLIS CPU trace replay | Built BLIS and replayed all 307 recorded OPS4 B0 chat requests as TraceV2 in about 0.06 s | Trace handoff works. BLIS has no calibrated Qwen3.8-27B/RTX PRO 6000 coefficients, so surrogate Llama/H200 numbers are **not predictive**. |
| Evaluator cost audit | Existing OPS4 candidate: 2744 s total, about 1350 s server startup, 1181 s benchmark, 202 s warmup | A one-task coarse screen could reject clear failures in about 13 minutes; a longer statistically useful stream will still be costly. No such gate is active yet. |

Machine-readable AIPerf planner output: [`aiperf-search-history.json`](aiperf-search-history.json). Full per-trial exports and logs: `.artifacts/aiperf-adaptive-ops4-spike/` (local, ignored by Git). BLIS build, converted trace and replay log: `.artifacts/blis-spike/` (local, ignored by Git). The temporary B0 container was stopped after the smoke.

Research and proposed next steps: [`AIPERF_ADAPTIVE_FINDINGS.md`](../../infra/AIPERF_ADAPTIVE_FINDINGS.md), [`BLISS_SPIKE.md`](../../infra/BLISS_SPIKE.md), [`OPS4_EVALUATION_REDESIGN.md`](../../infra/OPS4_EVALUATION_REDESIGN.md), and [`SEARCH_SPACE_EXPANSION.md`](../../infra/SEARCH_SPACE_EXPANSION.md). The next real checkpoint is a versioned development-stream B0 repeat and a validated one-task gate, followed by a sealed unseen test stream. The current OPS4 candidate remains unconfirmed.
