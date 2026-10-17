# AIPerf adaptive search: verified scope

Pinned installation: AIPerf 0.13.0 in `.venv`. The local capability spike previously completed three synthetic one-request iterations under `--search-planner bayesian`; that proved the interface ran, not that it found a useful load or serving configuration. A second bounded live smoke ran on the pinned B0 server.

| Question | Finding |
| --- | --- |
| What can it choose? | Numeric fields of AIPerf's benchmark configuration, including request rate and concurrency. It can probe more than one dimension and filter trials against declared SLA thresholds. |
| Can it choose vLLM knobs? | No. Its search-space paths resolve inside the AIPerf profiling configuration; it does not restart or reconfigure the serving process. Our trusted deployment controller remains necessary. |
| Which optimizer is installed? | The `bayesian` preset falls back to Optuna TPE here because the optional BoTorch/Torch dependencies are absent from the AIPerf environment. Do not describe the observed local runs as Gaussian-process BO. |
| Does it repeat trials? | Yes: each search iteration can run `--num-profile-runs` profile runs. Our live smoke uses one run/iteration for speed and makes no uncertainty claim. |
| Does it stop early? | Its search loop has iteration-level budget/convergence controls. The separate per-trial `--convergence-metric` feature is incompatible with `--search-*` in this pinned version. |
| Can it tune the rate of the frozen OPS4 trace? | No direct scalar rate on an exact fixed schedule. A rate search requires a rate-controlled run that changes timing semantics; an independently frozen schedule is then used for matched confirmation. |

This means AIPerf is useful for a **separate inner load-capacity experiment** once numeric TTFT/TPOT/error SLAs are agreed. It is not a shortcut that makes each outer server-setting candidate cheap: each adaptive iteration sends another batch of real requests. Run adaptive load search for B0 and promising finalists, then verify selected boundary points on fresh frozen traffic. Preserve the ordinary fixed-load A/B comparison for causal server-setting claims.

## Bounded live smoke

- Reproducer: [`aiperf-adaptive-smoke.sh`](aiperf-adaptive-smoke.sh), two iterations of 12 synthetic chat requests against a running B0 server. It varies AIPerf `rate` from 1.8 to 2.6 requests/s, records raw exports, and optimizes observed output-token throughput. The selected best point has no scientific status due to tiny samples and no SLA.
- Output: `.artifacts/aiperf-adaptive-ops4-spike/` (local, ignored by Git).
- Status: **completed**. `search_history.json` has two iterations, sampled configured rates 2.0996 and 2.0384 requests/s, 12/12 completed in each. It selected the second trial by observed output throughput, 134.26 versus 58.99 tokens/s. The first trial's request throughput was only 0.230 requests/s and median TTFT was 27.1 seconds, whereas the second trial's were 0.524 requests/s and 0.137 seconds. The first trial dispatched its 12 requests over roughly 42 seconds, despite its roughly 2.1 requests/s target; with `--concurrency 8`, the client had to wait for active requests to finish. There was no disjoint warmup before this smoke, and AIPerf dropped an optional GPU telemetry worker after missed heartbeats. These differences make the selected rate **uninterpretable as a capacity optimum**. They demonstrate why actual dispatch, warmup, concurrency binding, run order, and repeats must be checked before trusting an adaptive objective.
- `search_history.json`, both native per-trial exports, `console.log`, pinned `server-argv.json`, and `server.log` are saved in the output directory. The temporary B0 container was stopped and removed after evidence capture. The smoke did not alter the qualified OPS4 B0 or candidate artifacts.

## Primary sources

- [AIPerf 0.13 adaptive-search reference](https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/sweeping/bayesian-optimization.md).
- [AIPerf 0.13 tutorial](https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/tutorials/adaptive-search.md).
- Installed parser and resolver: `.venv/lib/python3.12/site-packages/aiperf/orchestrator/search_planner/parsing.py`, `.venv/lib/python3.12/site-packages/aiperf/config/flags/resolver.py`.
