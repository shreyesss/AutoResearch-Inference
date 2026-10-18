---
name: inference-critic
description: Independently critique vLLM and DeepEP optimization hypotheses, PR interpretations and benchmark designs against original code and measurements. Use to decide which source-level inference experiments to advance, revise or reject before implementation.
---

# Independent inference critic

Read `research/README.md`, `research/SOURCES.md`, and the requested batch's brief, hypothesis cards and evidence links. Prefer a fresh session distinct from the researcher. If reviewing your own work, label it self-review; do not claim independence.

Use original code, benchmark files and online primary sources to check consequential claims. Do not treat citation presence, prose agreement or a PR author's speedup claim as proof. Update PR status and inspected SHAs with an access date. Make source-access limits visible.

For each hypothesis, answer these questions with evidence:

| Check | Question |
|---|---|
| Applicability | Is this code/backend exercised by the measured model, build, topology and workload? Is the improvement already present? |
| Evidence | Do the exact rows, units and metric definitions support the symptom? Are raw traces needed for the proposed explanation? |
| Mechanism | Does the code change plausibly affect that symptom? What competing explanation or cheaper setting change could account for it? |
| Correctness | Could it change outputs, cache semantics, synchronization or numerical behavior? Is there a relevant oracle/test? |
| Experiment | Is there a cheap falsification, fair parent control and matched workload? Are profiling overhead, warmup, drift and selection bias handled? |
| Value and cost | Can it move a useful serving frontier? Are tradeoffs visible? Are build/hardware requirements and estimated cost justified? |

Explicitly check common errors: inferred DeepEP use from an EP flag, two replicas described as two nodes, cached-target share confused with observed hits, closed-loop concurrency confused with requests/s, aggregate ITL confused with request-level TPOT, and unrelated workloads combined into one frontier. Do not demand novelty for a useful upstream port. Do not add arbitrary sample floors or mandatory expensive sweeps.

Write `review.md`:

1. Summary table: hypothesis, strongest support, decisive objection, **advance / revise / reject**.
2. Per hypothesis: evidence actually checked, strengths, specific objections with source pointers, cheapest resolution, and the observation that would falsify it.
3. Recommend one next experiment, or state that none is ready. Identify what requires human choice versus further read-only research.

Advance means worth human consideration, not proven improvement or permission to run. Unknown hardware access may defer execution without invalidating an otherwise useful idea. A mechanism contradicted by the source should be rejected; missing fixable evidence should produce a concrete revision request.

Do not edit the researcher's original cards or historical results. After a revision, append the verdict change and its evidence. Use plain decisions with reasons rather than fabricated numeric rigor scores. Stop before implementation/GPU execution in this stage.

See `research/THIRD_PARTY.md` for adapted review principles.
