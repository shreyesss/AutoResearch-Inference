# Research results

[Research context](../docs/RESEARCH.md) · [machine-readable registry](registry.json) · [replication criteria](../docs/REPLICATION.md)

## Latest completed study: direct Optuna

- [Side-by-side development/test/B0](2026-10-18-direct-optuna/comparison.html)
- [Findings, exact configurations and noise](2026-10-18-direct-optuna/ANALYSIS.md)
- [Held-out operating curves](2026-10-18-direct-optuna/heldout-operating-curves.svg) / [held-out Pareto](2026-10-18-direct-optuna/heldout-pareto.svg)
- [All development and test plots](2026-10-18-direct-optuna/index.html)
- [Raw evidence, logs and inputs](2026-10-18-direct-optuna/evidence/README.md)

7,800 search/test requests plus 168 calibration requests. Trial 10's TTFT tradeoff survived held-out prompts; trial 9's throughput gain did not. One held-out run per candidate does not establish statistical significance.

## Earlier studies

| Record | Scope |
|---|---|
| [Short chat](2026-10-17-short-chat/README.md) | B0/MTP forced-length diagnostic |
| [OPS4 first search](2026-10-17-ops4-first-search/README.md) | Four-task Codex proposal/evaluation |
| [V2 gate](2026-10-17-v2-first-gate/README.md) | Mixed 36-request screen and initial TPE checkpoint |
| [Research reset](2026-10-18-research-reset/README.md) | Adaptive AIPerf, BLIS feasibility, small matched repeat |
| [Fast pilot v4](2026-10-18-fast-pilot-v4/README.md) | Eight proposal screens and exploratory three-rate curves |
| [B200 reference](../docs/B200_REFERENCE.md) | Imported DeepSeek analysis; separate workloads and hardware |

Historical reports retain their original checkpoint wording. They are evidence records, not current launch status. Raw evidence coverage differs by study and is stated in each record. Do not compare incompatible workload/model/load protocols as one Pareto frontier.
