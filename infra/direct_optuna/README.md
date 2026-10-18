# Direct Optuna implementation

Completed study: [protocol](../DIRECT_OPTUNA_RUN.md), [results](../../results/2026-10-18-direct-optuna/README.md), [replication criteria](../../docs/REPLICATION.md).

## Components

| File | Responsibility |
|---|---|
| `prepare.py` | Deterministically generate frozen mixed workload and prefix warmup inputs using the model tokenizer |
| `run.py` | Adapt pinned upstream auto-tuning-vllm: Optuna TPE, conditional graph field, B0/finalist enqueue, objective validation, SQLite and status |
| `measure.py` | GuideLLM requests, cache reset/warmup, token/cohort verification, server counters, per-point exports |
| `launch.sh` | Pinned Docker invocation, host model/environment/cache mounts, phase logs and timeout; refuses an existing phase DB |
| `chain.sh` | Search → frozen selection → confirmation → report; skips phases with completion receipts |
| `select_confirmation.py` | Freeze up to three development Pareto extrema before reading test results |
| `health.py`, `monitor.sh` | Container/heartbeat/handoff monitoring, GPU samples and report refresh; no automatic experiment changes |
| `report.py` | Native exports → aggregate/per-class CSVs and development/all-run plots |
| `compare.py` | Committed CSVs → side-by-side development/test report with matching B0s |
| `final_plots.py` | Committed CSVs → readable held-out operating curves and Pareto projections |
| `archive.py` | Immutable raw-evidence bundle plus hashes; verify every archived file |
| `requirements.txt`, `Dockerfile` | Benchmark environment pins and standalone image recipe |

Upstream revision: `bc856d4cad5f14d83b1bd284fbd7187d75c8c496`. Optuna 4.5.0, GuideLLM 0.7.1. The runtime used the pinned vLLM base image with read-only mounts for `/opt/tune-env` and the upstream checkout. The standalone Dockerfile has not been build-tested. A fresh machine still needs the pinned model, CUDA/Docker stack and benchmark environment; this is not a one-command portable installer.

## Read-only report workflow

From the repository root:

```bash
python3 infra/direct_optuna/archive.py --verify
python3 infra/direct_optuna/compare.py
.venv/bin/python infra/direct_optuna/final_plots.py
```

The first two commands use Python 3.11+ standard library. Plots need matplotlib. These work from committed files and do not need Docker/model weights.

To regenerate the native-derived CSVs and all original plots, restore the [evidence archive](../../results/2026-10-18-direct-optuna/evidence/README.md) if the local study is absent, then:

```bash
MPLCONFIGDIR=/tmp/iar-reports .venv/bin/python infra/direct_optuna/report.py
python3 infra/direct_optuna/compare.py
.venv/bin/python infra/direct_optuna/final_plots.py
```

`report.py` requires numpy/matplotlib and the native artifact layout. It caches the input signature in `report-state.json`; unchanged inputs do not trigger unnecessary redraws.

## Execution boundary

The host-specific runner hardcodes `.artifacts/optuna-direct-v1`, the GPU UUID and NVMe model/environment paths. The model generator also writes that study directory. Do not reuse it to overwrite a finished campaign. Before a new study, parameterize/version those paths and freeze the protocol. This cleanup changes documentation/reporting/archive tooling, not the measured search/evaluation algorithm.

The earlier `iar` CLI in `src/inference_autoresearch/` runs different AIPerf/Codex campaigns. It is not the entry point for this direct GuideLLM study.
