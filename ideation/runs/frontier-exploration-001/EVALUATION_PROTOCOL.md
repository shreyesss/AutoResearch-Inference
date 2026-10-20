# Common evaluation contract for later autoresearch

These are **proposed design choices**, not measured gains, user production SLOs, or authorization to execute GPU jobs. A per-idea design may tighten them but must state deviations before testing. Read [baseline audit](BASELINE_AUDIT.md) first.

## Objective and comparison boundaries

Increase sustainable SLO goodput per allocated GPU-hour, or lower latency at matched goodput/cost, without correctness/quality regression. Use separate frontiers for synthetic agent-f75, each Mooncake replay, precision variant and load mode. Compare against a fresh baseline run in the same experimental block, not only historical summary numbers.

- Primary capacity metric: maximum sustainable **strict** SLO goodput across offered-rate points, with the frozen AIPerf0.13.0 scorer and TTFT4s /ITL33.333ms /E2E75s settings from the archived replay manifest, unless a separately named SLO is predeclared.
- Report campaign length-aware goodput separately after recovering its exact scorer; never silently replace strict goodput with it.
- Fixed-load metric: E2E/TTFT/TPOT p50,p95,p99 and streaming-gap tails at identical offered requests and clock schedule. No artificial5% throughput target below arrival-limited saturation.
- Cost: allocated node-hours × declared node rate /good completed requests. Report GPU-hours/1000good requests alongside dollars. Include failed, startup and warmup allocation in campaign costs; separately report steady-state cost. Eight B200s at$36/node-hour is a scenario, not a price claim.

## Stage0: baseline and eligibility (CPU first)

Freeze resolved launch configuration, image/source/dirty diff, weights/tokenizer, request payloads and dataset hashes, routing policy, precision, batch and graph settings, clocks/power limits, client/scorer code versions. Use existing AIPerf manifest's tokenizer revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027` only if the runtime matches it.

Locate the exact implementation and check whether the proposal already exists or is ineligible for DSpark k5, EP topology, dtype or model backend. Record source file+SHA and behavior. Missing runtime information yields `blocked_baseline`, not invalidated. Existing equivalent behavior yields `already_present`; preserve that result and stop redundant work. Recover raw per-request/token outputs for the selected historical anchors if available; no need to download119GB indiscriminately.

## Stage1: correctness and cheap falsification

One isolated change. Run exact correctness/capture/buffer/rank-consistency checks from the idea's card before performance sweeps. Include cold/warm graph state, empty and uneven rank batches, long/mixed prefill, cancellation and streaming where relevant. Deterministic exact-preserving changes require reference agreement under a controlled deterministic kernel mode; floating-point reassociation requires predeclared numerical tolerance plus task-quality checks. Probabilistic speculative sampling requires distributional checks, not an unjustified identical-string requirement. Quantization changes require a separately frozen quality benchmark and acceptable error bound.

Microbenchmarks or short traces establish whether the proposed cost is present and whether the changed operation helps. Use short instrumented windows; run serving comparisons without heavy tracing. A kernel speedup alone never validates serving cost/latency improvement. Any memory error, rank mismatch, output corruption or graph replay failure halts that variant.

## Stage2: bounded screening

Per candidate, start with current baseline, strongest relevant static/known comparator, and one treatment. Keep all unrelated settings fixed. For policy ideas include an overhead-only or individual-component ablation.

1. Synthetic agent-f75: use the current 8192/1024 payload generator, declared75% cacheability target, fixed prefix schedule. Initial anchor c384; c64 andc512 are boundary checks if screening passes. Record actual cache hits. At c512 preserve the historical20s E2Ep95 target as a separately named *design target*, not an inferred universal SLO.
2. Replay: median and burst at1×, then1.25×/1.5×/2× until an eligibility guard fails. Use the identical arrival schedule and payloads for paired arms. Replay failures, client scheduling lag, errors, drops and queue growth count; dropping requests must not appear as improved latency.
3. Randomize AB/BA order within blocks, matched cache reset/warmup for each arm. Begin with two paired repeats of150s measurement plus120s warmup for the single selected cell. This is a screening estimate; it is not enough to claim tail significance or sustained capacity. Check request counts and stationarity.

Suggested initial GPU screening budget: **45node-minutes per idea**, excluding compilation/model loading but recording them. This limits the initial matrix; do not run every listed workload/variant exhaustively. At8GPUs that is6GPU-hours, or$27 at the declared scenario. Stop on correctness failure, absent target cost, or clear regression. A budget overrun is inconclusive, not proof of invalidation.

## Stage3: confirmation and protection against tuning overfit

Promote at most one frozen variant per idea. Freeze parameters and decision thresholds before viewing held-out cache-heavy replay and load transitions. Use at least five randomized paired blocks, increase toward ten only under a predeclared budget if intervals remain wide. Each confirmation cell should collect enough steady-state requests to estimate tails; target >=1000 completed requests per arm per block or extend duration within budget. A p99 based on too few tail samples is inconclusive.

Bootstrap paired **blocks**, not individual correlated token gaps, for a95% interval on relative goodput/cost and tail effects. Report each block and all attempted variants. Do not stop on the first favorable noisy repeat. If several candidates are promoted from screening, use an untouched final confirmation dataset and adjust family-wise comparisons or label exploration rather than claiming confirmatory significance.

Proposed promotion rule: point estimate >=5% strict-goodput gain at a saturated matched cell, lower95% interval >0, no >2% p95/p99 latency regression on declared guard workloads and no correctness/quality regression. Alternatively accept a predeclared >=5% fixed-load tail reduction with matched goodput/cost. These margins are engineering choices, not predictions. If guard intervals are too wide to establish non-inferiority, classify inconclusive. Do not average away per-workload regressions.

For sustainable capacity, require stable queue/backlog time series, full accounting of scheduled requests, >=99% completion (a proposed design guard), no unexplained errors, and no worsening client replay degradation. Measure post-load drain and backlog. Repeat the highest passing arrival point; an isolated run is not a capacity certificate.

## Required machine artifacts

Each evaluated variant must produce:

- `resolved-baseline.json`: all source/image/model/workload/scorer identifiers, launch args, hardware and conditions.
- `patch.diff` and build log; compiler/kernel cache keys and any backend selection diagnostics.
- `plan.json`: hypothesis/global ID, frozen policy ID, treatment and controls, parameter search bound, random seeds, stages, budgets, outcomes and stop rules.
- `requests.jsonl`: unique request ID, scheduled/sent/first-token/last-token times, token count, errors, SLO verdicts, prefix class, assigned replica/rank; token/chunk timestamps in an associated stream log.
- Metrics time series: pending/running queues, per-rank token load, cache hit/miss counters, graph replay/fallbacks, GPU memory/SM/communication, accepted/drafted/verified tokens when available.
- `metrics.json`: units, denominators, window definitions, raw and both named goodputs, all latency cohorts, allocated cost, paired confidence intervals and every guard result.
- `decision.json`: `supported_for_scope`, `invalidated_for_scope`, `inconclusive`, `execution_error`, `already_present` or `blocked_baseline`, with explicit reason and artifact hashes. Map only actual completed measurement conclusions to the memory's test-result verdicts; baseline uncertainty is not an experimental falsification.

## Memory integration

The consolidated experiment bundle references original global hypothesis IDs, policy and source artifacts. Register accepted and deferred designs as **planned** with `hypothesis.plan_test`; planning does not override their selection status. Keep initial source/baseline inspections as prerequisites for deferred candidates. Execution agents later call `start_test` and record artifact-backed `test_result` with scope and evaluator identity. Repetitions and changed baselines receive separate test IDs; never overwrite earlier negative results.
