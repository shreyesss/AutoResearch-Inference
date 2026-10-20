# C25 isolated sampler: prospective component contract

Independent evaluator designer, before candidate implementation and GPU output.
This contract releases bounded **component implementation and qualification**
after the source eligibility receipt is verified. It does not release a service
attempt or claim that unit fixtures cover full-model integration.

## Frozen eligible baseline and intervention

The attested installed service has no engine watermark configuration, despite
the request watermarking flag; the source chain leaves `draft_watermarker=None`.
The proposal therefore does not disable an active watermarker. Retain this
conditional eligibility guard explicitly. Target-only fallback or enabled
watermarking is not an eligible branch. Keep TP1, full vocabulary, AV off, no
draft top-k and no specialized SM100 executor.

Installed DSpark forms five sequential samples. Its Markov embedding and head
are BF16 checkpoint tensors of shape `[129280,256]`; the head is unquantized,
replicated, with BF16 output, scale 1 and no soft cap. The installed baseline
computes `base_logits[:,i] + bias` in BF16, then the original `gumbel_sample`
with request seed, `sample_pos - 1`, drafting salt, temperature and configured
Gumbel precision. **The installed sampler has no draft-step seed mixing.** The
step selects a cache column, not a different seed. An upstream import or call
to `spec_step_seed` is incompatible and must be removed in this port, with that
compatibility change documented. Cache contents are the pre-temperature logits.

The scoped candidate is only the unsharded upstream fused sampling/lookup/glue
path with the unchanged bias GEMM. A generic accessor may retrieve the existing
embedding table under the exact guards above. No new tensor math, vocabulary
mapping, confidence, rejection method, RNG, bias GEMM or graph execution mode.
Root verifies the developer's installed-source manifest and source chain;
nominal upstream source alone is insufficient.

## Ownership, artifact and resource envelope

The developer writes candidate code under `developer/` only. The evaluator
builder writes baseline wrapper, fixtures, comparison and timing code under
`tooling/` only; expected values never call the candidate. Root launches the
isolated pinned container, one physical GPU 0, no network, no package installs.
The new run mounts read-only as `/work`, resolved checkpoint read-only as
`/model`, and a unique writable evidence directory as `/out`. Exact command,
all input hashes, image/CUDA/torch/Triton versions, GPU UUID and allocation
start/end belong in the runtime receipt.

The first component allocation is capped at **45 minutes and 0.75 visible-GPU
hours**, including weight access, compilation, fixtures, timing and cleanup.
Record exclusive whole-node opportunity time separately. One execution
allocation is released after independent code review, with no automatic repeat
after a correctness failure or timeout. Preserve all partial output. A diagnosed
repair is a new reviewed revision and allocation, never overwrite/retry in
place. No service process or full model load is needed for this component.

## Independent reference and exact correctness gates

Load only `mtp.2.markov_head.embed.weight` and
`mtp.2.markov_head.head.weight` from the pinned shard, retaining header, tensor
shape/dtype and tensor-byte hashes. Weights must be actual finite checkpoint
values, not integer substitutes. Use fixed seed 20261020 for synthetic base
logits and fixture construction. These are real-weight component tests with
synthetic controlled activations, **not a real model-activation replay**.

The independent reference runs ordinary embedding lookup, the existing
unquantized BF16 bias projection, BF16 addition, and the unchanged installed
`gumbel_sample` for every one of five steps, then writes the output column. Its
expected next embedding is independently indexed from the sampled token. If
reusing the full logits processor is impractical, the builder must demonstrate
from the installed source that its ordinary PyTorch linear call has the exact
same dtype, operation and scaling; this may not replace it with a different
precision GEMM. Both arms retain that same GEMM. Compare the installed baseline
against itself first with identical component inputs; an unexpected baseline
mismatch makes that fixture inconclusive, not permission for a loose tolerance.

Require **exact token IDs, exact BF16 cache values, exact valid next embeddings
and preserved untouched sentinels**, plus counters reset to zero after every
completed call. No generic allclose tolerance or observed-match-rate threshold.
For deliberately nonfinite stress cases, compare NaN masks and all finite values
exactly; report these separately from finite service-like inputs. There is no
permission to relax finite-case equality after seeing candidate output.

Mandatory fixture groups:

1. Full-vocabulary five-step sequences with batch sizes 1, 5, 16, 32 and 64,
   both FP32 and FP64 Gumbel reduction modes. Temperature 1 is the frozen
   service configuration; include temperature 0, 0.7 and 1.3 as correctness
   stress. For batches above one, mix temperatures across state indices.
   At batch one, use all four temperatures as separate cases. Anchor IDs cover
   first/last vocabulary rows, block boundaries and fixed random rows.
2. Dense identity state mapping, a nonidentity/permuted state mapping and mixed
   valid/negative padded mappings. Positions cover 1, 128, 8192 and consecutive
   five-step positions; request seeds cover 0, 1, a value above 2^32 and a
   negative signed value. Verify cache writes use state rows while draft tokens
   use active request rows. Untouched state rows/columns and padding must retain
   sentinels. At zero active rows the wrapper must no-op or use its declared
   baseline fallback; no invalid zero-grid candidate launch.
3. Independently constructed temperature-zero logits exercise all-equal scores,
   first-maximum ties within/across 1024-token blocks, last valid token and the
   final partial vocabulary block. Set base/bias pairs around BF16 rounding
   boundaries so an unrounded FP32 fused sum produces a detectably different
   cached value. Include a NaN in early and late blocks as a separately labeled
   comparator-semantic stress, without crediting it as normal workload evidence.
4. Same captured five-step component graph replayed 128 times with unchanged
   inputs, then 32 replays with in-place changes to anchors, seeds, positions,
   state mapping and base logits before each replay. Compare to the independent
   reference after each changed-input replay. Exercise shape sequence
   `64,1,32,5,64` with persistent scratch where supported, so request reuse and
   stale partial data cannot pass only on a first clean invocation. Scratch
   allocation/counter initialization belong outside capture; legitimate
   per-call costs remain inside the measured component. No concurrent use of
   one scratch object on multiple streams is supported unless separately
   specified and tested; the current service path is ordered.

The evaluator must demonstrate these intentionally wrong controls fail the
relevant check: changed seed on draft steps above zero, wrong cache state row,
missing BF16 rounding before caching, and a nonzero stale arrival counter. To
avoid a deliberate stalled device kernel, the stale-counter negative control
may be rejected by an independent prelaunch invariant check; it must not be
silently zeroed by the assertion. A corrupt sampled output or cache value must
also fail comparison. Negative controls are isolated from timing and normal
candidate results, and their rejection must be recorded.

Failure of any finite required correctness, sentinel, reset or baseline
repeatability check stops timing. Retain mismatch location and minimal inputs;
do not proceed because a larger sample has a low error rate. These fixtures
qualify the component's exact sampled/cache ownership under their inputs. They
do not certify end-to-end EOS, cancellation, recovery, KV/request ownership or
model quality; those remain required integration gates before service timing.

## Component timing, conditional on all correctness gates

Measure the **entire five-step sequential sampler component**, including anchor
lookup, five unchanged bias GEMMs, additions/sampling/cache/output/embedding
glue and any candidate-required initialization. Base logits are identical,
precomputed inputs in both arms, because the unchanged backbone/base projection
is outside this intervention. Capture this component in CUDA graphs for both
arms. This matches graph execution mode locally, but is not yet the full model
FULL graph or its exact allocator/occupancy context; report that limitation.
Do not compare eager baseline against graph candidate.

Use the actual baseline Gumbel precision and temperature 1 for primary timing.
Report each batch size 1, 5, 16, 32 and 64 separately; do not invent traffic
weights. Warm each captured arm for 20 replays. For each shape collect exactly
30 paired blocks, alternating AB and BA order; each arm block is 100 replays
bracketed by same-stream CUDA events. Synchronize only after the block; do not
profile with CUPTI during these measurements. Preserve every block duration and
order, device clock/power context when available, and any failure. No discard
of slow blocks, best-of-repeat or optional early stopping.

The analysis unit is the paired block. Report absolute microseconds saved per
five-step call and percent gain, with 10,000 whole-pair bootstrap resamples,
seed 20261020 and linearly interpolated 95% percentile bounds, using the mean
paired percent gain and separately the mean paired absolute saving. These
single-session intervals describe local timing variability, not generalization
across service runs or devices.

Call component savings **qualified for further integration design** only when
the lower 95% gain bound is positive at batch sizes 5, 16 and 32 and no observed
mean regression exceeds 3% at batch 1 or 64, with correctness intact. Mixed or
imprecise results are reported by shape and remain inconclusive for the broad
seq64 proposal; no selective favorable weighting. This criterion does not
constitute the service promotion threshold.

Before expensive integration, the next design must establish native eligible
call/shape frequencies and whether those saved intervals are exposed in the
actual FULL graph/service. Compute an explicit optimistic primary-latency
opportunity bound from measured absolute savings and actual invocation counts;
if even that bound cannot reach the frozen 2% useful-service threshold, defer
this candidate for the current budget. A favorable optimistic bound alone is
not expected benefit. Integration must preserve RNG/cache and pass independent
EOS/cancel/recovery and rejection-path fixtures before an unprofiled screen.
No full service attempt is consumed or released by this component contract.
