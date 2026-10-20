# Fixed screen A/B descriptive context

A: `20261020-183933`; B: `20261020-192708`. Both use the common approved context reader `042a330f…`; the descriptive join uses independently approved `a708b8c6…`. This report makes no performance or accuracy decision.

All 4004 workload keys are present in both arms, with zero invalid or duplicate keys. The 4003 requests with reported results in both have exactly equal actual input lengths, output lengths and prompt-token counts. The retained A failure is `session_000482` (HTTP502/reset); B completed that same key with 931 input tokens and 9 output tokens. Both long-output cohorts contain 1692 requests. The joined CSV retains all 4004 rows.

| Request-cohort quantity | A, whole reporting cohort | B, whole reporting cohort |
| --- | ---: | ---: |
| Completed / attempted | 4003 /4004 |4004 /4004 |
| Core speculative reports |4003|4004|
| Fully observed per-step reports |3987|3988|
| Verify steps S |265716|265882|
| Proposed draft tokens D |1328580|1329410|
| Accepted draft tokens A |448869|448689|
| Step-weighted acceptance length |2.689281037|2.687549364|
| Draft acceptance fraction |0.337856207|0.337509873|

Each arm has 16 zero-step, one-token outputs whose optional per-step lists are absent. These remain valid core reports; no empty lists were synthesized. There are no nonzero-step missing-list gaps. All reported widths are 5. Common-valid comparisons use 4003 nonerror keys: A S/D/A =265716/1328580/448869; B =265880/1329400/448683. This separate subset never replaces scorer endpoints or whole-run totals.

A first chunks contain 4001 successes with1 token, one with7 (`session_003467`,234 output tokens), and one with4 (`session_003469`,42 output tokens). B contains 4003 with1 token and one with6 (`session_003706`,423 output tokens). Each long cohort has 1691 first chunks of 1 token and one larger first chunk. Server counts are used consistently; neither arm has ITL fallback, later-usage substitution, malformed chunks or first-count warnings. The single failed A row has no content.

Client cached-prompt share is 27.797100% in A and 28.259502% in B (B−A +0.462403 percentage points). On common keys, cached counts differ on 205 requests: 102 higher in B and 103 lower, totaling 159936 more cached prompt tokens in B; 3798 are equal. Warmup completed 52 requests in A versus 53 in B, both without errors. These differences remain context for independent interpretation; equal cache state is not assumed.

Primary independent telemetry has complete required counter intervals for all eight endpoint/rank identities in both arms, with no observed counter decreases. All eight observed preemption deltas are zero in each arm. Categorical KV configuration keys are exactly equal, with one configuration per rank per arm. Rank counter distributions differ and are retained individually; GPU sample means/coverage are retained per physical index, without inferring rank ownership. Per-GPU SM-utilization sample means span 97.79–98.77% in A and 98.48–98.81% in B. These are descriptive collection-loop sample means, not time-weighted kernel measurements.

The corroborating AIPerf endpoint export lacks replica 1’s post-end boundary in both arms. That gap remains visible; the prospectively fixed independent collector supplies the primary intervals. Engine intervals can include adjacent work and are not substituted for the exact client cohorts. Both existing scorer outputs remain SLO-ineligible; replay p99 is 4.87108608ms(A) and 5.05046272ms(B), with degraded 0 in both. The large console replay warnings correspond to the separate warmup aggregates.

Evidence: [paired context JSON](screen-pair-context-comparison.json), [full outer request join](screen-pair-requests-joined.csv), [A export audit](screen-A-export-audit.json), [B export audit](screen-B-export-audit.json), [A client/trace attestation](screen-A-client-manifest-check.json), [B client/trace attestation](screen-B-client-manifest-check.json). Source hashes are preserved in the receipts; trace/runtime identity remains externally attested. Independent evaluator review is required before any paired interpretation.
