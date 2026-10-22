# Round79 — selectively compress expert-output return, not dispatch

**Outcome: one distinct deferred research proposal, EC79-01, plus a rejected direct RAC predictor port. No implementation qualification, typed hypothesis creation, performance forecast or GPU execution.** The useful component is optional FP8 combine transport from DeepGEMM #382, separated from that donor's broader W4A4 changes. This is explicitly a lossy arithmetic change; frozen weights and FP32 accumulation do not make it lossless.

Baseline remains planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, TP1/DP4/EP4 on B200, baseline d464. These are source-plan facts, not an attested live image. No precision or quality waiver is inferred.

## 1. Source question and adaptive retrieval

Recalled all 147 compact records in two pages with a stable inventory hash; selected communication-related records for closer comparison. Paginated retained report searches covered combine/quantization, expert output and communication/FP8. Exact phrase searches for FP8 combine and DeepGEMM 382 found no report matches. This is bounded literal/manual prior coverage, not semantic novelty certification. Prior MF19 concerns input staging; WP38/RD01 concern weights; M01 concerns GEMM tactics; round52 concerns readiness and communication scheduling. None of the inspected cards establishes reduced-precision expert-output return. Existing low-rank/whole-model compression and backend-switch ideas do not silently authorize this arithmetic change.

The starting source fact was concrete: `MegaMoEBuffer` allocates BF16 combine rows even with FP8 activations. The current L2 epilogue rounds expert partials to BF16 and writes each selected slot to the source rank. The source rank later reads those partials and accumulates in FP32. The return representation therefore differs from the already quantized dispatch path.

Two actual dated searches tested nearby terminology:

1. OpenAlex, August 1–October 22: `mixture experts inference communication quantization combine`, ten records. Most concern weight offload, edge systems or unrelated feature codecs. RAC added residual/reference compression terminology and a clear cost/quality warning.
2. arXiv, June 1–October 22: explicit MoE/mixture-of-experts AND combine/all-to-all AND quantization/compression/aggregation, ten records. The exact query and date filter were retained without hidden relaxation. Generic combine/compression terms still matched image codecs and pruning; these are recorded negatives, not useful return-path evidence.

The loop then switched to local PR triangulation. Four full-corpus searches returned 339, 8, 11 and 4 matches for combine/FP8, combine/compression, hierarchical/combine and expert/low-rank respectively; only six opening records per query were materialized. A two-record selected import and actual `pr-search` replay covered DeepGEMM #382 and older DeepEP #161. The latter is only a short opening-record precedent here. DeepGEMM #382 initially had an empty body, so its title was not accepted as code evidence. Normal `investigate` hydrated all 14 file patches, and a second invocation retrieved six exact-head source files. No broad repository refresh occurred.

## 2. Recent paper component: RAC's codec discipline, not its whole deployment

[RAC: Reference-Aware Activation Compression for Communication-Efficient Split LLM Inference, 2608.04991](https://arxiv.org/html/2608.04991), August 2026, was read in the design, calibration and cost sections. It reconstructs transmitted activations at the sender so subsequent references agree with the receiver, counts packed values/scales/alignment/outlier metadata, and calibrates quality alongside cost. Those are useful component-level evaluation principles for a communication representation.

Its direct decode mechanism needs boundary-specific one-layer Transformer predictors trained on preceding reconstructed activations. The model split has stable local/cloud boundaries; routed expert identity and location can change per token in our target. The predictors, reference state, error distribution and edge-network overlap are not present in the pinned MegaMoE path. Direct predictor/residual-codec transplantation is rejected as scoped. Dropping that machinery does not preserve the paper's compression result, but a simpler direct quantizer remains a valid separate component.

RAC also reports high-bandwidth crossover against raw transfer and median/tail regressions at some points. Its Mbit/s local/cloud experiments do not establish benefit on intra-node NVLink. Some reported stage accounting excludes overlapped prediction/lookup work; that is not a zero-cost assumption available here. No paper headline speedup or quality result transfers to this target.

## 3. Exact donor component and target delta

[DeepGEMM #382](https://github.com/deepseek-ai/DeepGEMM/pull/382), exact head `edc5c10c7eae4f2a27cd9aa916ceed914a6f65bb`, is closed with no merged timestamp and draft=true in the fetched metadata. Its implementation provides separate activation-format and combine-format controls. `use_fp4_acts` forbids fused shared experts; `use_fp8_combine` does not. Therefore **FP8 activations plus existing MXFP4 weights plus fused shared experts can retain their original contract while changing the output transport**, subject to a local adapter. Adopting native W4A4 is not required and is excluded from EC79.

The donor adds:

- A separate `combine_dtype`/`kUseFp8Combine` choice in the buffer and dispatch interface.
- E4M3 values with one UE8M0 scale per 128 output columns. The producer first reads the already BF16-rounded partial, takes a 16-lane maximum across eight values per lane, scales and packs FP8, then stores payload and scale.
- A correspondingly sized combine buffer plus scale buffer, and a consumer that decodes E4M3, applies the scale and accumulates in FP32 before final BF16 output.

This is absent in the inspected a7a implementation: its combine buffer is fixed BF16, the epilogue writes BF16 payload, and its reduction loads BF16. The c455 vLLM adapter neither passes a combine format nor includes one in its symmetric-buffer cache key. A source upgrade or explicit component port is required; this is not an existing supported flag on the frozen path.

### Preserve the newer baseline schedule

The donor was built on an earlier scheduler. Current a7a has per-peer combine-ready release/acquire and token-chunk traversal, with the shared slot first followed by routed slots in top-k order. The donor diff retains an earlier barrier/iteration structure. Porting the full donor would change more than representation and could regress current improvements.

Adapt only buffer layout, payload/scale production, decode and static format plumbing. Keep current task scheduling, valid-row guards, ring lifetime, per-peer completion and reduction order. The existing completion signal must cover **both payload and scales**. Retain shape/capacity/graph addresses; add the representation to every buffer/JIT ownership key that distinguishes incompatible layouts. Mixed formats must not alias the same cached buffer. Changing mode invalidates the old layout: existing captured pointers cannot be reused without the appropriate allocation and graph recapture. This is an adapter requirement, not an observed baseline corruption.

The donor's global format also quantizes local routed and shared slots. Those slots do not necessarily cross NVLink, so their added numerical/codec cost cannot be justified by remote-byte savings alone. Inter-rank savings are bounded by actual remote routed slots (at most six), not all seven allocated routed-plus-shared slots. A remote-only variant would require explicit mixed-format bookkeeping and is not already provided by the donor. It is a later declared variant, not a free property of EC79's initial all-slot control.

Target H=5120 is divisible by 128; the checkpoint has six routed selections and one shared expert. These facts do not establish the remote fraction or active branch. Scale handling for zero, subnormal, overflow, NaN/Inf, saturation and signed zero requires explicit native admission tests. The unguarded scale helper must not be generalized to all values merely from ordinary random tests.

## 4. What the donor results do and do not show

The retained donor documentation reports GB300 EP4 measurements at H7168, I3072, with native MXFP4 activations and FP8 combine in **both** compared revisions. Those numbers concern the larger scheduler/rewrite comparison; they do not isolate FP8-combine benefit. Our target has H5120, I2304, FP8 activations, a shared expert and a newer baseline schedule. Static buffer reductions in the donor also mix ring-capacity and activation-format changes; none is credited solely to combine transport.

The inspected reference test is single-rank synthetic data, H2048, top2 and no fused shared expert. It tests different format arms against a float32 reference using a scalar tolerance. Those author tests were not run here. They do not validate EP4 visibility, the actual model, later routing decisions, long-output quality or the frozen service objective.

## 5. Executed cheapest numerical falsifier

`combine_boundary_control.py` is standard-library exact rational arithmetic with an ideal E4M3 nearest-even grid and group128 power-of-two scale. It is not CUDA emulation or model evidence.

One BF16 partial group contains 129/128 followed by ones; another contains minus ones. Both groups select scale 1/256. The first coordinate reconstructs as 1 and -1 after FP8 transport. Baseline FP32 sum then BF16 is 1/128; changed sum is zero. Both final values are exactly BF16 representable. This deliberately selected cancellation example disproves a **lossless transport** claim even though the donor rounds to BF16 first and accumulates in FP32. It does not estimate target error prevalence or demonstrate unacceptable task quality.

For H5120, logical payload is 10,240 BF16 bytes per partial versus 5,120 E4M3 bytes plus 40 scale bytes. This excludes allocation padding, transactions, signaling, local/remote routing, and encoding/decoding. It is not measured network traffic and supplies no ITL speed forecast. No timing, device query, native import or code compilation occurred.

## 6. EC79-01 and decision gates

**Proposal:** selectively adapt optional group128 E4M3/UE8M0 expert-output combine to the existing FP8-activation/MXFP4-weight MegaMoE path, retaining current shared experts, routing, task scheduling and reduction order. Compare unchanged BF16 combine against FP8 combine at a static admitted format. No W4A4 switch, training, intentional routing-policy alteration or expert pruning. The same router weights and algorithm do not guarantee the same later expert selections after changed activations; that is part of the numerical/quality gate.

**Status: deferred research candidate.** There is a source-supported absent component and a plausible cost pathway, but arithmetic changes and unknown exposure prevent implementation/service qualification. If the applicable correctness contract requires exact target-only token equality, the new representation must pass that gate; approximate quality or a small tensor error cannot silently replace it. No tolerance or task-quality waiver is invented.

A future authorized matched investigation should first establish:

1. Actual backend/image/config and reachable graph shapes; same weights, routing policy, activation precision, shared expert, capacity and schedule for both arms.
2. Original-format identity control after the local port, then full payload/scale indexing and visibility across EP ranks, graph replay, partial rows, empty experts and buffer reuse. Preserve the a7a reduction order.
3. Tensor and downstream logits/token/quality comparisons under the existing task contract, including cancellation/outliers and finite/nonfinite admission. FP32 accumulation alone is insufficient. Standard Mooncake/agent-p75 runs measure service objectives but do not by themselves certify a changed numerical target. The smallest added future probe is a paired replay of a fixed held-out set of representative target prompts: record baseline/candidate MoE outputs and downstream logits on common prefixes, then compare actual autoregressive output hashes and any trusted code/math task checks applicable to that set. Common-prefix logit error is a diagnostic, not a substitute for generated-output behavior. If exact output equality is the task contract, require it; otherwise the permitted task-quality budget must be defined from the task before promotion, not copied from the donor tolerance. This additional probe is needed specifically because the intervention changes numerical activations; it does not replace the standard service load evaluation.
4. Only after admission, matched existing workload ITL/TTFT/tails/errors and output counts. Record actual remote slots and exposed epilogue/combine waits alongside quantize/dequantize resource cost. A tensor-level microbenchmark or payload ratio is not a service win.

Nulls are useful: BF16 may win because the link is not the critical path, encode/decode costs exceed transfer savings, only a small fraction is remote, or quality fails. Keep BF16 as the unchanged fallback. No numerical ROI is supplied because the relevant target exposure and error data are absent.

## 7. Yield and stopping rule

Two provider queries, 20 returned records/20 distinct paper identities; one selected recent full text; four bounded PR corpus searches; two selected PR records replayed; one hydrated PR with 14 patches and six exact-head source files. Direct RAC predictor transport was rejected as scoped; FP8 combine is one deferred new author proposal, not multiple candidates for its buffer/scale/consumer components. Zero typed identities, zero implementation/service promotions, zero GPU runs.

The decisive adaptation came from source triangulation: neither accepting the whole donor W4A4 package nor rejecting it for shared-expert incompatibility would have found this separable return component. Search broadness produced irrelevant hits; the next step became exact code, not more synonyms. All receipts and negative dispositions are retained. No new tool patch, canonical write, snapshot publication, S3 sync or Git change is claimed.
