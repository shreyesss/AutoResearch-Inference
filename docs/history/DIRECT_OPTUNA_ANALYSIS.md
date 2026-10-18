> Historical narrative, including development-only checkpoint and subsequent held-out update. See the [current final analysis](../../results/2026-10-18-direct-optuna/ANALYSIS.md).

# Direct Optuna search: findings and confirmation status

[Side-by-side development, held-out and baseline comparison](../../results/2026-10-18-direct-optuna/comparison.html)

## Final held-out result — 19 October 2026, 01:43 IST

**Confirmation finished: 5/5 configurations, 15/15 points, 1,800/1,800 valid requests, zero failed trials.** Together with search: 7,800 measured requests (plus 168 calibration requests).

The earlier development findings below are historical. The 10% throughput gain for search trial 9 **did not reproduce** on held-out inputs. Search trial 10 is the strongest remaining latency lead.

At 32 concurrent clients, 120 held-out requests per run:

| Original search configuration | Output tokens/s | p90 TTFT seconds | p90 TPOT ms/token |
|---|---:|---:|---:|
| B0 before | 384.39 | 6.697 | 66.00 |
| Trial 9 | 383.86 | 6.759 | 68.53 |
| Trial 10 | 387.48 | 4.437 | 68.18 |
| Trial 24 | 273.43 | 27.292 | 52.76 |
| B0 after | 386.65 | 6.263 | 67.33 |

Trial 10 reduced p90 TTFT by **29–34% against both baseline runs**, with throughput within 1% and TPOT **1.3–3.3% worse**. It changed batched tokens 8192→4096, max sequences 512→64, GPU memory fraction .92→.95. All other settings matched B0. At 16 clients it also improved TTFT (2.456s vs B0 3.179/2.893s); at 64 clients the difference was smaller (13.523s vs 14.288/13.985s). This is evidence of a latency tradeoff that carries over to held-out prompts, not a universal win or proof of statistical significance. There was only one held-out run of each candidate and two B0 runs.

Trial 9 has essentially baseline throughput at 32 clients, worse TPOT, and no meaningful TTFT gain. At 64 its throughput is only 0.8–1.8% above the two baselines. The original +10% result should not be used as a claimed optimization win.

Trial 24 again buys faster decode with much worse queueing: p90 TTFT reaches 66.99s at 64 clients. It is unsuitable for the service goals.

The full held-out values are in [points.csv](../../results/2026-10-18-direct-optuna/points.csv); [operating-curves.svg](../../results/2026-10-18-direct-optuna/operating-curves.svg) includes the confirmation runs. Confirmation IDs map to original search IDs as follows: 0=B0 before, 1=search 9, 2=search 10, 3=search 24, 4=B0 after. The dedicated TTFT–TPOT frontier plots remain development-only and are labelled accordingly.

---

Snapshot: 19 October 2026, approximately 00:57 IST. Search finished at 20:37 IST on 18 October. Held-out confirmation was recovered and started at 00:53 IST on 19 October; no held-out conclusion is claimed here. Live status is in `.artifacts/optuna-direct-v1/status.json` and `monitor-health.json`.

## Honest conclusion

Optuna found a **candidate throughput gain of 10.0%** at 32 clients, with almost unchanged decode TPOT and 2.8% worse p90 TTFT. This is worth confirming, but it is not yet a repeatable improvement. **No candidate dominates B0 on all three objectives. No configuration passes all four classes' research targets at either development load.** There is no statistical-significance result.

The sampler was Optuna 4.5.0 multivariate TPE via InseeFrLab/auto-tuning-vllm, evaluated by GuideLLM 0.7.1. No LLM proposed configurations in this experiment. Of 25 completed trials, B0 plus eight candidates were startup observations; sixteen were guided TPE trials. There were 24 unique configurations because trials 10 and 11 repeated exactly the same configuration.

## What was actually measured

- Qwen/Qwen3.8-27B, BF16, TP=1, context limit 40,960, vLLM 0.28.0, one RTX PRO 6000 Blackwell Server Edition GPU.
- One synthetic mixed workload with shared prefixes. It tests serving performance, not answer correctness or real multi-turn sessions.

| Class | Mix | Input tokens including template | Forced output tokens | Requests per 120-request point |
|---|---:|---:|---:|---:|
| Chat | 45% | ~512 | 256 | 54 |
| Agent-like | 20% | ~4096 | 512 | 24 |
| Code-like | 20% | ~2048 | 512 | 24 |
| Document | 15% | ~8192 | 256 | 18 |

Input counts are within four tokens of targets and the exact count is checked per request. Temperature 0, thinking disabled, streaming, ignore EOS to force the output length. Prefix reuse is engineered: 16 prefixes per class, Zipf(1.2), approximately 50% shared text. Actual cache-hit counters are saved; they are not assumed to equal 50%.

Each configuration received 120 requests at 16 concurrent clients and 120 at 32. A completion frees a slot for another request: **closed-loop concurrency, not fixed offered requests/s or burst arrivals**. The two load points use different frozen development pools; each configuration sees the same requests at a given load. Thus the connecting lines describe these protocol points, not a pure causal load sweep with identical prompts at every load.

Every point resets prefix cache, probes the wire format, resets again, and warms shared prefixes before measurement. Each configuration launches vLLM once and reuses it for both points. All 6,000 search requests completed with validated token counts, unique frozen request IDs, and no errored/incomplete requests. Calibration contributed another 168 requests, excluded from candidate comparisons.

Search wall time was approximately 3h26m. Per-configuration mean 8.17 minutes, median 8.34, range 6.92–9.18, including startup and preparation. The optimizer scored aggregate output tokens/s, request-weighted p90 TTFT and request-weighted p90 decode TPOT at 32 clients. TPOT is (last-token time minus first-token time)/(output tokens minus one). p50/p99, per-class metrics and server counters are also retained.

## Main development results

All entries below use the same 32-client, 120-request development point.

| Trial | Output tokens/s | p90 TTFT seconds | p90 TPOT ms/token | Interpretation vs B0 |
|---|---:|---:|---:|---|
| B0 / 0 | 378.86 | 5.388 | 69.86 | Reference |
| 9 | 416.81 | 5.541 | 69.37 | +10.02% throughput; +2.83% TTFT; -0.70% TPOT |
| 10 | 378.66 | 4.953 | 69.60 | Essentially same throughput; -8.07% TTFT, unconfirmed |
| 11 | 380.95 | 5.668 | 69.62 | Exact repeat of trial 10; its TTFT gain disappears |
| 20 | 375.37 | 7.052 | 67.29 | -3.68% TPOT at the expense of +30.88% TTFT |
| 21 | 378.17 | 5.474 | 67.49 | -3.40% TPOT with roughly baseline throughput/TTFT |
| 24 | 271.51 | 27.485 | 53.61 | -23.26% TPOT, but -28.33% throughput and +410.08% TTFT |

### Exact configurations

| Parameter | B0 | Trial 9 | Trial 10 (=11) | Trial 24 |
|---|---:|---:|---:|---:|
| max_num_batched_tokens | 8192 | 8192 | 4096 | 4096 |
| max_num_seqs | 512 | **64** | **64** | **16** |
| gpu_memory_utilization | 0.92 | 0.92 | **0.95** | **0.95** |
| long_prefill_token_threshold | 0 | 0 | 0 | **4096** |
| async_scheduling | true | true | true | true |
| enforce_eager | false | false | false | false |
| max_cudagraph_capture_size | 512 | 512 | 512 | **128** |
| enable_prefix_caching | true | true | true | true |

Chunked prefill was always enabled; model, precision, hardware and MTP-off were fixed. The eight-field domain is in `configs/direct-optuna-study.json`; there are 9,216 nominal conditional combinations. Only 24 unique configurations were measured, so this is not an exhaustive search.

Trial 9's only change is max_num_seqs 512→64. It has **no throughput improvement at 16 clients** (-0.33%), so the observation is load-dependent. Both caps exceed 32 clients: this is not evidence that restricting admission to 64 directly removed a measured queue. Changes in runtime allocation/graph behavior or timing are possible explanations, not established causes.

Trial 24 shows a useful warning about optimizing TPOT alone. Its sequence cap is 16 while 32 clients are outstanding. Exported p90 waiting requests was 16 (B0 and trial 9: 0). Faster decode is bought with much longer waiting for first token. Multiple parameters changed, so this does not isolate every causal contribution. It is mathematically nondominated, but is a poor service choice for our latency goals.

All six three-objective frontier points retain prefix caching, async scheduling and CUDA graphs. This is an association across jointly changed configurations; the study does not isolate the benefit of each feature.

## Noise and robustness

Trials 10 and 11 are an accidental same-config repeat on the same development cohorts. At 32 clients:

- Throughput: 378.66→380.95 (+0.60%).
- p90 TTFT: 4.953→5.668 seconds (+14.44%).
- p90 TPOT: 69.601→69.623 ms (+0.03%).

Two repeats do not estimate a reliable noise distribution, but demonstrate that the apparent 8% TTFT gain is not stable in these measurements. Trial 9's 10% throughput gain is larger than this pair's throughput variation, but that is not a significance test for trial 9. Candidate selection over 24 attempts can also favor lucky measurements. We need independent runs before claiming a winner.

120 requests gives only about 12 observations in the aggregate upper decile; individual classes have 18–54 requests. p99 is especially unstable. Request latencies share queueing/server conditions, so treating requests as independent repeated experiments would overstate confidence. No fabricated confidence interval or p-value is reported.

A throughput-only improvement does not establish the class-specific targets. At 32 clients, trial 9 chat p90 TTFT is 4.943s vs B0 3.613s, and chat p90 TPOT is 73.53 vs 71.62ms. Aggregate metrics can hide these regressions. None of the configurations passes every class at either measured development concurrency.

## Held-out confirmation: recovered and running

The automatic chain stopped after the successful search container exited. The shell log reports a digest fragment as a command; this is consistent with a launcher rewritten while Bash was blocked in Docker, but that root cause was not independently reproduced. The old monitor checked whether the search phase finished, so it failed to flag the missing next phase. **Earlier assurance that held-out evaluation would automatically follow was not fulfilled.**

Search data and native logs were preserved. The Docker console was recovered separately. The launcher now parses the full function before executing, appends logs, and the chain skips completed phases. Health monitoring now flags a completed search with a stalled confirmation handoff. The benchmark, optimizer objectives and selection rule have not changed.

The predeclared selection rule froze trials **9, 10, 24** before reading any test outcomes. Confirmation sequence:

**B0 → trial 9 → trial 10 → trial 24 → B0 repeat**

Each gets 120 requests at 16/32/64 clients, using held-out test-a/test-b pools. Total planned: 1,800 measured requests. Configurations are fixed, test results do not feed the optimizer, and the final B0 repeat measures temporal drift. At 16 and 64, the same test-a cohort is used; 32 uses test-b. This tests prompt generalization within the same synthetic distribution, not a new production workload.

This will be stronger evidence than the development search. It still provides only one held-out run per candidate and two baseline runs, not extensive repeated randomized trials. Small gains may remain inconclusive. An additional paired repeat would be justified if the surviving gain is close to baseline drift; no further campaign is silently added here.

## Plots and interpretation

- [p90 TTFT vs TPOT](../../results/2026-10-18-direct-optuna/ttft-tpot-pareto.svg): separate panels at 16/32 clients; lower-left is better, color is throughput, labels are trial IDs.
- [p50/p90/p99 TTFT vs TPOT](../../results/2026-10-18-direct-optuna/ttft-tpot-percentiles.svg).
- [Throughput–latency projections of the three-objective frontier](../../results/2026-10-18-direct-optuna/pareto.svg).
- [Operating curves](../../results/2026-10-18-direct-optuna/operating-curves.svg), [per-class p90](../../results/2026-10-18-direct-optuna/class-curves.svg), [all measured values](../../results/2026-10-18-direct-optuna/points.csv).

At 32 clients, the **three-objective** observed Pareto set is B0, 9, 10, 20, 21, 24. The **latency-only p90** set is 10, 21, 20, 24. Trial 9 is on the first set because of throughput; it is not on the latency-only set. Frontier membership describes measured point estimates and does not establish significance or suitability for the service. Lines connect observations, not fitted capacity curves.
