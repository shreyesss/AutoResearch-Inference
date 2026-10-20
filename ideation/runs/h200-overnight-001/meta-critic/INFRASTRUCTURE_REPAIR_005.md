# Meta-critic: preserve the failed allocation and repair identity cheaply

Reviewed the finalized `native-pair-001/execution.json`, A router log and
artifact inventory after the first native allocation. A reached all eight
native receipts; root reports the required capture/oracle/restoration passes
and 960 samples per rank. The controller then raised
`PermissionError(13, 'Permission denied')` immediately after router startup,
before controlled traffic, and did not launch B. The execution receipt records
unchanged inputs, no remaining GPU processes/running containers, no owned live
children, and watchdog disarm after idle verification. Docker removal returned
zombie-process errors, which remain in the cleanup record rather than being
silently discarded.

This is an **incomplete infrastructure allocation**, not an unfavorable C25
optimization result or failed native oracle. There is no candidate native
measurement and no full integration or service result. The likely cause is
the unprivileged controller reading root-owned container host `/proc/PID/exe`
inside its identity helper; this remains a diagnosis to reproduce cheaply,
not an assumption to bypass.

**Recommend one reviewed repair and fresh named A/B pair 002 within the original
cumulative envelope.** The objective is still worth pursuing: the component
result is qualified, native A demonstrated fixture feasibility, and the failure
occurs in post-readiness host bookkeeping. Abandoning the mechanism because of
that failure would confuse tooling reliability with scientific value. Blindly
repeating the same cold load would be equally wasteful.

Required concrete repair sequence:

1. Before editing, preserve the exact controller/watchdog and related frozen
   input bytes used by 001. At this review, its frozen input hashes still match
   the current controller (`8305ed51e193fba4b295ed4cefacb388fa4e56ef83bfbc599429ec27fbfed42d`)
   and watchdog (`8783bf8580e25f269b7d699cd6cc52e9132cdaa5a5e1098080c8451cf4683583`).
   A hash-only pointer to a subsequently edited file is insufficient restoration.
2. Reproduce the entire post-readiness identity sequence with a short root-owned
   **CPU-only** container using the pinned image. No model load or GPU access is
   needed. Bind Docker container ID, immutable image/mount/config, host PID and
   start identity, and actual in-container `/proc/1` executable/arguments where
   host permissions deny them. Record the access failure and substitute source
   explicitly; do not omit identity fields silently or change host permissions.
   Test both expected success and a missing/wrong identity case.
3. Have the independent evaluator accept the narrow identity/controller repair,
   new input hashes and the reduced shared limits before launch. Keep candidate,
   native oracle, timing workload and controlled fixture semantics unchanged.
   Preserve 001 as a failed unique allocation and give 002 a new output root.

001 consumed **1,151.491759 allocation seconds / 2.558871 H200-hours**. Under
the original cumulative 90-minute / 12-H200-hour ceiling, the remainder is
**4,248.508241 seconds (70.8085 minutes) / 9.441129 H200-hours**. Retaining the
final five-minute cleanup reserve leaves **3,948.508241 work seconds** for 002.
Enforce these reduced limits in the controller and independent watchdog; do not
reset a new 90-minute allowance. Record CPU diagnostic time separately from
the summed active node allocations and do not hide the first startup cost.
The evaluator additionally proposes retaining the original absolute 85/90-minute
deadlines from 001's start. That stricter interpretation is also sound: use the
earlier of the absolute deadline and cumulative remaining allowance, and record
that CPU diagnosis consumes calendar slack even while GPUs are idle.

A's native readiness took about 18.2 minutes. Two comparable starts plus the
fixed traffic, bounded review and cleanup can reasonably fit the remaining
budget. Before admitting B, compare remaining time with the observed startup
cost and fixed remaining work. If A unexpectedly consumes most of the budget,
stop with an incomplete record rather than begin a predictably unfinished cold
load. Make that decision from time/resource evidence, never favorable A timing.

Alternatives considered:

- Reusing 001 A with a new B would save one startup, but 001 lacks its planned
  runtime identity and real request lifecycle phase. It would create a changed
  pairing/provenance scope and is unnecessary given the remaining feasible
  budget. Do not splice its timings into 002 or choose between baselines after
  seeing B. Preserve 001's valid partial evidence independently.
- Stopping immediately would conserve resources but leave the most promising
  mechanism unevaluated because of a reproducible host-access issue. The
  remaining budget and already demonstrated native fixture make a narrow
  diagnosed repair preferable.
- Increasing the GPU budget, changing the candidate or loosening the native
  oracle is not justified by this error. Another unexpected failure would need
  a new explicit diagnosis/allocation decision, not an automatic retry loop.

The fresh pair remains a padded-native integration pilot. Even a positive
result will not by itself establish improved production drafting or ITL.
