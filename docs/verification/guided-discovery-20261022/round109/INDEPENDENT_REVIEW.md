# Independent review: static SWA precision allocation

## Verdict

**Retain as a distinct deferred, quality-gated hypothesis.** The intervention is source-grounded and absent at the inspected target boundary. Unknown exposed gain does not warrant rejecting it; neither does an intentional change to target activations automatically violate the research task. It is a larger codec/reader/specification extension than the narrow operation-elision candidates, with meaningful quality and integration uncertainty. This review creates no typed record or status transition and authorizes no GPU work.

The title should continue to identify **target SWA representation**, not a generic switch enabling the already-present compressed NVFP4 format. No novelty claim is supported over the known mixed-precision/all-pool cache family. The retained153-card inventory contains no exact selected-layer SWA policy intervention; EC79, QH45, CR64, AT03 and round83 act on different boundaries or reuse existing representations.

## Source chain and actual reuse

Pinned `attention.py:515–532` assigns SWA528 independently of compressed288; the native comment makes that distinction explicit. The fused writer documents512 FP8 bytes plus16 UE8M0 scales and quantizes RoPE dimensions too. A new SWA encoder must consume the same pre-quantization latent/RoPE boundary, not merely reinterpret the existing FP8 bytes or substitute the compressor's pre-RoPE path. It must preserve the query work, slot semantics and the declared new representation's scale/rounding contract.

The Mega caller (`flash_mla_mega_attn.py:326–365`) passes SWA as original and compressed KV as extra. At FlashMLA API379 the originalFP4 format is explicitly rejected; the instantiated mixed specialization is originalV41/extraV41_FP4. Deleting that guard is insufficient. The reader's scale addressing at kernel209 selects offsets by `F::IS_FP4`, and descriptor setup and scale staging retain original/extra assumptions. A valid adapter must reconcile roles and formats, pure-SWA/no-extra layers, all-extra or boundary-straddling blocks, both CTA scale paths and the output/sink pipeline. This is a repairable interface gap, not evidence that low precision SWA is inherently invalid.

The prefill gather is a real reusable component: `cache_utils.py:764–823` dispatches by the record width, keeps `gather_lens`, offset and block-table inputs, and sends288B to Triton. The existing SWA caller already supplies a tail length and offset. Reuse still requires matching the new encoder and validating those semantics; the existing FP8 CuteDSL path may be faster. It is inappropriate to discard the whole proposal because no complete native SWA port exists.

## Structural correctness versus target quality

The report correctly separates two contracts: codec/layout/cache correctness relative to the **new declared FP4 representation**, and downstream quality relative to original FP8 execution. The former can have an exact reference; the latter intentionally changes target activations and may change the target distribution. A quality budget is required before promotion, not invented in this review. A proof of speculative losslessness relative to the original target cannot qualify this intervention. Conversely, a changed BF16 output alone is not proof of unacceptable service quality.

Clarification for future typed text: keeping compressed format, indexer policy and drafter weights fixed does **not** keep their contents or outcomes fixed. Changed SWA outputs can propagate into later compressed latent values, indexer queries/selections, MoE routes, draft confidence and proposal distributions. This is a policy-isolation arm, not isolation of all other tensor values. The packet already acknowledges downstream routing and confidence; preserve this explicit meaning when claiming unchanged components.

The shared K/V latent must be calibrated through its complete QK and PV effects. MultiAlloc's separate absolute gradient terms are a surrogate; they cannot be transplanted as an exact tied-latent loss predictor. A shared-graph derivative or a clearly conservative surrogate is an admissible adaptation. No weight updates are needed for the paper's profiling, but its forward/backward still requires model execution and remains outside the current CPU-only task. Forward-only ablation is a different method. Selecting only static layer allocation also omits the paper's token preservation and cannot inherit its joint-method results.

Static policy should be part of the cache-format configuration identity for allocation, prefix reuse/transfer and replay. Draft pages must retain their own format; global cache configuration mutation must not accidentally apply target-layer precision choices to DSpark. Under unchanged policy, standard speculative rejected-token slot handling must still work. Cross-policy KV reuse is not valid merely because token IDs/prefix hashes match. The author already requires cache identity and speculative commits; this states the concrete ownership implication without alleging an existing runtime bug.

## Memory and cost interpretation

I independently recomputed the conditional128SWA+512compressed logical record counts:215,040→184,320B, saving30,720B or1/7. This excludes masks, cache reuse, invalid entries, all other tensors, page padding and kernel work. It does not establish actual HBM transactions, allocated bytes, bandwidth pressure or14.3% service benefit. Pure-SWA has a different denominator; fewer valid SWA slots reduce the mixed fraction. Do not sum this ceiling across layers or add it to CR64/AT02 savings without measuring the shared denominator.

`attention.py:570–581` and the planner/spec sources make physical allocation a separate question: per-layer record widths, aligned pages, shared block stride and grouping must agree with indexer/compressed/draft pages. Window128 does not imply only128 resident records under every replay/prefix policy. The proposed physical-spec plan is a useful next non-GPU falsifier. If padding erases capacity savings, the **capacity rationale** fails for that configuration, while smaller logical reads remain a separate unmeasured traffic hypothesis. Do not conflate the two outcomes.

The retained SGLang37138 opening body's slower all-pool FP4 numbers are relevant counterevidence to automatic speed claims, not reproduced target data or a definitive rejection. Four PR bodies were read; no diff/head implementation audit was claimed. The new FP4 reader still dequantizes for BF16 attention; no FP4 tensor-core throughput benefit follows from storage precision alone.

## Useful next gate and stopping rule

Construct a bounded static-policy physical spec/layout plan for the exact retained model and planned settings, with original baseline policy as a control. Report actual chosen configuration assumptions explicitly; do not call them live attestation. This can decide whether allocation savings survive grouping and identify required original/extra reader specialization. After that source gate, additional integer byte examples cannot resolve quality, calibration stability or service cost.

Future authorized evaluation should keep the original target sampling/AV/stop policy, record actual completed output lengths, confidence/acceptance and route changes, and compare matched physical budgets for calibrated versus transparent fixed subsets. Hold out tasks and rollout data from policy selection. A capacity gain with slower decoding is a valid result, but does not satisfy the primary long-output ITL objective. No numerical degradation tolerance, GPU schedule or performance forecast is approved here.

## Evidence checked

42 author-file hashes,28 exact exported revision fingerprints,11 quoted claims and ten pinned source-copy equalities pass. The153-card inventory is unique and uses a consistent pagination inventory hash. Source hashes/pins are in the verified author manifest; actual review checks are in `checks.json`. Read depth: MultiAlloc sections4.2–4.5 and the report's experimental caveats; target writer/API/reader/gather/spec/caller branches above; retained prior inventory and candidate distinctions. No new online query, target import, model execution, native compilation or timing test. Author manifest: `d721174e18c6740042d60d5f2f5d408ee8ce9a7c3cb1e391a9b4ff2c5f7eb262`.
