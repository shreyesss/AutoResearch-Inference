# Round58 — first-draft-layer broadcast specialization

**Decision: retain a parked component, zero new hypotheses and no status changes.** This is a concrete missing specialization in pinned source, but it has neither native numerical validation nor evidence of material exposed decode time. No GPU/native/model code was executed. No deployment, canonical state, cloud or Git changes.

## 1. Adaptive discovery and prior comparison

One dated arXiv query (2026-08-01 inclusive through 2026-10-23 exclusive) returned eight papers. Query expansion, all hits, provider revisions and command receipts are retained. The question was intermediate tensor traffic/producer-consumer work, deliberately allowing compiler papers. Seven papers were screened at abstract depth; FuTransformer was read at fulltext sections 2.2 and 3.2.1–3.2.3, with its accuracy and hardware scope checked. One fulltext cache miss and two GitHub metadata/diff requests occurred; no model calls. Query breadth produced SQL/NPU/compiler studies as well as relevant GPU work; these are explicitly classified, not supporting votes.

Full compact prior inventory is retained in two pages (143 records); standalone reports were searched for first-layer mHC/broadcast/summed projection. No exact draft-entry specialization card was found. This does **not** make it a qualified new idea. PJ01 removes dead context-projection columns; MF19 changes mHC→MoE output representation; OP36 changes the attention output-projection handoff; EG01 changes Engram staging; WP38 changes expert-weight packets. None is this first draft-layer coefficient input. Existing mHC tuning/overlap and round29 must remain controls, not be counted again as new contributions.

[FuTransformer §3.2.2](https://arxiv.org/html/2610.23796v1) folds a fixed RMSNorm gain into preprocessed weights, with normalization scaling moved to an epilogue. Its separate producer-side quantization uses delayed scaling. We selectively reuse the engineering question—can a fixed/broadcast operand be absorbed before inference?—not its quantization, Llama/Hopper performance, quality tradeoff or exact algorithm. The draft broadcast opportunity was resolved from target code; the paper does not demonstrate it.

## 2. Exact reachable operation

Baseline: planned Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170, callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883, TP1/DP4/EP4 B200, native DSpark5, temp1/top_p1. This is retained configuration, not a new live attestation.

[Draft forward](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/nvidia/dspark.py) line224 materializes `inputs_embeds.unsqueeze(-2).repeat(1, self.hc_mult, 1)`, then starts its three decoder layers with residual/pre-mix unset. The first decoder receives a 3D residual. At H5120/hc4 its first attention coefficient matrix has 24 outputs over K20480. Later draft layers are not identical-input broadcast cases.

[Target decoder and finalizer](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/models/deepseek_v41/nvidia/model.py) already implement a 2D entry branch: finalize_mhc_broadcast_weights sums the four FP32 weight blocks into a 24×5120 derived matrix; the first decoder uses that matrix with the unexpanded embedding. It still materializes a contiguous four-stream residual for subsequent operations. Draft classes do not expose this finalizer or a post-load hook; the generic loader only invokes the top-level post-load method if present. Passing 2D input alone would therefore reach an assertion, not an enabled optimization.

Native DSpark `_generate_draft` calls the model once on its padded query rows. Its default predicted-anchor policy uses five rows/request, with another supported policy using 1+k. Do not multiply a per-forward saving by five separate backbone calls. Actual padded T and selected graph mode must be recorded.

The possible narrow adaptation is: retain original draft FP32 parameters, derive the first layer's summed matrix after final loading, refresh it on replacement/reload, pass a 2D first-layer input and reuse the existing delayed-mHC branch. This is not a runtime patch in this round.

## 3. Why stronger fusion is not a drop-in

`mhc_pre_broadcast_tilelang` at tilelang.py685 already writes a residual output alongside normalization, but its four outputs are residual/post/comb/layer_input. The current delayed path needs post/comb/layer_input/**next_pre_mix**. Replacing one call with the old helper would lose the carried pre-mix contract. A combined residual-write/delayed-pre-mix kernel would need a deliberate adapter and correctness tests; it cannot be presented as an already-supported knob.

[SGLang #41704](https://github.com/sgl-project/sglang/pull/41704), inspected at head0bbebaccf3c24902d717fea6032e8d9662d9606c, merged, contains a separate one-load/multiple-store Triton broadcast replacing repeat. All three file patches are retained. It still writes every residual copy. Its final diff does **not** contain the opening body's advertised strided first-sublayer norm change; do not count that as inspected code. Its Engram text-only `where` removal changes literal image-token behavior and is outside this component. No donor speedup is transferred.

## 4. Numerical and lifecycle gates

Real arithmetic permits summing weight blocks before multiplying identical input streams. Floating point does not generally preserve this reassociation. `source_contract.py` gives a BF16-representable input/FP32-weight scalar counterexample: sequential unfolded sum1 versus pre-summed2. It does not reproduce native TF32 reduction, prove actual trained weights fail, or establish service divergence. It blocks an unsupported universal bitwise claim. The RMS coefficient denominator changes from input_size20480 to5120 alongside repeated versus unique sum-of-squares; their real means agree, but native reduction and split choices require differential validation. The ordinary BF16 collapsed input, nonlinear coefficient/Sinkhorn outputs and subsequent draft confidence/proposal probabilities all remain relevant.

Original frozen weights can remain unchanged while a derived sum is built, but derived arithmetic still changes. Temp1 lossless speculative sampling requires the verifier to use the actual new proposal distribution; this does not by itself promise identical random streams, acceptance or output sequence to the original draft.

[PR60009 opening record](https://github.com/vllm-project/vllm/pull/60009) explicitly leaves weight-derived `hc_attn_fn_broadcast` copies outside its sleep/reload buffer fix because layerwise reload can leave registered copies stale. This is retained author-reported counterevidence, not a fresh diff audit. Do not blindly register a buffer and claim lifecycle safety. Bind a derived copy to its actual source parameter/load generation; rebuild after updates and preserve graph storage only with a proven reload contract. No reload/sleep workload is assumed active here.

## 5. Work bound, not latency prediction

Conditional per actual draft row:

| Quantity | Value |
|---|---:|
| Coefficient MACs before | 491,520 |
| Coefficient MACs after | 122,880 |
| MACs removed | 368,640 (75% of this one coefficient projection) |
| Full/summed coefficient storage | 1,966,080 / 491,520 bytes |
| Four-stream BF16 residual still required | 40,960 bytes |

These are shape counts, not HBM bytes measured or timing. The derived copy adds residency if original weights are retained. Narrowing K does not remove the coefficient launch; the ordinary 2D branch still constructs the residual. Existing FULL-graph small-row overlap may hide some cost, and capture can remove repeated host allocation overhead. Actual kernel choice, splits and occupancy can change. No 75% draft, round or ITL claim follows.

If exposed baseline time for this operation is E and measured replacement plus new overhead is E', the available round reduction is E−E' when positive; E is currently unknown. Even eliminating it cannot save more than its exposed contribution. Nominal weights are small compared with the rest of the draft, so this is lower priority than source-supported PJ01 dead-column work and the major expert path. A separate broadcast-write fusion could remove one launch only if compiled integration establishes that; no such claim is made now.

## 6. Fastest falsifier and future evaluation

Completed no-GPU checks: exact AST finds the repeated entry and absent draft finalizer; source maps current 2D/3D branches and stale helper contract; scalar reassociation counterexample; full prior inventory and PR diff inspection. These establish a scoped investigation, not decoder correctness.

Next useful no-GPU evidence would be an existing source-pinned loaded backend/shape/profile receipt showing this first-draft coefficient operation materially exposed. Trace-applicability5351 found no suitable exact-target trace in its bounded local search; don't fabricate one. Without such evidence, park.

If later GPU work is separately authorized, compare (A) current draft, (B) summed first-layer coefficient path with unchanged residual handling, (C) optional residual-write fusion with the delayed pre-mix ABI repaired. Test eager/FULL graph, padded rows, empty rank, variable request count, reload/replacement, coefficient values, next_pre_mix, draft logits/confidence and actual probabilities. Preserve target model and sampler contract. Use the existing agent-p75 and Mooncake service workloads for final TTFT/ITL/tail/goodput comparison; no new service workload is justified. Add a narrow internal component trace only to establish exposure and numerical boundaries those black-box workloads cannot diagnose. No invented SLA threshold, independent timing samples or promotion decision.

Reopen only with that exposure evidence and a bounded numerical/lifecycle adapter plan. A known implementation omission is not automatically a high-value experiment.
