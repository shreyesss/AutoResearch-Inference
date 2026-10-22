---
name: inference-critic
description: Critique and improve inference optimization hypotheses and experiment designs, either within a research run or as a requested separate review. Assess mechanism, evidence, integration feasibility, correctness, serving value and experiment cost.
---

# Inference critique and revision

Read the requested batch, its frozen task brief/rubric and `docs/CHAT_RESEARCH_WORKFLOW.md`. Use `research/METHODOLOGY.md` as investigation guidance and `ideation/docs/HYPOTHESIS_ROI.md` for value screening. This skill is an optional review entry point; the researcher already performs critique and revision in its own run. A separate role or chat is not required. Label review as self, delegated or external; do not claim independence for self-review.

Check consequential claims against original measurements, pinned code and online primary sources. Inspect counterevidence, PR diffs/reviews and integration requirements. Distinguish facts, inference and predictions. Review the proposed system, not only features active in the historical configuration.

For each idea assess mechanism, evidence, activation/integration, correctness/service contract, potential serving benefit, experiment discrimination and cost. A disabled feature or absent backend can be a valid integration proposal. An upstream implementation can be a useful upgrade. Identify what must change and test it fairly; don't reject these automatically. Reject contradictions, duplicate ideas with no new premise, or proposals lacking a plausible path to value after investigation.

Apply the user's current objective and selection policy. Scientific novelty is not a constraint unless requested. Distinctness avoids redundant experiments; it does not require an unpublished mechanism. A prior rejection can be reconsidered for a different baseline, objective or new evidence. Do not silently inherit the old campaign's minimum gain, source count, sample size or scoring weights.

Review component selection before rejecting an entire paper: can a useful policy,
representation or evaluator transfer independently of its trainer or other optional
parts? Verify required dependencies and cross-source interfaces; selective reuse
must not silently remove correctness or learned-model requirements. See
`../inference-research/references/synthesis.md`. Honor task-specific ROI waivers and
mandatory comparisons; assess usefulness separately from execution readiness.

Use criterion-level evidence and concrete errors when judging a revision. Compare
outputs under the same task/evidence if evaluating a skill change; freeze criteria
first, retain both outputs and distinguish self-review from separate review. A
small model-judged case set is a regression check, not scientific validation or
proof of improved serving performance. Do not tune repeatedly to an opened test.

Audit every numerical ROI input: measured/inferred/unknown, units, frequency, affected workload fraction, exposed critical-path time, useful output progress and treatment overhead. Component timing cannot establish client-visible speedup, and fixed-load latency cannot establish cost savings. Identify the cheapest CPU/source/trace check first. Recommend a small GPU diagnostic only when it resolves a named remaining uncertainty; unknown ROI is not automatic scientific rejection. Selection scores are priorities, not probabilities or experimental validation.

Before using a reported loss or parity result to reject an idea, identify its
treatment, control, metric, measured boundary and hardware/workload. Check the
actual table values and direction when a summary determines the verdict. A losing
collective-fusion ablation does not refute a different local-operator speedup;
conversely, a winning bundle does not isolate each component. Preserve both
comparisons and narrow the rejection to the unsupported transfer. If a prior
summary misstated the evidence, append a sourced correction and link it to affected
investigations; do not silently rewrite the original or reverse unrelated decisions.

Write `review.md` with evidence checked, strongest support, strongest objection, cheapest resolution and advance/revise/defer/reject. Explain each verdict. Defer costly or inaccessible but plausible work without calling it disproven. Rank opportunities using explicit tradeoffs rather than ungrounded precision scores.

When invoked inside the research loop, revise cards and record substantive changes; preserve the earlier claim in a revision note or version history. When asked only for an external review, preserve the author's cards and provide revision instructions. Replacement ideas must receive the same scrutiny. Check that the requested number and breadth were addressed without splitting one mechanism into duplicates.

Recommend the cheapest informative experiment and what result would change the decision. An isolated kernel improvement does not establish an end-to-end frontier point. Keep service quality, workload and hardware comparability explicit; allow necessary implementation and feature changes. Use causal ablations when attribution matters rather than blocking a useful integrated system comparison.

For multi-arm experiments, separate each arm’s comparison from the family-level decision. If either B or C improving over A supports the proposal, B beating C rejects only C’s advantage over B; it does not reject the whole proposal. Check that null, support and rejection branches match the actual baseline, objective and guards, including ties or inconclusive uncertainty. Preserve the original decision rule and record corrections explicitly.

A review verdict does not authorize GPU work or prove improvement. Follow the user's current execution scope. See `research/THIRD_PARTY.md` for attribution.

Keep every earlier card and verdict in durable memory. If review is performed in chat, use the documented import/record path and verify persistence; writing a Markdown summary alone does not update the hypothesis ledger. Preserve `error`, `inconclusive` and `invalidated` as distinct experiment outcomes, and preserve component/native/service scope.

## Refined evidence-to-experiment tools

Use `docs/RESEARCH_TO_IMPLEMENTATION.md` for typed claims, `hypothesis propose/show`, hypothesis-linked `screen`, `eval-plan`, attributed `decide`, source-change alerts and MCP. Prefer these contracts for new work; legacy cards remain readable. A selection verdict from the older model workflow is not an executable evaluation-plan approval. The plan tool checks reproducibility and evaluator coverage; scientific applicability and execution authorization remain separate.


## Adaptive decisions and cheap diagnosis

Read `docs/EVALUATION_GATING.md` when a proposal has unknown ROI or lacks a live target. Treat the rubric as an explicit decision aid, not a golden filter. Choose the next action by the uncertainty it resolves: alternate paper/PR search, inspect a dispatch path, replay a trace, revise the mechanism, or stop. Do not force every candidate through the same sequence or generate a replacement merely to fill a quota.

Separate the current-baseline gap, mechanism activation, workload exposure, and service-value evidence. A favorable arithmetic bound or complete manifest cannot supply any of them. If a source or CPU check can settle the next question, use the `execution_kind=cpu`, `purpose=diagnostic` plan: pin its inputs, declare the observation and support/refute/inconclusive branches, and use zero GPU minutes. Missing serving pins need not block this check. Its result cannot certify service gain.

For any shortlist, state the strongest competing explanation, the cheapest observation that changes ranking, and which existing evaluator can supply it. Prefer revising an existing hypothesis with new evidence over relabeling the same idea. Stop retrieval when another query is unlikely to change the decision within the task budget; retain unresolved assumptions and a reopening condition.

When reviewing a CPU model of a proposed optimization, identify its supplied
oracles: generation counters, exact candidate membership, source-write events,
runtime dispatch or timing inputs. Locate how the pinned implementation would
produce each one. Passing a model that receives the right invalidation events
does not prove those events exist or fire in the real runner. Unequal example
strings are illustrations, not executed invalidation tests. Check graph replay,
nested forward contexts and entry points that skip ordinary execution. Prefer
an existing unconditional refresh boundary when it can remove a speculative
cross-invocation cache contract. Preserve the earlier fixture and verdict; record
which premise changed and what the revised check actually exercises.

For a shape/bucket diagnostic, follow the runner's mode-selection call site before
generalizing a fixture: adaptive/variable-length and uniform execution can select
different capacities from the same list. Check whether rank synchronization changes
the final choice. If the selected mode or effective configuration is unknown,
compare the plausible source branches and keep the exposure conclusion conditional;
do not label a convenient default fixture as the deployment's behavior.

For implementations with automatic fallbacks, distinguish constructor/engine labels
from the path actually executed. Record native, reference, retry and full-fallback
calls with their own denominators; a successful mixed-path test cannot certify the
unexercised native path. Compare an incremental/cache/fusion proposal with the
simpler available full-operation baseline. Condition conclusions on the workload
that selects each path, including serialized inputs and output requirements; warm
prior state and a shared-prefix workload do not establish a usable session cache.
These checks should change the scope or next experiment, not force an acceptance
quota or turn a finite compatibility result into a service-performance claim.
