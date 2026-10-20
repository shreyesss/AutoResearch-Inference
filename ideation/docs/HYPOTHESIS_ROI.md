# Hypothesis value, cost and pilot rubric

Recorded 2026-10-21 (Asia/Calcutta), following the user's C03 review feedback.
This is a prospective requirement in generation/review prompts and the research
workflow. It does not change sealed experiment decisions or implement an
automatic execution gate in the Python tools.

Novelty is already off unless requested. The next improvement is to rank ideas by
plausible optimization benefit, time to obtain that benefit, and the cost of
resolving uncertainty. A technically valid inefficiency alone is insufficient.

## What C03 teaches

The [mechanism review](../runs/c03-mechanism-review-001/REPORT.md) established
smaller draft graphs on 6.30% of recorded online events and 3.87% fewer draft rows
within supported FULL events. It did not establish milliseconds saved. Neither
percentage is a service speedup estimate. The activation gate answered whether
the mechanism occurred, but did not answer whether it was worth a service attempt.

## Required rubric for each candidate

Freeze the task's objective, minimum worthwhile gain, resource limits and
promotion rule before pilots. Use the following evidence fields in the brief,
card and test plan; any scoring weights remain task-specific and explicit.

| Dimension | Required content | Decision rule |
| --- | --- | --- |
| Baseline and mechanism | Exact installed path, hardware, workload, strongest existing comparator, and work removed or shortened. | An inactive path or an already-enabled identical mechanism needs a different experiment. Unknown activation calls for inspection. |
| Expected optimization delta | Primary metric and units; low/base/high conditional gain estimates with assumptions; affected workload fraction; component time and overlap; added overhead; correctness and tail constraints. Label every input measured, inferred or unknown. | Row counts, event frequency and upstream percentages cannot stand in for local time. Unknown gain may justify a pilot, but cannot be reported as established ROI. |
| Expected time and cost | Low/base/high engineering hours for inspection, implementation, integration and correctness; pilot and confirmation GPU-hours; startup/capture time; likely maintenance cost. State resource prices only if known. | Compare options under the actual remaining budget. Include evaluator preparation and failed setup risk, not just patch size. |
| Pilot value | The one uncertainty that changes the decision; cheapest discriminating measurement; control and representative shapes; artifact requirements; wall-clock/GPU-hour cap. | A pilot must be able to stop or change the proposal. Merely proving activation is insufficient when time materiality is the unresolved question. |
| Promotion and stopping | Predeclared support, stop and inconclusive conditions; minimum worthwhile service gain; independent correctness requirements; permitted follow-up budget. | Advance only when evidence supports a plausible gain after overhead. Preserve negative/inconclusive results; a high reviewer score cannot override a required unknown. |

Keep numerical expectations honest. If component time is unknown, state which
measurement supplies it rather than inventing a base estimate. Required fields
can be unknown at ideation; unresolved materiality blocks an expensive attempt,
not the cheap diagnostic that can resolve it. Compare candidates by expected
benefit and both engineering/GPU cost; retain alternatives where neither dominates.
Do not turn a reviewer score into a probability of success.

## Pilot sequence

1. **Inspect applicability.** Check the installed dispatch and baseline behavior,
   then identify the affected operation and representative workload shapes.
2. **Measure materiality.** Obtain a bounded baseline profile and, where feasible,
   a matched-shape component comparison or minimal prototype. Account for graph
   buckets, rank participation, tiling, communication, synchronization and added
   control cost. Label occupied GPU time separately from exposed critical-path
   time; a trace that cannot establish the latter must retain that uncertainty.
3. **Update the estimate and decide.** Weight component savings by representative
   workload exposure, retain uncertainty and compare with the task's worthwhile
   gain. Stop when a defensible optimistic bound is too small; defer when evidence
   cannot resolve the question within budget. A further pilot needs a named gap
   and bounded cost.
4. **Run the service screen only after qualification.** Preserve the frozen
   objective, matched control, correctness checks and tail guards. Profiled runs
   inform diagnosis; unprofiled service runs establish service results. The C03
   contract's 2% primary-benefit threshold is local to that contract, not a
   universal hypothesis-selection threshold.

For non-overlapping work in a measured time window, a conditional saved-time
estimate is `sum(event_count × net_saved_time_per_event) / baseline_elapsed_time`.
Use compatible phases and denominators and avoid double-counting parallel ranks
or overlapping kernels. If exposed time or linear transfer is unknown, report
scenarios, not a bound or a service prediction. Tail latency, queueing and maximum
capacity need their own service measurements.

When deployment economics are known, estimate payback from implementation and
evaluation cost divided by demonstrated savings per unit time. A fixed-load ITL
gain does not itself establish fewer GPUs or lower spend. Until that conversion
is measured, report metric improvement, engineering hours and GPU-hours separately.

## Calibration after every attempt

Preserve the original expected delta, uncertainty and budget alongside actual
pilot cost, engineering time and scoped service results. Record which assumption
failed: applicability, activation, component saving, service transfer, correctness
or integration cost. Track how often pilots changed the decision and how much
expensive evaluation they avoided. Improve future estimates from these outcomes,
not from the number of proposals, sources downloaded or novelty scores.

Use the existing [task rubric and memory](ADAPTIVE_POLICY_AND_MEMORY.md) and
`hypothesis.plan_test` interfaces. The rubric-generation prompt now asks for
value, effort and pilot criteria; proposal and critique prompts explicitly cover
them. Proposals use the existing `predicted_direction`, `experiment.cost` and
experiment decision fields. Their current schemas do not mechanically enforce
the completeness of ROI estimates or authorize execution. Existing frozen rubrics
and historical decisions remain unchanged; new runs should generate or explicitly
adopt an appropriate rubric.

## Course correction without changing an old result

Use the requested meta-critic to challenge gates that do not answer the next decision, especially after an unexpected setup failure or a valid incremental improvement. Record a prospective new scope and independent evaluator review when changing the endpoint or diagnostic. Preserve exact correctness, input identity and cost accounting; keep the previous result and its threshold unchanged.

Report the evidence level explicitly: applicable source path, correct faster component, native graph activation/performance, real request lifecycle, and matched service benefit are different conclusions. A single startup pair supplies exploratory within-start precision, not independent launch replication. If many predeclared cells are inspected, a positive per-cell interval is not a simultaneous confidence statement. Publish the whole matrix and stop when additional information is unlikely to justify its cost.
