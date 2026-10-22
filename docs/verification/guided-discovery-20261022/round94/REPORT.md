# Round94 — useful bounds before requesting a new counter

## Result

The general non-identifiability in round91 is real, but it is not a reason to
reject all existing acceptance metrics. For FV86, existing accepted/scheduled
counts can bound the number of residual rows eligible for omission. A compatible
histogram can tighten the bound, and maximum-depth acceptance identifies a
particular complete-pass case even under AV. This is an additive evaluation
refinement; FV86 remains deferred. No compatible target workload measurement,
service estimate, new optimization identity or GPU execution is supplied.

## Source-grounded assumptions

Use the exact mapping and branch before applying these bounds. Let s be the
scheduler's valid scheduled draft count, m the actual admitted count, and a the
verifier's accepted draft count. The inspected source supports separate CPU
scheduled counts and GPU AV capacities; this calculation assumes a correctly
paired observation for which `0 <= a <= m <= s <= 5` holds.

The positive lower bound additionally requires FV86's eligible nongreedy,
full-probability block branch and all admitted draft IDs valid. Synthetic
acceptance, one-hot draft handling, placeholders, a different accepted-count
meaning, asynchronous mispairing, or a bonus/stop adjustment not matching the
source void that application. If eligibility is unverified, use a zero lower
bound. Do not take model name or a mean acceptance length as evidence that these
conditions hold. Counter resets and aggregated worker/interval boundaries must
also match before combining counts.

The pinned scheduler metrics are observed before subsequent stop handling. This
is a useful property of the inspected source, not a guarantee about every
external benchmark artifact. AV capacities do not exceed their incoming valid
capacity. The scalar calculation does not simulate the native allocation,
confidence values, RNG, CUDA graph or residual kernel.

## Per-observation bounds

For an eligible observation, omitted residual rows are

`R = (m - 1) * 1[a == m and m >= 2]`.

Since m is hidden but lies between a and s:

- Lower bound: `L = max(a-1,0)` when `a == s`; otherwise0.
- Upper bound: `U = max(a-1,0)`.

If a=s, all three counts coincide. In particular, accepted5 under a verified
five-draft ceiling forces admission5 and a complete pass. If a<s, admission=a
can make it complete, while a larger admission can make it partial. Accepted0
or1 cannot save an interior row regardless of its admission. Unknown eligibility
sets L=0 while preserving U as a conservative arithmetic ceiling.

Sum these bounds over compatible observations. For beneficial complete-pass
count itself, the corresponding bounds are `1[a == s and a >= 2]` and
`1[a >= 2]`. A known global AV budget or confidence constraints may tighten the
bounds; ignoring them enlarges the feasible set and cannot justify a tighter
claim. Sharpness here is only over the stated relaxed hidden-count model.

## If only a histogram or total is available

With fixed scheduled5, let H_j count observations with accepted j drafts.
Known eligibility gives:

`4*H_5 <= total omitted rows <= sum(max(j-1,0)*H_j)`.

This does not require actual per-request admission. With only N observations and
A total accepted drafts (0<=A<=5N), relaxed sharp bounds are:

`4*max(0,A-4N) <= total omitted rows <= A-ceil(A/5)`.

The lower bound follows because each observation without five accepted drafts
accounts for at most four; at least A-4N must therefore accept five. The upper
bound packs accepted tokens into as few positive observations as possible,
since each positive observation loses at least one row from its saving ceiling.
For A=0, both sides are0. A published mean rounded to two decimals does not
supply exact A: preserve its uncertainty or use the underlying integer counters.
Mean acceptance that includes a bonus must first be converted using its verified
denominator and semantics. No numerical workload bound is computed here.

## What this can decide cheaply

1. Read a concrete compatible artifact and prove counter/branch identity.
2. Compute bounds from its richest existing fields, retaining unknown eligibility.
3. If the upper bound already gives too little opportunity under an independently
   supported cost model, defer the experiment without new instrumentation.
4. If the bounds are wide enough to change the decision, collect effective
   admission or the actual terminal flag only when separately authorized.

Even exact omitted-row counts do not provide exposed residual time. Under the
previously stated BF16/BF16 arrays and vocabulary129280, one omitted row has
517,120 logical input bytes; multiplying by rows counts source-level reads, not
HBM traffic, microseconds, ITL or saved launch overhead. Flag cost, cache reuse,
overlap, kernel minimum work and numerical parity remain separate gates. Do not
convert a byte ceiling into an assured service gain.

## CPU verification and yield

A stdlib exhaustive hidden-state enumerator checked all21 single `(s,a)` pairs
for s<=5,9,261 triples of observed pairs and175,616 hidden assignments. A separate
accepted-array aggregation checked54 `(N,A)` combinations for N1..4, including
A0 and maximum acceptance. Analytic lower/upper limits match the enumerated
extrema under the explicit relaxed assumptions. These are finite arithmetic
controls, not workload, AV or GPU tests.

No search provider call was needed: the decision gap concerned the information
already present in pinned metrics. Frozen prior reports/reviews and the six-file
source export are reused without changing their original identities or retrieval
dates. No new general CLI/MCP command is introduced before a real artifact needs
this calculation. A bounded script suffices and avoids growing the tool surface
for an unobserved data path. Yield: one evaluation refinement; zero new cards,
implementation qualifications or measured serving wins.
