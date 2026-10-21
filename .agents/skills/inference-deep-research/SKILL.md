---
name: inference-deep-research
description: Investigate inference research papers and their implementations, compare competing mechanisms and baselines, and retain revision-grounded author claims for task-specific hypothesis synthesis.
---

# Deep research as inspectable evidence

Use `docs/RESEARCH_TO_IMPLEMENTATION.md`. The current agent conducts the investigation; deterministic tools retain sources, claims, proposals and decisions. MCP transports the same tools and does not supply an additional research mind.

Frame the uncertainty that changes the engineering decision. Use query expansion, source/date filters, neighboring mechanisms and negative findings. Inspect relevant previous hypotheses and deferred decisions before retrieval. Respect configured provider budgets and cached responses; extend a search only to resolve a concrete gap. Search scores and citation counts do not establish applicability or novelty.

Use bounded `investigate` for selected primary text, citation links and pinned implementation files. Read the relevant method, comparator, appendix, limitations and correctness assumptions. Distinguish abstract-only knowledge, openly accessible full text, implementation inspection and reproduced observations. If a paper is inaccessible, retain the metadata and gap. Do not invent its tables or reproduce its claimed gain in a target estimate.

Record atomic author claims with `claim record`: exact source revision, excerpt/locator, original conditions and reported-result origin. Link competing and refuting claims explicitly. Known arXiv/DOI aliases can unify mirrors; similar titles cannot. Check `changes` and the hypothesis dossier for newer source revisions before relying on an old decision.

Generate a falsifiable target hypothesis with mechanism, proposed change, prerequisite, counterevidence, target-profile version and cheapest falsifier. Use `hypothesis propose`; source results remain separate. Use task-derived criteria and require novelty only when requested. Run `screen` with target measurement provenance; absent timing/acceptance data should produce an informative diagnostic, not an invented gain. End with an evidence-linked recommendation and an evaluation handoff whose unresolved requirements are visible.
