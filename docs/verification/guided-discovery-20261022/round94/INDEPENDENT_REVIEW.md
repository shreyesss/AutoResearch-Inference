# Independent review: round94 conditional opportunity bounds

Verdict: no blocker to retaining this as a useful FV86 evaluation refinement. It changes neither FV86's deferred status nor its performance qualification. All seven frozen artifacts, seven exact revision quotes and six archive/export body equalities passed independent checks. I reviewed the algebra and source; I did not rerun the author's enumeration or execute native code.

## Algebra

For eligible observations with a <= m <= s, complete acceptance has a=m, so R=max(a-1,0). An incomplete pass gives R=0. When a=s, every feasible m equals a; when a<s, m=a and m>a give both extremes. This proves the reported interval and additive interval sums over independently unconstrained hidden counts. Accepted0/1 correctly give zero opportunity, including the empty-block case.

For N observations and A accepted drafts, at least max(0,A-4N) observations must contain five accepts; filling the rest to at most four attains the lower construction. To maximize sum(max(a-1,0)), minimize the number of nonzero observations: ceil(A/5). Packing fives and a final remainder attains A-ceil(A/5). The reported sharpness is only for this relaxed integer model. Native confidence/global budget constraints can remove extremizers. The fixed-five histogram formula is correct; in fact its bounds remain conservative when five is only the admitted-count ceiling, although smaller known scheduled counts can tighten the lower side.

The script's finite enumeration corroborates these formulas rather than validating source-to-workload applicability. Its joint counts treat hidden admissions independently and do not simulate AV, EOS, RNG, probability rounding, or the residual kernel.

## Source boundary

Pinned scheduler.py:2195-2234 computes accepted drafts from generated length minus the configured sampled-token count, observes grammar-adjusted scheduled drafts, then handles stop truncation at 2250+. stats.py:385-420 stores the paired detailed arrays and an acceptance histogram; its mean acceptance includes a bonus. adaptive_verification.py:412-438 bounds admission by incoming capacities and rebuilds logits/query boundaries. These are code facts, not evidence any retained serving run enabled detailed metrics or has the required branch.

The native rejection_sampler_utils.py:568-644 stops nongreedy verification at a placeholder; an all-admitted accepted count cannot cross such a placeholder. Therefore, once the exact native nongreedy full-q block branch and count mapping are established, a=s together with a<=m<=s also proves full admission and validity of that accepted prefix. Do not unnecessarily demand a new validity counter for such already-proved maximum-depth events. This does not remove the branch, full-q, synthetic-mode, pairing or ceiling gates. Unknown eligibility still warrants a zero lower bound.

The upper bound remains an arithmetic opportunity ceiling for the scoped FV86 branch, not a universal bound for some broader future residual optimization. Aggregated counters must share request/worker/time/reset scope; rounded means or bonus-inclusive means cannot silently stand in for exact A. N is the number of compatible verification observations, not request count. Existing summary histogram totals can supply N and A when their provenance is verified.

## Decision use and limits

This appropriately improves on a blanket 'existing metrics are insufficient' conclusion: metrics can be non-identifying yet useful for bounds. First examine an existing compatible artifact; do not collect new counters merely to reproduce information already forced by accepted5. Conversely, unknown branch or unmatched fields cannot generate a positive unconditional lower bound.

Even exact rows do not determine exposed time. The 517120-byte number assumes two BF16 vocabulary arrays and counts logical source reads only. Cache effects, flag overhead, scheduling overlap, graph launch cost and numerical correctness remain unmeasured. The report correctly supplies no workload number, native proof, new card or serving win.

Read-only review notes: an initial attempted path named dspark/rejection_sampler.py did not exist; the actual verifier inspected was spec_decode/rejection_sampler_utils.py. No source or frozen author artifact was modified.
