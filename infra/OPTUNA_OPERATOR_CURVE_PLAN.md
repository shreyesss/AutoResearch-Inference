# Proposed Optuna serving study

**Operational update:** the user subsequently selected direct use of
`InseeFrLab/auto-tuning-vllm`. The concrete run is documented in
[DIRECT_OPTUNA_RUN.md](DIRECT_OPTUNA_RUN.md): upstream Optuna controller +
GuideLLM, with 120-request cohorts per search point. That document supersedes
this proposal's AIPerf implementation choice and duration-based search windows.

2026-10-18. Discussion proposal, not an activated campaign. Existing workload,
SLA and campaign files have not been changed by this proposal.

## Decision

Use Optuna to choose combinations of vLLM settings. Use AIPerf to generate
traffic and measure them. Keep the LLM available for interpreting evidence,
investigating failures and proposing new mechanisms outside the parameter
domain. It need not propose every numeric configuration.

Eight small, noisy pilot trials do not establish whether LLM search or Bayesian
optimization is superior. They do justify testing a standard optimizer against
a better defined benchmark. Neither optimizer fixes measurement noise or model
startup cost.

## What the B200 experiments actually did

Sources: `Deepseek_serve/testing/workloads/latency-active-matrix.yaml`,
`Deepseek_serve/testing/common/generate_workload.py`,
`Deepseek_serve/testing/common/loadgen.py`, `Deepseek_serve/ops_latency/README.md`,
and `b200-bench-analysis/PARETO_FINDINGS.md`.

| Family | Input tokens | Exact output tokens | Mixed share |
|---|---:|---:|---:|
| Chat | 512 | 256 | 45% |
| Agent-like, single request | 8,192 | 1,024 | 20% |
| Code-like | 2,048 | 1,024 | 20% |
| Long document | 32,768 | 512 | 15% |

These are generated text/templates padded to token lengths. Labels do not imply
code correctness evaluation, real tool execution, or dependent agent sessions.
Outputs are forced with minimum/maximum token limits and EOS suppression.
Code and agent cases enable thinking; agent cases also carry tool definitions.

Prefix cases target 25%, 50%, or 75% shared input tokens, with a pool of 64
prefixes sampled using Zipf(1.2); some cases have a zero intentional reuse
control. Target fraction and achieved cache hit share are separate measurements.
The strongest comparable plotted frontier is the 8K/1K agent-f75 case.

Closed-loop sweeps hold outstanding request count constant: completions trigger
new requests, so requests/s is an outcome. Open-loop runs have a specified mean
requests/s and exponentially distributed interarrival times. This Poisson
traffic has random bunching; the active protocol defers explicit burst scenarios.
Production Mooncake replays are another experiment family.

Lengths/cache rules stay fixed within a comparison. Concurrency or offered rate
varies between points. The server is loaded once per configuration. The active
protocol specifies 120s warmup, 180s single-client floor and 300s open-loop knee
measurements with conditional rate adjustments. Archived concurrency sweeps
also used shorter points. The 255-point archive is not one uniform experiment.

## Proposed input for our first optimization study

Pinned Qwen3.8-27B, BF16, TP1, current vLLM image and one RTX PRO 6000 Blackwell.
Keep the context limit at the current 40,960. Use one mixed synthetic benchmark
with four classes, rather than four full benchmark runs per candidate.

| Class | Share | Input tokens including template | Exact output tokens | Existing research p90 TTFT target |
|---|---:|---:|---:|---:|
| Chat | 45% | 512 | 256 | 1.5s |
| Agent-like | 20% | 4,096 | 512 | 2.5s |
| Code-like | 20% | 2,048 | 512 | 0.75s |
| Document | 15% | 8,192 | 256 | 12s |

Existing p90 TPOT target: 70ms/token for each class, with zero observed errors.
These remain research targets, not established application requirements.

The reduced lengths deliberately define a new study. They reduce expensive
document prefills and long decodes while retaining mixed prefill/decode pressure.
They are not production proportions or proof of improvement on original 32K
document traffic. Hardware adaptation also requires calibrating concurrency and
requests/s; token lengths should ultimately follow the intended service.

Use temperature zero and thinking disabled for this first serving study. Exact
lengths must be verified with the pinned tokenizer/template and returned usage.
Freeze class order in balanced shuffled blocks, unique prompt suffixes and all
seeds. Provision enough unique requests to avoid dataset wraparound.

Target 50% intentional shared-prefix tokens using 16 prefixes per class and
Zipf(1.2). This smaller prefix pool is a proposed short-window fixture, not the
B200 pool or a production estimate. Verify actual token-prefix identity and
vLLM cache hit counters before admitting cache on/off as a search axis. Cache
off must still receive identical prompts. Warm the shared prefixes explicitly;
never warm full measured prompts. Report achieved reuse, including incidental
template reuse. Each load point has a disjoint suffix set and an equivalent
cache preparation protocol.

## Search and evaluation

1. **B0 calibration checkpoint.** Keep B0 loaded. Probe closed-loop client
   concurrency 1, 2, 4, 8, 16, 32 for up to 60s each, stopping on excessive
   latency or failures. Extend only if still clearly below useful load. Select
   a moderate anchor and an anchor near the observed throughput/latency knee.
   Repeat both at 120s. Record variation, sample counts, queue, dispatch lag,
   drain, cache hits and wall time. These determine whether 120s is informative.
   There is no new arbitrary per-class sample minimum for exploratory search.
2. **Configuration search.** Propose 24 distinct combinations: eight initial
   random trials followed by 16 TPE-guided trials. Explicitly configure
   `TPESampler(multivariate=True, group=True, n_startup_trials=8, seed=...)` in a
   pinned compatible Optuna version. B0 is separately recorded. One GPU means
   one configuration at a time; a configuration can change multiple fields.
3. **Per candidate.** Launch once; record startup separately; perform the same
   warmup/cache preparation as B0. Run both frozen concurrency anchors for
   120s each. Reuse the hot server. Only boot/runtime failures or gross overload
   terminate early. A valid poor result is retained as optimizer feedback.
4. **Optimizer objectives.** At the fixed higher anchor, maximize measured output
   tokens/s and minimize p90 TTFT and p90 per-request TPOT. Retain the lower
   anchor as a separate operating point. This produces raw, interpretable
   objectives; report per-class distributions so aggregate improvement cannot
   conceal a class regression. Exploratory Pareto membership is distinct from
   passing every class SLO. Do not maximize fixed low-rate throughput, where the
   offered traffic itself caps the result.
5. **Development promotion.** Periodically give promising configurations extra
   points while their server is loaded, under a fixed extra-evaluation budget.
   Those points do not change the common two-anchor objective. Reload B0 between
   search batches for drift checks; extend promising close comparisons rather
   than doubling all trials. Store all individual windows instead of averaging
   percentile values.
6. **Open-loop capacity profiles.** B0 and up to three finalists receive AIPerf
   adaptive request-rate profiles, initially capped at five 120s probes each.
   Hold workload and class proportions fixed. Use the existing class-aware
   assessment for p90 targets; never substitute aggregate p90 for class targets.
   Verify whether native AIPerf planner feedback supports these class constraints
   or requires our existing assessment adapter before claiming SLA integration.
   If the budget ends before a boundary is bracketed, publish the measured range.
   Cap outstanding work only as an overload abort, not an invisible rate limiter.
7. **Independent confirmation.** Freeze the finalist selection. Repeat selected
   rates on disjoint prompts, prefix pools and arrival seeds at 300s/window.
   Report repeat variation and all failures/censoring. These are the held-out
   results, not feedback for the same study. A fresh study is needed to tune to
   findings from that test. Low-count tails remain descriptive.

Duration is a budget, not a promised sample count. Collect outcomes for requests
started in each window, including drain and timeouts; do not drop slow requests
from percentile calculations. Preserve AIPerf's native metric definitions and
report total wall/drain time alongside throughput. A shorter or aborted trial
cannot silently become a normal complete point. Queue growth, unmet offered
rate, generator lag and output-length mismatch invalidate capacity claims.

Closed-loop discovery produces operating curves efficiently but reduces
offered traffic automatically as responses slow. Open-loop confirmation tests
whether the service sustains an independent arrival process. Both are needed.

## Proposed search space

These are proposed values subject to pinned-runtime compatibility checks, not
newly activated fields. Use conditional sampling to avoid meaningless combos.

| Parameter | Proposed values |
|---|---|
| `max_num_batched_tokens` | 2,048 / 4,096 / 8,192 / 16,384 |
| `max_num_seqs` | 16 / 32 / 64 / 128 / 256 / 512 |
| `gpu_memory_utilization` | 0.85 / 0.90 / 0.92 / 0.95 |
| `long_prefill_token_threshold` | 0 / 1,024 / 2,048 / 4,096 |
| `async_scheduling` | false / true |
| `enforce_eager` | false / true |
| `max_cudagraph_capture_size` | 32 / 64 / 128 / 256 / 512; only when eager is false |
| `enable_prefix_caching` | false / true; after token/cache instrumentation checkpoint |

Retain the exact B0 configuration, including its effective defaults. Keep
chunked prefill enabled in this study. Record resolved async and graph settings.
Low sequence caps may perform poorly; that is measurable, not a presumed win.
Memory changes need allocated-KV, occupancy and preemption diagnostics.

MTP/speculation needs a separate natural-text workload and real acceptance
telemetry before performance claims transfer. Synthetic rejection/acceptance
simulation is insufficient. Quantization similarly needs quality checks. This
proposal does not pad the search with axes whose consequences we cannot measure.

## Transfer/stress checks after discovery

On selected configurations, use zero intentional prefix reuse; the original
longer B200-like shapes; and a deterministic burst schedule. Proposed burst:
30s at twice the mean arrival rate followed by 120s at 0.75 times the mean,
repeated twice. Its overall mean equals the steady test rate. These checks
measure transfer and robustness separately; they do not establish real
production representativeness. Fix them before selection if used as held-out
tests. Any check used to influence selection is development evidence.

## Reuse and implementation gap

`src/inference_autoresearch/search/optimizer.py` already implements Optuna
ask/tell, SQLite resume and multi-parameter proposals. Its present objective is
throughput ratio versus worst latency ratio, with six startup trials; it does
not implement this proposed study. The completed v4 pilot used Codex.
`agent/SKILL.md` prefers one interpretable override or a justified interaction;
the schema does not enforce single-parameter changes.

[auto-tuning-vllm](https://github.com/InseeFrLab/auto-tuning-vllm) provides server
trial orchestration, configurable Optuna samplers, GuideLLM benchmarking,
storage and dashboard tooling. Its
[sampler factory](https://github.com/InseeFrLab/auto-tuning-vllm/blob/main/auto_tune_vllm/core/study_controller.py)
supports TPE, GP, BoTorch, random, grid and NSGA-II. Optuna presence alone does
not prove Bayesian search was selected. Its default benchmark provider uses
GuideLLM concurrent streams; switching providers would require rebaselining.

Reuse Optuna and appropriate upstream lifecycle/reporting patterns; adapt the
existing AIPerf measurement path rather than introduce a second benchmark
definition mid-study. Necessary changes: workload fixture and cache evidence,
duration-based two-anchor runner, conditional multivariate sampler, objective
versioning, class-aware adaptive profile handoff and comparable curve reporting.
The code is not ready to launch this plan merely by changing `--proposer`.

## Expected outputs and time

Output: full candidate vectors; two matched operating points per completed
candidate; denser finalist curves; p50/p90/p99 TTFT and TPOT; throughput;
per-class target attainment; observed feasible rate ranges; separate confirmed
points; Optuna history; Pareto plots; raw requests; GPU/server diagnostics;
config/workload hashes; timings and failures. No guarantee that any candidate
beats B0. Improvement must survive repeats and the declared transfer scope.

First checkpoint: B0 calibration and repeat variability, followed by three
complete Optuna cycles with measured end-to-end time. For 24 candidates,
budget at least `24 * (startup + warmup + 4 minutes + drain)` plus B0/profile/test
work. The sampler saves proposal effort and can improve trial selection; it
does not eliminate vLLM restarts. Set the overnight wall budget from those
first cycles, not an unmeasured trials/hour promise.

References checked 2026-10-18:
- https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html
- https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/sweeping/bayesian-optimization.md
- https://github.com/InseeFrLab/auto-tuning-vllm/blob/main/docs/configuration.md
