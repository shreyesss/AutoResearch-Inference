# Independent numerical and dispatch review: mHC → MegaMoE inputs

The useful subset of vLLM #57977 is direct production of FP8 activation/scales
alongside the existing BF16 routing input. It does not remove the router, routing
staging, or every BF16 write. This is a source-level candidate, not a measured
benefit for the planned TP1/DP4/EP4 layout.

## Numerical boundary

The pinned DeepGEMM epilogue explicitly rounds normalized values to BF16 before
FP8 conversion. That is necessary to compare against `prepare_megamoe`, whose
input is already BF16. Fusing directly from an unrounded FP32 accumulator would
change the numerical algorithm. Retaining BF16 here also preserves the router's
input representation; it does not itself prove identical upstream reductions.

`scale_contract.py` independently transcribes two formula pairs from the pinned
sources. It compares all **32,640 nonnegative finite BF16 bit patterns** as group
amax values: the Triton clamp/divide/exponent-ceiling expression and the
DeepGEMM integer-exponent expression agree in this CPU model. The respective
shared-expert scale-row addressing formulas agree for **28,672 pairs** spanning
seven block sizes and cross-page rows. Exact source hashes are in the receipt.

These checks resolve an obvious formula mismatch concern. They do not execute
Triton, PTX packing, CUDA conversion, normalization reductions or a distributed
consumer. NaN/infinity propagation, actual division lowering, BF16 subnormal
handling, and FP8 byte equivalence remain outside this check. Powers of two
make scaling favorable, but the source comment saying "exact" is not a device
differential test. Actual scale layout must use the consumer's selected BLOCK_M.

## Dispatch counterevidence

Independent reading of pinned `model.py:506` confirms overlap is retained for
eligible FULL graphs with 1–16 captured query-token rows. The donor's overlap
branch returns `fp8_out=None` before entering MegaMHC. Therefore these shapes do
not receive this direct-activation benefit. The source support predicate does
not require TP4; TP1 alone does not eliminate the overlap path.

Do not estimate savings for those rows, disable overlap to manufacture exposure,
or use batch-size labels as substitutes for actual captured row counts. A
six-query speculative bundle, padding, graph bucket choice and ubatching can
change which arm is used. Initially scope the candidate to shapes that already
execute MegaMHC, retaining all existing dispatch choices.

## Cheapest next evidence and decision

From existing CPU-readable launch/capture artifacts, establish the proportions
of frames using MegaMHC versus overlap/TileLang, together with layer eligibility,
graph shape and shared-scale block configuration. Unknown exposure stays
unknown. Source-driven geometry may bound bytes or removed launches, but does
not supply a latency forecast. Keep a one-pass version that writes BF16 router
input plus FP8 payload/scales; preserve symmetric-buffer ownership, graph-stable
addresses and lane separation until consumers finish.

Disposition: **deferred, bounded source/CPU investigation justified**. The
formula checks are positive compatibility evidence; the overlap branch is
material counterevidence to a small-concurrency decode benefit. Neither grants
implementation or service qualification. No GPU action was performed.
