# Independent round54 review

## Verdict

No blocking correction. Retain FI6360 as a parked, conditional tuning/evaluation component: zero new hypothesis and zero implementation qualification. The report distinguishes source capability from deployment exposure and avoids transferring author B300/GB300 numbers to the planned B200 service.

## Evidence inspected

Verified all 38 frozen author file hashes/lengths and all nine target copies byte-for-byte against callgideon/vllm c4557869393db4d75c483d92edd02a5125500883. Donor source is zcnrex/flashinfer 96f9b9947c19ce6ceb864c4a4fa9ee532ad3f8a8, PR6360 open/unmerged. Read the dispatch/wrapper/admission paths, model call sites, warmup/cache coordination, donor BF16 configuration, profiler and cache-policy code. Reviewed retained prior inventory/matches and the actual proposed three controls. No new online retrieval was required for this independent review.

Replayed the exact extracted dispatch function in a reviewer-owned copy using inert platform/availability/callee stubs. All five cases reproduce the author's JSON exactly. This verifies only conditional Python dispatch, not per-call tensor admission, GPU availability, compilation, numerical equivalence, loaded settings or speed. No torch/model/native/backend imports occurred. Author artifacts were not modified.

## Source conclusions

- CUDA linear_backend=auto misses the explicit FlashInfer mapping and selects F.linear. The only exposed FlashInfer BF16 choice here is flashinfer_cutedsl. Default source behavior is not live backend attestation.
- Eligible unquantized indexer weights_proj and owner wk are concrete reachability candidates. Auxiliary-stream placement of weights_proj may hide any local saving. The compressor's direct torch.mm and quantized DSpark/context projections cannot be included merely because their inputs are BF16.
- Donor chain8 flushes before the captured graph sample, not between its eight launches. Oversized weight arenas can reuse the original input; do not interpret every chain as eight independent cold-cache calls. The policy intentionally changes the profiling workload.
- Legacy user-loaded configs check policy during tuning. Serving without re-tuning is not a guarantee that historical cache entries are retroactively invalidated. The report's warmup/re-ranking/reload requirements therefore matter.
- The explicit cute-dsl family uses a cuBLASLt fallback above M=32. That fallback explicitly ignores PDL; recording the wrapper's PDL flag alone does not establish actual dependency-launch behavior. This is an additional interpretation caveat, not a report blocker.
- Existing warmup already aligns buckets with DSpark capacity and coordinates rank cache behavior. The donor is not evidence that these mechanisms are absent.

## Prior overlap, controls and numerical gates

M01/DA01 is histogram-conditioned MegaMoE tactic selection. It shares the need for representative tactic evaluation but changes a different operation/decision signal. PJ01/OP36/EG01 quantized projection paths do not establish BF16 exposure. Keeping this as an evaluator/control component rather than manufacturing another implementation card is appropriate; related prior work is not a blanket rejection of the donor.

A→B activates an explicit backend. B→C must retain the same dependency, available kernel candidates, buckets and chosen shape workload, changing only profiling policy. Otherwise B→C is confounded by dependency/kernel changes. Exact target dtype/strides/alignment/bias, batch-invariant mode, eligible owner layers, fallback decisions, cache provenance and rank coordination remain prerequisites.

A different tactic can change reduction ordering/rounding. Donor tolerance tests and frozen weights do not certify target greedy equality or a stochastic sampling contract. Future authorized numerical, output, failure and tail checks are required. Existing agent75/Mooncake can measure service effects; additional module/tactic/cache instrumentation is diagnostic coverage, not grounds for replacing the workloads. f*r is only a conditional upper-bound decomposition when f is exposed eligible time; neither f nor a B200 target r has been measured here.

## Next distinct search direction

Investigate **byte-exact, page-local indexer cache layout and scale/payload coalescing**, before another tactic-ranking variant. There is a concrete source question: attention.py101–109 declares MXFP4 68-byte and FP8 132-byte indexer records; sparse_attn_indexer.py348–367 exposes the MXFP4 page using explicit 68-byte logical strides to DeepGEMM. Does the actual writer/reader schedule introduce avoidable scale/payload transactions that an ABI-compatible page layout or reader staging can remove while preserving every stored bit?

This is a question, not a missing-component claim or performance hypothesis yet. Start with exact producer and native reader address maps, page padding and the first useful consumer. Dense adjacent-row scans may already coalesce efficiently; a non-power-of-two record alone proves no waste. Compute actual lane/sector ownership from source before searching papers. If there is no avoidable transaction or the reader already rearranges scales optimally, stop. If a concrete gap survives, search recent primary work on GPU quantized-cache AoS/SoA layouts and scale-factor data movement, retaining only exact inference components.

Compare against AT03 cross-layer dequantized gather reuse, physical-index fusion, MP17 reuse and LC lossless representation screens. This direction changes neither precision nor selected key support and does not require training; it still needs both writer/reader and cache-spec compatibility, plus graph/alias lifetime review. No novelty, exposure, bandwidth or ITL gain is asserted. This source-first question is distinct from the current BF16 tuning policy; it is proposed because the packed cache ABI is explicit while its transaction efficiency remains unestablished.
