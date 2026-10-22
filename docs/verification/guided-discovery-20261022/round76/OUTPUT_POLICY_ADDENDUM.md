# Output-policy addendum

A different valid proposal can change the seeded coupling and therefore finite output tokens, EOS positions and output lengths while preserving the target distribution. Same-seed token equality is not the correctness criterion for a changed-temperature stochastic arm. The temperature1 identity path should preserve the original implementation behavior.

For the existing Mooncake/agent-p75 workload, preserve EOS, stop rules and output limits; record completed token counts, completion status and realized output lengths. Use paired requests with repeated trials and appropriate length/context strata. Do not silently force ignore-EOS or compare unmatched output lengths as evidence of a service win. Separate target-distribution correctness tests from measured progress/ITL and tail/quality checks. This narrows evaluation admission without changing the deferred verdict.
