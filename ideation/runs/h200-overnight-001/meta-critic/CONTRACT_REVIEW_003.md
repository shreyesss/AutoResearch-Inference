# Meta-critic review of the concrete C25 native contract

Reviewed `../evaluator/C25_NATIVE_PILOT_CONTRACT.md` and
`../evaluator/C25_NATIVE_OVERLAY_REVIEW.md` before native execution. The plan
implements the recommended course correction: a separately declared, bounded
native integration question; exact actual-input oracle; installed event timing;
and short real request lifecycle checks. It preserves the service endpoint and
old verdicts, avoids another isolated component repetition, and uses two fresh
starts rather than a complicated graph-switching implementation.

**Support implementation and final executable review.** No additional broad
correctness matrix, CUPTI coverage threshold, full production trace or universal
2% native minimum is needed. The source review keeps the treatment narrow and
the declared proof level is appropriate. Final release remains the independent
evaluator's decision after concrete hook/oracle/controller review.

Three small prospective clarifications were sent to root and evaluator:

- Reserve cleanup time under the shared 90-minute deadline. Two complete
  40-minute startup/native allowances plus two five-minute traffic allowances
  leave no cleanup slack. For example, stop useful work by minute 85 and use
  the final five minutes for forced drain/owned-process cleanup; tighter early
  per-arm limits can preserve a useful second arm. This is scheduling, not a
  reason to extend the GPU budget after an unfavorable result.
- State restoration must cover every state mutation introduced by the evaluator
  setup, including sampler CPU/UVA counterparts and request-state overrides,
  and preserve the original allocation/reset mechanism. Do not inadvertently
  demand cloning every transient input/workspace/KV buffer touched by an
  existing dummy replay. Such buffers are normally reused by design. Fresh
  request ownership, expected outputs, recovery and drain are the meaningful
  follow-on contamination checks. A concrete list of modified persistent
  state is better than an unbounded restoration requirement.
- A positive within-start interval in at least one of the replica/shape cells
  is an exploratory matrix signal, not family-wise 95% evidence of an overall
  treatment effect. Keep every cell and its control visible. No extra
  correction machinery is required for the declared exploratory allocation
  decision, but the report must not inflate the inference.

The exact scope deserves continued emphasis. Installed `model_runner.py`
constructs the dummy batch with `is_padding=not is_profile`; its source comment
explains that profiling/warmup routes tokens to experts specifically when
padding is disabled. This pilot deliberately retains padding and suppressed
draft context-KV writes, while exercising actual native graph capture and the
valid sampling/cache path. Therefore its percentage denominator is a
**padded native proposal**, not a production draft pass with ordinary expert
and attention work. Absolute savings, pointer/descriptor activation and exact
native-input correctness remain useful evidence. The controlled actual-request
fixtures test real request integration; they do not retroactively make the
dummy timing a production stage or service measurement.

The fixed four-shape matrix, within-start repeated blocks and target control
can answer whether integration retains the expected mechanism. One A/B
startup pair remains exposed to arm-order/startup drift. Preserve that
limitation when selecting the next allocation. A positive padded-stage result
may justify an actual-request timing design, but is not itself completion of
the user's larger goal of improved service inference metrics.
