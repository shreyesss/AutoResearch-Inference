# Handoff validation — v0.2

Checked 17 October 2026. These checks validate this documentation package, not the proposed application.

- 9 JSON files parse.
- 3 bundled DTO examples satisfy all bundled schema constraints.
- 5 invalid proposal mutations rejected (workload/root override, missing falsification, empty predictions, unknown observation).
- Variable-length natural-EOS dependent-session fixture satisfies amended schema.
- Mock request conservation and effective-throughput arithmetic reconcile.
- Artificial Pareto fixture reproduces expected nondominated/tied set.
- Relative Markdown links resolve (8); fenced code blocks balance.
- Exactly 3 agent briefs; all include v0.2 requirements.
- Example qualification and holdout policies match decisions.

Schema checking used a local recursive checker covering every keyword present in the three bundled schemas; it is not a general JSON Schema implementation. Runtime builders must use a production validator and cross-field semantic checks.

No raw dataset mining, Docker build, AIPerf benchmark, Codex proposer or target GPU experiment ran in producing this update. Workload proportions, hardware/runtime pins, source characterization and sensitivity results remain pending. There is no measured performance gain or completed experimental setup claim. See ACCEPTANCE.md for implementation and real qualification requirements.
