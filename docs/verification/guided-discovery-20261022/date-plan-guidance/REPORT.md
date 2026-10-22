# Structured search dates: a focused skill correction

Observed round105 failure: both expansion plans named dates in must_keep prose, but their runnable recipes had after/before=null. The actual paper-search calls correctly applied inclusive2026-09-01/exclusive2026-10-23. This was a plan/execution provenance mismatch, not an online date-filter failure.

The inference-discovery skill now specifies structured dates on expand or its query rows, matching actual dates in prior observations, and additive corrections when execution was right. No prose date parser, query rewrite, new provider call or deterministic workflow was added. The agent retained corrected plans without replaying the network searches.

Validation actually performed:
- Existing compile_plan replay: prose-only bounds remained null; structured bounds produced exactly the actual query/provider/date recipe. Prior observations retained their actual dates. check.json contains this bounded check.
- Skill validator passed using the already installed isolated PyYAML dependency at /tmp/autoresearch-skill-validator-deps. Initial repo/system Python invocations lacked PyYAML and failed before validation; no dependency was added to production.
- Research suite:408 tests and29 subtests passed in11.80 seconds.
- bootstrap-node.sh --dry-run passed without changes.

This verifies tool semantics and the focused instruction, not an improvement in agent judgment, paper recall or hypothesis yield. No independent behavioral A/B test is claimed. Production Python code is unchanged; the skill alone changed. No GPU work or serving mutation.
