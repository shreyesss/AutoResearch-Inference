# Meta-critic acceptance of the narrow root identity repair

Reviewed `native-root/controller_v2.py`, `render_v2.py`,
`launch-native-pair-002.json`, `identity-cpu-reproduction.json` and
`identity-helper-preflight.json` before allocation 002. The original source and
review/manifest bytes are preserved under 001's `frozen-source/`.

The CPU reproduction demonstrates the exact denied host `/proc/PID/exe` read.
The revised actual helper succeeds against a root-owned pinned-image CPU
container, records the denied host executable field explicitly, obtains the
actual PID1 executable and argv inside the container, and requires matching
host/container start ticks. Pre/post Docker inspection binds the same container
ID and host PID and requires that it remain running. The existing worker
identity path also passes against a real container child. Cleanup succeeds.
This is a provenance-preserving repair, not removal of the identity gate.

All input hashes common to manifests 001 and 002 are identical. Only the root
controller and renderer inputs are replaced by their versioned repairs. After
normalizing the run ID, both arms' full command, mount and traffic specifications
are identical. Candidate and scientific evaluator semantics are unchanged.

The controller converts the original `2026-10-20T22:54:00.993689+00:00` budget
origin into monotonic deadlines and passes that same origin to the unchanged
independent watchdog. Work therefore ends at **00:19:00.993689 UTC on
21 October**, and hard cleanup at **00:24:00.993689 UTC**. CPU diagnosis consumes
calendar slack; the budget is not restarted. The B admission test uses observed
A startup/native duration plus 300 seconds of traffic and 120 seconds of
reserve. It is based on cost, not measured native performance, and prevents a
predictably unfinished second cold load.

Support the evaluator's independent release of fresh pair 002 after its final
hash review. No additional scientific gate or code change is recommended by
this meta-review. Preserve 001 as infrastructure-incomplete, analyze 002 by its
own frozen pair, and keep the padded-native scope and lifecycle qualifications
visible in the eventual decision.
