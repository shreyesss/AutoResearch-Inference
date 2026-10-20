# Meta-critic review of the proposed native-stage pilot

This follows `COURSE_CORRECTION_001.md` and root/evaluator discussion before
native pilot implementation or outputs. Root proposes two freshly attested
baseline/candidate launches, capped at 90 minutes on the eight-GPU node, using
the installed `StepTimingCollector` and native graph machinery. This is a
reasonable, simpler allocation than inventing a dual-path graph-switching
system. The cap is 12 GPU-hours including cold loads, traffic, drain and cleanup.

**Proceed with concrete design, with explicit valid-state witnesses.** An
initial evaluator warning followed the shared `Speculator.prepare_inputs` path
and suggested dummy drafting always uses negative mappings. The evaluator
corrected that source reading before a contract or native output: DSpark uses
`DFlash.prepare_dflash_inputs`, which copies `InputBatch.idx_mapping` and masks
padded rows; `dummy_run` suppresses context KV writes separately. Therefore the
initial all-negative warning is not an established blocker, and a startup
fixture may be feasible. The runner's `valid_dummy_state_slots` argument alone
still does not attest the complete state. Trace the exact handoff and record
actual temperature, seeds, state mapping and cache updates at the candidate
call. These checks must establish that the fixture exercises C25's relevant
production sampling behavior rather than an inactive padded path.

Two acceptable small designs are an evaluator-owned controlled valid-state
native graph fixture, or bounded real requests with native CUDA-event timing.
Choose the one with the least new machinery after checking implementation cost.
A controlled fixture may initialize state explicitly; it must not silently
change the production meaning of dummy cooperation. Production request
semantics and the original baseline remain intact. Native graph replay with
actual weights and controlled valid activations can establish scoped inference
stage improvement; it still cannot establish service latency or model quality.

The installed collector is suitable for a narrow measurement: it records four
CUDA events in issue order, queues steps and synchronizes at collection end.
This avoids the old CUPTI cross-domain association problem. Its `drafter_ms`
brackets the complete `propose` stage, including any event-visible idle gaps;
it is not automatically the pure graph kernel union. Name the endpoint exactly
and use the same bracket in A/B. Do not add target/draft events as though their
sum necessarily equals the entire decode cycle. If a whole-cycle endpoint is
desired, give it its own outer same-stream bracket.

Freeze a small relevant shape/context set and fixed repetition/order schedule
before outputs. Record **actual** target and draft descriptors after DP padding
and graph rounding; requested logical sizes alone are insufficient. Require
activation and relevant work completeness, not the old C24 requirement for ten
real decode cycles in every trace cell or 95% categorized CUPTI activity. Those
criteria served a different measurement and would obstruct this one without
adding validity. Include unchanged target-stage timings as a diagnostic control
for gross arm drift, and retain per-rank observations without treating ranks as
independent experiments or summing them into wall time.

One baseline launch followed by one candidate launch is an exploratory native
comparison. Repeated blocks estimate within-session variation; they do not
eliminate launch/order/thermal confounding. Report that limitation directly.
Use the pilot to establish activation, integration correctness and native gain
scale; do not sell a narrow replay bootstrap as confirmed service evidence.
If the result is worth confirming, the next design can buy independent
alternating launch blocks. This first pilot does not need that expense in order
to be decision-useful.

The designer should require exact native token/cache/ownership checks relevant
to the integration before accepting a performance result. Full request EOS,
cancellation, rejection and recovery remain necessary before **service timing**.
They need not prevent a clearly scoped native-stage timing pilot whose finite
controlled state has already passed independent correctness. That distinction
keeps the gate proportional to the claim without waiving lifecycle checks.

Historical waiting/running telemetry does not currently establish a queueing
amplification mechanism. Small direct component savings can justify this native
stage pilot; neither speculative amplification nor a promised 2% ITL win is
needed. After the pilot, root and evaluator should decide whether one service
attempt has enough expected value, while retaining the other attempt. Report a
negative or inconclusive native result without expanding shapes until one wins.
