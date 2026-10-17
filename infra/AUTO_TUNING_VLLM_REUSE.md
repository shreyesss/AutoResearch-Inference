# Reuse assessment: InseeFrLab auto-tuning-vllm

**Status: design review, no dependency or evaluator changed.** Reviewed the upstream repository at commit `bc856d4cad5f14d83b1bd284fbd7187d75c8c496` on 18 October 2026. Its Apache-2.0 license permits reuse with the required notices. See the [repository](https://github.com/InseeFrLab/auto-tuning-vllm) and [architecture](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/docs/architecture.md).

## What is directly useful

| Upstream capability | Our use |
| --- | --- |
| Optuna study with `ask`/`tell`, TPE/GP/random/NSGA-II/grid samplers, SQLite/PostgreSQL, resume, constraints and failure records | Reuse as the **outer vLLM-setting optimizer** and a reproducible comparison to the Codex research agent. Do not implement another Bayesian sampler. |
| Study YAML and typed parameter ranges/lists | Compare or adapt for our versioned conditional domain, while preserving our pinned model/runtime identity and resolved effective config hash. |
| Trial user attributes, logging, Optuna Dashboard | Expose configuration, costs and selected scalar diagnostics; keep links to our full raw AIPerf and vLLM artifacts. |
| Benchmark-provider interface and execution-backend interface | Candidate adapter seams for our AIPerf/Docker evaluator. Test these before adopting the upstream controller. |

These are implemented in upstream's [study controller](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/auto_tune_vllm/core/study_controller.py), [benchmark provider](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/auto_tune_vllm/benchmarks/providers.py), and [trial controller](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/auto_tune_vllm/execution/trial_controller.py).

## The integration boundary

The upstream standard trial launches a local vLLM Python subprocess, waits for health, benchmarks with GuideLLM, parses its metrics, then stops the process. Its built-in providers are GuideLLM concurrency, trace replay and multimodal modes. Our trusted evaluator starts a pinned Docker image, replays frozen AIPerf requests, validates every request, and archives raw evidence. Running the upstream trial unchanged would create a second serving and measurement protocol rather than reuse our measured B0. The custom benchmark-provider hook alone changes the traffic generator; the upstream trial still owns server startup. Its objective validator accepts a fixed list of throughput/TTFT/ITL/request-latency metric names, so our class-specific gates and goodput contract also need an adapter or extension. Upstream lists `optimization.n_repeats` as future work; our evaluator must continue to own repeated windows and uncertainty. See [upstream configuration](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/docs/configuration.md) and [README roadmap](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/README.md).

## Proposed adoption test after evaluator approval

1. Pin the upstream commit and record license/notice provenance. Run its existing config and sampler tests in an isolated environment. Do not vendor or copy code before the adapter choice is made.
2. Implement a small `ExecutionBackend` adapter that maps one upstream `TrialConfig` to our typed, validated `iar` candidate and returns a `TrialResult` from our complete AIPerf cell. Keep the GPU lease, Docker launcher, workload hashes, raw ledger and gate promotion in our controller. Map Optuna trial number to our configuration and evaluation IDs.
3. Prove a baseline, one valid proposal, one invalid proposal, pause/resume and a two-objective study using the **mock** evaluator. Verify trial attributes link to raw artifacts and that test results never enter study feedback.
4. Run one matched real B0/candidate cell under this adapter. Inspect resolved server flags, accounting, timings and Optuna values against our native report. Accept upstream as the outer study layer only if it preserves these invariants without invasive changes.
5. If the adapter does not preserve them cleanly, use Optuna directly through its public `ask`/`tell` API inside our existing controller. That still reuses the optimization and storage engine; it avoids duplicating a full server lifecycle. Record the failed adapter reason so this decision is reviewable.

The outer study and the agent can then receive the **same** eligible serving domain, matched evaluation policy and GPU-time budget. AIPerf continues to search traffic rate inside selected server configurations. Upstream's GuideLLM synthetic/concurrency or trace results must not be pooled with our AIPerf fixed-schedule baseline.
