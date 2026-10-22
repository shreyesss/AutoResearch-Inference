# Independent round106 source review — frozen source packet

## Verdict

No blocker to retaining the author’s scoped zero-new source screen and conditional C106-3 component. No measured improvement or implementation readiness follows from the reviewed papers/donor. The selective bulk-reduction component is worth preserving as a conditional numerical/ABI experiment; arithmetic counterexamples refute a claimed bitwise drop-in, not permissible tolerance-controlled research or actual service quality.

## Decisive source distinctions

- Native scaled-FP8 dispatch at H=5120 selects a5120-byte pull under the8192-byte heuristic limit; its dispatch kNumChunks is1. Extra within-row chunk pipeline depth therefore has no steady-state chunk sequence to overlap at this exact geometry. This does not prove no inter-token or cross-role overlap is possible.
- Combine has a DIFFERENT chunk expression. H5120 exceeds32×128, forcing2 chunks, regardless of the other shared-memory condition. Each chunk contains2560 BF16 elements/5120bytes. It already reserves two load stages plus one store stage and prefetches the next selected contribution while accumulating the current one.
- Current combine reads BF16 expert outputs; shared slot is processed first, then routed slots in top-k order; float2 accumulators start atzero and final conversion to BF16 occurs after the ordered sum. Local and peer readiness/ring reuse are part of the contract. TMARED writes into an accumulated destination are not the same interface as independent slot writes followed by ordered reduction.
- FI2529 exact head4ce7581ac37e2a873c39dbaa7824d81f7c0c2dae replaces a vectorized atomic scatter-finalizer path with SMEM staging and cp.reduce.async bulk operations. It is not the native MegaMoE comparator. BF16 destination addition changes intermediate rounding; FP32 destination addition still needs an admitted accumulation order or an explicit tolerance policy. Preserving BF16 inputs and ordered FP32 updates might restore the arithmetic structure but adds destination staging/initialization, ordering and synchronization work that must be counted.
- Donor GB200 table point estimates are neutral at1/2/4/8 tokens and0.990× at16, with roughly1.024–1.038× at larger listed shapes. No variability or transfer proof is supplied. These numbers neither establish our small-batch benefit nor prove universal regression. They are counterevidence against assuming a generic primitive-level win.

## Counterexample scope

The author finite scalar controls use legal BF16 partial values: [256,1,-256] distinguishes round-after-each-add from FP32 sum/finalBF16; [2^24,1,-2^24] distinguishes FP32 orders. They are formula witnesses, not executed TMA instructions, actual model activation distributions, quality frequency or timing. No further random trials would close that exposure gap.

## Admission and next useful evidence

No generic NCCL swap is demonstrated for the native fused MegaMoE EP route/TP1 planned target. A standalone collective paper may inspire a component without supplying its ring, destination-zeroing, ordering, lifetime and arithmetic contract. A later arm should explicitly choose either preserve-current-arithmetic or a tolerance-controlled target arithmetic change, and compare complete operation cost plus service objective/quality under the actual source/config/workload. Current exposed combine/dispatch time remains unmeasured. Revisit only with an identified compatible operation and actual bottleneck evidence; do not spend another fixture count as improvement evidence.

This review is bounded to retained source/fulltext sections, donor finalizer and exact target dispatch/combine. No GPU/backend import, native execution, source modification or canonical mutation.

## Final frozen-packet alignment

Reviewed author manifest `c5f0969f6a308349a90f64e464da2aa96046d9b4d6fc3228679ab483a0d4e983`: all57 files,26 exported revision fingerprints and9 exact source quotations pass. Three reused target code files match earlier pinned copies byte-for-byte. Ten decisive source anchors are retained in checks.json. No author file was changed.

The final report incorporates the separate dispatch/combine chunk formulas, existing overlap, arithmetic-admission alternatives and small-shape point-estimate limits. T-CCL fulltext lines1193–1202 explicitly qualifies TP4 overlap with below-sequential minimum speedups; RailWave's retained quotation excludes grouping/prepacking/reconstruction from communication timing. These are donor-specific limits, not target measurements.

Source locations: target heuristic223–228 (pull size); target kernel540–614 (dispatch),1381–1415 (combine resources/chunks),1460–1514 (order/prefetch/float accumulation/final cast); donor finalizer1967–2062 (conversion/atomic versus bulk reduction) and utils314–347 (BF16/FP32 bulk-add instructions). Exact files and hashes are in the frozen author source manifest.

Reviewer’s first schema check assumed raw SQL revision envelopes and failed on the decoded export shape. That script/failure is preserved; the corrected checker accepts the actual decoded document form and still verifies every content fingerprint and quoted body. This was a review-tool assumption, not a source or scientific failure.

Recommendation remains exposure/adapter-gated, not a service experiment selection. The smallest useful next step is a concrete destination-format/initialization/completion design with all new passes counted. Generic extra scalar trials or a blanket bitwise-equivalence rule would not resolve that question.
