# Independent review: attention reduction, round30

Disposition: retain two narrow rejected transfers and one deferred fixed-reference reduction lead. No new accepted hypothesis or performance qualification.

All 65 frozen artifact hashes and sizes pass. Copied standard-library contracts.py into the reviewer directory; its output exactly matches the retained author result. Frozen originals were not modified.

## Source audit

At pinned target FlashMLA core.cuh lines 981–997, SO_full is published after P storage and required old-O rescaling. issue_sv (1069–1083) consumes both. One-CTA decode (1087–1136) already polls QK readiness independently of SO_full, subject to buffer reuse and issue-distance constraints. Donor FlashInfer #5602 head cb273439cf2de29a2546d53eb3053eb7083192a9 waits on both p_full and o_ready before PV (3916–3917). Copying the split readiness flags alone therefore establishes no earlier legal SV issue. The two-CTA/prefill branch remains fixed-interleaved; a different buffer/lookahead redesign is not rejected by this audit.

The synthetic early-SV example correctly exposes scaling the new contribution along with old O as wrong (1.25 versus 3.5). However the 27 dependency-model cases assign identical old/new equations: they illustrate the source-derived premise, and are not independent evidence that the real scheduler is equivalent. Do not count them as 27 target tests.

## Fixed-reference reduction

A common finite score shift cancels in exact normalized attention when the sink is included. The 100 float64 cases check that arithmetic identity, not BF16/FP8 numerics. Dropping the sink changes a constructed output from 0.5 to 1. A sample can miss a large score: the constructed 150-logit outlier overflows f32, but is not an observed target activation or a measurement of donor failure frequency.

Target already has slack-six rescaling and omits first-block O rescaling. Typical selected work here is 512 compressed keys plus 128 sliding-window keys; raw context length is not the reduction length. The author estimator samples 192 slots, so overhead and safety cannot be dismissed. Final query magnitude is not bounded by the earlier latent RMS normalization alone.

Whole-donor SM90/int8-cache transfer is unsupported for the pinned target. The reduction-only idea remains low-priority deferred pending a usable safe reference/fallback and a demonstrated removable cost. No hardware execution, live configuration attestation, numerical kernel certificate, or service forecast was performed.
