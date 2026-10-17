# OPS4 fresh-server B0: agent handoff

**Status:** four frozen inputs replay-validated; four matched fresh-server B0 cells valid; `iar qualify` returned `search_allowed: true` on 2026-10-17. This is an exploratory inference-metrics baseline, not an SLA or production-capacity claim.

## Frozen experiment

- Campaign: `configs/campaign-ops4.json` (`qwen38-27b-ops4-v1`); baseline config ID `cfg-8d0de585f89598b2160f`.
- Model/runtime: Qwen/Qwen3.8-27B revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0`, BF16, TP1, 40,960 context, vLLM 0.28.0, AIPerf 0.13.0, single pinned RTX PRO 6000 Blackwell GPU.
- Resolved B0 serving: `max_num_seqs=512`, `max_num_batched_tokens=8192`, `gpu_memory_utilization=0.92`, prefix caching on, chunked prefill on, MTP draft tokens 0.
- Protocol: fresh server per task; three disjoint warm requests; exact frozen independent, open-loop request bodies and dispatch times; all completions accounted; raw native AIPerf records plus server/GPU telemetry. Each task has its own fixed offered load. Exact hashes and input cards are under `configs/workloads/ops-frozen/`; replay validation is `infra/ops4-frozen-validation.json`.

## Matched B0 measurements

Output rate is completed output tokens divided by the task's effective timed window, including drain. TTFT is time to first token per request; TPOT is time per output token after first token per request. All tails are observed point estimates from one finite window.

| Task / frozen source setting | Requests | Output tok/s ↑ | TTFT p50 / p90 / p99 | TPOT p50 / p90 / p99 | Queue peak; drain / dispatch | Cell wall time |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Short chat, 2.56 configured RPS; nominal 512 in / forced 256 out | 307/307 | 564.39 | 178 / 245 / 310 ms | 51.56 / 54.25 / 55.01 ms/token | 0; 10.45 / 128.81 s | 535 s |
| Agent, 0.15 configured RPS; nominal 8192 in / forced 1024 out | 27/27 | 111.34 | 1362 / 1384 / 2422 ms | 45.96 / 51.64 / 53.26 ms/token | 0; 42.55 / 205.76 s | 628 s |
| Document, 0.05 configured RPS; nominal 32768 in / forced 512 out | 18/18 | 24.15 | 5707 / 7263 / 8373 ms | 55.85 / 86.11 / 86.80 ms/token | 0; 27.49 / 354.07 s | 812 s |
| Smooth mixed, 0.10 configured RPS; engineered 45% chat / 20% agent / 15% document / 20% code | 36/36 | 55.08 | 442 / 5697 / 9030 ms | 41.99 / 58.29 / 64.84 ms/token | 1; 23.58 / 362.19 s | 771 s |

All four cells are `valid`, `normal`, and frontier-eligible, with zero failed, timed-out, canceled, censored or undispatched requests. Server prefix-cache hit fraction was 0 in these cold streams; MTP was off. Dispatch lag p99 was below 1.1 ms on every task. Mixed used the predeclared `bounded_transient_queue` rule: peak queue 1 and drain 6.5% of dispatch, below limits of 3 and 10%. The other three had zero server queue. Document and mixed have only 18 and 36 requests; their p99 estimates are especially uncertain.

The four cells took 2751.1 s total (45.9 min). Fresh-server startup alone took 321–371 s per cell. A four-task candidate at this protocol will consume similar GPU time; use the recorded budget and avoid claims of a fast search loop that these timings do not support.

## Inspect the exact evidence

- B0 evaluation: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/qwen38-27b-ops4-v1/eval-90df9f1ed1f94fa586f4cea2b1fe0913/`. Each `cell-0*` folder has `cell-result.json`, `controller-validation.json`, `timing.json`, native AIPerf exports, normalized per-request records, server logs and telemetry.
- Qualification: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/qualification-report.json`; `qualification_grade=exploratory_four_task`, `search_allowed=true`, no blocked reasons. Sensitivity is not prequalified; the first candidate may test it.
- Twelve-coordinate config frontier: `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/report/suite-front.json` and `suite-front.csv`. The B0 and first candidate are both complete point-estimate frontier configurations; see `results/2026-10-17-ops4-first-search/README.md` for their comparison. `fronts.json`, `points.csv`, four Pareto SVGs and `REPORT.md` retain per-task inspection.

The earlier `.artifacts/ops-b0/` source curves selected the four arrival points. Those calibration measurements are separate from this matched B0 and are not substituted into the search ledger. The mixed weights are engineered, not a measured production distribution. All inputs are synthetic independent turns; semantic correctness, sessions and bursty traffic are outside this first four-task campaign.
