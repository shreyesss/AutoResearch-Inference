# Independent gates for the overnight continuation

Evaluator designer: `overnight_evaluator`. Written before any new candidate,
GPU pilot or service traffic in this continuation. Scope is independent design
and source/evidence review; evaluator implementation belongs to the separate
builder, candidate implementation to the optimization builder, and runtime
actions to the root orchestrator.

The user authorized continued overnight work following the previous protocol.
That authorizes advancing a qualified stage without a further permission round;
it does not change correctness, measurement, materiality or stopping rules.
The current order is C24, C25, C26 by plausible baseline-relative value and
decision value. Scores are priorities, not speedup estimates. Two full service
hypothesis attempts remain. Source checks and bounded diagnostics consume
recorded resources but do not retroactively become full performance attempts.

## Shared frozen endpoint and controls

The primary endpoint remains the existing scorer's long-output (at least 50
tokens) median ITL on Mooncake median at 0.5x. Preserve first-content-chunk and
fallback coverage. A positive unprofiled screening pair with neither observed
TTFT p99 nor E2E p99 regression above 3% may advance to confirmation. A useful
confirmed gain requires the paired run-level 95% lower ITL-gain bound to be at
least 2%, and upper paired 95% tail-regression bounds at most 3%, with at least
five alternating matched pairs, the frozen bootstrap procedure and a held-out
local burst regression pair. The exact procedure remains
`../../c03-test-plan-001/EXECUTION_BRIEF.md`; no request-level pseudoreplication.

Use only this node, its same eight H200 GPUs, pinned installed image/model and
original serving/client environments. Preserve the original profile, DP/EP/TP
layout, seq64, k5, temperature, top-p/top-k, watermark, RNG ownership, workload,
router and scorer. A specific candidate may change only its declared mechanism;
C24 may prospectively declare AV/prefix-policy arms. No combined C03 patch or
other optimization. Freeze actual installed files, not only a nominal revision.
All proposed source mounts are isolated and reversible. Diagnostic observations
must be absent from unprofiled service arms unless equal negligible overhead is
independently established.

Completion at least 99.5%, errors at most 0.1%, replay p99 at most 500 ms,
nondegraded replay, complete artifacts and existing token/rank coverage remain
required. Report service SLO eligibility independently of valid comparisons.
C03's unfavorable result and C24's old instrumentation-inconclusive result
remain unchanged. Do not repeat valid unfavorable screens until they win.

## C24: coupled verification and subsequent draft cost

### Offline mechanism and implementability gate

1. Attest the installed objective already includes its request-indexed draft
   term. Identify the exact missing budget-dependent term without claiming that
   drafting was altogether omitted.
2. Reconstruct candidate prefix allocations through all four ranks, DP maxima,
   graph rounding, actual target descriptor and subsequent draft descriptor.
   Cover empty ranks, unequal rank loads, both sides of every relevant bucket
   transition, unchanged descriptors, mixed prefill and maximum legal capacity.
   A source-derived mapping is a counterfactual, not observed runtime frequency.
3. A separate evaluator oracle must enumerate legal prefixes from inputs; it
   must not call the candidate objective to generate its expected answer.
   Include a deliberately wrong constant-draft model and wrong local-only DP
   model that the fixtures reject. Synthetic cost examples remain synthetic.
4. Specify when actual confidence, accepted progress, rank state and candidate
   costs become available. Identify extra collectives, synchronization, host
   reads or graph breaks required by the policy. Missing AV-off confidence is
   not repaired by inventing confidence or treating accepted length as a
   substitute. An infeasible globally informed policy cannot qualify a local
   implementable policy.

The next allocation remains bounded at eight engineer-hours of CPU/source work.
Equivalent existing correction or impossible interaction is a stop for this
specific mechanism. Unknown costs/occurrence/feasibility are a deferral. Neither
graph row counts nor the synthetic budget change establishes a latency benefit.

### Retained trace audit and measurement-repair gate

Keep all old source, traces, readers and verdicts immutable. A new offline
reader/output needs its own filename, hashes, source diff and independent
review. Its only permitted retrospective purpose is to diagnose or correct a
demonstrated interpretation defect. It cannot turn the old frozen verdict into
a passing historical run.

For each of the 647 flagged GPU activities, retain exact event identity,
process/thread/device/stream, correlation and external identifiers, source
event category, CPU launch start/end and GPU start/end. Determine whether IDs
are unique in their actual domain, whether runtime/driver records duplicate an
underlying call, whether graph replay has distinct association semantics, and
whether an independent flow/external-ID relation confirms the join. Reused IDs,
ambiguous parents and unmatched activities remain explicit failures. Kernel
name similarity, nearest timestamps, arbitrary tolerance and fitted clock
shifts are not attribution evidence. GPU execution can overlap a CPU launch's
duration, so only a causal assertion actually required by the interface may be
tested; a change to that assertion needs demonstrated trace semantics.

Investigate native-cycle coverage separately: replica 1/rank 2 at +90 s has
eight native execute ranges against 26 target scopes and only four complete
decode cycles. Determine from raw category/phase/lifetime evidence whether
ranges were truncated, omitted by scheduling/collection, or genuinely absent.
Do not reconstruct missing native prefill/decode counts from neighboring ranks
or assume every target is decode. Report profiler/export skew and all affected
scope boundaries.

A **new capture is conditional on a reviewed prospective addendum** containing:

- A demonstrated defect or a bounded, discriminating instrument check that
  resolves the remaining causal alternatives, with the exact capture/association
  change addressing each unresolved failure. Simply lengthening/repeating the
  previous schedule is insufficient.
- Exact installed observation diff and hashes, annotation/category vocabulary,
  unique event-join keys, native step/context/generation identity, exclusions,
  clock domains, graph-launch evidence and attribution negative controls.
- Fixed traffic and recording windows, a resource/timeout cap, one scheduled
  capture allocation without replacement windows, per-rank perturbation
  measurements, and the normal all-rank drain/archive/cleanup sequence.
- The original minimum ten complete eligible decode cycles in every rank/window,
  required target/draft association, at least 95% categorized device-busy union,
  and no truncation/dropped activity affecting the required scope. Missing
  required graph work cannot hide in the 5% allowance.

All category intervals are clipped into same-device half-open complete-cycle
boundaries. CPU time, GPU union, stage span and cycle span remain different
columns. Never add overlapping work or eight ranks into wall time. Target
collective residence includes waiting. Only observed dependency chains support
an exposed-time claim; occupied time alone does not. A replica/client path needs
shared step identity and comparable cross-rank clocks/dependencies.

The prior 20%-on-every-rank/window target occupancy rule remains a conditional
cost-materiality heuristic if reproduced under an adequate design. It does not
authorize a gain claim. A useful C24 policy comparison requires AV-off, stock AV,
a legal static policy locked using development data, and the proposed policy,
with total-cycle cost per actual accepted output including controller,
coordination, sampling and changed draft execution. Hold-out states and policy
selection rules must be frozen before performance comparison. The addendum must
set its decision-relevant uncertainty and minimum-saving rule before outputs;
this document does not invent a numerical component benefit from absent data.

## C25: isolated sampler fusion

The first allocation is at most four engineer-hours, CPU/source only. Attest the
actual launch/config algorithm, factory logic and object passed to the installed
draft path. The request's `watermark=true` alone proves neither presence nor
absence of a draft watermarker. Retain all constructor predicates and accessors,
vocabulary/layout restrictions, precision, graph scratch ownership and fallback
conditions. A source-only result must say whether it proves the effective
configuration or only a conditional branch; no runtime-object claim without a
runtime observation.

If an active draft watermarker conflicts with the extracted sampler, **stop the
scoped port**. Do not disable it or silently choose target-only watermarking.
A watermark-preserving redesign is a separately identified intervention with
new correctness and value/cost review. Likewise, do not enable SM100 specialized
decode merely to make an accessor available on H200. Absence of a generic
equivalent adapter is a feasibility hold.

If source/config eligibility passes, freeze independent tests before candidate
implementation: real checkpoint weights, per-request seed/position/step,
temperature and Gumbel precision, round-sensitive logits and ties, cache values,
valid/padded vocabulary, empty rows, counter initialization/reset, repeated graph
replay, EOS/cancellation/recovery and corrupt-row/stale-counter negative
controls. Exact ownership and discrete outcomes matter. Baseline free-form
repeatability is known to fail; use independently specified controlled fixtures
and predeclared numerical/distribution criteria rather than pretending a
free-form exact-output comparison is decisive. Integer-weight upstream tests
and unchanged acceptance length do not prove correctness.

A later bounded component pilot compares sampler with sampler inside matched
existing FULL graphs, with the bias GEMM retained in both arms. Include native
shapes/frequencies, scratch initialization, contention/fallback cost and
critical-path exposure. Freeze repeats, paired analysis, uncertainty and a
materiality rule before running it. Positive qualified component savings are
necessary before service integration allocation; eager-versus-graph or bundled
upstream gains do not qualify this isolated treatment. There is no GPU release
until the exact candidate and independent fixture/pilot contract are reviewed.

## C26: existing FP32-weight router applicability

At most three engineer-hours of CPU/source audit may resolve the remaining
gate. Read actual installed class inheritance/constructor, effective model
default/parameter dtype, registered parameter allocation, loader/casts and
dispatch predicates for target and draft routers. Sampled BF16 storage and FP32
output alone are insufficient. Cover all relevant key/class families and note
whether the sampled headers establish the entire eligible family.

A complete static installed chain proving the unchanged baseline allocates and
keeps BF16 router weights, and routes them to a different existing branch,
suffices to close the proposed FP32-weight port as inapplicable to this scope.
It does not require expensive service startup merely to restate the source
consequence. If dynamic casts or selection remain unresolved, record a narrow
inconclusive finding and defer. Do not cast weights to manufacture eligibility.

Reopen only with attested existing FP32 weights, an active eligible branch and
absence of an equivalent optimization. Then freeze real native shape coverage,
router/top-k decisions and rounding sensitivity, graph behavior, and quality
criteria before implementation or GPU allocation. Prior H200 results on other
models/shapes are context, not local materiality evidence.

## Decision records and stopping

Record applicability, implementability, correctness, timing adequacy,
materiality, service effect and SLO eligibility as separate statuses. A cheap
inapplicability finding is useful completed work, not a failed benchmark or
permission to run a different intervention under the same identity. Preserve
raw failures and engineer/GPU/wall cost. Keep the two-attempt ledger explicit.
No unqualified hypothesis is owed an expensive run merely to fill a top-three
quota. Root may advance a candidate only after the applicable independently
reviewed gates have concrete passing evidence.
