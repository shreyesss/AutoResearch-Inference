# Direct auto-tuning-vllm experiment

This is the concrete implementation selected after `OPTUNA_OPERATOR_CURVE_PLAN.md`.
The active optimizer is **Optuna multivariate TPE**, not an LLM. The upstream
InseeFrLab controller owns study creation, ask/tell, vLLM launches, trial cleanup,
SQLite storage and objective extraction. GuideLLM 0.7.1 generates traffic and
records measurements. Our adapter defines the mixed workload, cache conditioning,
two measurements per launch, conditional graph settings and result validation.

Upstream commit: `bc856d4cad5f14d83b1bd284fbd7187d75c8c496`.
Source: https://github.com/InseeFrLab/auto-tuning-vllm
Optuna: 4.5.0; `multivariate=True`, `group=True`, seed 20261018.
Runtime: the existing vLLM 0.28.0 image digest and model files. Benchmark packages
are in a separate environment; vLLM runs with the image's original Python.
The NVMe model mirror was SHA-256 checked against all 18 source weight shards.
Model/hardware: Qwen/Qwen3.8-27B, BF16, tensor parallelism 1, context limit
40,960, on one NVIDIA RTX PRO 6000 Blackwell Server Edition GPU (96GB class).

## Input and measurement

| Class | Mix | Target input tokens | Forced output tokens | Research p90 TTFT |
|---|---:|---:|---:|---:|
| Chat | 45% | 512 | 256 | 1,500ms |
| Agent-like | 20% | 4,096 | 512 | 2,500ms |
| Code-like | 20% | 2,048 | 512 | 750ms |
| Document | 15% | 8,192 | 256 | 12,000ms |

TPOT research target: p90 <=70ms/token for every class, zero observed errors.
This is a synthetic service-shaped mix. It is not a production trace, a coding
correctness test, or a multi-turn agent benchmark. Meaningful task templates are
expanded with synthetic reference material; exact generation length is forced.
Input counts include the Qwen template and are within four tokens of each target;
the exact count for every frozen request is stored. Thinking is disabled using
the pinned template's `enable_thinking=false` setting.

Each balanced block has 20 requests. Development has two disjoint 1,200-request
pools; held-out inputs have two disjoint 400-request pools. Input suffixes are
unique. The intended shared prefix fraction is 50%, with 16 prefixes per class,
Zipf(1.2) popularity. This target must be compared with actual cache-hit counters.
Prefix-cache off receives identical inputs. Prefixes are prepared before each
point; measured full prompts are never used for cache warmup.

The initial duration-based proposal was changed after inspecting GuideLLM's
`MaxDurationConstraint`: timed termination can cancel in-flight work. The direct
run instead uses native `max_requests` cohorts, validates completion and output
caps, and retains every request record. No incomplete cohort enters the optimizer.

- Calibration: one B0 launch, concurrency 1/4/8/16/32; 8 requests for the
  single-client floor and 40 for each other point. These are quick development
  diagnostics, not tail-SLA confirmation.
- Choose the first tested concurrency >=4 reaching 90% of the largest observed
  calibration throughput. This is an observed anchor, not a proven capacity.
- Search: 120 requests at that anchor and 120 at half that concurrency, minimum
  one. Both use the same server launch. The two points use different frozen
  input pools. Cache preparation is identical across configurations.
- Each point has a 600-second external watchdog. A timeout is a failed trial,
  not a shortened successful measurement. Full wall time and warmup are recorded.
- The first search trial is matched B0. The configured total is B0 plus 24
  candidates; nine startup observations include B0, leaving eight initial
  candidate observations before guided sampling, assuming successful trials.
- Three consecutive failed trials stop the campaign for inspection. Every
  launch takes the shared GPU lease; only one configuration runs at a time.
- Once search ends, freeze up to three distinct development Pareto extrema
  (throughput, TTFT, TPOT). If B0 dominates all candidates, test the best observed
  tradeoffs and report that negative result. The selection is saved before any
  held-out execution. Run B0, the selected candidates, then B0 again on held-out
  inputs at half-anchor / anchor / twice-anchor, 120 requests per point. Test
  results never feed the search sampler. The B0 repeat exposes drift; it does not
  by itself establish statistical confidence in every small difference.

The optimizer maximizes `output_tokens_per_second_mean` and minimizes
`time_to_first_token_ms_p90` and `inter_token_latency_ms_p90` at the same higher
concurrency for every configuration. GuideLLM's **inter_token_latency_ms** is
`(last token - first token)/(output tokens - 1)` per request, matching our decode
TPOT definition. Its separately named `time_per_output_token_ms` includes TTFT
and is not substituted. p50/p90/p99 and per-class target attainment are also saved.
GuideLLM's native aggregate ITL is weighted by output-token count. We retain that
native value but calculate the study's latency percentiles directly from request
records with **one vote per request**, matching a user-level interpretation.
The low-concurrency point is diagnostic; it cannot be cherry-picked as a trial's
optimization score. Class target passes are observations, not confidence claims.
The three objectives are raw throughput and latency. Class SLO targets are
reported alongside them; they are not hard feasibility constraints in this
Pareto study. An open-loop SLA-capacity campaign is a separate follow-up.

## Initial live checkpoint — 18 October, 11:41 UTC

Calibration completed with 168/168 valid requests, exact input/output token
counts, and no request failures. These short cohorts select search loads:

| Concurrent clients | Requests | Output tokens/s | p90 TTFT ms | p90 TPOT ms |
|---:|---:|---:|---:|---:|
| 1 | 8 | 26.3 | 687.8 | 37.8 |
| 4 | 40 | 88.6 | 1,200.1 | 41.4 |
| 8 | 40 | 157.9 | 2,004.4 | 43.3 |
| 16 | 40 | 199.6 | 3,760.6 | 51.1 |
| 32 | 40 | 339.9 | 8,471.4 | 69.5 |

The rule selected **16 and 32 concurrent clients**. Candidate scoring uses the
32-client point. Held-out curves use 16/32/64. Achieved requests/s is measured;
there is no fixed offered requests/s or Poisson arrival process in this
closed-loop protocol. Each completed request frees a client slot for another.
The initial fill and final drain are included in these finite cohorts.
The matched search B0 is measured again with 120 requests at each search load;
the smaller calibration numbers above are not the improvement reference.

Measured prefix-hit fraction was about 39–42% of queried prompt tokens, despite
the intended 50% shared-text prefix, because reusable cache blocks and common
text are different quantities. Full cache counters remain in each point folder.

The **matched search B0** completed at 11:50 UTC with 240/240 valid requests:

| Concurrent clients | Requests | Output tokens/s | p90 TTFT ms | p90 TPOT ms |
|---:|---:|---:|---:|---:|
| 16 | 120 | 275.2 | 3,276.1 | 50.8 |
| 32 | 120 | 378.9 | 5,388.3 | 69.9 |

Full trial wall time: 540.6 seconds. Upstream recorded 164.2 seconds of server
startup and 363.1 seconds of benchmark work, including preparation and client
setup. Optuna then automatically launched candidate 1. This is the reference
for candidate deltas; no candidate improvement was established at this checkpoint.

At **12:08 UTC**, B0 and two candidates had completed (720/720 measured search
requests valid, zero failed trials); candidate 3 had started automatically.

| Search trial | Output tokens/s at 32 clients | p90 TTFT ms | p90 TPOT ms | Full trial minutes |
|---|---:|---:|---:|---:|
| B0 / 0 | 378.9 | 5,388.3 | 69.9 | 9.0 |
| 1 | 299.1 | 8,539.4 | 93.0 | 9.1 |
| 2 | 322.2 | 6,970.5 | 80.7 | 7.9 |

B0 dominates both completed candidates at the scoring load. There is no
improvement yet. These are startup exploration samples; after B0 plus eight
startup candidates, the remaining 16 trials use guided TPE sampling. The live
report and status files supersede this timestamped snapshot.

## Serving search

See `configs/direct-optuna-study.json` for the executable domain. Eight fields:
batched tokens, sequence cap, GPU memory fraction, long-prefill threshold, async
scheduling, eager mode, CUDA graph cap, and prefix caching. Multiple fields may
change per trial. Graph cap is only sampled when graphs are enabled. There are
9,216 nominal conditional combinations before runtime equivalences/invalidities.
MTP, precision, model, hardware, context length and chunked-prefill enablement
remain fixed for this study.

## Inspection

- Calibration tmux: `tmux attach -t iar-optuna-calibration`
- Search tmux, once started: `tmux attach -t iar-optuna-search`
- Its `progress` window shows state; `logs` tails the trial and chain logs.
- This session runs `chain.sh`: search, frozen finalist selection, confirmation.
- Report/GPU monitor: `tmux attach -t iar-optuna-monitor`
- Status: `.artifacts/optuna-direct-v1/status.json`
- Current workload stage: `measurement-progress.json`; actual container state
  and heartbeat age: `monitor-health.json`. Unexpected exit/stale heartbeat
  creates `monitor-alert.json`. The monitor reports failure; it does not silently
  restart or change an experiment.
- Trial history: `.artifacts/optuna-direct-v1/trials.json`
- Phase histories: `search-trials.json` and `confirmation-trials.json`.
- Database: `.artifacts/optuna-direct-v1/search.sqlite3`
- Logs: `.artifacts/optuna-direct-v1/logs/`, plus phase console logs.
- Native measurements: `.artifacts/optuna-direct-v1/{phase}/trial_N/`.
- Report: `results/2026-10-18-direct-optuna/index.html` with points/class CSVs,
  p50/p90/p99 curves and the matched-anchor observed Pareto plot.

Do not compare calibration scores against search scores as a claim of improvement:
they have different cohort sizes. The matched reference is `search/trial_0`.
Repetitions and independent tests are required to distinguish close apparent wins.
This run's concurrency curves do not establish open-loop SLA capacity. AIPerf is
not running inside this direct GuideLLM campaign.

The currently running container uses the pinned base image with the isolated
benchmark environment and upstream checkout mounted read-only. The Dockerfile
under `infra/direct_optuna/` specifies the equivalent dependency installation
for a self-contained image; that Dockerfile has not yet been build-tested.

The upstream default enables its own baseline sweep; this is explicitly disabled
because we enqueue our fixed B0 and account for its trial budget ourselves. The
initial attempt exposing that default was stopped before measurements and retained
under `preflight-attempt-01/`.
