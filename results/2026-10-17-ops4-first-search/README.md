# OPS4 first real autoresearch iteration — 2026-10-17

## Scope and intervention

Campaign `qwen38-27b-ops4-v1` tunes one pinned Qwen/Qwen3.8-27B vLLM configuration on one RTX PRO 6000 Blackwell GPU. The four frozen tasks are short chat (307 requests), agent (27), long document (18), and smooth mixed (36). Every cell uses its task's exact fixed arrivals and bodies, a fresh server, disjoint warmup, and complete request accounting. The primary objectives on **each task** are output tokens/s up, TTFT p99 down, and TPOT p99 down: twelve separate coordinates.

- B0 `cfg-8d0de585f89598b2160f`: `max_num_seqs=512`, `max_num_batched_tokens=8192`, `gpu_memory_utilization=0.92`, prefix caching and chunked prefill on, MTP off.
- Codex proposal `ops4-attempt-0002-batch4096`, `cfg-32b1ae035e0ebc4c2d55`: **only** `max_num_batched_tokens=4096`; the other settings resolve to B0.
- Hypothesis: smaller prefill chunks may reduce decode interference in long and mixed traffic. Prediction was lower TPOT tails with possible TTFT/output-rate cost. Actual per-request prefill chunk sizes are not exported, so mechanism activation is not directly confirmed.

## Matched one-window results

All eight cells were `valid` and `normal`, with all planned requests completed and no failures, timeouts, cancellations, censoring, or undispatched requests. Values below are point estimates; p99 from 18 document or 36 mixed requests is especially uncertain.

| Task | B0 → 4096 output tok/s ↑ | B0 → 4096 TTFT p99 ↓ | B0 → 4096 TPOT p99 ↓ | Candidate queue peak; drain |
| --- | ---: | ---: | ---: | --- |
| Short chat | 564.388 → 564.234 | 310.07 → 294.90 ms | 55.010 → 55.018 ms/token | 0; 10.48 s |
| Agent | 111.342 → 111.376 | 2422.36 → 2191.90 ms | 53.256 → 52.728 ms/token | 0; 42.48 s |
| Document | 24.154 → 24.155 | 8373.32 → 7250.24 ms | 86.803 → 85.658 ms/token | 1; 27.47 s |
| Smooth mixed | 55.079 → 55.118 | 9029.83 → 8492.59 ms | 64.839 → 63.488 ms/token | 1; 23.31 s |

The 4096 candidate is not a confirmed improvement. Its observed output rate is essentially unchanged; agent, document and mixed tails moved lower, while chat output rate and TPOT changed slightly in the unfavorable direction. The twelve-coordinate point-estimate frontier therefore contains **both** B0 and the candidate. One matched window cannot separate small changes from run variation or establish a p99 SLA. The candidate took 2744.2 s (45.7 min) for four fresh-server cells, excluding Codex research time.

## Inspect or resume

- B0 raw cells: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/qwen38-27b-ops4-v1/eval-90df9f1ed1f94fa586f4cea2b1fe0913/`.
- Candidate raw cells: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/qwen38-27b-ops4-v1/eval-1b00fb8379744a1da19686725244e79d/`. Each has normalized and native AIPerf requests, cell result, controller validation, timing, server logs/telemetry, and `observation-receipt.json`.
- Agent workspace and Codex events: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/proposals/attempt-0002/`. The first attempt in `attempt-0001/` failed citation validation before GPU evaluation; its failure receipt and notes are preserved. The validator was fixed and the second attempt produced the measured proposal.
- Aggregate: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/report/suite-front.json`, `suite-front.csv`, `feedback.json`, per-task `pareto-*.svg`, and `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/inspection/INDEX.md`. `ledger.sqlite3` records transitions and outcomes.
- Qualification: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/qualification-report.json` reports `search_allowed=true`, grade `exploratory_four_task`.

The candidate requested queue/batch, token-budget, cache/memory, and graph diagnostics. Receipts state what exists: queue and cache gauges plus raw server metrics/logs are available; per-step batch composition, actual per-request prefill chunks, and structured graph coverage are not. No extra GPU profile was run. This tracked folder includes 39 compact machine-readable result, proposal, qualification and timing files with checksums in `ARTIFACTS.json`. The full raw request/server/GPU exports remain local under `.artifacts` and are ignored by Git.

**Next checkpoint:** repeat matched B0 and this candidate across the four tasks before claiming a tail-latency gain; then allow the agent to use the confirmed or rejected finding for its next proposal. The search controller can resume with `iar search --campaign configs/campaign-ops4.json --backend real --max-proposals 2 --resume`; that command spends one more four-task screen and does not itself confirm the first candidate.
