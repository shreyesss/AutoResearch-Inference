# Independent round42 residual-shortcut review

Verdict: agree with zero-new, park the direct p==1 residual-scan shortcut. A source-algebra identity is insufficient to certify reference equivalence. The report accurately stops before claiming a target decoder bug or a measured gain.

Read pinned cumulative-ratio update, residual producer, block rejection consumer and RNG helper. The residual producer's row j uses cumulative index j−1; the rejection consumer at i reads next-row mass. Current guards already omit first/bonus, placeholder-terminated and greedy rows. Block acceptance records the latest passing index, so later passing steps can mask an earlier local difference. Recovery depends on the final selected rejection location.

Independently verified9 original artifact hashes. Replayed the stdlib probe in a separate temporary directory with exact JSON equality. Separately derived its strongest finite counterexample with exact rational arithmetic: r=8388609/2^47 lies just above the midpoint for rounding1+r; binary32 RNE selects1+2^-23, subtraction yields2^-23, and h=8388609/2^24 is strictly below0.75. This example does not depend on accidental Python binary64 double rounding; the division result is representable. The exact tie instead rounds to1 and triggers the denominator-zero fallback.

## What it does not prove

Actual Triton lowering may reassociate or use approximate arithmetic; Python f32 division is not a native tl.div test. No compiled source, assembly, native seed trajectory, target logits or attainable target residual were checked. Even a finite residual in the legal mass interval is not evidence that this model's quantized distributions and reduction order produce it. The24 nonunit thresholds among241 constructed scalar cases are not failure prevalence, and nonunit h values above1 need not change any legal uniform decision. Infinity/NaN controls illustrate omitted admission assumptions, not known reachable normalized target inputs.

The conditional logical-byte ceiling2,068,480 is arithmetically correct for four eligible interior rows, two BF16 vectors and vocab129280. It excludes existing guards and does not represent NVLink/HBM traffic or exposed time. Normalization, other residual/recovery reads and launches remain. Saturation counts and actual input dtype are unknown. A correct algebraic reformulation that changes prior finite decisions would be a numerical/correctness change, not automatically a reference-preserving optimization.

No blanket mathematical impossibility is established. A narrower admitted shortcut might exist, but its compiler/numeric/RNG and workload premises would need evidence. The current stop/reopen rule is reasonable; more generic paper queries or scalar fixtures would not resolve those gates. No new hypotheses, canonical changes, network calls, GPUs or model imports in this review.
