# Independent review of the round87 block posterior derivation

**Verdict: no blocking correction. Retain zero-new evaluator refinement.** Frozen author manifest `e6fb5f9de1682b8284fdedaf682c7039f6690f8221bf0d1e2f49e17383a67de1` verified:19 artifacts and seven exact source-revision quotes. No author files changed.

The conditional reduction is supported under its stated ideal fixed-B assumptions. It does not equate conditioning on the proposed draft prefix with conditioning on the eventual target output.

1. For an output-compatible prefix of length j, proposal joint mass Q_j times the block accepted-prefix probability r_j is beta_j. The clipped forward ratio implies beta_j=min(beta_(j−1)*p_j,Q_j).
2. Sun Lemma3 identifies accepted-prefix survival. Integrating the next proposal token gives boundary probability r_j−sum_v min(r_j*p(v),q(v))=Z_j. Multiplying by Q_j and the residual draw yields beta_j*p(v)−beta_(j+1)(v).
3. The subsequent target suffix factor cancels when conditioning on a complete positive-probability target output. Thus survival a_j=beta_j/P_j and boundary mass a_j−a_(j+1) are correct; the full-block bonus mass is a_B. This agrees with the paper's B.2 future-target factorization.
4. The cap handling in trajectory_posterior correctly absorbs all remaining survival when the next chunk reaches/crosses the fixed horizon. The occupancy recurrence starts a new round after correction or the forced bonus boundary. At a zero-survival state, occupancy is zero and the unused ratio may safely be defined as zero; conditioning on a zero-target-probability output is excluded.

The author code's complete forward enumeration actually visits off-path proposal/target states and integrates the latest passing threshold and correction law. Its trajectory recursion does not call that forward enumeration. The matched fixtures preserve full p/q tables on the selected path, with q indexed by potential anchor, while modifying off-path branches. This is meaningful corroboration of the derivation, not independent proof by a large case count.

The result is more informative than a teacher-forced marginal overlap score. In this ideal fixed-B family it supplies the complete conditional round-count distribution. It still requires normalized q at every relevant possible anchor/depth along the target output. Logs from only the baseline's visited anchors cannot supply those counterfactual inputs. Target-law output samples are additionally needed for unbiased averaging over the target output distribution; arbitrary reference strings describe a different conditional evaluation population.

Native c455 implements logarithmic/clamped ratios, finite arithmetic, indexed random helpers, placeholders and separate AV state. The exact-real proof does not certify those arithmetic/RNG realizations or AV's cross-request policy. EOS/stop processors, near-cap shortening, unobserved drafter state and varying costs need explicit contracts. No law here predicts service ITL from expected rounds alone.

Retain as a zero-new evaluator refinement with a bounded fixed-B adapter as the next potential CPU action. Do not alter the earlier ordinary-versus-block counterexample or claim a serving optimization. No new hypothesis/status transition is warranted from this review.

## Independent check scope

I read the complete finite-enumeration/trajectory/occupancy code, report, native source anchors, and the primary paper's accepted-prefix lemma and future-target suffix factorization. Receipt totals were recomputed. One added reviewer control uses a ternary alphabet with context/anchor-dependent laws, N=3 and B=2; all27 positive conditional output distributions and occupancy means agree exactly. It reuses the reviewed author implementations with new inputs, so is not an independent implementation or a proof by testing. No native/GPU/model execution, new provider calls, canonical writes or source edits occurred.
