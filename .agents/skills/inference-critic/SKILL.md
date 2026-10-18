---
name: inference-critic
description: Critique and improve inference optimization hypotheses and experiment designs, either within a research run or as a requested separate review. Assess mechanism, evidence, integration feasibility, correctness, serving value and experiment cost.
---

# Inference critique and revision

Read the requested batch and `research/METHODOLOGY.md`'s rubric. This skill is an optional review entry point; the researcher already performs critique and revision in its own run. A separate role or chat is not required. Label review as self, delegated or external; do not claim independence for self-review.

Check consequential claims against original measurements, pinned code and online primary sources. Inspect counterevidence, PR diffs/reviews and integration requirements. Distinguish facts, inference and predictions. Review the proposed system, not only features active in the historical configuration.

For each idea assess mechanism, evidence, activation/integration, correctness/service contract, potential serving benefit, experiment discrimination and cost. A disabled feature or absent backend can be a valid integration proposal. An upstream implementation can be a useful upgrade. Identify what must change and test it fairly; don't reject these automatically. Reject contradictions, duplicate ideas with no new premise, or proposals lacking a plausible path to value after investigation.

Write `review.md` with evidence checked, strongest support, strongest objection, cheapest resolution and advance/revise/defer/reject. Explain each verdict. Defer costly or inaccessible but plausible work without calling it disproven. Rank opportunities using explicit tradeoffs rather than ungrounded precision scores.

When invoked inside the research loop, revise cards and record substantive changes; preserve the earlier claim in a revision note or version history. When asked only for an external review, preserve the author's cards and provide revision instructions. Replacement ideas must receive the same scrutiny. Check that the requested number and breadth were addressed without splitting one mechanism into duplicates.

Recommend the cheapest informative experiment and what result would change the decision. An isolated kernel improvement does not establish an end-to-end frontier point. Keep service quality, workload and hardware comparability explicit; allow necessary implementation and feature changes. Use causal ablations when attribution matters rather than blocking a useful integrated system comparison.

A review verdict does not authorize GPU work or prove improvement. Follow the user's current execution scope. See `research/THIRD_PARTY.md` for attribution.
