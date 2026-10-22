# Checkpoint33 — reject mismatched optimizations, retain useful dependencies

The CPU-only guided discovery loop remains active. Two recent-paper lanes closed
without a new performance hypothesis. They produced a conditional correctness
dependency and a parked nonstreaming component. A separate source audit refined
the observation required for [FV86](round86/REPORT.md). None supplies a measured
serving win or permission to run GPU work.

## 1. Communication observability exposed a correctness dependency

SigmaTrace, `2610.24328v1`, observes NIC UAR interactions. Its reported MoE
communication observations concern a host/NCCL deployment; they do not establish
visibility into our pinned MegaMoE direct peer-memory route. Its traffic skew is
not a throughput improvement, and its instrumentation has measured overhead.

PR triangulation did uncover a concrete missing source operation. DeepGEMM451,
open and unmerged at the retained head, resets the peer readiness tag before the
existing pull barrier. The pinned target does not. Reusing an identifier could
make an old readiness value appear current. The donor reports a changed-input
CUDA-graph failure on B300; our scalar/source inspection has **not reproduced
that failure on the target**. The PTX description of a temporal grid identifier
alone does not settle CUDA-graph identifier reuse.

Retain this as a conditional correctness prerequisite for affected communication
experiments. The future diagnostic needs exact dependency identity, changing
inputs, graph/eager comparison and memory-order/rank coverage. It is not a new
performance card or an excuse to run that diagnostic while GPUs are occupied.

[Source analysis](round88/REPORT.md) · [Independent review](round88/INDEPENDENT_REVIEW.md)

## 2. Host transport: inspect the actual route before porting a PR

ExaServe, `2609.10812v2`, reports a collapse with roughly195k converged SSE
connections across3072 replicas and sharply increased TCP retransmissions.
The measured proxy CPU remained below2%. This supports concentrated network I/O
as the reported problem; it does not identify our local Python serializer as a
bottleneck.

| Selected component | Pinned target and workload | Disposition |
|---|---|---|
| SGLang45097 MessagePack frame copy reduction | Target already reuses encoder buffers, tracks `copy=False` sends, receives multipart frames with `copy=False`, and directly decodes frames | Already present on inspected path; no new proposal |
| SGLang42889 direct Pydantic JSON serialization | Streaming target already calls `model_dump_json`; saved Bitlane benchmark streams. Nonstreaming target retains `JSONResponse(model_dump())` | Preserve selective nonstreaming component; no demonstrated workload exposure |
| Distributed streaming ingress | Paper topology differs substantially from retained one-node serving plan | Conditional topology component, no transferred speedup |
| Buffer more output tokens | Changes client delivery cadence and observed ITL | Not a free optimization; would need explicit latency semantics |

If nonstreaming traffic becomes relevant, the control is the target's existing
explicit `JSONResponse`, not the donor's former FastAPI auto-encoding path.
Preserve response field/default/alias behavior, errors, status, headers and custom
serializers. Source `copy=False` flags also do not prove that physical copying,
allocation or GIL contention is zero.

[Source analysis](round90/REPORT.md) · [Independent review](round90/INDEPENDENT_REVIEW.md)

## 3. Sampler ROI: verify what existing metrics actually count

The pinned stack has detailed per-request accepted/drafted arrays. The drafted
count comes from scheduled draft IDs, with grammar adjustment. Adaptive
verification chooses effective admission separately on the GPU. Therefore the
reported arrays do not generally identify whether every **admitted** token passed.

The same recorded scheduled5/accepted2 can describe admission2 with a complete
pass or admission5 with a partial pass. FV86 avoids a residual row in the former
and none in the latter. The finite witness holds the recorded summaries and
arrays fixed; it is an information-loss example, not an executed AV trajectory.

The independent reviewer also found an optional auxiliary routed-expert path
that internally consumes GPU-derived rejection counts. Its exported artifact
does not establish the required joint admission observation. This is a possible
future collection location, not evidence that suitable data already exists.

Use compatible existing observations first. A future diagnostic may need the
effective admitted/accepted joint count or the proposal's actual terminal flag,
plus branch eligibility and exposed stage cost. Avoid introducing per-request
GPU synchronization merely to measure it. Existing counters may still bound
particular cases under additional assumptions; the result is general
non-identifiability, not a claim that every counter is useless.

[Metric audit](round91/REPORT.md) · [Independent review](round91/INDEPENDENT_REVIEW.md)

## Yield and tool usefulness

| Lane | Actual coverage | Result |
|---|---|---|
|88 memory/communication | Two paper queries,22 hits/21 identities; one new selected fulltext; one selected PR with pinned source | Zero new performance cards; one conditional correctness dependency |
|90 host transport | Two paper queries,22 identities; one new selected fulltext;81 unique PR titles screened, two selected patch sets | Zero new performance cards; already-present paths and parked nonstreaming component |
|91 FV86 exposure | Six pinned files, seven exact quote anchors; existing artifact audits; no network query | One evaluation refinement; FV86 remains deferred |

Counts are per lane and must not be summed as globally distinct sources. Abstract
or title screening is not a full read. Source selection, exact file reads and
independent review changed the dispositions; another broad query would not
resolve these specific exposure gaps. No new tool code was warranted by these
lanes. The previously delivered fixed-block round estimator remains available.

**Zero implementation promotions, GPU experiments or measured serving wins in
this batch.** This checkpoint records rejections and retained components so the
next agent can build on them without regenerating the same proposals.

## Delivery and continued work

These small reports and controls are delivered through Git. Canonical retention
is separate: through80 has completed; the sole81→82/83→84/85→86 controller was
still pending in81 retention at the last read-only process check. Process
presence is not proof of forward progress.87,89 and88/91 have independently
reviewed sequential apply plans; this does not claim they have executed.

[87 retention review](retention-33/87_REVIEW.md) ·
[89 retention review](retention-33/89_REVIEW.md) ·
[88/91 retention review](retention-33/8891_REVIEW.md) ·
[Frozen packets and exact copies](source-copy-manifest-33.json)

No fresh S3 publication or VM restoration is asserted. The next active branches
inspect boundary-only indexer work and Engram row layout against exact dimensions,
existing implementations, packing costs and prior hypotheses. No acceptance
quota is imposed.
