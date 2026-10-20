# C25 component candidate, revision 1

Derived from the retained complete PR61869 unsharded fused sampler. The precise
patch and source/candidate hashes are alongside this file. The independent
[evaluator contract](../../evaluator/C25_COMPONENT_CONTRACT.md) was frozen before
implementation. No serving files are patched and no GPU execution was performed
by the developer.

`fused_sampler.py` exposes `DSparkFusedMarkovSampler`. The evaluator builder owns
the complete five-step wrapper, independent reference, fixtures and timing.
The candidate performs anchor embedding, then each `sample_step` receives the
unchanged BF16 bias GEMM result. It uses the actual installed
`gumbel_noised_argmax`; unlike upstream it does not mix the step into the seed.
Per-request cache state indexing is distinct from active request output indexing.
Counter allocation and zero initialization occur in the constructor. Every
completed sampling call resets each active counter. Zero active rows return
without a kernel launch. Reuse is restricted to ordered calls on one stream.
The next embedding is updated for steps0–3; the final step preserves step4's
input embedding because no subsequent bias GEMM consumes another embedding.

`adapter.py` is a proposed generic service eligibility boundary. It returns the
existing embedding table only for TP1, k5, AV off, no draft watermarker, no draft
topk or vocabulary mapping, ordinary BF16 embedding and matching unquantized
BF16 bias table, BF16 full-vocabulary cache and unscaled BF16 logits processing.
It returns None for fallback. It is not injected into the service or used to
compute evaluator expectations. It needs additional integration qualification
before use in a full model graph.

Static syntax checks passed. SM90 compilation, exact correctness, counter reuse
and materiality remain pending independent GPU evaluation; successful parsing
is not a kernel or performance test.
