# Round49 review update

[Independent review](INDEPENDENT_REVIEW.md) is complete. The component remains deferred; no new hypothesis identity or implementation promotion.

Two concrete source gates sharpen the adapter design:

1. The base head can pad to64 rows. Its selected logical output must be cropped to exactly K before the K-entry mapping; the unchanged full-vocabulary processor does not do this automatically.
2. Global `draft_vocab_size` or shared logits-processor changes would also affect Markov output shape/columns. Preserve full Markov dimensions and use separate width handling for the selected base head.

The original greedy identity mapping is another unsupported-mode boundary; probabilistic scatter support alone does not implement greedy selected-token mapping. Fixed support, capture/reload lifetime, actual q and full target recovery still need native validation.

The frozen author's rejection-sampler locator should use `callgideon/vllm`, not `vllm-project/vllm`, for revision c455. Audited source bytes are unchanged. The review records the correction additively.

Missing target head exposure and representative held-out token coverage still block a numerical ROI estimate. No additional synthetic probability test was run.
