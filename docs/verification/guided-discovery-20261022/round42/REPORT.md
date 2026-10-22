# Round42 — Saturated block-verification ratio is not enough to skip residual work

**Outcome: zero new hypotheses. Park the direct shortcut.** A narrow source check found possible removable work, but no reference-equivalent shortcut has been established. No paper/provider query, GPU invocation, kernel import, runtime patch, model or device probe was performed. Source and standard-library numerical diagnostics only.

## Question and prior comparison

At exact c455 Flash-1017 DSpark5/temp1, can the verifier omit its full-vocabulary residual-mass scan when the cumulative ratio is exactly one? This follows the actual remaining consumer found in round39, rather than repeating its producer-statistics proposal. C025 addresses draft Markov sampling; this is target/draft block-verification residual computation. The complete earlier139-record compact inventory was already read; read-only current inventory has141 records. The two additions, NQ33 and OP36, were read and concern different operations. No prior compact mechanism claims this shortcut. Distinctness is not a reason to create a card.

## Exact source control flow

Pinned `rejection_sampler_utils.py`, commit `c4557869393db4d75c483d92edd02a5125500883`:

- `_compute_cumulative_log_p_kernel:395` clamps each cumulative update to at most zero; exponentiating a zero yields p=1.
- `_compute_local_residual_mass_kernel:435+` already skips first/bonus positions, placeholder block ends and temperature0. For eligible positions it still reads both distributions and computes `sum(max(p*target_prob-draft_prob,0))`. The p for row j comes from cumulative index j−1.
- `_rejection_kernel:611+` consumes the next position's mass for the current position's acceptance threshold. It computes `denom = residual_mass + 1.0 - prefix_joint_ratio`, then `h = where(denom>0,residual_mass/denom,1)`.
- The block branch updates the **latest passing index** (`accepted_length = where(u<=h,i+1,accepted_length)`). It does not stop at the first failed acceptance test as the ordinary tokenwise branch does. Placeholders still terminate verification. Recovery subsequently uses the chosen rejected position and its cumulative ratio.
- `gumbel.py:66+` uses `tl.rand`, clamps away zero, and mixes step into the seed. No actual seed trajectory was run or claimed in this diagnostic.

In exact real arithmetic, p=1 makes h=1 for positive residual and the explicit zero-denominator fallback also yields1. It is tempting to skip the distribution reads and substitute zero partials. That would be an algorithmic algebra argument, not yet a proof about the current floating implementation.

## Executed falsifier

`threshold_probe.py` emulates explicit binary32 round-to-nearest operations using Python `struct`; it does **not** execute Triton or establish its final lowering.

For a legal finite scalar residual just above 2^-24:

| Quantity | Value |
|---|---:|
| residual | 5.960465188081798e-08 |
| round32(round32(residual+1)−1) | 1.1920928955078125e-07 |
| computed h under that operation order | 0.5000000596046448 |
| substituted h | 1 |

A test uniform0.75 therefore produces a different local decision. It is an illustrative representable uniform, not a reproduced native seed. This is an especially clear cancellation counterexample; residual.001 also gives a smaller discrepancy. Of241 bounded finite scalar values,24 did not yield exactly unit h in this model. These are test-grid counts, not runtime frequencies or an error-rate estimate.

The probe also preserves cases for residual0, the tie/boundary around2^-24, residual infinity and NaN. In the source formula, positive infinity can produce NaN h, while a NaN denominator takes the explicit fallback; the shortcut cannot assume those are equivalent. Nonfinite states are not claimed valid target distributions.

**Compiler limitation:** if the actual compiler reassociates the expression to residual+(1−p), the finite p=1 discrepancy can disappear. No compiled assembly, native RNG or device result was inspected. Thus this is a counterexample to an unqualified source-algebra equivalence claim, not a demonstrated target decoder bug. A correctness fix that changes the baseline's finite behavior is also a different task from a reference-preserving speed optimization.

The block-state fixture additionally shows an earlier changed test can alter final accepted length if no later test passes, but can be overwritten by a later passing test. This prevents pretending each affected local test maps one-to-one to emitted-token changes. It is a scalar control illustration, not a realized model trace.

## Materiality and decision

At k5 there are at most four interior residual rows. With both distributions BF16, skipping every such row would avoid at most **2,068,480 logical input bytes per full request block**, before existing guards. Normalization scans, cumulative-ratio computation, recovery reads and kernel launches remain. The actual number of saturated rows, input dtype, cache behavior, and exposed time are unknown. Exp/reduction work is also potentially removed, but no timing estimate is assigned.

A narrower RNG-dependent certified bound might be derivable, but it would require exact lowering/rounding and finite-value admission and still needs exposure evidence. It is not implemented or recommended as a new hypothesis now. Do not replace the current algorithm with a mathematically cleaner decoder while labelling it the same reference.

**Reopen only if** approved exact-runtime artifacts establish the actual arithmetic lowering and a safe equivalent shortcut, plus representative saturation counts and exposed residual-stage time. A paper search cannot resolve those implementation prerequisites. Stop before additional broad retrieval or synthetic-fixture accumulation. No new candidate or status transition.
