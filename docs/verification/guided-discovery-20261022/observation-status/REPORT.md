# Safe observation-status validation guidance

## Observed failure

The retained round73 plan `query-plan-02-invalid.json` supplies `off_topic` for observation index 1. Its original `expand-02.json` is empty because CLI errors go to stderr. A fresh isolated replay of the exact plan before this change returned only the generic sanitized `ValueError` message. `before.json`, `before.stdout` and `before.stderr` preserve that reproduced result and input hash; the historical packet remains unchanged.

## Narrow change

`QueryPlanObservationStatusError` carries only compiler-owned static guidance, a zero-based index restricted to 0–49, and the unchanged allowed values: `useful`, `irrelevant`, `empty`, `error`, `redundant`. The invalid submitted value is never passed to the exception. Its message does not echo the question, query, reason or other submitted content.

CLI returns `query_plan_observation_status_invalid`, `field: observations`, `index`, and `allowed_values`. MCP returns the same code, bounded location and allowed values in its safe error message. Existing row-shape guidance remains intact; unrelated/provider errors keep their existing sanitization. No status aliases, automatic correction, query execution or provider request was added.

The workflow documentation now describes this repair path. A caller must explicitly choose the appropriate existing status and resubmit its plan.

## Executed verification

- **Actual retained-plan replay:** before patch, generic `ValueError`; after patch, actionable `observations[1].status` guidance with all five allowed values. The failing call still exits 1 with empty stdout. `after-invalid.*` retains it.
- **Explicit repair:** a separate copy changes only observation 1's `status` from `off_topic` to `irrelevant`. The command succeeds and reports zero network calls. `after-corrected.*` and both input plans preserve the distinction; this was an author correction, not tool inference.
- **Focused tests:** `.venv/bin/python -m pytest ideation/tests/test_query_plan_errors.py -q` — **29 passed**. Actual CLI subprocess and MCP client calls verify guidance, correction and zero provider requests. Secret sentinels in submitted status/query/reason/question do not appear in errors. Existing provider-secret controls still pass. All five accepted statuses retain their exact values. Invalid error locations are rejected.
- **Required research gate:** `.venv/bin/python -m pytest ideation/tests -q` — **382 passed, 29 subtests passed**.
- **Bootstrap gate:** `scripts/bootstrap-node.sh --dry-run` — passed, no changes made.
- `git diff --check` — passed.

This demonstrates a concrete schema-error repair, not improved hypothesis quality or new scientific yield. No GPU/native/model imports, serving changes, canonical/cloud writes or Git commits occurred. CLI field replay used an isolated local state. `code-manifest.json` pins the reviewed implementation and tests; the source failure packet was preserved.
