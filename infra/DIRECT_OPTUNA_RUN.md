# Direct Optuna / GuideLLM study — completed

Study ID: `optuna-direct-v1`. Search: 18 October 2026. Held-out confirmation finished **19 October 2026, 01:43 IST**. All 25 search and five confirmation trials completed, zero failed trials. [Results](../results/2026-10-18-direct-optuna/README.md) · [comparison](../results/2026-10-18-direct-optuna/comparison.html) · [code map](direct_optuna/README.md).

## Question and scope

Can joint changes to eight vLLM serving controls improve the throughput/latency tradeoff on a frozen mixed workload, and does a development improvement survive unseen prompts?

This study uses Optuna 4.5.0 multivariate/grouped TPE with seed 20261018, the InseeFrLab auto-tuning-vllm controller pinned at `bc856d4cad5f14d83b1bd284fbd7187d75c8c496`, and GuideLLM 0.7.1. There is no LLM proposal loop or AIPerf adaptive traffic search in this run.

## Fixed environment

| Component | Value |
|---|---|
| Model | Qwen/Qwen3.8-27B; BF16; model revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` |
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Server Edition, 96 GB class |
| vLLM | 0.28.0; TP=1; context limit 40,960 |
| Image | `vllm/vllm-openai@sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14` |
| Static behavior | Chunked prefill enabled; MTP disabled; thinking disabled; temperature 0; streaming |
| Input identity | [workload card](../results/2026-10-18-direct-optuna/workload-card.json) and archived exact JSONL |
| Model/source identity | [model manifest](../results/2026-10-18-direct-optuna/model-manifest.json), [study manifest](../results/2026-10-18-direct-optuna/study-manifest.json), phase source-hash receipts |

The model's 18 weight shards were SHA-256 matched to the NVMe mirror. The benchmark environment was isolated from the base image's Python used by vLLM subprocesses.

## Inputs and load

| Class | Share | Input tokens including template | Forced output | Count per point | Research p90 TTFT |
|---|---:|---:|---:|---:|---:|
| Chat | 45% | ~512 | 256 | 54 | 1.5s |
| Agent-like | 20% | ~4096 | 512 | 24 | 2.5s |
| Code-like | 20% | ~2048 | 512 | 24 | .75s |
| Document | 15% | ~8192 | 256 | 18 | 12s |

The additional targets are p90 TPOT ≤70ms/token per class and zero observed request failures. These are approved research diagnostics, not hard Optuna constraints or established application SLAs.

Synthetic task templates contain repeated reference material. They are not production samples, correctness tests or dependent agent sessions. Output lengths are forced with ignore-EOS; exact input counts must be within four tokens of their targets and must match the frozen row. Every block of 20 requests is balanced 9/4/4/3.

Development pools: `dev-a`, `dev-b`, 1200 rows each. Test pools: `test-a`, `test-b`, 400 rows each. Measurement consumes the first 120 rows of each specified pool; pool size must not be reported as the number actually benchmarked. Full prompts and prefix namespaces are disjoint between splits.

Engineered reuse: 16 shared prefixes per class, Zipf(1.2) popularity, intended shared text fraction ~50%. Actual server prefix-hit counters are saved; shared text is not automatically an equal cache-hit percentage.

At each point: reset cache → one exact-token wire probe → reset cache again → warm only 64 shared prefixes (four parallel requests, one output token each) → run the fixed cohort → validate and export. Probe/warmup is outside the timed cohort.

**Closed-loop concurrency:** a completion frees a slot for the next request. There is no fixed offered RPS, Poisson arrival schedule or burst generator. Initial fill/final drain are included. Since the 16/32 points use different input pools, a connecting line is an operating-point summary, not a pure load-only causal sweep.

## Evaluation phases

| Phase | Configurations | Clients | Requests | Purpose |
|---|---|---|---|---|
| Calibration | B0 once | 1 / 4 / 8 / 16 / 32 | 8 / 40 / 40 / 40 / 40 | Select a diagnostic load anchor |
| Development | B0 + 24 trials | 16 / 32 | 120 / 120 each | Optimize joint configuration; score at 32 |
| Held-out | B0 → 9 → 10 → 24 → B0 | 16 / 32 / 64 | 120 / 120 / 120 each | Unseen prompts, operating points and baseline drift |

The calibration rule selected the first tested concurrency ≥4 reaching 90% of the highest observed calibration throughput: 32, with lower diagnostic point 16. Calibration's smaller cohorts are not the improvement baseline.

Search uses dev-a at 16, dev-b at 32. Held-out uses test-a at 16/64, test-b at 32. Both phases launch one server per configuration, reusing it across points with cache resets. The search has nine startup observations (B0 + eight candidates), then 16 guided TPE trials. Trials 10 and 11 happened to repeat exactly the same configuration: 25 trials, 24 unique settings.

The frozen finalist rule chooses up to three distinct throughput/TTFT/TPOT extrema of the development three-objective Pareto frontier. It selected 9/10/24 before any held-out measurements. No test feedback enters the sampler. Confirmation trial IDs 0/1/2/3/4 map to B0/9/10/24/B0.

## Objectives and diagnostics

At 32 clients: maximize output tokens/s; minimize request-weighted p90 TTFT; minimize request-weighted p90 decode TPOT. GuideLLM names the latter `inter_token_latency_ms`: `(last token time − first token time)/(output tokens − 1)`. Its separately named time-per-output-token metric includes TTFT and is not substituted.

GuideLLM's native aggregate ITL quantiles are token-weighted. The adapter recomputes p50/p90/p99 from individual requests, one vote each, while retaining native values separately. Logs include throughput, achieved RPS, completion counts, per-class percentiles/target checks, prefix hits, preemptions, queue/cache diagnostics, GPU utilization and phase timing. Actual per-request prefill chunk traces were not collected.

## Search domain and B0

[Executable domain](../configs/direct-optuna-study.json), [readable parameter table](../README.md#search-surface). Eight fields: batching, sequence cap, GPU memory fraction, long-prefill threshold, async scheduling, eager mode, graph cap (conditional on graphs), prefix caching. All may change jointly. MTP, model, hardware, precision, context and chunked-prefill enablement stay fixed.

B0: batch8192 / seq512 / memory.92 / long-threshold0 / async-on / eager-off / graph512 / prefix-on. The generic upstream baseline sweep is disabled; this exact B0 is explicitly enqueued.

## Validity and failure policy

Each point requires exactly 120 successful records (calibration has its declared smaller counts), zero errors/incompletes, exact frozen IDs, unique full prompts and exact measured input/output counts. Objectives must be positive finite values. Invalid evidence is not scored.

A point has a 600-second watchdog; each Docker phase has an eight-hour bound. A timeout is a failure, not a successful shortened cohort. There is no performance-based early pruning in this study. One GPU configuration runs at a time under the shared GPU lock. B0 failure or three consecutive failed trials stops the controller.

The search-to-confirmation shell handoff initially failed after all search results had completed. It was recovered without changing benchmark protocol or candidate selection. Both failure and recovery evidence are preserved; see [tracking](../docs/TRACKING.md). Phase completion is now independently checked from a mere live tmux session.

## Results and evidence limits

Search: 6,000 valid requests, ~3h26m, mean 8.17 minutes/config including startup/preparation. Confirmation: 1,800 valid requests, ~49 minutes. Plus 168 calibration requests. Trial 9's development throughput gain did not reproduce. Trial 10 improved held-out p90 TTFT at 32 clients by 29–34%, with throughput within 1% and TPOT 1.3–3.3% worse. This is a latency tradeoff, not an all-metric victory.

The test suite offers one run/candidate and two B0 runs. p99 and class tails remain descriptive; repeated paired experiments are needed before a stronger repeatability claim. [Replication criteria and next checkpoint](../docs/REPLICATION.md).

All raw requests, logs, databases, frozen input files and receipts are now preserved in the [checksummed evidence archive](../results/2026-10-18-direct-optuna/evidence/README.md). [Implementation / read-only commands](direct_optuna/README.md). Original chronological launch notes remain in [history](../docs/history/DIRECT_OPTUNA_CHECKPOINTS.md).
