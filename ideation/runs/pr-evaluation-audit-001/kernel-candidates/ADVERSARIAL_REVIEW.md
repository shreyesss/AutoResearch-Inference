# Final experiment-card adversarial review

Reviewed the root PROTOCOL.md, SPECS builder and E01/E06/E08/E09/E10/E18/G02/G03 against the frozen primary source bodies. No broad retrieval or root-file edits performed.

## Required corrections sent to the parent

1. **E10: storage mode is a gate, not an assumed baseline.** Record resolved `dp_shared_memory`, `use_thp`, `embedding_across_dp` and CPU offload. #59923 operates on DP-sharded tables (`dp_shared_memory=false`); #62359 changes the backing of DP-shared tables. They cannot be treated as additive changes on one unchanged branch. Add explicit separate #59327 and #59923 arms, or describe them as inclusion checks only. #59849 requires the relevant pinned-table allocation path; a shared-table baseline may bypass it.
2. **E06: #59922 needs its own arm and dependency gate.** It is not implemented by #60802's auto-dispatch change. It depends on vLLM #59921 and the **vllm-project/DeepGEMM** fork PRs #24/#25. Require BF16 top512, page128, H32/D128 and verification lengths1–6. Preserve the current default comparator and short-context n6 negative control; source reports a default/new ratio0.775 for one such case.
3. **E09: distinguish prefill and decode precision eligibility.** FlashMLA #227's prefill leg uses BF16 KV; its decode leg uses all-FP8 KV. Both are B200148SM/H64/QNorm-off specializations, with measured TopK640. Mixed-FP4 decode stays on fallback. Restricting all arms to FP8 KV would discard the prefill leg, while assuming all MegaAttention decode calls engage would overstate coverage.
4. **E01: BF16 logits may already be the dependency default.** #61149's newer SM100 DeepGEMM API returns BF16 logits and removes `logits_dtype`. A separate precision arm exists only on a compatible older API with a separable change. Keep length-aware selection as the principal isolated treatment; do not claim removal of a conversion already absent.

## Reviewed and retained

- G02 correctly makes #62467 conditional on reachable shape/backend; the current primary description does not establish a shipped-default DeepSeek trigger.
- G03 correctly separates DeepGEMM #478 mHC epochs from #451 MegaMoE readiness and requires exact vendored-header inspection plus changed-input graph replay.
- E08 correctly separates #57977 activation propagation from #61971 position-cast reuse. Retain the cards' TP4 source-versus-TP1 target qualification and numerical/quality checks.
- E18 correctly treats #61149/#61371 as dependency baselines, not free wins. Preserve the explicit #61371 KV-capacity cost and FlashInfer #5523 route-level admission/integration requirement.
- Shared protocol correctly retains the native synthetic cache workload and Mooncake replay/scorer, labels price assumptions, resamples paired runs rather than requests, and distinguishes applicability failure from performance invalidation.

No GPU experiment, deployment, code change or test-plan registration was performed during this review.
