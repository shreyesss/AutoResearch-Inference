# Round 80 — Reusing a quality diagnostic without importing a weight-allocation objective

## Decision

Retain a **diagnostic refinement of EC79-01**, the optional FP8 expert-return representation. No new hypothesis, weight conversion, gradient collection, native implementation, or GPU experiment was performed. EC79 remains conditional and deferred; the earlier finite cancellation example still proves that the proposed representation is not lossless.

The recent NatScale paper, *Beyond Expert Rankings: Contrast Calibration for Mixed-Precision MoE Quantization*, provides a useful way to distinguish native event exposure, local output error, and downstream quality. Its complete allocation objective does not transfer to this transport-only intervention. This follow-up narrows the future experiment instead of importing the paper's training or weight-format machinery.

## Sources and retrieval

The source is arXiv **2610.20353v1**, retrieved as `fulltext:2610.20353v1`, https://arxiv.org/html/2610.20353v1. The exact fulltext and normalized source record are retained. We read sections 3.1–3.4, the fidelity/task comparison and contrast ablation, Limitations, and Appendix B. Fulltext availability does not mean every table, appendix, repository, or proof was independently reproduced.

The paper was already one of round79's 20 search results, where it was explicitly left for follow-up. A fresh readonly retained-source lookup found its metadata, selected import preserved the prior query lineage, and one bounded `investigate` obtained its fulltext with one logical HTTP cache miss. This round made **zero new provider search queries**, read one selected fulltext, and imported one already-retained pinned code document. Citation repository links were not treated as authored implementation or fetched. No retrieval failure occurred; the initial local lookup's broad output-error query was bounded to five of 65 matches and was not an exhaustive prior search.

The target boundary is unchanged: callgideon/vllm c455786 with DeepGEMM a7a927, planned Flash1017 TP1/DP4/EP4. The paper evaluates weight encodings including Flash-0731, which is not target revision evidence. Round79's full target/donor compatibility review remains required.

## What transfers, and what does not

| Component | Disposition for EC79 | Reason |
|---|---|---|
| Native output residuals and explicit routed-event exposure | Retain as a diagnostic design principle | Measure the perturbation actually introduced, and distinguish replay counts from deployment exposure. |
| Joint gate/up/down weight replay | Adapt only the interface-level idea | EC79 changes the already-BF16-rounded return partial, not those weights or their expert computation. |
| Gradient sensitivity plus calibrated contrast | Not adopted | No target gradients exist; this adds model passes and a proxy whose calibration is not an admission tolerance. |
| Weight-spectrum prior and bit-precision decay | Reject direct transfer | Its unchanged-weight branch can zero the score despite nonzero return-codec error. |
| LP weight-byte allocation and its gap guarantee | Reject direct transfer | It bounds optimization of a fixed empirical proxy under stored-weight bytes, not communication latency or task degradation. |
| Native-output KL/top1 alongside task metrics | Retain the distinction | The paper itself reports different metric/task rankings; none is an automatic substitute for the others. |

### A concrete direct-transfer failure

Equations 7–8 define `d_i = w_i * A_i * E_i`. Each projection's structural factor includes an indicator that is zero when it retains the paper's native MXFP4 encoding. Blindly carrying this unchanged-weight branch into EC79 makes every projection indicator zero, hence `A_i = 0` and `d_i = 0`, even if the transport residual `E_i` is nonzero. This is an algebraic mismatch of objectives, not a bug in the paper's weight-allocation task and not an impossibility result for adapted calibration. Omitting or redesigning that factor would be a new, explicitly justified diagnostic; it would not inherit NatScale's complete objective guarantee.

The existing round79 finite BF16 cancellation example is retained here as **reused evidence**, not rerun or counted as a new test. It changes a combined coordinate from 1/128 to zero after the proposed transport conversion. That suffices to show why a zero weight-change score cannot certify transport fidelity. It says nothing about actual target prevalence or task loss.

Appendix B supplies a first-order interpretation only on a differentiable real-valued graph with locally unchanged routing. Its derivative requires matched native events; the implementation's separate replay events can differ near routing boundaries. Pooling, contrast calibration, and the structural prior remain empirical choices. Consequently neither a good local RMS score nor the LP gap certifies finite perturbations through later routing and generation.

## Minimal refinement of the future EC79 evaluation

1. **Use the real codec boundary.** On held-out native request events, retain the already-weighted BF16 expert return partial before compression, its decoded candidate, layer/expert/request identity, valid event count, and actual local/remote destination. Exclude padding and invalid expert slots. Native a7a applies routing weights upstream in the L1 activation epilogue; multiplying return residuals by the same routing weight again would change the diagnostic.
2. **Measure both local and combined errors.** Report per-partial residuals, but also replay the existing shared-first then routed-top-k FP32 accumulation and final BF16 rounding on the complete set of partials for a token. Separate shared/local slots, which still incur codec error but provide no remote-link byte saving. Preserve the current accumulation order; cancellation makes isolated expert RMS insufficient to describe combined output error.
3. **Keep counts explicit.** Native event frequency and replay sample count are different quantities. Report per-event error distributions and counts before any exposure-weighted aggregate; do not apply frequency twice. A sampling scheme must explain how it represents native events. No six-fold mixture or one-nat setting is copied as a target requirement.
4. **Separate attribution from quality.** Fixed-prefix/fixed-route replay identifies local error. Paired full-vocabulary next-token distribution comparisons and top-token agreement on common prefixes assess downstream fidelity, while actual autoregressive outputs and the existing applicable code/math task checks assess generation behavior. Later routing may change. These tests need numerical/task-derived acceptance criteria set before promotion; no arbitrary tolerance is imported from donor kernel tests or NatScale.
5. **Keep benefit evaluation unchanged.** Existing Mooncake and agent75 load/latency measurements remain the serving benefit test. Quality probes are needed here specifically because EC79 changes target activations. They are not new requirements for unrelated exact transformations. Use actual remote slots and allocation costs for communication accounting; no paper storage ratio becomes an ITL forecast.

This is an experiment-design refinement, not a new per-expert mixed-format policy. Per-expert adaptive transport would additionally alter EC79's static JIT, symmetric allocation, format-key and readiness contracts and requires separate justification. No such feature is proposed here.

## Yield, rubric, and next decision

One existing intervention refined; zero new formal hypotheses; one full objective rejected as a direct transfer; one set of diagnostic components retained. The source adds useful **quality-evaluation specificity**, not stronger evidence of speedup or actual target codec tolerance. Target perturbation/remote exposure remains unmeasured, and execution remains unauthorized under the user's GPU prohibition.

The next informative artifact, if later authorized, is a matched native BF16-partial trace with complete token combine membership and downstream outputs. It must preserve request-disjoint held-out coverage and native-versus-replay event denominators. Without that artifact, another sensitivity exponent sweep or synthetic error sweep would not improve EC79's ranking. No model, native code, device, compiler, serving, canonical state, cloud, or Git operation was run in this round.
