---
name: inference-implementation
description: Turn a selected inference hypothesis into a reproducible code-change and evaluation handoff, or implement and test it within the user's authorized execution scope.
---

# Inference implementation handoff

Read the selected card, frozen rubric, evidence dossier and prior attempt history, then `docs/CHAT_RESEARCH_WORKFLOW.md` and `docs/PORTABLE_SETUP.md`. AutoResearch owns the research/attempt record; Bitlane is a separate serving/deployment checkout. Resolve the actual source/image and hardware pins rather than borrowing them from a historical campaign.

Prepare a concrete handoff with hypothesis ID, immutable baseline ID, source citations/pins, target functions/config changes, dependencies, correctness oracle, ROI assumptions, cheapest falsification, benchmark commands and artifact locations. Record which commands are verified and which are proposed. Preserve existing code changes and use an isolated branch/worktree where needed. A research recommendation alone does not authorize launching a deployment or GPU job; current user authorization determines execution scope.

Start with the cheapest decisive source inspection, unit/component check or CPU trace replay. If GPU work is necessary and authorized, constrain the first attempt to the uncertainty that blocks promotion. Record compilation, startup/capture and measurement cost separately. Do not equate an unsupported code path, setup error or out-of-memory crash with a disproven performance mechanism.

Prefer the pinned Mooncake and agent-75/AIPerf workloads already used by the target deployment. Inspect their actual manifests and load semantics. Add a custom evaluator **only** when neither exposes the proposed mechanism or its correctness condition; state the missing stimulus/observable and reuse the existing runner where possible. Prefix reuse requires verified hits; speculation requires useful accepted progress and correctness; scheduler/routing changes require representative arrival/state feedback. Keep profiler runs separate from scored serving runs.

Define control/treatment, request identities/seeds, token-length/cohort coverage, load mode, cache preparation, resource basis, primary metric, separate quality/tail guards and support/reject/inconclusive criteria before execution. A component attempt can motivate a native or service attempt but cannot validate it. Keep new attempts in the experiment registry via `researchctl experiment create/transition/get`; accepted/planned requires explicit ROI and an evaluation plan. Use a new ID for retries or changed baseline/scope and link the predecessor.

Collect source/build/image pins, actual invocation, raw observations and artifact hashes. Record `running` only when execution starts. Record measured outcomes with their original scope, and retain rejected/inconclusive/error results as well as wins. Finish with the decision, evidence level, unresolved uncertainty and next cheapest useful action; do not report a prediction as achieved TTFT/TPOT/ITL/cost improvement.

## Refined evidence-to-experiment tools

Use `docs/RESEARCH_TO_IMPLEMENTATION.md` for typed claims, `hypothesis propose/show`, hypothesis-linked `screen`, `eval-plan`, attributed `decide`, source-change alerts and MCP. Prefer these contracts for new work; legacy cards remain readable. A selection verdict from the older model workflow is not an executable evaluation-plan approval. The plan tool checks reproducibility and evaluator coverage; scientific applicability and execution authorization remain separate.
