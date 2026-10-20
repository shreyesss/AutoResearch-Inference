# C25 candidate: independent source scope review

Reviewed before GPU compilation or correctness outputs. The candidate is a
component port, not mounted into a serving container. Source inspection accepts
its scope for the independent component tests; it does not certify execution.

Candidate `developer/candidate/fused_sampler.py` at SHA256
`7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9`
differs from retained upstream sampler SHA256
`56b7b1fe27eef271e83d76b90689ed8084204c160541100ff47327112cd4252f`
only by removal of incompatible draft-step seed mixing, documentation of the
installed RNG identity, and no-op guards for zero active rows. It retains the
installed `gumbel_noised_argmax`, BF16 sum rounding before cache/sample use,
valid state-row cache masking, request-row draft output, 1024-token block
partitioning, and GPU arrival-counter reduction/reset. The source imports no
SM100 specialized decoder or new dependency.

The separate proposed accessor is guarded by TP1/k5/AV-off, no draft watermark,
no top-k/reduced-vocabulary path, BF16 ordinary embedding/head/cache and matching
vocabulary/processor semantics. It is not integrated or certified as a serving
fallback by this component review. An integration patch will need its own
source diff and exercise of every fallback branch.

The important unresolved risks remain exact NaN/tie behavior, real-weight
round-sensitive results, mask/state ownership, FP64 precision, visibility of
partial writes across arrival-counter updates and scratch reuse across graph
replays. The contract's independent fixtures and negative controls specifically
target those risks. No source argument alone waives those tests. The last step
does not update the next-step embedding; the expected fixture must compare
embeddings only where a following step exists, rather than invent a final
embedding requirement absent from the candidate/installed consumer.

GPU release remains pending the evaluator builder's separate baseline/fixture/
timing harness review and root's one-device identity/resource receipt.
