# Independent target-summary correction review

**The corrected counterexample establishes the stated information-loss claim.** The original varying-draft example did not isolate target-only compression when the complete draft vector remains available. Keep both artifacts and the explicit correction; do not credit the earlier example with the repaired conclusion.

With full draft q=(.4,.3,.3), alpha=.8, selected target token0=.4 and target complement=.6 fixed, target vectors (.4,.5,.1) and (.4,.1,.5) require residuals (0,.1,0) and (0,0,.1). A third target (.4,.45,.15) requires (0,.06,0). Thus the retained inputs are identical but both recovery identity and total residual mass can differ. I independently recomputed these exact rational expressions; this is a mathematical check, not independent model/native evidence.

This also covers a representation retaining selected logits and a total log-normalizer: choose the full logits as log(target probabilities), with total normalizer zero and the same selected logit. It does not establish insufficiency for richer summaries that retain extra per-token information, an RNG-dependent sufficient sampling state, chunked residual accumulation with sufficient recovery information, or recomputation. Only the selected-plus-complement target summary with full q and alpha is refuted here. It does not disprove Pruned CTC or exact streaming designs.

The pinned source computes max(alpha*target-draft,0) for residual mass at rejection_sampler_utils.py490–494 and individual residual logits at871–893. The preceding target/draft selected ratio .4/.5=.8 is a valid probability construction; it does not demonstrate an observed target prefix, native floating arithmetic, actual acceptance event or full verifier correctness. The source branch requires draft logits and block verification; placeholder/bonus and one-hot branches have different contracts. Do not generalize this particular expression to every rejection path.

The new critic instruction correctly requires holding all retained inputs fixed, varying discarded information, and naming the exact representation rejected. It avoids the draft-versus-target confusion observed here. This is an instruction repair with a concrete motivating mistake, not an experimentally demonstrated increase in research quality. No runtime code, source evidence or scientific status was changed by this review.

Original author packet, correction and source pins remain unchanged. No GPU/backend import, online fetch, full-pipeline probability test or latency claim.
