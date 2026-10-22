# QH45 review and typed workflow update

The original round45 report remains frozen at its pre-review state. [Independent review](INDEPENDENT_REVIEW.md) now supports retaining the candidate as **deferred**, with a concrete DSpark integration gap and no implementation/service qualification.

Two clarifications constrain the proposed first arm:

- Existing FP8 helper is PTPC **W8A8**, including dynamic activation quantization; it is not a weight-only treatment. NVFP4 is separately W4A16.
- Its batch-invariant fallback can reconstruct the full BF16 weight each call. Kernel selection/mode must be attested before assuming FP8 execution or a reduced traffic model.

The existing confidence head may also become miscalibrated as proposal probabilities change. Rebuilding latency profiles does not recalibrate acceptance. Keep its weights fixed and measure prediction, acceptance and budget behavior in a later authorized experiment.

The actual production tools ran in the isolated research state: five source-grounded claims → QH45 proposal → ROI screen → CPU diagnostic plan → deferred decision. [Receipt](typed-flow-summary.json): `advance_diagnostic`, null target gain, plan structurally `ready_for_review`, decision `deferred`, zero GPU calls. The plan explicitly labels its scalar/source probe as an already-executed diagnostic replay, not native verification or fresh economic evidence. Next useful work is retained backend/memory/head-exposure evidence, not more toy probability cases.

Hypothesis ID: `hypothesis:4d38f92df2b2ade451a5487906d4354f000aab08cd0afbddd8aec508015be82e`. Canonical import and S3 coverage are **not claimed** here. Typed-workflow independent review is still in progress.
