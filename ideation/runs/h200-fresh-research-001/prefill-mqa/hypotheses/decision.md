# Hypothesis decision

Untested proposals. Scores are prioritization judgments, not predicted speedups.

Selected for test design: 0. Requested: 1.

## h200-contiguous-mqa-epilogue-001

Test a minimal port of DeepGEMM #452’s contiguous SM90 FP8 MQA epilogue into the pinned H200 build, conditional on proving active header use and a safe numerical domain. The supplied installed excerpt retains fmaxf and unhalved KV scales, establishing a source-level delta but no execution or bottleneck evidence. The PR author reports H200 microbenchmark gains from substituting full-rate FADD with an absolute-value operand and compensating both output scales. Our transfer hypothesis is lower exposed prefill time and TTFT where uncached requests invoke this kernel; warm-prefix and paged-only traffic should benefit little directly. Compare against the equally compiled, warmed stock epilogue at unchanged launch settings. Reject unconditional bit-exactness: overflow, underflow, exceptional values and downstream top-k stability must be resolved before serving tests. Serving value remains unmeasured.

**Decision:** rejected

**Reasons:** Quote not found: github:deepseek-ai/DeepGEMM:452:live-page; h200_applicability_and_correctness_required: The matching SM90 header and author-reported H200 tests support a plausible narrow port. However, active artifact provenance and a sufficient numerical-domain invariant remain unknown. The author's "bit-exact numerics" assertion is not generally valid: intermediate doubling can overflow, scale halving can underflow, and exceptional-value behavior differs. The proposal correctly acknowledges these issues and specifies reference, top-k, graph/cache, distributed and quality checks, but their outcomes and applicable G01–G05 definitions are unavailable.

**Cheap test:** Future experiment only: follow attestation, activation, correctness, unprofiled screening, separate mechanism diagnosis, then paired confirmation and held-out evaluation. Change only the coupled three-line epilogue operation. Inspect generated SM90A code for the relevant FMNMX-to-FADD substitution, compensation and unexpected spills or instruction growth. Across every replica/rank, count patched-kernel hits over independently identified eligible contiguous-prefill call opportunities, reporting shapes and score volume; also report eligible calls over all prefill calls. Join requests to final ranks. Use equally warmed JIT artifacts with separately controlled cold KV prefixes and confirmed warm-prefix hits.

**Reject if:** Adequate primary-workload coverage establishes that the changed kernel is unused or already equivalent; a supported-domain correctness failure has no acceptable remedy; or sufficiently precise paired results exclude the predeclared useful gain or show unacceptable quality, TTFT-tail, TPOT or goodput regressions. A microbenchmark win without primary serving value rejects promotion for this baseline.
