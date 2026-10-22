# Independent round58 review — first draft-entry specialization

**Agree with zero-new parked component.** The inspected draft has a concrete source omission relative to the target's existing first-layer specialization. Missing native numerical/lifecycle and exposed-time evidence prevents an implementation priority or speed claim.

## Reachability and the actual removable work

The native draft explicitly repeat-materializes its input embedding into hc4 streams before entering its three decoder layers with no residual/pre-mix. The first layer takes the3D branch and projects the flattened20480 input into24 coefficient outputs. The target already has a2D first-layer branch using summed FP32 weight blocks and an explicit5120-wide coefficient input. Both branches retain a four-stream BF16 residual. This is one first-layer operation per draft backbone invocation, not all three layers or five separate draft backbone calls. Its work denominator must use actual padded query rows and graph mode.

The draft classes inherit nn.Module and expose neither the target model's finalizer nor a top-level process_weights_after_loading hook. Generic loader processing does not manufacture this derived tensor: it invokes quant-method/attention hooks and then a top-level hook only if supplied. Passing2D input alone would hit the decoder's non-None assertion. A legitimate adapter must initialize after final weights and refresh before any read after replacement; hot reload, sleeping/offload and graph storage stability are separate conditions. Target copy_ behavior only helps if its update path is actually called.

## Numerical and ABI boundaries

The summation is FP32; real-arithmetic distribution over identical embedding streams is sound. Reassociation changes FP32/TF32 reduction order and possibly split configuration. The saved scalar1vs2 example correctly refutes a universal bitwise assertion for its explicitly sequential FP32 order; it is not actual trained-weight, TF32, kernel or decoder evidence. It should not become a blanket veto of an otherwise valid changed draft proposal.

The narrower input changes the squared-sum denominator to5120 in both delayed execution paths; repeated-vector mean square equals the expanded version in real arithmetic. Native reductions and nonlinear coefficient/Sinkhorn outputs still need validation. The collapsed BF16 input and carried next_pre_mix must remain correct. The old standalone broadcast helper returns residual/post/comb/input rather than the current delayed post/comb/input/next-pre contract, so matching tuple length does not make it interchangeable.

For stochastic speculative decoding, an altered draft is not automatically an altered target distribution if the verified lossless sampler uses the actual new proposal consistently. Any adapter must preserve that native contract, Markov/base probability bookkeeping and confidence/scheduling consistency. Do not reuse old proposal probabilities or promise identical seeded output/acceptance. The report correctly leaves native validation open.

## Evidence transfer and priority

FuTransformer's fixed-gain folding is an inspiration for looking for static algebraic structure, not a proof of this mHC rewrite or a transferable Hopper gain. The selected SGLang diff replaces repeat with a one-load/multiple-store copy while retaining all output bytes; it does not supply the advertised first-norm optimization or a native delayed-mHC adapter. PR60009 opening prose is a useful stale-derived-weight warning, with no fresh implementation audit claimed.

The shape-derived75% reduction is only this24-output projection's MAC count. Coefficient weights may be cached; launch, residual writes and downstream work persist; overlap can hide the coefficient work. No75% draft/ITL reduction or additive MF19/PJ01 gain follows. The existing derived copy also adds roughly0.49MB if original weights remain resident. Prior families change different operations, but novelty relative to those cards is not sufficient reason to create a new implementation task.

The next useful input is a compatible existing loaded-backend/padded-shape/component-exposure receipt. Without one, no further synthetic numerical examples or GPU experiments are justified. If later authorized and material, separate summed-coefficient and residual-write-fusion arms and validate delayed ABI, numerical proposal contract, refresh/lifetime and serving guards.

All33 author hashes and seven pinned target source copies match. Source and saved scalar receipt were reviewed, not executed. No GPU/native import, model, new provider call, canonical mutation or hypothesis transition occurred; original packet remains unchanged.
