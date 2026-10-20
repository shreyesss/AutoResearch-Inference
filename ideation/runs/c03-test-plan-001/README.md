# C03 plan package

Start with the [execution brief](EXECUTION_BRIEF.md). It fixes this node, 0.5× trace replay, the exact existing profile and current environments, with independent evaluator design, evaluator implementation and optimization roles. No experiment or optimization implementation has run.

- [Baseline audit](baseline-audit.md) and [machine-readable evidence](baseline-audit.json): corrected local median is complete and meets fidelity gates, while service SLOs remain unmet; burst is a different-node reference.
- [Independent evaluator design](evaluator-design.md): frozen metrics, reference assertions, falsification sequence, exact future command and paired inference.
- [Evaluator builder review](evaluator-builder-review.md): reusable pieces, missing work and scope boundaries.
- [Optimization implementation review](/home/ubuntu/Deepseek_serve-c03/C03_IMPLEMENTATION_REVIEW.md): installed behavior, final upstream semantics, minimal source isolation and rollback.
- [Triage ledger](TRIAGE.md) and [input manifest](input-manifest.json): current state and pinned inputs.

The source family is [C03](../h200-cross-audit-comparison-001/families/C03.md). The original research and baseline results are preserved. Worktree branches are `experiment/c03-plan` and `experiment/c03-logical-draft`.
