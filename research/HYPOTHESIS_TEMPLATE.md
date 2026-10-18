# H01 — proposed improvement and intended effect

Status: proposed / revised / deferred / rejected / approved for experiment / measured.

Type: original idea / cross-system adaptation / upstream port / feature activation / backend or policy integration.
Confidence: [evidence-based judgment]. Readiness: [investigate / cheap test ready / implementation ready].
New relative to prior batches: [mechanism or changed premise; cite related cards].

## Claim and mechanism

For **[model, hardware/topology, workload, operating range]**, changing **[implementation, feature, backend or policy]** should improve **[metric]** because **[mechanism]**. Expected regressions: **[tradeoffs]**. Label the expected effect as a hypothesis; justify any numeric forecast or omit it.

## Evidence and applicability

- Baseline: full config/overlays, source/image/model pins and run IDs.
- Observation: exact file/row/metric and units. Separate measured facts from inference.
- Code: repository, commit, path and symbols; explain the active path or how the proposed capability will be integrated/activated.
- Prior work: paper/PR links, PR state and inspected SHAs, authorship; already present, port, extension or new idea?
- Missing evidence / competing explanations: what could invalidate the mechanism?

## Proposed change and integration

Files/functions, settings/features and intended change; dependencies and build implications. Include an unchanged-parent control. An activation, upstream reuse or combined integration is valid. Explain the simplest implementation and any alternatives. Separate system-benefit claims from causal attribution that needs ablations.

## Cheapest falsification

Exact check, microbenchmark or targeted profile; inputs/shapes/topology, correctness oracle, metric and result that would reject the mechanism. Include a concrete command when source/tooling supports it; mark unverified commands as proposed. Estimate setup and execution cost separately, with basis or unknown.

## Serving experiment if it survives

- Baseline vs candidate: matched service contract, request bodies/seeds, token lengths, cache preparation, load mode and resource budget. List all candidate code/config/backend changes. Declare quality or hardware differences explicitly; do not silently merge incomparable points.
- Correctness: relevant upstream tests, numerical tolerances/output checks; MTP or cache semantics require more than latency tests.
- Outcomes: primary metric, throughput/latency tradeoffs, failures, mechanism counters; request-level versus aggregate metric definitions.
- Budget: proposed sample/duration/repeats, rationale and total GPU time; no unexplained universal sample floor.
- Robustness: run order/B0 drift check, repeated selected points and distinct final inputs; profiler separate from scored measurements.
- Decision: explicit advance/reject/inconclusive criteria, established before execution.

## Critique, revision and human decision

Label review as self/delegated/external. Record the strongest objection, source checks, revisions and unresolved issues. Link review and preserve the prior claim or summarize the revision. Human experiment selection remains distinct from a review recommendation.
