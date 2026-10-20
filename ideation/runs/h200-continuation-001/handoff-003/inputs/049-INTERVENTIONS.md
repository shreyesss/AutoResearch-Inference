# Intervention and allocation plan

The first allocation is **offline investigation**, with no serving attempt
selected. Local ITL deltas remain unknown. This is deliberate uncertainty:
neither graph rows, upstream kernel gains nor synthetic costs establish the
expected H200 service benefit. The retained rubric weights value 30, pilot
decision value 25, engineering cost/fit 20, evaluation cost 15 and evidence/history
10. Scores prioritize test design; they are not success probabilities.

## 1. Continue C24 with dispatch-dependent total-cost qualification

**Specific upgrade:** investigate replacing the constant-with-respect-to-budget
draft term with costs of the target **and subsequent draft descriptors after DP
synchronization**. Preserve five-token proposals, real probabilistic verification
and all previous C24/C03 outcomes. Do not propose merely adding drafting cost;
the installed controller already includes it.

**Cheapest next work, cap 8 engineering hours / 0 GPU-hours:**

1. Trace candidate per-request prefixes through the actual installed varlen,
   graph-selection and draft-sizing chain for all four ranks of each replica.
   Include empty ranks, ragged requests, bucket boundaries and mixed prefill.
   A local rank's budget cannot be priced independently of DP maxima. Record
   any additional coordination an implementable policy would require.
2. Replay stock and counterfactual choices against an independent prefix-budget
   oracle. Keep invented costs labeled synthetic. Separate decision differences
   from real savings; test unchanged-descriptor cases as zero opportunity.
3. Audit the retained C24 traces and reader. Identify exactly why one cell has
   only four eligible cycles and five cells have invalid CPU/GPU associations.
   A proposed measurement repair must change the relevant capture/association
   design; repeating the failed schedule is not a repair. Missing cycles and
   invalid associations remain missing, never imputed as measurements.
4. Produce a measurement addendum with independently reviewable event joins,
   all-rank adequacy checks, analysis units, uncertainty handling and a resource
   cap. If the reader cannot recover sufficient information, state the required
   future capture change and stop this offline allocation.

**Comparison:** AV-off fixed k5; stock AV; a legal static verification-prefix
policy chosen on development states and then locked; and the corrected policy.
Use identical state/cost inputs for policy comparisons. The intended objective
is exposed complete-cycle cost per actual accepted output token, including
controller, sampling, communication and altered draft work. Summed GPU time
across ranks and collective residence are not removable critical-path time.

**Advance only if:** a real missing dependency is established, a legal
implementation is feasible, the timing design can pass the existing adequacy
gate, and qualified measurements can discriminate useful net savings from
overhead and lost progress. The prior gate requires at least ten complete
decode-only cycles per rank/window, valid associations and at least 95%
categorized device-busy union. Passing that gate alone does not prove savings.

**Stop/defer:** an equivalent correction already exists, the interaction cannot
occur, or an adequate measurement shows the corrected policy loses to a legal
comparator. Missing timing/confidence, insufficient occurrences or budget
exhaustion are inconclusive. No automatic C24 rerun follows this document.

## 2. Isolate DSpark sampler fusion, subject to exact baseline gates

**Specific intervention:** extract the unsharded sampling fusion from vLLM
PR61869 while preserving the existing H200 executor, bias GEMM, Marlin experts,
k5, RNG identity, logits cache and watermark semantics. Do not combine it with
the upstream SM100 specialized engine, vocabulary sharding, new graph capture
or AV. This is a separate mechanism from C03's draft-capacity reduction.

**Cheapest next work, cap 4 engineering hours / 0 GPU-hours:** resolve the actual
draft watermark object/configuration; inspect every constructor predicate and
embedding accessor; review the full retained launcher/reduction and scratch
lifetime; identify a generic adapter independent of specialized decode. Stop
the scoped port if preserving an active draft watermarker or another frozen
semantic requirement is incompatible. A request-level watermark flag is not an
object/dispatch attestation.

**Correctness design before implementation:** real checkpoint weights and
controlled inputs; seed/step/position identity; temperature and Gumbel precision;
rounding-sensitive logits and ties; vocabulary/padding layout; cached draft
probabilities; empty rows; arrival-counter reset; repeated graph replay; EOS,
cancellation and recovery. Use independent expected outcomes and corrupt-row /
stale-counter negative controls. Upstream integer-weight parity and acceptance
length are insufficient. Freeze numerical/distribution rules before observing
candidate outputs, accounting for the baseline's known free-form repeatability
limitations.

**Materiality design:** compare sampler against sampler within matched existing
FULL graphs, using native shapes and eligible-call frequencies. Keep the bias
GEMM in both arms. Price scratch initialization, contention, fallbacks and
critical-path exposure. An eager-versus-graph comparison or a GB300 bundled
speedup cannot qualify this port. Before any integration allocation, require
positive qualified component savings and an explicit uncertainty/materiality
rule. Missing timing is a deferral, not a positive result.

## 3. Hold the FP32-weight router port after the cheap check

The candidate asks whether PR61903's SM90 BF16x3 router branch can shorten a
locally active FP32-weight GEMM. Sampled checkpoint gates are BF16 and nominal
GateLinear already distinguishes BF16 weights from FP32 output. There is no
demonstrated eligible local branch. Preserve the idea as a conditional port;
do not spend a GPU slot or change weights merely to activate it. Reopen only
with attested installed loading/cast/dispatch evidence and an absent equivalent
optimization. Exact native shapes, routing/top-k effects and changed-math
quality would then need qualification.

## Conditional budgets and service gate

The model-generated budgets below are **planning ceilings**, not measured effort,
approved reservations or a portfolio to run in full. Compilation, roughly
26-minute historical cold startup per service arm, capture, warmup and cleanup
are included; cap exhaustion is inconclusive and no automatic retry is budgeted.

| Candidate | First CPU/source cap | Conditional implementation/correctness cap | Conditional instrumentation/analysis cap | Future component + integration GPU ceiling |
| --- | ---: | ---: | ---: | ---: |
| C24 cost model | 8 engineer-hours | 32 engineer-hours, early feasibility stop | 16 engineer-hours | 24 GPU-hours |
| Sampler fusion | 4 engineer-hours | 32 engineer-hours, early feasibility stop | 10 engineer-hours | 22 GPU-hours |
| Router port | Original audit cap 3 engineer-hours; now held | 20 engineer-hours including feasibility checkpoint | 8 engineer-hours | 20 GPU-hours; not released |

Do not add these ceilings together as a commitment. Even these pilots can cost
as much as a service screen; cheap eligibility and intermediate stops matter.
If one candidate later qualifies, its proposed separate service envelope is
20 GPU-hours for two 75-minute eight-GPU screen arms, 100 GPU-hours for five
matched confirmation pairs, and 20 GPU-hours for a held-out allowance. Validate
these caps against the actual evaluator schedule before allocation. At node
price P per hour, an allocation costs `GPU-hours / 8 × P`; P is unknown here.

For the frozen Mooncake 0.5x contract, retain the positive screen, 2% primary ITL
promotion criterion, 3% TTFT/E2E tail guards and at least five alternating
matched confirmation pairs for a small gain. Preserve all correctness and
workload gates, native agent-f75 8K/1K traffic and held-out ragged, mixed,
long-context and cache conditions. Diagnostic/profiler runs remain separate
from the unprofiled service frontier. Two full service attempts remain; this
research pass consumes neither.

DeepInfer host-event pooling and large-queue optimizations remain inspection
leads until an equivalent expensive local path is established. The broad Hopper
engine port remains a separate integration project. A fourth proposal is not
required to fill a quota.
