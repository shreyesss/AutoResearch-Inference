# Experiment tracking and logging

## Three storage layers

| Layer | What belongs here | Current example |
|---|---|---|
| Versioned code / protocol | Exact search domain, baseline, workload generator, evaluator and dependencies | `infra/direct_optuna/`, `configs/direct-optuna-study.json` |
| Committed result package | Analysis, CSVs, plots, manifests and durable raw-evidence snapshot | `results/2026-10-18-direct-optuna/` |
| Local execution workspace | Mutable status, live logs, containers' outputs and databases | `.artifacts/optuna-direct-v1/` |

The direct study's entire completed execution workspace is also preserved in its [evidence archive](../results/2026-10-18-direct-optuna/evidence/README.md). Older studies may only have compact exports in Git; their READMEs state the local evidence locations. Do not infer that all historical raw logs are backed up in this repository.

## Direct-study evidence map

Paths below are relative to `.artifacts/optuna-direct-v1/` or the archive root.

| Path | Contents |
|---|---|
| `search-trials.json`, `confirmation-trials.json` | Original trial IDs, sampled and resolved settings, objective values, timing and outcome |
| `search.sqlite3`, `confirmation.sqlite3` | Native Optuna state; confirmation IDs map through `search_trial` attributes |
| `*-protocol.json`, `*-resolved-config.json`, `*-source-hashes.json` | Measured protocol, resolved search configuration and exact source hashes |
| `confirmation-selection.json` | Frozen finalist selection and B0-before/after ordering |
| `dev-*.jsonl`, `test-*.jsonl`, `*-warmup.json` | Exact frozen request pools and separate cache warmup inputs |
| `{phase}/trial_N/c*-window*/guidellm.json` | Native per-request results, request bodies and client metrics |
| `point.json`, `validation.json` | Request/token/cohort checks and completion receipts |
| `command.json`, `measurement-spec.json` | Executed client arguments and point protocol |
| `metrics-before.prom`, `metrics-after.prom` | Server counters around each measured point |
| `logs/{study}/trial_N/{controller,vllm,benchmark}.log` | Controller lifecycle, server startup/runtime and benchmark logs |
| `search-container-recovered.log` | Recovered full search console; the small `search-console.log` retains the handoff error |
| `confirmation-recovery.json` | Recorded handoff failure, recovery and limitations of the root-cause diagnosis |
| `gpu-monitor.csv` | GPU utilization, memory and power observations |
| `status.json`, `measurement-progress.json`, `monitor-health.json` | Last observed controller/measurement/container state; timestamps are part of their meaning |
| `*-finished.json` | Phase completion counts; authoritative for completed work |
| `preflight-attempt-*`, `client-smoke-NOT-REAL.json` | Failed setup and explicitly labelled mock compatibility evidence; excluded from performance results |

Search finished successfully but its original shell handoff failed. The phase-only monitor did not flag the missing confirmation stage. The corrected monitor alerts on a stalled handoff, and launcher functions are parsed before long-running commands. The final archive preserves both the failure and recovery; no failed event is erased.

## Compatibility and reporting

Compare metrics only at a matched model/image, hardware, input/cache policy, load mode, concurrency/rate, split, percentile definition and completion policy. Development and test have different prompts: each uses its own B0. Calibration's shorter cohorts are not the candidate baseline. GuideLLM's native token-weighted ITL percentile is retained separately from the study's request-weighted TPOT percentile.

The human-facing comparison uses original search IDs. In confirmation: trial 0=B0 before, 1=search 9, 2=search 10, 3=search 24, 4=B0 after.

## Starting future studies

Use a new study ID and output directory. Freeze config, inputs, objectives, seed, cache preparation, failure policy and finalist rule before measurements. Preserve unsuccessful trials and every intervention. Maintain append-only phase logs, native exports and a frozen selection receipt before test. Record code/image/model hashes at execution, not only the current Git HEAD.

The existing direct launcher uses a fixed study directory and refuses an existing phase database. `prepare.py` writes that same directory and must not be rerun over completed inputs. Parameterizing the runner for multiple new study IDs is future engineering work, not an already-supported CLI feature.

When publishing a completed study: generate CSV/plots, verify cohort counts and source mapping, freeze and verify evidence, update the research index, and commit the result with its limitations. Do not mix mock results or incomplete cohorts into a frontier. Do not commit model weights, environments, credentials or caches.
