# Round99 — selection can make discarded randomness unsafe

## Why this control matters

The ongoing exact-sampling investigation considers sharing randomness between a
draft proposal and target-only sampling. A budget or confidence policy may see
draft randomness before deciding how much to verify. It is unsafe to assume that
an uncommitted draw can always be discarded and replaced without conditioning
on that decision. This packet supplies a deliberately small falsifier of that
assumption. It is not a report that current native AV or rejection sampling is
biased, and it creates no optimization hypothesis or performance qualification.

## Fully enumerated example

Let U and V be independent fair bits. The reference target emits U, so P(0)=1/2.
A lookahead proposal has exposed U. A policy decides whether to admit that
position for verification. The naive scheme emits U when admitted, but otherwise
discards it and emits the fresh V at the same output position.

| Admission rule | Discard/resample P(0) | Keep the position's U P(0) |
|---|---|---|
| Admit neither outcome |1/2|1/2|
| Admit only when U=0 |3/4|1/2|
| Admit only when U=1 |1/4|1/2|
| Admit both outcomes |1/2|1/2|

For the second rule, half the cases directly emit0; the other half resample a
fair bit, adding another1/4. The symmetric rule biases the opposite way. If the
admission decision uses an independent gate bit instead of U, replacement again
gives1/2. Thus the objection is selective replacement after inspecting correlated
randomness, not a prohibition on every adaptive budget or every resampling step.

The stdlib Fraction control enumerates16 joint outcomes across the four rules,
plus8 for the independent-gate control. It computes exact finite probabilities,
not Monte Carlo estimates or a model benchmark.

## Consequence for a possible shared-noise verifier

A candidate design can preserve a request/absolute-output-position noise identity
until that position commits, regenerating the same values instead of resampling
after lookahead-dependent scheduling. That is a possible invariant to test; this
one-bit control does not establish a complete categorical/Gumbel implementation.
An alternative design may prove its stopping decision independent of the replaced
noise or use a valid conditional correction. The control does not force a single
algorithmic solution.

A real integration must establish what confidence/AV observes, which noise keys
include draft/round salts, which uncommitted positions survive truncation/retry,
request-slot reuse, per-position/vocabulary independence, target logit processors,
full support, bonus/EOS handling and output/cache semantics. A toy persistent
coin cannot supply those facts. Conversely, native rejection sampling has its
own correction law; this example does not refute that existing algorithm.

The source research and any future first-match verifier-law proposal belong to
round98 and its independent review. This packet is a complementary countercontrol
against one implementation assumption. It does not repeat that lane's paper
search or claim its continuous-law proof, native parity, acceptance advantage or
sampler-time savings. No GPU/model/native import, serving change, network call,
new collection or canonical mutation occurred.

## Next use

Include a stopping/unused-noise test when judging a shared-noise proposal.
An exact target-only pathwise oracle is a stronger diagnostic than accepted-length
alone. Match the target source and numerical/RNG contract before interpreting it;
accepted progress and net per-round cost still decide performance separately.
Do not promote an alternative law because this small bias counterexample is fixed.
