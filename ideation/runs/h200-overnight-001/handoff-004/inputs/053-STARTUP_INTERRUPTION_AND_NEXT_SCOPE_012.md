# Native003 interruption and a distinct prospective next experiment

Native B003 ended without any observer receipt or request traffic. Its final
execution record reports758.582seconds and1.685738allocatedGPU-hours, unchanged
inputs, no hard-cap overrun, no remaining GPU processes/containers/owned
children and watchdog disarm after verified idle. This supplies no candidate
correctness or performance result. The original native campaign cannot admit
another cold start under its frozen time guard; close it as
infrastructure-incomplete, retaining A001/A002 and the declared but unrealized
A002/B003 comparison.

The controller's final exception is a30-second nvidia-smi telemetry timeout.
That is not established as the initiating cause: retained Docker events show
both containers receivedSIGTERM at23:56:48, before that exception. Their APIs
also record those signals. The watchdog deadline was not due. Root found a
nearby new SSH session, but its command is unknown; temporal correlation does
not identify the sender or intent. Root has requested node-ownership
clarification and holds further GPU allocation pending it. Do not silently
remove that hold, blame C25, or call this merely a telemetry implementation bug.

## Economical prospective course correction

If node ownership is clarified and independent execution review accepts the
plan, a separately named **candidate-first B then baseline A live-stage
experiment** is defensible. Strong exact component evidence remains, and no
native B performance was observed. Test loaded B's native exact oracle and
scoped lifecycle before spending on baseline live startup. This changes the
allocation sequence prospectively; it does not turn unavailable paired-native
timing into a pass or reset the original native budget.

Requiring a fresh standalone padded-native pair before the actual-request
measurement would repeat cold-start cost primarily to recover a cheaper stage
of the funnel that has become operationally expensive. Actual native
correctness and activation can be checked on the same loaded candidate.
Treat missing paired-native timing as missing information, with a deliberately
revised rationale for the different live endpoint. A002 remains historical
correctness/reference evidence; do not compare its timings to a changed live
overlay as though the original paired-native experiment completed.

Prefer the same26-request lifecycle sequence on both fresh arms, followed by
the same eight metric primers and fixed AIPerf warmup/cohort. This avoids
asymmetric candidate preconditioning without another restart. Bind the real
prior lifecycle receipt, counter offsets and request IDs; classify its calls
separately. The later driver cannot still assert fresh-zero counters or no
prior client traffic. Strict drain, exact ownership/forced EOS and accepted
cancel/recovery remain required; unconstrained natural-stop coverage alone
may remain incomplete for the declared ignore-EOS diagnostic.

Root can freeze complete-line log-prefix snapshots after the lifecycle drain,
including byte length/hash, process/run identity and cutoff, for independent
acceptance before measured traffic. Waiting until the container is destroyed
to freeze those already-completed events would force an unnecessary restart.
Preserve final full logs too. Reviewer/controller coordination time counts
against the allocation, with no indefinite GPU-held approval wait.

At the observed approximately18-minute starts, two starts plus15minutes maximum
traffic per arm total66node-minutes before review/cleanup. A75-minute hard/
70-minute work allocation is feasible but has a narrow worst-case margin.
Keep a prospectively explicit second-start guard using actual first startup,
the full second-arm allowance and reserve. The reported cumulative C25 cost
around6.68GPU-hours plus a10GPU-hour cap fits22, but the exact ledger, successful
event-pool preflight and final new contract must bind release. Do not spend the
remaining ceiling automatically or silently extend a running allocation.

For future telemetry, a bounded timeout can be retained as a missing optional
temperature/clock sample rather than itself terminating healthy progress.
Resource identity, actual backend termination, correctness and deadlines remain
hard requirements. This change does not explain or override003's earlier
SIGTERM events. CPU preparation and documentation can proceed while ownership
is unresolved; GPU work cannot.

## Simplification adopted before any new allocation

Support evaluator/root's subsequent proposal to **omit the redundant eight
primers** after identical26-request lifecycle qualification on both arms. That
lifecycle already exercises every engine and ends with strict observed drain.
Bind its exact final cumulative counters and all lifecycle request IDs as
authorized prior traffic, then start the unchanged common warmup/cohort. The
earlier suggestion to preserve the separate eight primers adds no readiness
evidence in this revised sequence. Their removal reduces duplicate work and
phase complexity without relaxing a meaningful check. Root's closed ledger is
approximately6.676231C25GPU-hours, with the5.50-second supervised event-pool
preflight complete and idle; ownership clarification still precedes release.
