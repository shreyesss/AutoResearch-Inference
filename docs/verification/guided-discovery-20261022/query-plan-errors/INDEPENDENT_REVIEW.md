# Independent review: actionable query-plan row errors

**No blocker found.** The production change is limited to a nonobject element in the existing `queries` or `observations` arrays. The compiler raises a dedicated ValueError subtype with compiler-owned field names and bounded zero-based positions. Guidance names the required fields and suggests an empty observation list when appropriate. The submitted value never enters that message.

Array size/type limits, query/observation schemas, allowed statuses, successful compilation and provider paths are unchanged. Other invalid input still uses the existing sanitized boundary. This patch does not turn arbitrary exception text into user-facing text or claim all malformed plans now have detailed diagnostics.

CLI and MCP explicitly recognize only the new error type. Other provider exceptions remain type-only/generic. Constructor checks reject invalid locations, including bool indices, before message construction. The `_request` call sites pass static field names and enumerate validated bounded arrays; no caller data is used as a field name. No provider or HTTP implementation was changed.

I read the actual production diff and tests, verified the frozen implementation hashes, and independently ran the focused test file: **12 passed in 0.73s**. These include actual CLI subprocess and MCP failure/corrected-success paths plus secret-sentinel provider errors. The tests verify no provider call from expansion; the retained external replay additionally reports denied socket hooks. This is bounded behavior evidence, not a proof against every network API or an improvement in research quality. The author's full-suite/bootstrap results were inspected as receipts and were not rerun by this reviewer.

No code edits, canonical mutations, cloud/provider requests, GPU calls or serving changes were made by this review.
