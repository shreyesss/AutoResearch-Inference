# Actual-image applicability audit

CPU/source audit, 2026-10-20 UTC. No GPU execution, model loading, service traffic,
package installation or original-environment modification. Sources were read
from the pinned image with `docker run --rm --network none` without GPU access.
[Manifest](source-manifest.json) records each extracted file and hash;
[collector](collect_cpu_evidence.py) reproduces header and configuration receipts.
The initial collector invocation failed on a local parent-path error; fixing that
path produced the retained receipts. No scientific result was derived from that failure.

## C25: eligible configuration, with an essential RNG compatibility change

The retained [runtime identity](../../av-k5-timing-001/runtime-identity.json)
contains the effective engine argv for both replicas. Neither has a
`--watermark-config`, `--config` file or dtype override. Actual image
`engine/arg_utils.py:709,2120` defaults the engine watermark configuration to
`None` and preserves that value. `spec_decode/speculator.py:193` consequently
leaves `draft_watermarker=None`. The target model runner also selects ordinary
`Sampler` when this configuration is absent (`model_runner.py:467`). This is a
source/configuration inference from an attested prior launch, not a new live
object dump. [Receipt](effective-config-evidence.json).

Thus prior client requests containing `watermarking=True` do **not** establish
that this service instantiated either watermark implementation. The frozen
block-rejection setting is another cross-check: this installed watermark
configuration validator requires standard rejection if a watermark engine is
configured. We must preserve effective baseline configuration and the request
contract. Do not add or remove watermarking while testing fusion. A future engine
watermark configuration must disable this narrow fused adapter or require a
separately qualified watermark-preserving implementation.

The sampled service's `ready-replica-0.log:228` explicitly reports BF16 head dtype.
Both target and draft vocabularies use 129280 tokens; no draft-topk config is
set; AV is explicitly off; TP is one. The checkpoint's Markov tables are
`mtp.2.markov_head.embed.weight` and `mtp.2.markov_head.head.weight`, both BF16
`[129280,256]`, in `model-00046-of-00048.safetensors`. The first becomes
`model.model.markov_head.markov_w1.weight`, an ordinary `nn.Embedding`; the bias
head is replicated and continues through the existing logits processor/GEMM.
The draft cache uses model head dtype, BF16. These metadata facts are retained in
[checkpoint receipt](checkpoint-metadata.json).

**The upstream sampler is not a verbatim drop-in.** It imports `spec_step_seed`
and salts the seed with the draft step. The actual pinned `sample/gumbel.py` has
no such function: it uses request seed, position-minus-one, and the existing draft
position salt; the draft column controls only cache placement. The port must
remove the upstream helper import and call. Copying its RNG behavior would
change the baseline seeded distribution realization. Independent evaluation has
been notified before candidate implementation.

Proposed bounded component intervention: preserve the exact installed
`gumbel_noised_argmax`; retain the bias GEMM; fuse BF16-rounded logits addition,
pre-temperature cache store, reduction, token store and next embedding load.
Use the complete retained 284-line upstream sampler as the implementation base
with the above compatibility delta and a generic direct accessor. The adapter
must require TP1, full vocabulary/identity mapping, ordinary embedding layout,
no draft topk, no draft watermarker, and AV off. Failed eligibility falls back to
the original loop. No specialized SM100 executor or sharded sampler is included.

First qualify against the installed loop on real Markov weights and controlled
base logits, preserving exact tokens, logits cache, next embeddings, invalid-row
masking and repeated graph scratch reuse. This is a component qualification, not
full service correctness or a quality/performance claim. Same-graph component
timing can establish an upper bound on useful savings; service materiality and
an independently frozen integration qualification remain required.

## C26: stop this FP32-weight port for the current baseline

The new header scan covers **all 43 gate tensors**, not only three samples:
40 target gates `[384,5120]` and three draft gates `[128,5120]`; all are BF16.
The actual loaded-path source closes the remaining dtype question without
changing or loading the model:

* `base_loader.py:72` constructs under `set_default_torch_dtype(model_config.dtype)`;
  prior engine log records `dtype=torch.bfloat16`, matching checkpoint config.
* V4.1's MoE constructor (`deepseek_v41/nvidia/model.py:124`) inherits the V4
  constructor. `deepseek_v4/nvidia/model.py:850` constructs `GateLinear` with
  `out_dtype=torch.float32` and no `params_dtype` or `force_fp32_compute` override.
* `linear.py:281` takes the current default dtype; `create_weights:177` allocates
  that dtype. The unquantized replicated loader `linear.py:401` uses
  `param.data.copy_(loaded_weight)`, preserving destination dtype.
* V4.1's generic gate loading branch (`model.py:1295`) calls that loader. CUDA
  unquantized post-load processing has no conversion branch. No gate FP32 cast
  appears in the actual target or draft model paths inspected.
* `gate_linear.py:123` requires **FP32 weight** for BF16x3 eligibility, besides its
  current Blackwell platform gate. BF16-weight/FP32-output follows existing
  low-latency BF16 or cuBLAS paths. The exact specialized FP32 shape table also
  excludes the local 5120-wide shapes.

This is a source/configuration applicability rejection for C26's proposed
FP32-weight mechanism, not a measured router-performance rejection. Do not cast
weights simply to activate the hypothesis. A different BF16 router intervention
would require a new mechanism and its own evidence/materiality gate.
