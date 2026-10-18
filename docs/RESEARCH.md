# Research index

The goal is better measured serving configurations and understandable tradeoffs. An optimizer or LLM is an experiment-selection tool, not the outcome.

## Current completed study

- [Protocol and environment](../infra/DIRECT_OPTUNA_RUN.md)
- [Implementation and reproducibility commands](../infra/direct_optuna/README.md)
- [Development/test/B0 comparison](../results/2026-10-18-direct-optuna/comparison.html)
- [Findings and negative results](../results/2026-10-18-direct-optuna/ANALYSIS.md)
- [Held-out curves](../results/2026-10-18-direct-optuna/heldout-operating-curves.svg) and [held-out Pareto](../results/2026-10-18-direct-optuna/heldout-pareto.svg)
- [Evidence archive](../results/2026-10-18-direct-optuna/evidence/README.md)

Trial 10's latency tradeoff survived held-out inputs; trial 9's development throughput gain did not. No maximum sustainable capacity or statistically confirmed winner is established.

## Completed results and research checkpoints

| Study | Evaluator / selection | What the record supports |
|---|---|---|
| [Short-chat vertical slice](../results/2026-10-17-short-chat/README.md) | AIPerf; B0 vs MTP1 | Forced-length short-chat tradeoffs; repeat/quality gates were still open |
| [OPS4 first search](../results/2026-10-17-ops4-first-search/README.md) | AIPerf; Codex proposal | Four-task exploratory evaluation, telemetry and proposal receipts |
| [V2 first gate](../results/2026-10-17-v2-first-gate/README.md) | AIPerf; Codex/TPE checkpoints | Small mixed screen and startup-verifier correction; not confirmed capacity |
| [Adaptive load / BLIS spike](../results/2026-10-18-research-reset/README.md) | AIPerf adaptive planner / BLIS | Integration feasibility; BLIS was not calibrated for this hardware/model |
| [Fast pilot v4](../results/2026-10-18-fast-pilot-v4/README.md) | Codex / AIPerf | Eight 36-request screens and three-rate exploratory curves; no sealed test |
| [Direct Optuna](../results/2026-10-18-direct-optuna/README.md) | Optuna TPE / GuideLLM | Completed search plus independent held-out inputs and bracketing B0 repeats |
| [Imported B200 reference](../docs/B200_REFERENCE.md) | External DeepSeek campaign | 255 report points with source provenance; separate protocol, model and hardware |

Do not merge these studies into one frontier: workloads, models, client modes, cache treatment, percentiles and protocols differ. Imported B200 points include multiple views of measurements; row count is not a count of independent experiments.

## Earlier design documents, preserved

These explain the evolution of the project. Their future-tense plans and launch status are historical, not statements about the completed direct study.

| Topic | Documents |
|---|---|
| Initial architecture | [UNDERSTANDING](../UNDERSTANDING.md), [IMPLEMENTATION](../IMPLEMENTATION.md), [EXPERIMENT_DESIGN](../EXPERIMENT_DESIGN.md) |
| Early manual results | [EXECUTIVE_SUMMARY](../EXECUTIVE_SUMMARY.md), [manual search](../infra/MANUAL_SERVING_SEARCH.md) |
| Evaluator redesign | [EVALUATION_V2_PLAN](../EVALUATION_V2_PLAN.md), [adaptive evaluation](../infra/ADAPTIVE_EVAL_PLAN.md), [OPS4 redesign](../infra/OPS4_EVALUATION_REDESIGN.md) |
| Agent and search plans | [agent research](../infra/AGENT_RESEARCH_PLAN.md), [search expansion](../infra/SERVING_SEARCH_EXPANSION_PLAN.md), [Optuna curve plan](../infra/OPTUNA_OPERATOR_CURVE_PLAN.md) |
| Previous navigation / checkpoint prose | [old root README](history/ROOT_README.md), [old infra README](history/INFRA_README.md), [direct-study launch checkpoints](history/DIRECT_OPTUNA_CHECKPOINTS.md), [original development/held-out narrative](history/DIRECT_OPTUNA_ANALYSIS.md) |

## Current direction: source-level research

The parameter study stops here. The [new plan](../research/README.md) uses B200 evidence, refreshed Deepseek_serve source, online literature and PR analysis to produce the requested number of hypotheses, experiment designs and integrated critique/revisions for human selection. Feature activation, backend changes and new policies are valid research directions. [Meta decisions](../research/META.md) preserve process lessons and future-harness ideas. Two [repository skills](../research/README.md#run-in-a-fresh-codex-session) support a fresh session without a new orchestration service.

## Deferred parameter-study follow-ups

1. Freeze a focused repeated comparison of B0 and trial 10, with a declared throughput/TPOT tradeoff budget and primary load.
2. Check whether the TTFT gain exceeds baseline variation across runs and request classes. Report inconclusive outcomes honestly.
3. If useful, separate the three parameter changes to identify which contributes; this is a causal follow-up, not a retrospective explanation.
4. Then consider a versioned open-loop SLA-capacity study or additional workload shapes. Use the existing observations to choose the next question, not to redefine a successful result afterward.

See [replication criteria](REPLICATION.md). Nothing here claims those future steps are implemented or completed.
