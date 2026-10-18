# Codebase map

## Direct Optuna study

`infra/direct_optuna/` is the active implementation for the completed Optuna/GuideLLM experiment. The [component map](../infra/direct_optuna/README.md) identifies workload generation, controller, evaluator, lifecycle, monitoring, archival and reports. `configs/direct-optuna-study.json` is its serving domain; phase receipts capture actual evaluation settings.

## Earlier reusable AIPerf / Codex harness

| Component | Location | Role |
|---|---|---|
| CLI | `src/inference_autoresearch/cli.py` | `iar` entry point for earlier campaigns |
| Workloads | `src/inference_autoresearch/workloads/` | Registry, source/asset qualification |
| Benchmark adapters | `src/inference_autoresearch/benchmark/` | AIPerf execution and adaptive/SLA profiling |
| Runtime | `src/inference_autoresearch/runtime/` | Docker serving configuration and lifecycle |
| Evaluation | `src/inference_autoresearch/evaluation/` | Cell/suite validation, splits, sensitivity and SLA policies |
| Search | `src/inference_autoresearch/search/` | Codex proposer, Optuna variants, gates and reports |
| Storage | `src/inference_autoresearch/storage/` | Ledger and inspection exports |
| Agent instructions | `agent/` | Earlier Codex skill, reference, environment and research policy |
| Containers | `deploy/` | Earlier harness and isolated proposer runtime |
| Tests | `tests/` | Unit/integration-style checks for those versioned components |

These modules remain in their original paths because tests, configs and historical records reference them. Their existence is not evidence that every earlier proposed feature is active in the direct study. The current study uses GuideLLM and no LLM proposer. All changes from the organization task are documentation, report/evidence tools and imported reference material; no serving/evaluation algorithm is silently replaced.

## Checks

For the preserved research package: `python3 scripts/check-research-records.py` and `python3 infra/direct_optuna/archive.py --verify`. The former checks the registry/import hashes and recomputes direct-study request quantiles/counts from the archived native records against the committed CSVs.

The older package tests use `.venv/bin/pytest`; they are not a scientific repeatability test and do not establish performance. Reporting commands do not start a GPU workload. See [tracking policy](TRACKING.md) before creating a new campaign.
