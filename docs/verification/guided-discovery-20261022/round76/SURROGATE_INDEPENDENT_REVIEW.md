# Independent check: PC76 surrogate reversal

No blocker to the narrowly stated counterexample. I independently wrote and executed exact Fraction calculations from the supplied three target states and temperature-scaled proposal weights. Both the accepted-parent-mass formula and enumeration of all four proposed token paths agree.

At temperature 1, surrogate=577507/338000 (1.7086005917), actual accepted draft count=59899/33800 (1.7721597633). At temperature 2, surrogate=281329/162000 (1.7365987654), actual=4687/2700 (1.7359259259). Thus the surrogate improves while expected accepted count decreases.

The key distinction is the probability of reaching a particular accepted parent: min(p(v),q(v)). Averaging child overlap under p and multiplying by aggregate root acceptance uses a different parent distribution. This is a counterexample to treating the explicitly defined teacher-forced surrogate as a guaranteed progress-ranking metric. It does not invalidate using that objective to screen candidates, refute PC76, or reproduce the complete paper study.

Scope is ordinary two-token sequential rejection with positive support and stopping at first rejection, no EOS. The example was supplied by root after deliberate counterexample search; this review is independent arithmetic, not blinded selection or prevalence measurement. Native DSpark block rejection, confidence/AV scheduling, finite precision and serving cost remain untested. No native imports, GPU work, network or canonical mutation occurred.
