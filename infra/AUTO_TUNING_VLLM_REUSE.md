# Reuse assessment: InseeFrLab auto-tuning-vllm

**Status: outer study implemented with Optuna's public ask/tell API; the upstream trial controller was not adopted.** Reviewed the upstream repository at commit `bc856d4cad5f14d83b1bd284fbd7187d75c8c496` on 18 October 2026. Its Apache-2.0 license permits reuse with the required notices. See the [repository](https://github.com/InseeFrLab/auto-tuning-vllm) and [architecture](https://github.com/InseeFrLab/auto-tuning-vllm/blob/bc856d4cad5f14d83b1bd284fbd7187d75c8c496/docs/architecture.md).

The v2 overnight search uses a persistent SQLite Optuna study and multiobjective
TPE with six startup trials for an 18-proposal budget. Each valid frozen mixed
cell supplies two exploratory objectives: matched-B0 output-throughput ratio
(maximize) and the worse of matched-B0 TTFT/TPOT p90 ratios (minimize). Every
raw metric remains in the ledger. This is a sampler signal, not an SLA or a
confirmed improvement. The evaluator and GPU lease remain in our controller;
one mixed triage cell is run per proposal. See
[`optimizer.py`](../src/inference_autoresearch/search/optimizer.py) and
[`controller.py`](../src/inference_autoresearch/search/controller.py).

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

## Adoption decision and remaining validation

The adapter spike found that the upstream controller would replace our trusted
server lifecycle and benchmark protocol. We therefore chose its Optuna study
pattern through Optuna directly. CPU-only mock search/resume checks passed;
the first matched real mixed B0/candidate run and timing comparison remain to
be measured before claiming an effective overnight optimizer.

1. The upstream integration boundary was reviewed at the pinned commit. Its built-in trial owns local vLLM/GuideLLM execution, so it does not preserve our Docker/AIPerf evidence contract without replacing its core controller.
2. The v2 controller now maps each Optuna trial to a validated serving configuration and one frozen AIPerf mixed cell. SQLite stores sampler state; the ledger stores configuration, cell IDs, raw metrics and decisions. The CPU-only mock test checks a two-objective study, one mixed cell per candidate and resume without replaying prior cells.
3. The next check is one real matched B0/candidate cell. Inspect flags, request accounting, p90 ratios, startup time and Optuna values against the raw evaluator report. Then measure total GPU minutes and repeat noise before comparing the sampler with the Codex agent.

The outer study and the agent can then receive the **same** eligible serving domain, matched evaluation policy and GPU-time budget. AIPerf continues to search traffic rate inside selected server configurations. Upstream's GuideLLM synthetic/concurrency or trace results must not be pooled with our AIPerf fixed-schedule baseline.
