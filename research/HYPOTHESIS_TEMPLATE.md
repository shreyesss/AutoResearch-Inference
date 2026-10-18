# H01 — specific source change and intended effect

Status: proposed / revised / rejected / approved for experiment / measured.

## Claim and mechanism

For **[model, hardware/topology, workload, operating range]**, changing **[source behavior]** should improve **[metric]** because **[mechanism]**. Expected regressions: **[tradeoffs]**. Label the expected effect as a hypothesis; justify any numeric forecast or omit it.

## Evidence and applicability

- Baseline: full config/overlays, source/image/model pins and run IDs.
- Observation: exact file/row/metric and units. Separate measured facts from inference.
- Code: repository, commit, path and symbols; show this path is exercised.
- Prior work: paper/PR links, PR state and inspected SHAs, authorship; already present, port, extension or new idea?
- Missing evidence / competing explanations: what could invalidate the mechanism?

## Proposed patch

Files/functions and intended change; dependencies and build implications. Include an unchanged-parent control. Explain why a simpler setting change is insufficient or why this needs a code change.

## Cheapest falsification

Exact check, microbenchmark or targeted profile; inputs/shapes/topology, correctness oracle, metric and result that would reject the mechanism. Include a concrete command when source/tooling supports it; mark unverified commands as proposed. Estimate setup and execution cost separately, with basis or unknown.

## Serving experiment if it survives

- Parent vs patch: same model, config, request bodies/seeds, input/output lengths, cache preparation, load mode and operating points.
- Correctness: relevant upstream tests, numerical tolerances/output checks; MTP or cache semantics require more than latency tests.
- Outcomes: primary metric, throughput/latency tradeoffs, failures, mechanism counters; request-level versus aggregate metric definitions.
- Budget: proposed sample/duration/repeats, rationale and total GPU time; no unexplained universal sample floor.
- Robustness: run order/B0 drift check, repeated selected points and distinct final inputs; profiler separate from scored measurements.
- Decision: explicit advance/reject/inconclusive criteria, established before execution.

## Critic response and human decision

Link review; list changes made, unresolved objections and decision. Preserve previous versions or summarize the revision. Do not mark an experiment approved merely because a critic advances the idea.
