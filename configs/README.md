# Configuration index

**Completed direct study:** [direct-optuna-study.json](direct-optuna-study.json). This contains the eight-field serving domain, B0, objectives and pinned settings. The actual point counts and concurrency protocol were resolved by `infra/direct_optuna/run.py`; consult the [execution receipts](../results/2026-10-18-direct-optuna/evidence/README.md), not only the generic upstream `benchmark` defaults.

Other `campaign*`, `search-domain*`, `evaluation*`, `sla-*`, `pilot-*` and workload registries belong to earlier AIPerf/Codex studies. They are preserved with their versioned filenames. They do not silently extend the direct study's search domain or act as its hard SLA constraints.

[Current runbook](../infra/DIRECT_OPTUNA_RUN.md) · [historical studies](../docs/RESEARCH.md) · [replication criteria](../docs/REPLICATION.md)
