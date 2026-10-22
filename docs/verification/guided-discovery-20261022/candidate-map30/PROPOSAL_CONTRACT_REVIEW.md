# Independent candidate-map review

**Disposition: useful navigation; one qualification clarification recommended.** This is a bounded source/wording review, not a new selection, runtime validation or evidence-based speed ranking. Author map is unchanged and exact reviewed bytes are copied alongside this note.

## PJ01: preserve the distinction between draft and target arithmetic

The map correctly says a smaller context GEMM can change tactic/rounding and that nominal MAC savings do not supply ITL. Comparing its KV output through normalization/cache is a useful diagnostic of where numerical differences enter. That comparison must not become a universal requirement for bit-identical draft KV, logits or sampled tokens.

At c455, native draft context processing computes fused Q|KV, selects the KV columns, normalizes, then writes the draft layer cache (`nvidia/dspark.py:164–196`). Changed width can change this draft computation. In the probabilistic path, `_sample_sequential` forms base-plus-parent-Markov logits and passes the resulting logits to `_sample_logits`; that sampler passes the actual values to the q-logit cache (`gpu/spec_decode/dspark/speculator.py:116–191`). The gumbel kernel explicitly caches pre-temperature source logits and applies the same temperature path for sampling (`gpu/sample/gumbel.py:242–277`). Thus an altered draft distribution is not inherently a target-output-law error: it can remain valid when the actual conditional proposal law used to draw each token is represented correctly in every acceptance/residual consumer and request/step/cache lifetime, while the target and correct verifier remain unchanged.

This is a conditional correctness argument, not proof that a proposed adapter or this engine satisfies all numerical/stochastic contracts. Preserve the target-facing contract, proposal/cache consistency, support and effective sampling-mode gates. If exact draft equality was an experiment's intended isolation control, a mismatch means that control failed; it need not invalidate the entire implementation. Different draft numerics can also change confidence/AV budgets, acceptance, generated output lengths and performance; measure them rather than assuming an execution-only comparison. For greedy target decoding, differential target-output equality remains relevant; stochastic losslessness does not require identical same-seed finite outputs after a proposal change.

Suggested PJ01 objection wording:

> Confirm the actual prepared layout/backend and compare the smaller GEMM through KV norm/cache. Treat any draft numerical difference as a proposal/AV-consistency diagnostic, not automatic rejection: preserve the target-facing decoding contract and ensure sampling plus every verifier consumer use the actual proposal. Changed width/tactic and changed accepted progress both require measurement; MAC reduction is not saved ITL.

This relaxation does not apply indiscriminately to EC79: its return codec changes target expert arithmetic. Merely caching a new draft q cannot repair a changed target distribution. EC79 retains its explicit target numerical/task admission contract.

## Other map checks

- The scoped headings explicitly disclaim expected-speed ranking; they do not introduce accepted statuses or supersede immutable historical baselines. The candidate set is selective, not a claim that every prior direction was rejected.
- AV68 remains a conditional same-step copy elision, and the map asks for effective AV activation rather than silently changing baseline policy. HM65's cross-step invalidation/lifetime burden remains distinct; neither comparison implies larger gain.
- ER73/EM75 same-kernel interaction and PJ01/shared-quant/CF59/sampling interactions are correctly nonadditive. CF59 still needs the actual legal overlap window, early-release preservation and scratch admission; a source split alone is not a measured window.
- CR64 cache priority is not guaranteed residency. A consumer sequence with intervening weights is an appropriate future comparison; NORMAL and LAST must each be judged against FIRST, with inconclusive data not relabeled equivalence.
- Round78 wording “retained a rejected-feature component” is ambiguous. More precise: it retained a potentially reusable feature component while rejecting direct native transfer without a tree/cache adapter. This avoids suggesting that an otherwise useful component was itself disproved.
- Future round82 remains explicitly an unreviewed lead. This review does not assess its merits.

No code, card, status or source report was changed. No backend import, GPU, numeric tensor test or online query was performed. Source quotation/call-path inspection supports the clarification; it does not close any candidate's implementation or service gate.
