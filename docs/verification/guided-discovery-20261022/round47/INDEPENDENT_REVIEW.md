# Independent review: AT01 geometric block certificate refinement

**Retain the selective full-radius component as an existing AT01 option, deferred.** Rejecting an attenuated/probabilistic score as an exact certificate is warranted; rejecting every component of the papers would not be. No new hypothesis identity or performance qualification is justified by this round.

## Mathematical scope

For every stored key in a block, Cauchy–Schwarz bounds its per-head dot product by `q·c ± ||q||r` when the center/radius actually enclose those keys. ReLU preserves order. Multiplication by a negative learned head weight reverses the inequality, so using its lower ReLU endpoint in the aggregate upper bound is necessary. Summing those per-head bounds is conservative even when their extrema are not simultaneously achievable; that looseness is a potential cost, not an exactness problem. The author formula handles the sign correctly.

The two scalar counterexamples show that the **quoted policy expressions**, used alone as exact maximum bounds, can exclude an actual winner. They do not disprove paper-level empirical quality or the paper's complete rescue procedure. The 500 finite float64 trials are consistency checks, not a theorem for floating-point native execution, target key distributions or useful pruning. No more synthetic trials are needed for that distinction.

A BF16-rounded centroid plus a radius around the original unrounded centroid is not automatically safe. Radius must enclose the actual dequantized stored key vectors around the stored center, or explicitly add center-quantization error. Native query/scale values, learned weights, tensor-core accumulation and BF16 logit output need an outward error envelope. Do not reintroduce a different reference score by using high-precision source projections. Equality at the threshold cannot be discarded under exact tie identity. Nonfinite or uncertain bounds require fallback.

## Native applicability

Pinned attention source makes the sparse-logits path conditional on the runtime flag, candidate buffers, a nonproducer layer and MXFP4 keys. It maintains separate key caches; sharing candidate indices or schedules is not a proof of shared key values. Keys are projected, normalized, rotary-transformed and quantized, with nonboundary compressor rows skipped. Summaries must follow exactly that ownership and update boundary, including request slot reuse, tail updates and current-forward writes.

The original candidate producer also computes block candidates. A token Top512 certificate is insufficient to omit that producer's other output. Restricting the initial design to candidate consumers correctly avoids this unsolved coupling. Even there, the bound and seed threshold must refer to the current visible candidate domain; the existing metadata expansion/reuse should remain intact. A 64-key enclosing block may contain extra invisible keys without making the bound unsafe, but that can eliminate useful rejection. Those extra keys must never become actual selected outputs.

One can use any 512 valid exact scores to establish a lower bound on the eventual kth score; it need not first evaluate the entire domain. Seed selection/read cost and repeated per-query 32-head bound evaluations still count. If the domain has fewer than 512 eligible keys, it offers no Top512 exclusion opportunity. Summary initialization and maintenance are real additional work, and sparse candidate filtering can already make the remaining domain too small for this stage to win.

## Decision-changing next evidence

A compatible retained trace of actual stored quantized Q/K, scales, signed weights and visibility is the useful next CPU input. It could falsify materiality through low safe rejection or high seed/maintenance cost; it would still not establish device latency. No such trace was retrieved here, and the report does not claim an exhaustive archive absence. Keep this refinement parked until that evidence or a later authorized capture exists.

The PR screens have appropriately limited read depth. Opening-body evidence that a fusion leaves paged scheduling unchanged is enough to withhold a direct decode claim, but not a complete independent kernel audit. Existing sparse schedule reuse forbids multiplying hypothetical metadata savings per layer. LiteTopK's approximate tie/score tolerance is not an exact token-identity guarantee; an exact adaptation remains possible in principle. No PDL percentage transfers from a different donor baseline.

This review read the report, mathematical probe, pertinent paper expressions and pinned indexer producer/consumer code; it did not execute kernels, inspect an author implementation, verify empirical pruning, or rerun the 500 author scalar cases. No canonical mutation.
