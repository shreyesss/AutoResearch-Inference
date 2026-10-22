# Observed research-tool failures and repairs

22 October 2026; CPU research tooling only. No GPU or serving changes.

## Artifact relocation

A real local storage snapshot/restore retained a hypothesis result file but left its historical absolute reference unusable. Retrying the same result at the restored path falsely conflicted. New in-state references now use state-relative paths. Reads resolve legacy canonical records by an unambiguous suffix and verify size/hash without changing historical events. Identical retries return the original event. External files remain explicitly unretained.

The original failing fixture was rerun after the repair; its event ID, event count and stored historical path stayed unchanged. Eight added tests cover actual relocation, corruption, missing files, traversal, symlink escape, ambiguous suffixes and changed-result conflicts. See [artifact contract](../../../ideation/docs/HYPOTHESIS_ARTIFACTS.md). Full original evidence is in the external batch under `tool-verification/artifact-relocation/`.

## Missing local source

Round5 attempted to inspect SGLang roadmap42170 in an isolated corpus. Its absence surfaced as a generic KeyError, which did not distinguish missing retention from a provider problem. `show` and MCP `source_show` now expose `source_not_retained` or `source_revision_not_retained`, explain local coverage and available revision history, and never fetch implicitly or silently replace a pinned revision. Error text contains no user input or provider URL.

Two added CLI/MCP tests exercise the actual error path; command failures remain journaled. The existing exact-revision test still passes. No new provider or orchestration layer was introduced.

## Verification

- Full research suite: **258 passed**, 5.63 seconds.
- Bootstrap dry-run: exit0, no changes.
- Diff whitespace check: passed.
- An initial manual focused-test invocation named a nonexistent test file and ran zero tests; the corrected full suite above is the verification evidence.

These checks establish tool behavior, not improved scientific judgment or inference throughput. No claim that the two repairs increase accepted-hypothesis yield has been tested.
