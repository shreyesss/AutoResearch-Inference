# From several sources to one testable intervention

Use this when a promising paper partly fits the task, sources disagree, or combining
methods may solve a gap. These are reasoning aids, not a checklist every search
must complete. User scope governs implementation and experiments.

## Decompose before accepting or rejecting

Identify the useful unit: objective, mechanism, policy, representation, training
procedure, runtime implementation or evaluator. A paper can contribute one unit
without the whole package being appropriate.

For consequential components, retain a compact table:

| Source component and exact evidence | Required dependencies | Target fit / change | Disposition and reason |
|---|---|---|---|
| What the source actually does | Weights, inputs, architecture, semantics, hardware | Present / adaptable / missing / incompatible / unknown | Reuse / adapt / omit / investigate |

Distinguish optional performance enhancement from a dependency required to make a
component correct. Omitting a training loss is legitimate only if the inference
method can operate with the available frozen model; a missing learned representation
cannot be removed by renaming it an inference policy. A performance claim about
the full trained package does not become a claim about the reused component.

Example from the user's TreeSpark planning process: candidate-tree construction,
tree verification, acceptance calibration and drafter training are separate units.
One can propose frozen-weight tree selection and fit permitted scalar parameters
while omitting neural training. One cannot omit branch-correct attention, position,
Engram/CED state or cache commits merely because the policy is training-free.
Two similarly named papers remain distinct. This example teaches decomposition;
its checkpoint, GSM8K restriction and waived ROI are specific to that task.

For proposal-distribution or policy calibration, separate the fitting objective
from the deployed probability contract. A training paper's acceptance-overlap
objective can motivate fitting permitted scalar parameters with frozen weights;
its trained-model gains and teacher-forced surrogate do not transfer with it.
Changing the policy can change sampled parents and reached states, so a
request-disjoint split alone does not make baseline traces a valid estimate of
the new policy's online progress. State which counterfactuals the data actually
cover. For lossless speculative sampling, trace the actual proposal through
normalizers, acceptance and residual recovery, including cached dtype/scaling;
adjusting sampling or acceptance alone can bias outputs. Make effective support
and confidence/scheduling policies explicit, so changes to them are not silently
credited to scalar calibration. A lossless claim requires the target distribution
to remain unchanged.
Stochastic correctness need not imply identical outputs at the same seed; retain
the workload's EOS/length policy and account for actual completed outputs.
These checks arose in [PC76's selective objective/PR synthesis](../../../../docs/verification/guided-discovery-20261022/round76/REPORT.md);
that investigation is a deferred proposal, not evidence of a serving win.

## Synthesize with a compatibility argument

Generate only combinations with a causal reason to help. Useful moves include
selective reuse, adapting one source's mechanism to another's representation,
replacing a bottleneck component, and using conflicting results to identify a
boundary condition. Novel terminology or more citations adds no value by itself.

For a proposed combination, state:

1. **Ingredients:** which source supplies which component, and which components
   are deliberately omitted. Retain source identities and revisions/read depth.
2. **Connection:** output/input contract, state ownership, ordering and invariants
   that make the components compatible. Unknown connections are hypotheses.
3. **Target delta:** what changes from the actual baseline, what already exists,
   where the path runs, and what workload situations expose it.
4. **New prediction and alternative:** what observable differs if the mechanism
   is useful versus if the strongest competing explanation holds.
5. **Tradeoff:** additional work, memory, contention, accuracy or maintenance.
   Do not sum headline speedups or treat shared authors' artifacts as replications.

For an overlap, readiness or staging change, identify the producer event, affected
consumers, and the first useful operation that can start earlier; compare with the
target's existing independent issue or polling path. Preserve accumulator and
buffer-reuse dependencies, and distinguish branches where the event is absent or
the producer already overlaps work. An abstract DAG test assigning identical old
and new readiness equations illustrates its premise; it is not independent
evidence that the implementations have those dependencies. Establish them from
the actual consumer paths before drawing that conclusion.

Keep an evidence graph simple: claim → source revision; hypothesis → supporting,
opposing or background claims. A hypothesis `derived_from` another hypothesis
means substantive method ancestry. Sharing a citation alone does not make one
hypothesis a descendant. A source table/PR can invalidate one component without
invalidating all related proposals.

## Separate selection from execution readiness

Extract current user constraints before applying a rubric. State which requirements
are mandatory for this task and which are preferences. If the user mandates both
variants, design both even when one preceding variant loses. If implementation is
authorized before a separate ROI campaign, unknown ROI does not block coding;
correctness and matched controls still govern interpretation. The present research
session may itself forbid implementation/GPU work even when an attached example
describes a future execution plan.

Use a small task-derived rubric with observable reasons, for example:

- mechanism and source support;
- compatibility of the selected components with the target;
- plausible useful improvement under the workload;
- a discriminating and affordable comparison;
- scope fidelity and unresolved risks.

Add novelty only when requested. Define what would pass/fail each relevant
criterion; avoid a universal numeric sum that hides fatal contradictions. Confidence
in the mechanism, priority for investigation and readiness to execute are different
judgments. Keep unknowns unknown. An author-reported gain is not a local ROI input.

## Design the comparison around the claim

First specify the decision the experiment must resolve. For a composite proposal,
compare the whole candidate to a credible control for system benefit; use component
ablations only when attribution changes the next decision. Equal node/compute
budgets may test selection quality; independently tuned wall-clock configurations
answer deployment value. They are different estimands.

Choose the user's workload and metric semantics, not a memorized benchmark suite.
Reuse existing evaluators when their inputs and observables answer the question.
Explain any added probe by a missing observable. Preserve source implementation,
output/correctness requirements, matched controls, request splits and failure
accounting. Never invent a sample size, performance threshold or GPU authorization
to make a plan look complete. Required pins can remain execution blockers while
the hypothesis remains worth developing.

## Critique, revise, and judge tool usefulness

Write a compact self-review against the task rubric, with the strongest objection
and its source or explicit missing evidence. Revision should change a mechanism,
dependency, comparison or disposition; adding reassuring prose is not improvement.
A separate reviewer is useful for consequential assumptions or skill evaluation.
Self-critique is model judgment, not experimental validation. Preserve unresolved
disagreement; do not iterate until the judge says yes.

For consequential tool calls, retain:

`decision_gap → command/receipt → observed evidence or failure → decision_change → next_action`

Examples: a failed provider query calls for retry/provider adjustment, not rejection
of the scientific idea; a source read revealing an existing optimization narrows
the proposed delta; a cached repeat may be useful for inspecting a new passage,
but is not another independent result. Measure usefulness by uncertainty resolved,
candidate revision or avoided wrong experiment, not number of calls/papers or an
unsupported numerical information-gain score. Cheap unknowns need not always be
resolved first if they would not change the decision. Stop when another action
cannot change the selected next step within budget.

## Retain the reasoning with existing tools

No extra orchestration engine is required. `hypothesis propose` preserves additional
card fields: use `card.synthesis` for selected/omitted components and compatibility,
and `card.alternatives` for competing explanations. Link grounded claims normally.
`decide` preserves additional `review` and `tool_use` fields alongside its required
actor/status/rationale/reopen_when. Record rubric judgments with evidence and
changes, and tool receipts with observed decision impact. These optional fields
are retained JSON, not an automatic semantic validator or execution permission.
Keep all failed/deferred ideas and revisions in the existing memory.

## Research basis and limits

These are selectively borrowed engineering ideas, not reproduced results:

- [Scideator](https://arxiv.org/html/2409.14634v6): purpose/mechanism/evaluation
  facets support partial reuse and cross-paper inspiration. Its creativity study
  does not demonstrate faster serving or uniformly better feasibility.
- [DiscoveryRSI](https://arxiv.org/html/2610.23839v1): claim, investigation,
  decision criteria and alternatives; distinguish substantive revision from
  repetition, and scientific development from executable readiness.
- [The Agentic Scientist / official AI Scientist v3](https://arxiv.org/html/2610.18933v1):
  typed contracts and evaluator invariants. Its reported evaluation drift shows
  why a rubric pass cannot certify an experiment.
- [AI co-scientist](https://arxiv.org/html/2502.18864v1): repair nonfundamental
  assumptions rather than automatically discarding a useful core. Biomedical
  findings do not establish transfer to our hardware.
- [Self-correction study](https://arxiv.org/html/2310.01798v2): criticism without
  external feedback can fail in the tested reasoning settings. Require evidence
  for revisions; another agent's agreement is not independent measurement.
