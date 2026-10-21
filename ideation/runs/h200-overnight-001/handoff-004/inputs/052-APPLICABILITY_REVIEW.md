# Independent source applicability review

Reviewed before candidate GPU work. This evaluator did not extract or implement
the candidate. Independently checked all **190 retained installed-source file
hashes** against the developer manifest and read the controlling allocation,
loader, dispatch, watermark, sampling and Markov-head source chains. The receipt
uses the actual pinned image, including its differences from nominal upstream.

## C25: source/configuration eligibility passes for a bounded component

The prior actual engine argv has no watermark configuration/config-file override.
Installed EngineArgs defaults the configuration to None and its factory preserves
None; the speculator constructs a draft watermarker only for a non-None engine
configuration. The target runner separately selects ordinary Sampler. Therefore
the frozen configuration implies no draft watermarker, even though client
requests contain a watermark flag. This is a source/configuration inference,
not a new runtime object dump. Preserve both effective configuration and request
fields; a future non-None watermark configuration must fall back to the original
loop unless a separate semantic-preserving implementation is qualified.

Actual DSpark has the full vocabulary, TP1, AV off and no draft top-k. The
Markov embedding is ordinary BF16 `[129280,256]`; its replicated unquantized
head has the same stored shape, BF16 output and default scale/no soft cap. The
original sampler caches pre-temperature BF16 sums and uses request seed,
sample-position-minus-one and the drafting position salt. It does not mix draft
step into the seed. The upstream `spec_step_seed` import/call must therefore be
removed, with an independent changed-seed negative control detecting a mistake.

**Decision:** source eligibility supports the separate bounded component
implementation and evaluation in `C25_COMPONENT_CONTRACT.md` plus its prospective
shape addendum. It does not establish H200 compilation, exact parity, reset/race
safety, actual FULL-model graph equivalence, materiality or service correctness.
All of those gates remain. No full service attempt is released.

## C26: proposed FP32-weight port is inapplicable to the frozen baseline

The new metadata receipt enumerates **43 BF16 gate tensors**: 40 target and
three draft, replacing the earlier three-sample uncertainty. Actual model
loading constructs under the attested BF16 default. V4.1 inherits the V4 gate
constructor, which requests FP32 **output** but neither FP32 parameter dtype nor
forced FP32 compute. LinearBase uses the BF16 default; the unquantized parameter
allocation retains it, and `param.data.copy_(loaded_weight)` does not replace
the destination dtype. The inspected CUDA post-load path has no FP32 conversion.

Actual GateLinear requires FP32 **weights** for both its BF16x3 route and its
specific FP32-kernel route. Local shapes are also absent from the latter's
supported table. Existing BF16-weight/FP32-output paths are separately eligible.
Thus the proposed FP32-weight Hopper port does not apply to the preserved
configuration. No GPU startup is needed to establish this static consequence.

**Decision:** close the current C26 intervention as
`inapplicable_to_frozen_baseline`, with no kernel/GPU/service allocation. This is
not a measured router performance rejection. Reopening requires actual changed
eligibility evidence and a declared scope delta; converting weights solely to
activate the old proposal does not qualify. Another BF16-router optimization
would be a distinct intervention, not a silent continuation of this port.

## Reviewed evidence identities

| Artifact | SHA256 |
| --- | --- |
| `developer/APPLICABILITY.md` | `f852c4b310d4ce8966992bda99bdd1dc6dec94fab5c12e22706d2fc7974dffa2` |
| `developer/source-manifest.json` | `8467be03e18411ead746744e2ccc8a8db829b9e4fc026ceff0e9862f57db1d3b` |
| `developer/checkpoint-metadata.json` | `157c1292db1f60b2cae9c63c50f8e58a52815d4554160ef04e8a9842bd1a9aaa` |
| `developer/effective-config-evidence.json` | `5a19626c7d5ffd6e78a0ada534ca2a4482d0a29ba9b9ea8ad54511b53be93779` |
| Prior actual runtime identity | `c92c46e83878f0be9f7821741ed0ae08f43bcff29e850b4c24b705a584d7835c` |

Header/source inference is explicitly narrower than a new loaded-model runtime
observation. Root must reattest installed source/configuration before any later
service integration. Neither remaining full hypothesis attempt was consumed by
this review.

## Pre-component supplemental source review

The developer subsequently retained one additional installed file,
`source/vllm/model_executor/layers/utils.py`, SHA256
`ae2f43ca8ce60fa7045b20510286cca750c912e348201c8fd66615de0372d938`.
Independently checked its dispatch: `dispatch_unquantized_gemm()` defaults to
`auto`, which reaches `default_unquantized_gemm` on this CUDA path; that function
calls ordinary `torch.nn.functional.linear`. The separate environment-controlled
batch-invariant branch in `UnquantizedEmbeddingMethod.apply` remains explicit
and must be recorded by the component harness. This closes the previously
noted need to prove GEMM dispatch rather than infer it from BF16 labels.

Verified all **191** retained file hashes against updated source-manifest SHA256
`29d5e44696b5da9acebc0c4078aabbbd4fa268381a76cd55b59c35e73bd20478`.
The earlier 190-file review above remains its original snapshot. Applicability
decisions are unchanged; the component contract and independent harness review
still control GPU release.
