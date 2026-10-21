# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 1. Requested: 1.

## treespark_transfer_diagnostic_20261022_01

Test whether a load-adaptive tree verification budget improves DeepSeek-V4.1-Flash service cost per accepted token on H200 or B200. First re-attest the Mooncake and agent-75 manifests and serving configuration: fixed DSpark k5 is historical context, and an adaptive controller may already be present. If the live drafter exposes parent-conditioned scores and the verifier can accept packed tree masks, use matched traces to price each candidate budget by exposed drafter, verifier, and sampling time divided by accepted tokens. Compare a load-dependent policy with the strongest feasible static budget chosen on calibration data. Keep hardware decisions separate. A short paired service pilot follows only if the configuration and trace checks show an eligible path and plausible net saving; neither paper’s reported gain predicts local throughput.

**Decision:** accepted

**Reasons:** Passed structural and critic gates; engineering review remains

**Cheap test:** A locally priced per-round tree or verification-budget policy conditioned on load, only after compatibility and trace gates pass.

**Reject if:** The feature is already active with equivalent behavior, required score or verifier interfaces are absent, replay cannot beat the static comparator after all costs, or a sufficiently precise paired pilot favors the control.
