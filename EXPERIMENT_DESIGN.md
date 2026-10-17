# Qwen serving autoresearch: executable experiment contract

**State, 17 October 2026:** the executable vertical slice has passed real two-load B0 and Dockerized MTP1 pilot measurements with complete request accounting. The sensitivity pilot has one repeat; the negative control and representative mixed/session/semantic suite remain unqualified. No autonomous campaign or production representative result has been produced. The immutable rsynced handoff remains in `inference-autoresearch-handoff/`; executable code and campaign revisions live outside it.

## The question and authority boundary

Find reproducible serving-configuration tradeoffs for the pinned Qwen3.8-27B model on one RTX PRO 6000 Blackwell. AIPerf supplies/replays requests and exports measurements; vLLM serves the model. The Codex proposer chooses only admissible **vLLM settings**. The controller owns inputs, arrival schedules, model/runtime pins, validity, GPU lifecycle, metrics, budgets and promotion. AIPerf request rate and client concurrency are evaluator inputs, never candidate settings.

The primary vector is completed output tokens/s **up**, request TTFT p99 **down**, request TPOT p99 **down**. Report p50s, completion/error/censoring, dispatch lag, queue/backlog, eligible denominators and uncertainty. There is no invented SLA or weighted score. A frontier groups only compatible workload, cache and measurement protocols; exact-load conditional views are separate. Baseline B0 appears in every comparison.

## Frozen suite policy

| Family | Current evidence | First implementation use | Required before real search qualification |
|---|---|---|---|
| Short chat | Frozen 154/192 request schedules at 2.56/3.2 requests/s; exact asset hashes and 20 measured cells | Real diagnostic end-to-end fixture and regression control | Keep it diagnostic; longer tail windows before a p99 claim |
| Mixed prefill/decode | `Deepseek_serve` supplies synthetic-mixed and mixed-bursty YAMLs; 30-request mixed realization at 0.5 requests/s | Build a frozen diagnostic card, then measure its own B0 load curve | Source-backed shares or a declared target deployment mix, Qwen realization and B0 calibration |
| Session growth/reuse | Qualified bounded TraceLab split and two-turn native replay; reconstructed text and missing achieved cache-hit counter | Build recorded-history card with explicit source limitations | Complete session asset, achieved reuse/cache protocol, realistic offered population and B0 calibration |
| Semantic check | Qualified SpecBench split; five native prompt replays | MTP smoke/correctness and natural-output checks | Meaningful, non-leaking prompts and output/quality policy |

The mixed-bursty file is a stress check for finalists; it does not inherit the smooth mix's load rate. The held-out split is evaluated after search and not shown to the proposer. The supplied synthetic mix's 45/20/15/20 weights are **not production measurements**. If no deployment mix is available, results stay explicitly scoped to an engineered diagnostic mix. Do not silently relabel it representative.

## Baseline and common loads

The exact B0 is the feasible stock vLLM configuration: BF16, TP1, 40,960 context, sequence cap 512 because stock 1024 failed boot, token budget 8192, GPU memory fraction 0.92, prefix cache on, chunked prefill on, MTP off and CUDA graphs on. Resolve effective defaults from the running pinned image rather than inferring them from omitted command-line flags. The image, model revision, GPU UUID and initial proposed domain are pinned in `configs/campaign.json` and `configs/search-domain.json`.

For each family, validate payloads, scheduled versus actual dispatch, server-tokenized lengths, output policy, cache preparation and raw request completeness. Warm on disjoint inputs; define cold/prewarmed/burn-in behavior per card. Calibrate sustainable B0 load with bounded repeats and stationary completion/backlog checks. Freeze one common absolute screen rate and a finalist ladder initially at 60/80/100/120% of that family's B0 reference. The candidate sees exactly the same offered schedule and content as B0; it never gets its own favorable rate. At underload, throughput is demand-limited; latency may be the observable benefit.

Short screens are provisional. Confirmation requires matched repeated windows, at least an initial 1,000 eligible-request target and a declared interval-precision/cost rule; hitting the count alone does not certify p99. Count every planned request, including not dispatched and dependency blocked requests. A run with rising backlog cannot claim sustainable capacity merely because it eventually drains.

## Conditional search domain

`configs/search-domain.json` keeps B0 values inside the domain and admits sequence cap, token budget, memory fraction, prefix cache, native MTP depth, and verified chunked-prefill controls. It is a set of **conditional candidates**, not an assumed feasible Cartesian product. Boot, exact resolved setting, observed concurrency, memory pressure, reuse, MTP acceptance and active prefill contention decide whether a contrast is meaningful. Unsupported or inactive axes remain recorded. CUDA graph controls, offload, precision and source/kernel edits require separate evidence and versioned amendments. No domain change rewrites old campaign history.

The evaluator-owned sensitivity pilot is frozen in `configs/pilot-plan.json`: two matched B0 repeats per load, MTP1 as a binding mechanism probe, and sequence cap 64 as a predeclared inactive-axis control. Each contrast is evaluated on both short-chat loads with a fresh server per cell. The MTP contrast needs measured acceptance and an effect outside B0 repeat variation; the control needs zero queue and a flat result. Real autonomous search opens only when a qualification report also links representative mixed/session/semantic workloads, tail evidence and a frozen active domain. The existing manual MTP result is enough to motivate this pilot; it does not qualify real search.

## Harness and observable results

1. `doctor` records hardware, pins, Docker/GPU access, model files, AIPerf and Codex availability. No mock evidence becomes a real result.
2. `characterize` and `prepare` record source audit, card, exact payload/schedule/dependency hashes, transformations and expected mechanisms. Native AIPerf loaders/replay are reused where verified.
3. `baseline` and `pilot` run one GPU lease at a time. Each cell stores exact Docker argv/effective settings, request records, AIPerf exports, server logs/metrics, GPU telemetry, startup/warm/measure/drain costs, validity labels and diagnostics.
4. `search` gives one isolated Codex CLI proposer a frozen instruction file, schema-constrained proposal format and a filesystem research workspace. The prompt points to paths; the proposer selects which staged, hash-checked source and non-held-out measurement files to inspect and can write a short `notes.md` for the next attempt. The controller validates and runs its proposal. Failed Codex calls are failures, not random-search fallbacks.
5. `report` writes per-load and per-family Pareto fronts, B0/candidate load curves, per-class mixture tails, completed/failed counts, queue/drain, uncertainty and cost. All proposals, dominated points and failures remain in the ledger. Resume never duplicates a completed candidate/replicate.

Only the controller can run Docker/AIPerf or alter experiment state. The proposer can browse its staged research files with shell tools and write only its current notes; earlier attempts, source evidence and measured results are read-only. The Docker container has no GPU, Docker socket or host repository mount. The single procedural instruction is `agent/SKILL.md`; reference material and evidence are versioned inputs rather than mutable instructions. The ledger and prior notes provide same-campaign memory. Curated cross-campaign lessons, automatic observation fulfillment and controlled profiling remain unimplemented.

## Iteration cost and inspection

The real two-cell B0 evaluation took 966.5 seconds; the two-cell MTP1 evaluation took 865.6 seconds. The present `fresh-server-cell-v1` protocol boots a separate model server for each cell. New evaluations record wall time for tokenizer preflight, server start, warmup, benchmark, result processing and server shutdown in `evaluation-timings.json` and each cell's `timing.json`. `iar inspect` regenerates `inspection/INDEX.md` and `index.json` from the ledger with evaluation, feedback and artifact paths; raw request, AIPerf, server and GPU files remain available under their original run directory.

An optional one-scenario triage stage can reject invalid or overloaded candidates before the full two-load screen. It has a separate matched B0 and protocol identity; its point estimates are provisional and cannot satisfy full-screen or qualification evidence. The current campaign has **not** opted into triage. This gate chiefly saves time on failures. Faster ordinary iterations require a separately validated same-server bundle or cache-reset protocol with a new matched B0; no such protocol is currently qualified. Do not compare results across the old and any future protocol as if they were matched.

## Inspection sequence

| Checkpoint | Inspect before proceeding |
|---|---|
| A. Executable vertical slice | A frozen short-chat card/hash, resolved B0 and MTP settings, one complete real or clearly labeled mock cell, raw accounting, logs and exported comparison |
| B. Workload readiness | Mixed and session cards, source-to-target realization, B0 curves and cache/semantic validation |
| C. Scientific gate | Repeated baseline and sensitivity report, active conditional domain, suite revision and explicit qualification verdict |
| D. Bounded agent run | Proposal/evidence audit, safe lifecycle, provisional Pareto report, costs and restart behavior |
| E. Confirmation | Matched finalist/B0 repeats and untouched held-out results with tail uncertainty |

Progress labels are distinct: code implemented, mock tested, traffic validated, pilot qualified, autonomous campaign executed and improvement confirmed. A failed or flat scientific gate can still leave a useful evaluator and report.
