# Independent root review: round52 communication

Verdict: retain two deferred components; neither qualifies for implementation or a service-gain forecast. All75 author artifacts match the frozen manifest. This is a selected-source review, not native execution or an independent reproduction of donor benchmarks.

## Duplicate input pulls

Pinned DeepGEMM a7a927 source reads src_token_topk_idx per expert, divides by top-k for src_token_idx, then pulls the activation and scales into that expert pool row. Thus repeated logical pulls are real when multiple local experts choose the same token. This does not measure remote traffic or exposed wait: source-local duplicates and existing hardware caching matter.

I independently read the selected source loop, ring-empty/readiness protocol and the exact FI5374 head TUNING negative result. The donor reports four H200s, two interleaved rounds,26 buckets, dispatch dedup and receiver cache within±0.1% full-layer time. The author correctly treats this as strong counterevidence, not a B200 impossibility proof. Combining routed outputs is excluded because it changes the critical path and accumulation order.

A carrier row in the existing modulo ring cannot be retained for a new reader without a new lifetime/forward-progress protocol. A separate stable cache is an alternative to specify, not a free implementation. The proposed bookkeeping control is necessary but must also preserve the same routing, quantization and tactic choices. Lower byte counts alone are insufficient to qualify this branch.

## Ready-source execution

I read CascadeEP's threshold, AppendixC lane/packing protocol, hardware/method and selected ablation passages. The transferable inference-only mechanism is explicit: source–destination generation signals, system release/acquire, thresholded ready-token grouping, separate scratch and inverse route maps. Opportunistic weight fetching is separable and excluded. The paper's Async+SF arm changes both threshold and multi-stream execution. Future evaluation should either hold stream policy fixed when testing threshold or add a separate multi-stream arm; do not attribute that bundled effect solely to threshold.

Pinned scheduler fetch_expert_recv_count waits for a completion high word equal to numSMs*numRanks; the resulting full counts determine total blocks, task offsets and waves. Deleting only the dispatch barrier is therefore invalid. The proposal must specify stable per-lane offsets/counts, completion for empty ranks, final flush and ring generation before implementation. Source-level existence of a full-count dependency does not establish target attention skew or a service bottleneck.

The donor setup is EP8 B200 disaggregated prefill, different model/runtime and split SGLang/DeepEP kernels. Our planned EP4 fused path is not that setup. TTFT is the plausible target; current primary long-output ITL cannot inherit the paper's reported gains. Retain as a prefill architecture lane, with mixed-serving ITL guards, not a promoted primary-objective hypothesis.

## Other scope and evidence

UBEP's direct512-byte atomic flag/payload argument depends on its CM384 transaction contract. The author correctly rejects only that transplant, not all separately proved NVIDIA synchronization schemes. Payload-sentinel validity needs an invariant over future payloads. Static source inspection and initial weight checks do not establish it.

The four paper texts are unversioned HTML with retained content hashes. The PR is an observed unmerged head/base, not an installed backend. Bounded lexical report recall is useful but not exhaustive semantic deduplication. The reported20 hits/16 identities/four fulltexts and two deferred components are discovery accounting, not two validated improvements. No native execution, GPU call or measured target gain was performed by this review.
