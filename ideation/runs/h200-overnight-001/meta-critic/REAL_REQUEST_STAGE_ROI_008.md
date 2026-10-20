# Prospective ROI of one actual-request stage pilot

Written while native 002 A is loading, without its performance results. This
answers root's request for a concrete next action if 002 is positive and
independent lifecycle acceptance completes. It does not extend 002, change its
deadline, or release another GPU allocation.

**Conditionally favor one narrow actual-request drafting-stage A/B pilot over
automatically parking at padded evidence or immediately buying a full Mooncake
screen.** It would answer a genuinely new question: does C25 save time while
ordinary requests execute the actual expert, attention, context-KV and rejection
path? A positive result would be a scoped improvement measured during real
inference. It would still not be confirmed primary service ITL or a production
qualification.

## Expected signal and practical value

The measured component saving at relevant historical shapes is 45–83 microseconds
per complete five-step call. That is a reasonable scale to test, not a promised
live-stage delta. The percent effect depends on the actual full drafting span:
for illustration, 50 microseconds is 2.5% of 2 ms and 0.5% of 10 ms. Neither
denominator is measured live here. Native 002 may show whether integration
retains the mechanism, but its padded expert/attention denominator cannot price
production drafting.

The installed live path creates `AsyncOutput` and starts copying target output
before it invokes the drafter, expressly to overlap the two. Thus even a shorter
live drafter span is not automatically exposed client latency. Record actual
request output/progress and invocation counts, report the stage's absolute
saving, and keep exposed/client gain unknown unless separately measured. Do not
turn the stage percentage into ITL percentage or assume queueing amplification.

## Feasible narrow observation, with a real source gap

Source review of installed `model_runner.py` shows that `sample_tokens()` calls
the real `self.speculator.propose(...)` around line 2221. It does **not** call
the collector's `forward_end`, `drafter_start` or `drafter_end`; those currently
exist only in `_dummy_run`. Merely enabling `StepTimingCollector.collect()`
would therefore miss real intervals or mix them with dummy cooperation.

The evaluator builder can instead add a small identical observation patch
directly around that live proposal call. Two same-stream CUDA events bracket
the declared proposal stage; no sampler/candidate/graph change is needed.
Observe actual request IDs, valid mappings, logical/executed descriptors,
real/dummy identity and available CPU metadata outside the bracket. Explicitly
exclude cold capture/dummy cooperation from the real endpoint and retain their
counts. Do not read GPU state back synchronously in the measured hot path.

Use a bounded event buffer and defer elapsed-time resolution and export until
the events complete, without per-step `synchronize()` or disk writes. The
concrete safe stop/export path is a prelaunch design item: a counter alone is
not proof that all device events completed. Reuse an already available control
or narrowly scoped observer mechanism if possible. A polling/export thread or
new RPC must be reviewed for ownership, boundedness and perturbation before
adoption; neither is assumed available here. Do not add a general profiler
framework or revive CUPTI cross-domain attribution for this question.

Freeze a small controlled request schedule with sufficiently long outputs and
explicit routing to the ranks being claimed. Reusing the deterministic token
fixtures can hold committed progress constant while still running ordinary
model/attention/expert work; disclose that constrained output is a controlled
inference workload, not the natural Mooncake distribution. One or two relevant
concurrency/context conditions are enough to answer the stage question. Do not
require a broad workload suite, every historical shape, or the old C24 trace
coverage rules. Record missing/unexpected shapes instead of adding traffic
until an attractive cell appears.

Keep exact native/component correctness and accepted lifecycle receipts. The
new hook needs focused CPU/small synthetic controls for real/dummy selection,
event ownership, pending-event export and intentional wrong IDs, plus a source
review establishing that observations cannot change sampler state. It does not
need another 108-fixture sampler repetition. The actual candidate remains
unchanged. Use fixed warmup/measurement/repetition rules, preserve every block,
and retain the limitation of one A/B launch pair if that is the chosen design.
Instrumented request timings cannot replace the unprofiled service frontier.

## Cost and release decision

Using the observed 18-minute startup, two starts plus short fixed traffic/drain
should cost roughly 45–50 node-minutes. At the older 26-minute startup, the
same plan is closer to 60–65 minutes: approximately **6–8.7 H200-hours**. This
is materially less than a full 80–96-minute Mooncake pair and could fit the
original conditional C25 component/integration ceiling of 22 GPU-hours.
Compute the actual remainder after 002; include failed 001, component failures
and successful allocations. A planning ceiling is not an automatic allocation.

Propose an initial **one-engineer-hour CPU design/preflight ceiling** for this
narrow observer and request plan. If safe finite export, native identity or
unchanged-state observation requires broad new machinery, stop the design
allocation and explain the gap instead of growing the framework overnight.
If it stays narrow, the evaluator/root should freeze a concrete GPU ceiling
using actual startup costs and the remaining 22-hour envelope, with cleanup
reserve and B admission check. It is a new named allocation; 002's original
85/90-minute clock is never restarted or extended.

Advance this design only if 002 has a plausible positive native signal at
relevant cells, no observed correctness failure, completed lifecycle acceptance,
and enough remaining budget for both arms. For null/mixed/drift-dominated native
evidence, apply `PROSPECTIVE_NEXT_DECISION_007.md` first; do not spend merely
because an actual-request metric would make a better success story. If the live
stage pilot is positive, the remaining service decision should use its actual
absolute gain, progress and exposure limitations. If it is null, negative or
inconclusive, retain that result and stop automatic escalation.
