# Adaptive research iteration — 22 October 2026

Scope: improve and exercise CPU-side hypothesis research. No GPU experiments,
profiling, model launches or serving changes. GPU availability observations from
earlier runs are not evidence of current availability.

## Implemented changes

- Agent-authored semantic query rounds retain mechanism, purpose, observations,
  constraints, permitted relaxations and stop reasons. Exact repeats are flagged,
  not prohibited. The host chooses and revises searches; there is no hidden model
  inside `expand`. Explicit missing/null plan files fail instead of silently
  reverting to lexical hints.
- Dated arXiv searches can relax plain terms after an empty response while keeping
  date bounds. Explicit field/Boolean queries are preserved. Results expose
  abstracts, attempted queries and cache receipts; known mirrors are grouped by
  explicit paper identity, not treated as independent evidence.
- CLI/MCP local search supports `any`/`all` and chosen date fields. Source reads can
  select retained revisions. MCP now exposes hypothesis recall, command history
  and checkpoint, for 19 tools. Client registration is still separate; this work
  operates through the CLI.
- Interactive `--defer-snapshot` retains local evidence and journals without a
  full backup per call. Pending checkpoint state is explicit. Defaults are
  unchanged; an existing backfill writer lock can still block interactive calls.
- CPU diagnostic plans require pinned inputs, observables, falsification and zero
  GPU budget without demanding fabricated serving pins or numeric ROI. Simulated
  positive ROI cannot qualify serving plans. Readiness remains a structural check,
  not scientific validation or permission to execute.
- Discovery, PR research, hypothesis and critic skills now describe adaptive
  evidence-driven decisions and prior-work recall. Novelty remains task-dependent.

## Verification actually run

` .venv/bin/python -m pytest ideation/tests -q `: **239 passed in 5.49s**.

`scripts/bootstrap-node.sh --dry-run`: passed; no installation or service changes.

`git diff --check`: passed. Four modified skills validated with the skill-creator
validator. Independent implementation review found the missing-plan fallback bug;
it was corrected and covered by a real CLI regression test.

Tests cover contracts, routing, caching and persistence. They do not prove paper
recall, scientific usefulness or GPU performance. No paid LLM pipeline was invoked
by the new query planner or tests.

## Independent field test

External working artifacts:
`~/.local/share/autoresearch-reviews/adaptive-discovery-20261022/`.
The field agent uses an isolated state root to avoid interfering with canonical
backfill. It performs online discovery, retained-PR searches and pinned source
inspection. A separate critic reviews applicability and missing measurements.

The initial review rejected repackaging bounded replay and adaptive prefill as new
proposals: both already exist in prior research. It narrowed Engram work from
generic prefetch to earlier WKV projection, preserving existing packed lookup/
transport and explicitly accounting for stream workspace and MegaMoE fences.
The field report carries the final source pins, dispositions and evidence gaps.
No measured target improvement is claimed. An isolated local checkpoint is not
canonical S3 publication or VM delivery.

## Operating instructions

See [chat workflow](../../CHAT_RESEARCH_WORKFLOW.md),
[system design](../../SYSTEM_DESIGN.md) and
[evaluation gating](../../EVALUATION_GATING.md).

Choose the next research call to resolve a named uncertainty. Preserve failed
queries and counterevidence. When target source/workload exposure is unknown,
retain the candidate as conditional and name the cheapest missing observation.
Do not turn a successful schema check or source-author speedup into a service win.
