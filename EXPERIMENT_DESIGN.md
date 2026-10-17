# Qwen serving autoresearch: executable experiment contract

**Next protocol proposal (18 October 2026):** [Evaluation v2](EVALUATION_V2_PLAN.md) defines the staged evaluator, exploratory/adaptive load curves, independent test, expanded serving domain, and agent evidence changes for review. This file remains the contract for the existing fixed-four campaign until a new version is implemented and qualified.

**State, 17 October 2026:** the earlier two-load short-chat vertical slice passed real B0 and MTP1 pilot measurements. The current `qwen38-27b-ops4-v1` study is calibrating and freezing four synthetic tasks before its own fresh-server B0. No autonomous four-task candidate result or production representative result has been produced. The immutable rsynced handoff remains in `inference-autoresearch-handoff/`; executable code and campaign revisions live outside it.

## The question and authority boundary

Find reproducible serving-configuration tradeoffs for the pinned Qwen3.8-27B model on one RTX PRO 6000 Blackwell. AIPerf supplies/replays requests and exports measurements; vLLM serves the model. The Codex proposer chooses only admissible **vLLM settings**. The controller owns inputs, arrival schedules, model/runtime pins, validity, GPU lifecycle, metrics, budgets and promotion. AIPerf request rate and client concurrency are evaluator inputs, never candidate settings.

The primary vector is completed output tokens/s **up**, request TTFT p99 **down**, request TPOT p99 **down**, separately on each of the four tasks. Report p50/p90, completion/error/censoring, dispatch lag, queue/backlog, eligible denominators and uncertainty. There is no invented SLA or weighted score. The four-task configuration frontier uses all twelve coordinates; per-task exact-load fronts remain available. Baseline B0 appears in every comparison.

## Frozen suite policy

The pinned `ops_aiperf` input set is six synthetic YAMLs (chat, agent, code, document, mixed, mixed-bursty), three Mooncake windows (median, burst, cache-heavy), and Exgentic. Their source snapshots live in `configs/workloads/ops-aiperf-source/`. AgentX is excluded from this Qwen campaign: none of its 393 complete source trajectories fit the pinned 40,960-token context. The rsynced source remains unchanged.

The **fixed four-task v1 serving study** evaluates every proposed configuration on the same four exact schedules:

| Task | Input and intended mechanism | Campaign role |
|---|---|---|
| Short chat | 512 nominal input, 256 forced output; decode/queue | Every candidate |
| Agent | 8,192 input, 1,024 forced output, Qwen thinking on; long reasoning output | Every candidate |
| Long document | 32,768 nominal input, 512 forced output; long prefill/KV pressure | Every candidate |
| Smooth mixed | 45% chat, 20% agent, 15% document, 20% code; prefill/decode interference | Every candidate |

Calibration is in progress under `.artifacts/ops-b0/`. `configs/campaign-ops4.json` is the new campaign identity; it will not borrow old short-chat or manual-search outcomes. The exact four source-derived schedules require independent fixed-schedule replay, complete accounting and registry promotion before a real four-task B0 screen. Search starts only after that screen has a valid B0 on all four tasks. The first autonomous candidate may establish parameter sensitivity; the scientific grade is exploratory inference metrics, not a p99 SLA or production-representative claim. The supplied smooth mix's 45/20/15/20 weights are **not production measurements**.

The code, document, bursty mixed, three Mooncake windows and Exgentic profiles remain prepared outside this campaign. They do not gate the four-task research loop or enter its Pareto vector. AgentX remains excluded by context. The study holds model, GPU, image, output policy, four input bodies and arrival schedules fixed; only admitted vLLM serving settings change. Every result retains raw requests, server/GPU telemetry, per-task metrics, feedback and agent research notes. The report preserves per-task Pareto fronts and a four-task configuration frontier without averaging metric values across tasks. Natural-answer quality, dependent sessions and deployment representativeness are outside this four-task inference-metrics claim.

## Baseline and common loads

The exact B0 is the feasible stock vLLM configuration: BF16, TP1, 40,960 context, sequence cap 512 because stock 1024 failed boot, token budget 8192, GPU memory fraction 0.92, prefix cache on, chunked prefill on, MTP off and CUDA graphs on. Resolve effective defaults from the running pinned image rather than inferring them from omitted command-line flags. The image, model revision, GPU UUID and domain for this study are pinned in `configs/campaign-ops4.json` and `configs/search-domain.json`.

For each of the four tasks, validate payloads, scheduled versus actual dispatch, server-tokenized lengths, forced output, cache preparation and raw request completeness. Warm on disjoint inputs. Select one ordinary B0 point per task from its source curve, then freeze exact request bodies and arrival times. The candidate sees exactly the same four schedules and content as B0; it never gets its own favorable rate. At underload, throughput is demand-limited; latency may be the observable benefit.

These finite screens are provisional, especially for p99. Confirmation requires matched repeated windows and a declared uncertainty/cost rule. Count every planned request, including not dispatched requests. A run with rising backlog cannot claim sustainable capacity merely because it eventually drains.

## Conditional search domain

`configs/search-domain.json` keeps B0 values inside the domain and currently activates sequence cap, token budget, memory fraction, prefix cache, and native MTP depth. Chunked-prefill controls are recorded but inactive pending exact runtime and workload evidence. It is a set of **conditional candidates**, not an assumed feasible Cartesian product. Boot, exact resolved setting, observed concurrency, memory pressure, reuse, MTP acceptance and active prefill contention decide whether a contrast is meaningful. Unsupported or inactive axes remain recorded. CUDA graph controls, offload, precision and source/kernel edits require separate evidence and versioned amendments. No domain change rewrites old campaign history.

The earlier `configs/pilot-plan.json` and its MTP sensitivity test belong to the separate two-load short-chat campaign. The four-task campaign opens exploratory autonomous search after the exact four inputs are independently replay-validated and an eligible fresh-server B0 exists on each. Its first agent proposal can test parameter sensitivity. It does not claim a repeat-qualified p99 SLA, semantic quality, or representative production behavior.

## Harness and observable results

1. `doctor` records hardware, pins, Docker/GPU access, model files, AIPerf and Codex availability. No mock evidence becomes a real result.
2. `characterize` and `prepare` record source audit, card, exact payload/schedule/dependency hashes, transformations and expected mechanisms. Native AIPerf loaders/replay are reused where verified.
3. `baseline` and `pilot` run one GPU lease at a time. Each cell stores exact Docker argv/effective settings, request records, AIPerf exports, server logs/metrics, GPU telemetry, startup/warm/measure/drain costs, validity labels and diagnostics.
4. `search` gives one isolated Codex CLI proposer a frozen instruction file, schema-constrained proposal format and a filesystem research workspace. The prompt points to paths; the proposer selects which staged, hash-checked source and non-held-out measurement files to inspect and can write a short `notes.md` for the next attempt. The controller validates and runs its proposal. Failed Codex calls are failures, not random-search fallbacks.
5. `report` writes the all-four-task configuration frontier, per-task exact-load fronts, B0/candidate metrics, completed/failed counts, queue/drain and cost. All proposals, dominated points and failures remain in the ledger. Resume never duplicates a completed candidate/replicate.

Only the controller can run Docker/AIPerf or alter experiment state. The proposer can browse its staged research files with shell tools and write only its current notes; earlier attempts, source evidence and measured results are read-only. The Docker container has no GPU, Docker socket or host repository mount. The single procedural instruction is `agent/SKILL.md`; reference material and evidence are versioned inputs rather than mutable instructions. The ledger and prior notes provide same-campaign memory. Curated cross-campaign lessons, automatic observation fulfillment and controlled profiling remain unimplemented.

## Iteration cost and inspection

The earlier two-cell B0 evaluation took 966.5 seconds; its MTP1 evaluation took 865.6 seconds. Four-task wall time remains to be measured. The current `fresh-server-cell-v1` protocol boots a separate model server for each cell. New evaluations record wall time for tokenizer preflight, server start, warmup, benchmark, result processing and server shutdown in `evaluation-timings.json` and each cell's `timing.json`. `iar inspect` regenerates `inspection/INDEX.md` and `index.json` from the ledger with evaluation, feedback and artifact paths; raw request, AIPerf, server and GPU files remain available under their original run directory.

The fixed four-task campaign does not use a one-task triage shortcut: each admissible configuration needs all four measurements for the suite frontier. Early boot, accounting or overload failures stop a candidate. Faster ordinary iterations require a separately validated same-server bundle or cache-reset protocol with a new matched B0; no such protocol is currently qualified. Do not compare results across different protocols as if they were matched.

## Inspection sequence

| Checkpoint | Inspect before proceeding |
|---|---|
| A. Input load choice | Four source B0 curves, exact requests, queue/drain, prompt/output and cache observations |
| B. Frozen replay | Four complete independent AIPerf fixed-schedule cells, content hashes and `validated` cards |
| C. Four-task B0 | One eligible fresh-server screen per task, raw exports and explicit `iar qualify` verdict |
| D. First agent iteration | Isolated Codex proposal, all four matched candidate cells, research notes, complete-suite frontier and costs |
| E. Confirmation | Matched finalist/B0 repeats and tail uncertainty for claims beyond exploratory point estimates |

Progress labels are distinct: code implemented, mock tested, traffic validated, pilot qualified, autonomous campaign executed and improvement confirmed. A failed or flat scientific gate can still leave a useful evaluator and report.
