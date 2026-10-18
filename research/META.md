# Meta-level decisions and learning

Maintained by the meta coordinator with the user. This is the durable record of goals, process corrections and future-harness ideas. Research workers read relevant decisions and propose updates; the coordinator curates them. It is not a claim that an autonomous harness already exists.

## Objective and responsibilities

**Outcome:** improve real inference-serving operating curves and Pareto frontiers while preserving a declared service-quality contract. Optimizers, research agents and orchestration are tools toward that outcome.

**Meta coordinator:** maintain user intent, research scope, skill quality, experiment workflow, accumulated lessons and the path toward automation. Inspect workers' outputs and help the user choose experiments. Do not present its own generated hypothesis as independently reviewed.

**Research worker:** discover opportunities, read sources, synthesize the requested ideas, critique/revise them and provide executable experiment plans. Native subagents can investigate separate mechanisms. Self-critique is allowed and labeled.

**Human checkpoint now:** select experiments and authorize execution scope. Once a stage is authorized, do not ask repeatedly for the same permission. No new GPU execution is authorized by a research-planning request alone.

## Accepted design decisions from this conversation

| Decision | Reason / implementation consequence |
|---|---|
| Preserve completed TPE study | It is completed evidence. Current focus is broader serving/library research, not another tuning campaign. |
| Broad improvement surface | Include code, feature activation, new backends, versions, policies and paper-derived adaptations. Current enabled features are a starting point, not the boundary. |
| Requested idea count per run | No fixed cap of four. Search broadly enough for N distinct plausible ideas; disclose readiness and genuine shortfalls without padding. |
| Critique within the research run | No mandatory second chat or reviewer role. Self/delegated/external reviews are labeled; revisions must address objections. |
| Real literature plus implementation research | Read methods/evaluation and follow citations; inspect PR diffs/reviews and competing systems. PR backport hunting alone is insufficient. |
| Smallest useful tests | Isolate an operation or component where possible; load full models only when needed to answer the question. |
| Fast path to a frontier point | Start with one matched serving point, expand promising candidates to curves and selected repeats. Avoid full-suite gates for every idea. |
| Fairness without freezing innovation | Keep the service contract and measurement comparable; allow the candidate's necessary settings/backend changes. Use later ablations for causal attribution. |
| Simple memory and observability | Files for sources, ideas, revisions, experiments and decisions; inspectable raw outputs. No mandatory full-history context injection. |
| Minimal present implementation | Skills and human review now. Add harness mechanics when repeated useful work establishes a need. |

## Lesson from b200-source-001

The first batch reconstructed source/backend facts and surfaced one backport. The critic caught a configuration-dependent claim. But the instructions over-weighted compatibility with the unchanged baseline, capped output at four and made separate review mandatory. This narrowed discovery and created extra user handoffs. User feedback: research must be broader and deliver requested new ideas, with integrated critique and clearer routes to cheap experiments.

Correction implemented in the current skills/method: separate current-path claims from activation/integration opportunities, add paper/citation and cross-engine discovery, use requested N, support delegated investigation and self-revision, and assess service-level comparisons separately from causal ablations. The first batch remains historical evidence; its claims are not silently rewritten by this process correction.

## Eventual autonomous harness — proposals, not implemented

- Research queue spanning mechanisms, with provenance, prior attempts and reasons to revisit; avoid rediscovering rejected ideas without changed evidence.
- Separate budgets for research, building, GPU startup, measurement and confirmation; prioritize expected information/value per total cost.
- Proposal → critique/revision → cheap check → serving point → promotion/repetition → frontier update. Permit branching and early rejection; no mandatory expensive stage for every idea.
- Track complete candidate deltas and dependency graphs; reuse compatible builds, loaded servers and baselines where valid, with cache/drift checks.
- Record source/patch/config/workload hashes, raw observations, counters, correctness outcomes, failures and run durations. Plot all points, uncertainty and dominated candidates.
- Promote using observed effect and evidence quality. Treat weak/noisy results as inconclusive, with bounded additional testing; don't quietly turn research targets into production SLAs.
- Feed measured and rejected outcomes back into discovery. Evaluate research quality by useful experiments and reproducible improvements, not idea volume, citations or elaborate prose.
- Expand autonomy only after the human-guided workflow reliably produces worthwhile experiments. Model and tooling remain configurable.

## How to maintain this file

After substantive user steering or an experiment/process failure, record the changed decision, its evidence and the consequence for skills or experiment design. Distinguish accepted direction, proposed mechanism and measured result. Link relevant batch artifacts when available. Keep the active record short; archive superseded detail if it grows. A new research batch should not require replaying this conversation.
