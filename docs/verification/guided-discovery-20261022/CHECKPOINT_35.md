# Checkpoint35 — test proposed changes instead of accumulating instructions

The CPU-only discovery loop continues. This batch adds a source closure, an
alternative implementation arm for a parked component, and a null result from
a controlled critic-guidance comparison. **No new typed hypothesis, implementation
promotion or measured service improvement.**

## Recent compiler research: a useful method, no missing target operation

Round95 screened15 paper identities from two bounded queries and fetched
TrainBridge `2610.29171v1`. Its concrete KeyShift functionalization concerns a
one-token shift of part of a donor attention head. No matching operation was
found in the inspected target preparation path. Generic normalization/RoPE/cache
and quantized handoffs also cannot be proposed solely from a fused function name:
the target's actual call can disable one sub-operation while MegaAttention owns it
internally. The independent review traced that distinction.

The paper's matched eager/compiled evaluation approach remains useful. It does
not require adopting the donor's agent framework, and it does not establish a new
runtime improvement here. The remaining output handoff belongs to existing OP36.
Two retained PR bodies were replayed; no uninspected donor repository is claimed
as implementation evidence.

[Report](round95/REPORT.md) · [Independent review](round95/INDEPENDENT_REVIEW.md)

## Index-K producer fusion: packing is avoidable, efficiency is unresolved

Round96 examines an alternative to round92's compact-and-project arm. The
compressor producer could compute index-K from its BF16-rounded512-element latent
and emit a full-row K buffer while preserving the original main-cache latent.
This could remove a separate projection call and avoid dynamic packing.

The existing producer is a four-warp, single-boundary program, however. Adding
128 dot products there can lose the batched GEMM's weight and tensor-core reuse.
Both original BF16 rounding boundaries must remain explicit; native tactic and
output parity are unproved. Moving K before the first compressor event also
delays main-cache insertion that previously overlapped K preparation. Scalar
dependency examples demonstrate that fusion can help or hurt even at equal
arithmetic cost; they are hypothetical schedules, not measured timings.

The independent review adds a concrete coverage gate: prove that every row read
by the unchanged index-K writer is emitted in that invocation despite different
state-slot and index-slot predicates. Allocating a full-shape buffer does not
prove its consumed rows are initialized.

**Disposition:** retain this as an optional arm of the same parked component,
with no new identity or numerical speedup claim. No native patch was built.

[Source/control analysis](round96/REPORT.md) ·
[Independent review](round96/INDEPENDENT_REVIEW.md)

## Critic-skill change: no demonstrated gain, so do not apply it

The proposed paragraph encouraged deriving useful bounds from incomplete
counters before commissioning additional measurements. Four raw cases and their
expected arithmetic were frozen before testing. Two separate fresh-context agents
received the same evidence and inherited model settings: one used the existing
skill, the other used a copied skill with that paragraph added. No production
skill was changed.

| Synthetic case | Correct removable-row range | Existing guidance | Proposed guidance |
|---|---|---|---|
| Paired eligible counts |8–9|Correct|Correct|
| Aggregate eligible counts |12–34|Correct|Correct|
| Unobserved sampling modes |0–9|Correct|Correct|
| Known complete pass |4|Correct|Correct|

Both kept logical bytes separate from latency, recognized unknown eligibility,
used verification observations rather than requests, and avoided unauthorized
collection. There was **no changed decision or corrected error** attributable to
the paragraph. More explicit wording is not an improvement metric.

Leave the production skill unchanged. This is one paired synthetic check, with
parent judgment against previously frozen criteria—not a statistical benchmark,
native verification, proof of improved paper retrieval, or universal skill
validation. The useful new scientific result remains round94's source-grounded
bounds, rather than another instruction layered onto the critic.

[Method and limits](critic-bound-guidance/REPORT.md) ·
[Raw cases](critic-bound-guidance/cases.json) ·
[Current-skill answer](critic-bound-guidance/control-answer.md) ·
[Proposed-skill answer](critic-bound-guidance/treatment-answer.md) ·
[Recorded checks](critic-bound-guidance/judgments.json)

## State and next research

Source-only retention plans for90/92/93/94 and95/96 passed independent restored
artifact/revision checks. They are predecessor-gated approvals, not completion or
cloud-sync receipts. The existing controller was still waiting behind backfill
publication at its last observation. No competing writer or forced unlock was
used. Git holds the selected small reports/controls; full external packets retain
the source library, tool receipts and original skill-test inputs.

[90/92/93/94 retention review](retention-35/90929394_REVIEW.md) ·
[95/96 retention review](retention-35/9596_REVIEW.md) ·
[Exact copies and frozen packet hashes](source-copy-manifest-35.json)

Active branches now revisit a previously body-only fixed-iteration Sinkhorn
implementation for selective transfer, and recent exact-sampling work against
the native verifier's full-probability and residual requirements. Prior rejected
families remain in scope as counterevidence, not a blanket prohibition on useful
components.
