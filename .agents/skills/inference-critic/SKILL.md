---
name: inference-critic
description: Critique and improve inference optimization hypotheses and experiment designs, either within a research run or as a requested separate review. Assess mechanism, evidence, integration feasibility, correctness, serving value and experiment cost.
---

# Inference critique and revision

Read the requested batch, its frozen task brief/rubric and `docs/CHAT_RESEARCH_WORKFLOW.md`. Use `research/METHODOLOGY.md` as investigation guidance and `ideation/docs/HYPOTHESIS_ROI.md` for value screening. This skill is an optional review entry point; the researcher already performs critique and revision in its own run. A separate role or chat is not required. Label review as self, delegated or external; do not claim independence for self-review.

Check consequential claims against original measurements, pinned code and online primary sources. Inspect counterevidence, PR diffs/reviews and integration requirements. Distinguish facts, inference and predictions. Review the proposed system, not only features active in the historical configuration.

For each idea assess mechanism, evidence, activation/integration, correctness/service contract, potential serving benefit, experiment discrimination and cost. A disabled feature or absent backend can be a valid integration proposal. An upstream implementation can be a useful upgrade. Identify what must change and test it fairly; don't reject these automatically. Reject contradictions, duplicate ideas with no new premise, or proposals lacking a plausible path to value after investigation.

Apply the user's current objective and selection policy. Scientific novelty is not a constraint unless requested. Distinctness avoids redundant experiments; it does not require an unpublished mechanism. A prior rejection can be reconsidered for a different baseline, objective or new evidence. Do not silently inherit the old campaign's minimum gain, source count, sample size or scoring weights.

Audit every numerical ROI input: measured/inferred/unknown, units, frequency, affected workload fraction, exposed critical-path time, useful output progress and treatment overhead. Component timing cannot establish client-visible speedup, and fixed-load latency cannot establish cost savings. Identify the cheapest CPU/source/trace check first. Recommend a small GPU diagnostic only when it resolves a named remaining uncertainty; unknown ROI is not automatic scientific rejection. Selection scores are priorities, not probabilities or experimental validation.

Write `review.md` with evidence checked, strongest support, strongest objection, cheapest resolution and advance/revise/defer/reject. Explain each verdict. Defer costly or inaccessible but plausible work without calling it disproven. Rank opportunities using explicit tradeoffs rather than ungrounded precision scores.

When invoked inside the research loop, revise cards and record substantive changes; preserve the earlier claim in a revision note or version history. When asked only for an external review, preserve the author's cards and provide revision instructions. Replacement ideas must receive the same scrutiny. Check that the requested number and breadth were addressed without splitting one mechanism into duplicates.

Recommend the cheapest informative experiment and what result would change the decision. An isolated kernel improvement does not establish an end-to-end frontier point. Keep service quality, workload and hardware comparability explicit; allow necessary implementation and feature changes. Use causal ablations when attribution matters rather than blocking a useful integrated system comparison.

A review verdict does not authorize GPU work or prove improvement. Follow the user's current execution scope. See `research/THIRD_PARTY.md` for attribution.

Keep every earlier card and verdict in durable memory. If review is performed in chat, use the documented import/record path and verify persistence; writing a Markdown summary alone does not update the hypothesis ledger. Preserve `error`, `inconclusive` and `invalidated` as distinct experiment outcomes, and preserve component/native/service scope.

## Refined evidence-to-experiment tools

Use `docs/RESEARCH_TO_IMPLEMENTATION.md` for typed claims, `hypothesis propose/show`, hypothesis-linked `screen`, `eval-plan`, attributed `decide`, source-change alerts and MCP. Prefer these contracts for new work; legacy cards remain readable. A selection verdict from the older model workflow is not an executable evaluation-plan approval. The plan tool checks reproducibility and evaluator coverage; scientific applicability and execution authorization remain separate.
