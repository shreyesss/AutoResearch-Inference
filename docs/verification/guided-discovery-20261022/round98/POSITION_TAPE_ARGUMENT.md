# A position-tape adaptation: sufficient assumptions and break-even

This is a mathematical design argument, not a statement about an implemented
decoder or measured performance. It concerns the single-chain component under
review in round98. The paper's number of drafts B is distinct from native
DSpark's speculative depth five.

## What is adapted rather than directly inherited

The retained full text of `2609.21858v1`, Appendix A.4, Theorem A.6 assumes
independent keyed sources across distinct contexts. A source keyed by request
and absolute output position intentionally shares randomness across alternative
contexts at the same position. That implementation proposal does not meet the
theorem's stated context-independence assumption. It needs its own argument.

## Sufficient pathwise invariant

Fix a request and a tape Z_0, Z_1, ... of independent random vectors, each with
independent unit exponential components over the target vocabulary. Let
F(h, Z_t) be an exact categorical target draw at history h and position t,
including the intended target logit processors. Zero-probability tokens have
infinite race scores; support is nonempty. The reference decoder is
Y_t = F(Y_<t, Z_t).

At a speculative round starting at n, proposals may be arbitrary functions of
the committed history, draft state and tape, including future tape entries.
For proposed tokens d_0, ..., d_(k-1), evaluate target samples

    y_j = F(committed_prefix + d_<j, Z_(n+j))

at the proposed contexts. Admission k may itself depend on lookahead. Commit
matching proposal/target tokens until the first mismatch, then commit that
target correction and stop the round. If all admitted proposals match, commit
the target bonus from the corresponding next context. The zero-admission case
commits a target draw at the unchanged prefix. Honor the same fixed output
limit and target-determined EOS policy as the reference.

Proof by induction on committed tokens: the round starts with the reference
prefix. Before every matching token, its proposed predecessors equal the
reference predecessors, so its target sample equals the reference draw at
that position. At the first mismatch, that same fact applies to the correction;
no descendant under the wrong proposal is committed. If all proposals match,
the bonus context also equals the reference prefix. Thus every round extends
the exact reference output, regardless of how its admission was selected.
Each round makes progress, so for any fixed finite output limit the complete
result equals the reference. Since the reference uses independent position
noise, its output has the intended autoregressive target law.

This is a sufficient construction, not a universal requirement for lossless
speculative sampling. An alternative conditional correction or appropriately
independent scheduling design can also be valid. Equality after conditioning
on an observed adaptive round length is not asserted; that selection event
can depend on future tokens. Finite-time cancellation is likewise a different
observation from a fixed-length completed output.

## What the argument does not establish

- A real PRNG/PRF has not been shown to realize the assumed independent tape.
- Round counters, request slots, retry counters and drafting salts must not
  silently replace Z_t while t remains uncommitted. Cross-request namespaces,
  slot reuse, rollback and absolute-position mapping need explicit contracts.
- Batched target evaluations must equal F at their proposed histories. Cached
  state, processors, sparse attention, graph padding and distributed execution
  must not leak information between speculative contexts.
- Bonus/EOS handling and side-effectful processors must follow the same
  reference state transitions. The finite CPU oracle does not test them.
- A fallback selected after inspecting proposal/noise-dependent conditions must
  not silently switch to fresh independent sampling. A safe fallback within this
  construction is target-only sampling at the current prefix with the same
  position tape. Alternatively prove the eligibility decision is independent of
  the replaced noise (for example a supported-mode decision measurable from the
  committed prefix) or supply a valid conditional correction. A static
  unsupported-request check before lookahead is different from a late
  invalid-draft or AV-triggered fallback.
- Exponential-race real arithmetic does not prove equality to the existing
  native sampler's finite-precision categorical implementation.
- This argument does not criticize the native block verifier, which has its
  own acceptance and residual-correction law.

## A quantitative screening condition without a fabricated forecast

For a fixed stationary workload abstraction, write g for mean committed tokens
per complete round and T for mean complete-round time. An alternative improves
decode throughput only when

    T_new / T_old < g_new / g_old.

This is a renewal-style screening relation, not a replacement for request-level
serving measurement. Queueing, EOS, context evolution, batch composition and
tail constraints still matter. Removing a fraction of one sampler component
does not imply the same reduction in T.

For the explicit one-proposal example p=(.6,.3,.1), q=(.2,.3,.5), shared
exponential race agreement is 18/35 and maximal coupling agreement is 3/5.
With a correction on mismatch and one bonus on agreement, expected progress is
53/35 versus 8/5. Consequently T_new/T_old must be below 53/56: complete-round
savings must exceed 3/56 (about 5.357%) just to break even in this hypothetical
block-length-one example. No such probability vectors or timings have been
measured for the deployment. This is not the expected progress of the native
five-token block verifier and must not be extrapolated as such.

For actual selection compare against the strongest compatible native sampler,
including applicable C025/FV86 changes, and measure both progress and complete
round cost. Full target logits remain required. A measured accepted-length gain
alone, a component timing alone, or the finite oracle alone cannot promote this
proposal.
