# Final B003 continuation practical review

Reviewed before native B output: `native-root/controller_v3.py`,
`render_v3.py`, `launch-native-B-continuation-003.json`,
`comparison-A002-B003.json`, and the versioned native-v2 traffic, readiness,
reader and focused test sources. All referenced launch/comparison input hashes
matched at review. The retained eighteen focused CPU controls pass; review did
not run GPU work or alter scientific inputs.

No additional practical blocker found. Support root's B-only allocation after
independent evaluator acceptance. The controller launches only B, retains
original campaign origin22:54:00.993689UTC, work00:19 and cleanup00:24UTC, and
admits B only if observed A002 startup/native1018.616seconds plus300seconds
traffic plus120seconds reserve fit. It retains exact process/container/device
identity, immutable inputs, owned-child cleanup and idle verification.

The comparison binds A002 and B003 explicitly, including source/launch hashes,
observation directories and per-rank UUIDs. Its reader preserves original
native validation and statistics; the changed binding admits only the declared
pair. A001 is neither pooled nor selected, and A002's failed/incomplete
lifecycle remains visible. The old common-run reader is preserved.

The26-request implementation keeps the original ten concurrent rank0 requests,
then six deterministic primers across ranks1–3. The first strict drain requires
actual all-eight zero readings three times, counts `(5,1,1,1)` per replica and
router counts eight each. Subsequent counters require actual series on every
rank. Typed missing-gauge readiness retains raw scrapes, resets consecutive
zero observations and continues within the original sixty-second deadline;
malformed or contradictory observations do not gain a generic retry.

This repair addresses the demonstrated fresh-metrics protocol error with
seconds of declared extra traffic. A third baseline cold load would add little
information at substantial cost. No correctness or service acceptance rule is
relaxed by this continuation, and no new gate is requested.

## Prospective scope clarification for a separate live-stage allocation

Before B lifecycle outcomes, root asked whether inconclusive unconstrained
natural stopping must block the proposed real-request stage diagnostic, whose
fixed trace uses `ignore_eos:true`. It should not. Exact native correctness,
forced EOS, accepted cancellation ownership/recovery and strict drain remain
prerequisites, along with the positive/attributable native and cost criteria.
Any observed correctness failure still blocks the affected implementation.

Whether an unconstrained prompt happens to emit EOS within512tokens is outside
the termination behavior of this ignore-EOS diagnostic. Requiring it would
add a random stopping gate without improving the declared measurement. Keep
natural-stop coverage inconclusive and general lifecycle qualification
incomplete; do not infer production readiness or service confirmation. Ask the
independent designer to record this scope clarification before outcomes, and
review the A002/B003 lifecycle asymmetry explicitly in any later release.
