# Query-plan row error repair

## Observed failure

The frozen round45 and router plans both supplied narrative strings in `observations`. Before this patch, actual CLI replay returned generic `ValueError` guidance about configuration, credentials or lineage. The compiler knew the row was malformed, but the boundary intentionally suppressed arbitrary exception text. Both original plan files and frozen failure receipts are unchanged.

## Narrow change

`QueryPlanRowError` is a `ValueError` subtype used only when an element of `queries` or `observations` is not an object. Its constructor admits only compiler-owned field names and bounded integer indices. CLI emits `query_plan_row_must_be_object`, field, zero-based index and static required-field guidance. MCP returns the same error code and safe location/guidance. Submitted values and arbitrary exception messages are not echoed.

Example: `observations[0] must be an object containing query, provider, status and reason. Use observations: [] when there are no prior searches to record.`

Valid compilation, semantic planning, provider requests, query wording, limits and accepted schemas are unchanged. Other failures—including invalid observation status—retain existing sanitized behavior; this is not a universal schema validator rewrite.

## Verification

- Focused tests: **12 passed**. Invalid strings, null, arrays and numbers across both row lists; actual CLI subprocess failure and corrected success; actual MCP failure/corrected success; arbitrary provider HTTP exception messages containing sentinel credentials remain hidden.
- Required research suite: **345 passed, 29 subtests passed**.
- Required `scripts/bootstrap-node.sh --dry-run`: succeeded; no changes made.
- `git diff --check`: passed.
- Actual retained-plan replay: two invalid originals and two corrected plans through both CLI and MCP. Invalid plans now identify `observations[0]`; corrected plans succeed. Socket-connect and provider-request hooks were denied during replay; observed MCP counts were zero. CLI calls ran under the same denial hooks. This is bounded no-network replay, not a complete proof against every possible network API.
- The initial focused MCP negative-control test incorrectly patched a function after the server closure captured it; it failed. The test now constructs the failure-server inside the patch and passes. An external replay script had an initial syntax typo, corrected before producing `after.json`.

## Scope

This improves error actionability for an observed agent input mistake. It does not demonstrate better paper recall, scientific reasoning or hypothesis quality. No canonical state, cloud publication, GPU or serving changes; no commit. `before.json`, `after.json` and the script preserve the finite field test. Code snapshots and hashes identify the reviewed implementation.
