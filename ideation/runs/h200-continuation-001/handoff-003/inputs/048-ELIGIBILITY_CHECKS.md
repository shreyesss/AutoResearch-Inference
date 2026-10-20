# Cheap applicability checks before implementation

These are source and CPU checks, not serving experiments. They were completed
after the first generation packet was frozen; the follow-up packet preserves
that timing rather than rewriting the original evidence.

## C24: a concrete cost-model question

The installed controller already charges draft time. The unresolved issue is
whether `draft_cost_ms[len(req_ids)]` correctly prices changes in the downstream
draft graph when the verification budget changes. The existing C24 source audit
gives a five-request counterfactual with target rows 36→16 and draft rows 35→80.
Neither row count is a latency estimate.

[The CPU probe](scripts/av_cost_probe.py) extracts the actual installed
`get_num_tokens` method without importing vLLM, Torch or CUDA. An independent
enumeration of all 6^5 prefix allocations agrees with the method at budget 11
under constant draft cost. With **invented** costs indexed by target graph bucket,
the exhaustive optimum becomes 3. [The receipt](av-cost-counterexample.json)
records the source hash, fixtures and scope.

This establishes a possible decision error under the assumed dependency. It
does not establish its frequency, real costs, a correct distributed controller
or an H200 gain. The next useful intervention is an offline joint-rank dispatch
reconstruction and a specific repair to the failed timing measurement design.
C24 remains instrumentation-inconclusive; its prior GPU hold remains intact.

## Router port: evidence against baseline eligibility

[Checkpoint headers](router-checkpoint-metadata.json) contain 43 matching gate
keys. The three sampled tensors—target layers 6 and 14 and draft MTP layer 0—are
stored as BF16, with shapes 384×5120, 384×5120 and 128×5120. Reading these headers
loaded no tensors and ran no GPU work. Stored dtype alone does not establish
the eventual loaded dtype.

The retained nominal
[GateLinear source](sources/pinned-vllm/vllm/model_executor/layers/fused_moe/router/gate_linear.py)
requires FP32 weights for the BF16x3 branch. FP32 output does not satisfy that
condition. Its BF16-weight/FP32-output branch already uses a different cuBLAS
path. The nominal DeepSeek constructor does not itself request FP32 weights.
These facts weaken the case for PR61903 on this baseline. Hold the port unless
an actual installed loader/cast and dispatch trace demonstrates FP32 weights
and an absent equivalent optimization. Do not convert weights merely to create
eligibility. Nominal sources remain distinct from attested installed files.

## Sampler fusion: watermark gate is still unresolved

The installed speculator constructs `draft_watermarker` through
`create_speculative_draft_watermarker`. The fetched pinned implementation has
SHA-256 `c2f7807bfbcea658c838c1fc39e35f734f258003880c98b644c4c2dd81ae90c5`,
matching the installed-file hash recorded in the earlier
[source review](../c03-execution-001/A-baseline-repeatability-source-review.md).
It constructs a draft watermarker for algorithms supporting speculative
decoding; the target-only fallback returns `None` only when allowed for an
otherwise unsupported algorithm. Thus the request-level `watermark=true` flag
does not establish whether the proposed fusion's `draft_watermarker is None`
gate holds.

The frozen profile and retained request logs did not resolve that constructor's
effective algorithm/configuration. No running local container was available
for an object inspection; no service was started. Preserve the unknown and
perform an exact configuration/source audit before porting. An active draft
watermarker would stop the scoped unwatermarked port. Disabling it would change
the experiment contract.

The complete upstream patch is retained locally; the model's earlier evidence
excerpt omitted parts of the sampler launcher/reduction. That is a packet-depth
limitation, not an unavailable download. The follow-up extracts and reviews the
complete [284-line new-file section](sources/proposed-fused-sampler.py), with a
[patch/extraction receipt](sources/proposed-fused-sampler-manifest.json). It uses
per-request partial maxima, an acquire/release arrival counter, last-arriver
reduction and counter reset; the launcher checks add/cache dtype compatibility
and supplies Gumbel precision and next-position behavior. These are testable
invariants, not proof of correct ordering or SM90 compilation. Real-weight
parity and graph/scratch qualification remain prerequisites. The upstream whole-PR specialized executor and
vocabulary sharding are outside the proposed narrow H200 intervention.
