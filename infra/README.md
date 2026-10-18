# Experiment tooling

## Current completed study

[Direct Optuna implementation](direct_optuna/README.md) · [runbook](DIRECT_OPTUNA_RUN.md) · [results](../results/2026-10-18-direct-optuna/README.md).

The eight-control Optuna/GuideLLM search and held-out confirmation are complete. Reporting, plotting and evidence verification run without a GPU. Use a new study ID and reviewed protocol for additional experiments.

## Earlier experiment tooling, retained

| Stage | Main record / tools |
|---|---|
| Input/client capability | [CAPABILITY_SPIKE](CAPABILITY_SPIKE.md), [DATASET_QUALIFICATION](DATASET_QUALIFICATION.md), [WORKLOAD_CONTROL_MATRIX](WORKLOAD_CONTROL_MATRIX.md) |
| Load calibration and sensitivity | [B0_LOAD_CALIBRATION](B0_LOAD_CALIBRATION.md), [SEQUENCE_CAP_SENSITIVITY_PILOT](SEQUENCE_CAP_SENSITIVITY_PILOT.md), [MANUAL_SERVING_SEARCH](MANUAL_SERVING_SEARCH.md) |
| Four-task suite | [OPS4_STUDY](OPS4_STUDY.md), [OPS4_BASELINE](OPS4_BASELINE.md) |
| Adaptive / simulator research | [AIPERF_ADAPTIVE_FINDINGS](AIPERF_ADAPTIVE_FINDINGS.md), [BLISS_SPIKE](BLISS_SPIKE.md) |
| Earlier SLA / Codex runs | [V3C_RUN](V3C_RUN.md), [SLA_AGENT_HANDOFF](SLA_AGENT_HANDOFF.md), [OVERNIGHT_V2_RUN](OVERNIGHT_V2_RUN.md) |
| Fast pilot v4 | `run_fast_operator_curve_v4.py`, `plot_fast_pilot_v4.py`, [result record](../results/2026-10-18-fast-pilot-v4/README.md) |

Those documents describe their own checkpoints. They are not instructions to launch the current study. Existing paths remain stable so historical commands, tests and provenance continue to resolve.

[Research history](../docs/RESEARCH.md) · [original infra README](../docs/history/INFRA_README.md)
