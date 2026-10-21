---
name: inference-pr-research
description: Investigate inference-engine PRs, issues and implementation changes for a target deployment. Trace applicability, regressions, benchmark claims and exact code revisions before proposing an experiment.
---

# PR evidence for a serving change

Use `docs/RESEARCH_TO_IMPLEMENTATION.md` for the current CLI/MCP contracts. Start from the user's target and available source/benchmark pins. A proposed upstream patch, a merged patch and a locally exercised code path are different facts.

Use `researchctl pr-search QUERY --repo OWNER/REPO --after DATE` for dated local openings; use `search` to include issues and discussions. Inspect coverage with `backfill status`. A local search does not contact GitHub. Explicit `refresh` resumes due collection. Read `show ID --history` before assuming a retained PR describes current upstream.

For promising changes use `investigate --question TEXT --source-id ID --max-http-calls N` to hydrate bounded primary evidence. Trace parent dependencies, changed files/symbols, dispatch conditions, head/base commits, comments that qualify measurements and correctness failures. Read actual source paths with pinned commits through the existing evidence tools; a title or README is insufficient to assert an active kernel/backend. Record unknown pins and access failures.

Extract separate mechanism, measured-result and limitation claims with `claim record`; include the exact excerpt and source revision. A numeric result needs its own excerpt, original metric/unit, baseline and conditions. The tool checks quotation identity, not scientific entailment. Attach support/refutation via `link-evidence`, including contradictory observations and rejected-backend reasons.

Synthesize the smallest useful next change or diagnostic. A direct port that cannot run on the current backend is inapplicable; a separate integration/transfer proposal may survive with its prerequisites stated. Use `hypothesis propose` with a falsifier and null target prediction unless a separately supported estimate exists. Keep every disposition with `decide`, including its reason and reopening trigger. Return persistent IDs and the cheapest next action; do not equate a paper/PR gain with a deployment gain.
