# Independent round29 review

**Verdict: no blocking factual correction for a deferred MF19 refinement.** Same hypothesis ID and baseline; zero new qualified improvements. The actual small-row overlap producer lacks the proposed packed output, while donor57977 supplies a useful consumer contract. It is a plausible source-level adaptation, not a compiled kernel or demonstrated saving.

## Review performed

Read the frozen report, probe and source contracts, independently checked all18 artifact hashes, and replayed the scalar/integer probe in reviewer-owned copied files. Output exactly matched the retained JSON:2560 differing BF16 values for the first-boundary example; exponent126 versus127 for the final-rounding example;70 shared-layout combinations;160 logical groups. No worker files were rewritten. Independently executed the exact pinned mhc_pre_delayed_overlap AST after removing backend imports and substituting allocation/launch/stream stubs:10 cases cover rows0/1/8/9/16 and supplied-input bypass. That confirms host enqueue branches only, not actual CUDA concurrency/completion.

## Decisive constraints

1. **Two rounding boundaries:** source retains BF16 collapse before RMS and BF16 normalization output before the separate consumer quantizer. The new producer must quantize the final BF16 values, not raw FP32 ol. CPU examples justify refusing shortcuts; they do not certify the compiled FP8 output or establish that target weights produce those adversarial values. The report correctly states this.
2. **Groups versus lanes:** hidden5120 partitions into160 groups32 across five1024-value logical tiles. NVIDIA uses64 collapse threads of a96-thread CTA. Neither divisibility nor the integer group fixture proves that a warp shuffle implements the right32-value group. Lowered compiler layout/resource inspection remains necessary.
3. **Overlap can regress:** rows1–8 execute input epilogue before side-stream dependency release; added quantization delays both input and coefficient work. Rows9–16 queue stats first but still face contention/input delay. The refinement correctly preserves the existing overlap route, rather than disabling it to force the original donor arm.
4. **Readiness/ownership:** supplied layer_input and zero-row branches do not emit new packed outputs. Allocating descriptors is not evidence they are populated. Symmetric storage is shared across compatible layer calls and lacks a layer/ubatch key; all prior-reader completion, all-rank allocation, capture and event ordering requirements remain. No race or safe concurrent-use proof was obtained here.
5. **Layouts and exceptional arithmetic:** routed/shared strides, shared BLOCK_M padded row map, group scale exponent packing and finite/nonfinite conversion semantics must be preserved. Synthetic integer permutation checks cover arithmetic only, not actual target BLOCK_M selection or buffer placement.
6. **ROI:** one BF16 input read (10240 logical bytes/row) is the explicit removed traffic. BF16 producer output/router use, FP8 and scale stores remain; quantization moves rather than vanishes. Donor routing-only staging still launches with one K tile. Cache residency, extra producer work and coefficient delay prohibit a cold-HBM-bandwidth latency estimate. No claim of endpoint improvement is supported yet.

## Retained disposition and next gate

Retain MF19 deferred, with this as an alternative producer arm. Before implementation qualification, require exact epilogue compile/lowering and byte-level differential on BF16 output, FP8 values and both scale layouts, including bypass/padding/repeated-shape cases; then actual ownership/order checks. These future GPU tests are not authorized or run in this review. Existing service workloads can evaluate performance later once the branch is attested; no additional evaluator or inherited numerical SLA threshold is justified by this CPU evidence.

No GPU/device query, model load, build, runtime import, network call, serving patch or canonical write occurred. Source reads plus pure-Python scalar/integer/AST execution are the complete independent verification scope.
