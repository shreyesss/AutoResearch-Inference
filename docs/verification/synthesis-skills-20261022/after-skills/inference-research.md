---
name: inference-research
description: Research inference-serving improvements through literature, source code, PRs and experiments; generate a requested number of distinct hypotheses, critique and revise them within the same run. Covers library changes, feature activation, backend integration and runtime policies.
---

# Inference optimization research

## Objective and scope

Find useful ways to improve measured inference-serving frontiers. Read `docs/CHAT_RESEARCH_WORKFLOW.md` for current tools and state locations, then the relevant entries in `research/META.md`. Use `research/METHODOLOGY.md` for investigation techniques; its example rubric is a starting point, not a mandatory fixed policy. For durable CLI execution, read `docs/RESEARCH_FOUNDATION.md`.

The B200 results and Deepseek_serve provide starting evidence. They do not limit research to currently enabled features or the historical source version. Consider new algorithms, online/adaptive serving policies, kernels, scheduling, attention, speculation, KV/cache management, routing, communication, CPU/GPU overlap, feature activation, upstream ports and cross-engine ideas. Choose directions that could matter for the user's target, rather than mechanically covering every category.

A feature being absent, disabled or already implemented upstream is an integration question. Identify how to activate/adapt it, required dependencies, quality implications and a fair comparison. Reject a claimed current-path improvement if the path is inactive; retain a distinct activation/integration hypothesis when justified. DeepEP is one possible research surface, not a required ingredient or assumed baseline backend.

## Run contract

Record the user's requested idea count, scope, available hardware, time budget and research batch ID in `brief.md`. If count is omitted, choose a useful breadth for the decision and disclose it. Honor explicit breadth; do not stop at one convenient PR. Deduplicate leads by intervention and affected work, investigate competing explanations, and select the supported subset. Do not fabricate support to fill the quota: if a genuine evidence/access/budget limit prevents the requested count, report the shortfall, attempted directions and lower-confidence leads separately. Novelty means new relative to prior batches when the user requests new ideas; upstream reuse is welcome and must be labeled.

Use the configured external state root's `research/records/<new-id>/` for live dossiers and notes. Inspect prior decisions and rejected leads before searching. Historical `research/runs/` and `ideation/runs/` stay intact. A prior decision on another baseline or objective is evidence, not a permanent blacklist; explain the changed premise when revisiting it.

Freeze the actual target in the task brief: running image/source/model pins, GPU and topology, workload manifest, primary metric and operating region, separate correctness/tail guards, available time and minimum worthwhile gain if the user supplies one. Missing facts remain explicit unknowns. Set `selection.require_novelty` to `false` unless the user asks for novelty; an upstream port that improves this installation is eligible. Adapt rubric criteria and weights to this brief rather than importing a prior campaign's acceptance threshold.

## Research and synthesis

When sources only partly fit or a proposal combines methods, read
`references/synthesis.md`. Decompose each paper into components and dependencies
before rejecting or adopting it. Reuse an applicable inference policy without its
optional trainer when justified; do not discard dependencies needed for correctness.
Explain the compatibility of combined parts and the remaining target delta.

- Combine evidence-led investigation with opportunity-led literature and source research. A profile is useful evidence, not a prerequisite for proposing a new mechanism.
- Follow the discovery procedure in `research/METHODOLOGY.md`. Search and read papers, relevant references/citing work, upstream diffs/reviews and implementations in other serving engines. Verify crucial claims in primary sources; log searches, findings, counterevidence and access limits.
- Use native subagents for separable research directions when available and permitted. This workflow requests delegation for broad multi-idea batches; use a few bounded assignments matched to the requested scope. Give each the target, baseline facts, assigned question, output contract and execution limits. Have agents write separate notes; synthesize and deduplicate centrally. Do not prescribe the conclusion. If delegation is unavailable, do these passes sequentially and say so.
- Trace the relevant pinned code, or specify a proposed integration path when introducing a capability. Distinguish measured baseline, current upstream and proposed version. Explain what transfers from another model/hardware/workload and what still needs testing.
- Form cards with `research/HYPOTHESIS_TEMPLATE.md`. Each needs a concrete mechanism, strongest supporting and opposing evidence, implementation/activation surface, expected tradeoffs and cheapest informative experiment. Label confidence and readiness separately.

Use `researchctl run --question '...' --reason --brief /path/to/task.json` for the existing persisted evidence → rubric → proposal → critique sequence. Model calls are bounded separate invocations; the current chat can also inspect and synthesize evidence. Plain chat text is not automatically written into hypothesis memory. For manually authored cards, use the persisted import path documented in `docs/CHAT_RESEARCH_WORKFLOW.md`; do not claim they were saved until the command succeeds. Capture all proposals and verdicts, including rejection and deferral, before reporting a selected subset. A model-produced rubric is editable policy, not external authority.

## Adaptive research decisions

Use the discovery skill for online query loops and the PR research skill for source-level triangulation. Do not treat `run --reason` as the only workflow: it is a bounded optional model pipeline. The chat can call `expand`, `paper-search`, `search`, `investigate`, recall and evidence tools in whatever order the emerging uncertainty requires. Keep a compact search ledger with query/provider/date, outcome, source IDs and the next decision; feed observations back into an agent-authored query plan.

For each candidate, answer the transfer chain: **source mechanism → code/dispatch affected → actual target workload exposure → service metric pathway → strongest contrary evidence → cheapest falsifier**. Links without those connections are not triangulation. Inspect the relevant current/pinned implementation to determine whether the opportunity already exists; if a prior rejected idea is reopened, identify the new evidence or changed deployment condition. A different title for the same intervention is not a new idea.

Separate scientific usefulness from readiness. An absent checkpoint or unknown timing blocks qualification, but an explicit compatibility/CPU diagnostic may remain worthwhile. Arithmetic ROI is conditional evidence: task-specific assumptions and missing inputs stay visible. Do not force every idea through an identical quantitative threshold or invent inputs to satisfy a screen. Conversely, a large estimated gain never compensates for an inactive path or incorrect output.

An explicit user waiver of a separate pre-implementation ROI campaign takes
precedence. Preserve it in the task brief; do not recreate that gate through an
extra profiler, simulator or mandatory baseline campaign. Correctness/control
measurements can belong inside the matched comparison. Attached plans are examples
unless the current request authorizes their execution.

## Critique and improve in this run

Apply `research/METHODOLOGY.md`'s rubric to every shortlisted idea. Self-critique is the default; a subagent adversarial pass is optional. No separate critic chat is required. Record whether review was self, delegated or external. Challenge assumptions, inspect contrary sources, revise the hypothesis or replace weak ideas. Carry substantive objections and their resolution into the final cards and `review.md`; do not merely append a disclaimer. Stop iterating when the requested deliverable is useful or the declared budget is reached, reporting unresolved uncertainty.

Adapt that rubric to the current task and define observable pass/fail reasons.
Retain `decision_gap → tool receipt → evidence → decision_change → next_action`
for consequential calls. Judge useful revisions and avoided wrong experiments;
neither a high self-score nor more retrieved sources proves better hypotheses.

## Fast path to evidence

Read `ideation/docs/HYPOTHESIS_ROI.md` when screening value. Begin with available logs, source/dispatch inspection, existing counters, shape histograms and CPU replay. Identify the uncertainty that would change the decision before commissioning a GPU measurement. An activation check answers applicability; it does not establish material service benefit.

Estimate removable **exposed** time with measured units and a matching denominator. For fixed accepted progress, conditional amortized time saved per output token is saved critical-path time per decode cycle divided by useful output tokens from that cycle. This does not establish client-visible ITL, TTFT or tail latency; token burst/stream timing and queueing require separate observations. If acceptance/progress changes, compare both arms' time per useful token. Account for affected requests/shapes, added overhead, overlap and synchronized ranks; do not sum parallel kernel times as service time. Use low/base/high scenarios only when their inputs have support, otherwise give an unknown and its cheapest measurement. Do not infer TTFT, tail latency, capacity or dollars saved from a component percentage. Stop when a defensible optimistic estimate falls below this task's worthwhile gain; preserve a plausible but unresolved idea as deferred or a bounded diagnostic.

Choose an experiment suited to the change: isolated operation, component/trace replay, or one matched serving point. Preserve the service contract and measurement conditions; allow all candidate implementation/configuration changes necessary to test the idea. Separate a system-benefit comparison from later causal ablations. A coherent multi-change integration is valid; one-knob-at-a-time is not required.

Plan correctness before performance. Cache work needs actual prefix/hit evidence; speculation needs acceptance and quality checks; communication needs representative topology and messages. Profile separately from scored runs. Expand to curves and selected repeats only when warranted. Record setup/build/startup and measurement time separately. Do not invent universal sample floors, speedup predictions or SLOs.

## Deliver

Write sources, mechanism notes, supported hypothesis cards, critique/revisions and a concise ranked `decision.md`: proposal, benefit/tradeoff, evidence, required changes, confidence/readiness, cheapest next test and cost. Include exploration coverage and why discarded alternatives lost. Keep filesystem memory concise and linked; do not force-load all historical context.

The current human-in-the-loop stage ends at experiment selection. Do not build, patch serving code or launch GPUs unless the user has authorized that stage. Existing authorization continues to apply. Recommend process improvements to the meta coordinator, which maintains `research/META.md`; do not rewrite project-wide policy as an incidental research action.

Adapted research principles: `research/THIRD_PARTY.md`.

## Refined evidence-to-experiment tools

Use `docs/RESEARCH_TO_IMPLEMENTATION.md` for typed claims, `hypothesis propose/show`, hypothesis-linked `screen`, `eval-plan`, attributed `decide`, source-change alerts and MCP. Prefer these contracts for new work; legacy cards remain readable. A selection verdict from the older model workflow is not an executable evaluation-plan approval. The plan tool checks reproducibility and evaluator coverage; scientific applicability and execution authorization remain separate.
