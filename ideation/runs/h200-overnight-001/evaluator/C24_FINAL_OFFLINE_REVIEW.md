# C24: independent outcome of this bounded allocation

**Offline feasibility advanced; instrumentation and service benefit remain
unresolved. No model recapture or AV service attempt is released.** The old
`av-k5-timing-001` instrumentation-inconclusive verdict is unchanged.

The retained-trace audit reproduces all 647 chronology flags using unique raw
correlation IDs. Of these, 460 have equal CPU/GPU external IDs, while 187 driver
associations lack that field on both sides; no conflicting external IDs were
reported. The missing-range problem is separate: replica 1/rank 2 at +90 s has
eight ProfilerStep/native ranges and 26 target scopes. Installed
`execute_dummy_batch` bypasses `annotate_profile`, so dummy cooperation can
produce target/draft ranges without advancing the real-worker schedule or
providing native context/generation identity. This is a source explanation for
a possible cause; it does not prove every one of the 19 outside-native scopes
was a dummy or restore the missing eligible cycles. Keep their exclusions.

## Synthetic instrument result

Independently reviewed `executions/synthetic-clock-001/execution.json`, all six
trace hashes, event receipt, parser output and complete console log. The root
execution used the intended GPU UUID and pinned image, no model/network mount,
unaltered frozen inputs, and returned all eight GPUs to idle. It completed in
4.39 seconds, 0.001219 visible-GPU hours; its whole-node opportunity accounting
is separately recorded. No profiler truncation/dropped-activity warning appears
in the saved console output.

All **384 expected CPU scopes** and **1,280 GPU kernel records** have explicit
unique associations. Single-operation eager and graph modes each show one
kernel per iteration, and the eight-operation graph shows eight, with consistent
device/stream and graph/node identity. CUDA-event intervals are finite and
positive. There are **zero negative CPU-start/GPU-start or CPU-start/GPU-end
offsets**. No timestamp correction or alternative historical attribution was
performed.

This result means the anomaly was not reproduced in these six small synthetic
episodes. It does not demonstrate correct absolute clock alignment under the
old serving workload. In particular, these 1024-square multiplications execute
for roughly 56 microseconds each, longer than many short activities implicated
by the historical sub-microsecond to tens-of-microseconds chronology offsets;
queued work also creates positive launch-to-execution delay. That limits the
negative probe's discrimination of small timestamp-domain errors. It does not
establish the cause or authorize removing the old chronology checks.

| Reviewed artifact | SHA256 |
| --- | --- |
| `executions/synthetic-clock-001/execution.json` | `6a95c3b9076b2810245e4c19af20707902ce344d97fc4dc66a860c1816f80684` |
| `executions/synthetic-clock-001/analysis.json` | `7685724db64da8c123de806da6629c1721a35ef27fe7b6d64d65bec0e9d1a83e` |
| `executions/synthetic-clock-001/probe/receipt.json` | `1ee5fd387f1a2973316ad8d4954c2cc74b0f5a2f3b0979b5b2b9718f33ef8a88` |
| `executions/synthetic-clock-001/stdout.log` | `f1ba192b3429f8711e9978f603bccb5f78fb76367dfa35c5a2828376df40e7d7` |

## Joint policy feasibility and the next intervention

Independently checked the developer's `C24_JOINT_DISPATCH.md` against installed
local budget selection before DP synchronization, the six-row CPU collective,
max-token/graph rounding, overwritten padded vector and reused target request
capacity for q5 drafting. A rank reducing its local budget need not reduce the
common target or subsequent draft graph when another rank sets the maximum.
The existing local objective already charges drafting, but its request-indexed
draft term does not express every such descriptor-dependent cost.

The current local decision has no current remote candidate progress/confidence
curves. An exact joint objective therefore requires a changed collective,
coordination placement or a declared stale-state approximation. None is free or
implemented here. AV-off traces also do not acquire learned confidence merely
because the checkpoint contains the head; source enables its computation only
with AV. Any replay must retain confidence age and request-slot generation.

The suggested **post-synchronization fill of already selected target capacity**
is a distinct feasible-looking revision: it might increase useful verified
progress while leaving selected descriptors unchanged. It is not proven free
work. Useful attention length, rejection/sampling cost, accepted output, and
derived CPU/GPU query/KV metadata can all change. It needs an explicit hypothesis
revision plus independent legal-prefix/metadata/guard tests and comparisons
against fixed-k5, stock AV and a locked static policy before implementation or
timing. The earlier synthetic coupled-cost counterexample does not validate it.

Allocate no eight-GPU cold load simply to repeat the failed schedule. A future
recapture needs explicit real/dummy identity, coordinated finite recording and
export behavior, a justified timestamp/association design, and the unchanged
all-rank minimum ten-cycle/95%-busy-coverage gates. Current evidence does not
satisfy that release. Preserve both full service attempts and prioritize C25's
now-applicable bounded component qualification.

## Prospective small diagnostic extension

The first probe's physical GPU 0 was also clean in the old study; the old
chronology anomalies were on physical GPUs 4, 6 and 7. Before any second probe
output, root requested a distinct bounded check on implicated GPU 6 with short,
minimally queued operations over a longer finite recording. Its separate
`C24_SHORT_OPERATION_PROBE.md` contract specifies that diagnostic, preserving
the first result and this interpretation. This extension does not release a
model-service recapture or change the old timing verdict. Its outcome will have
its own review rather than rewriting the first probe above.
