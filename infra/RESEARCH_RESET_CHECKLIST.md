# OPS4 research reset: execution checklist

Status: working checklist, 18 October 2026 (Asia/Kolkata). The current OPS4 results remain exploratory. This checklist does not change their campaign identity or claim a new evaluator is qualified.

## Next 1–2 hours

- [x] Audit the real search domain: five active vLLM settings; chunked-prefill controls are declared but inactive. Preserve the existing OPS4 domain and B0 identity while designing a versioned successor.
- [x] Decompose measured iteration cost from `results/2026-10-17-ops4-first-search/*/evaluation-timings.json`: about 46 minutes, with four model starts taking about half the time.
- [x] Verify AIPerf 0.13 adaptive search against its installed code and official documentation. Its search variables are benchmark inputs; it does not restart vLLM with candidate server settings. The local capability spike already ran a three-iteration synthetic interface check.
- [x] Run a bounded live AIPerf adaptive-load smoke on the pinned model and save native `search_history.json` and timing. Two 12-request trials completed; their selected rate is not a capacity result. See `AIPERF_ADAPTIVE_FINDINGS.md`.
- [x] Check BLIS installation, Qwen/Blackwell calibration coverage, TraceV2 conversion, and whether it models model-loading time. All 307 recorded chat requests replayed on a surrogate, but model/hardware calibration is absent. See `BLISS_SPIKE.md`.
- [x] Write the dev/test and fast-gate protocol with clear implemented/proposed labels, sample-size limits, frozen split identity, uncertainty, and promotion rules. See `OPS4_EVALUATION_REDESIGN.md`.
- [x] Run fresh-server mixed-task B0 and 4096 candidate repeats, then audit exact paired request IDs and shape-level changes. Both confirm cells were valid/normal with 36/36 completions. The frozen-stream tail direction repeated; see `results/2026-10-18-research-reset/paired-mixed.json`. This does not establish an independent test result.

## Design decisions to resolve before a new autonomous campaign

- [ ] Define a primary **development** workload: a longer, source-backed mixed stream with enough requests in each important length/traffic stratum. Keep per-stratum output rate, TTFT, and TPOT visible even if a single utility or feasible-goodput score is later chosen.
- [ ] Freeze independent **test** content and arrival schedules before proposing candidates. Keep test outcomes out of the agent's proposal context; run tests only on finalists selected using development data. Separate source/session identities where available; a different random seed alone tests only resampling from the same synthetic generator.
- [ ] Establish operational SLO thresholds or a declared utility function before using AIPerf's SLA-boundary planners. Current observed p99 values are measurements, not agreed SLOs.
- [ ] Decide load policy: fixed arrival points for paired config comparisons; adaptive load search for baseline characterization and selected finalists. Do not give each candidate a favorable load point and compare its throughput to a different load without a capacity/SLO protocol.
- [ ] Version a broader server search domain after checking support and binding in pinned vLLM. Candidate families: scheduling/token budgets, KV-cache allocation/precision, prefix/Mamba cache policy, MTP, CUDA graph/compilation, and, under a separate quality contract, numerical precision. Add conditional constraints and feasibility checks. Preserve failed boots and inactive mechanisms in the ledger.
- [ ] Validate a fast gate against historical known-good/known-bad contrasts. Candidate gate: static/boot check, short development smoke for failures and large regressions, longer development measurement for survivors, independent confirmation/test for finalists. Estimate false-reject rate and actual saved GPU time before deploying it.
- [ ] Decide whether the outer optimizer is agent hypotheses, mixed-variable Bayesian optimization, or a hybrid. AIPerf can own adaptive *load* trials; its native planner does not directly optimize vLLM launch settings. Compare against a simple BO baseline before attributing benefit to agent reasoning.

## Scientific claims still unavailable

- Stable p99 improvements from a single 18-request document or 36-request mixed window.
- Production-representative behavior from the engineered synthetic mix.
- BLIS-to-real parity without a calibrated model/hardware profile and matched trace semantics.
- SLA-constrained capacity without an explicit SLA and repeated boundary trials.
