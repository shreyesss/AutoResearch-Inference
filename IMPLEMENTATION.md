# Implementation and execution runbook — v0.2

## Build target and authority

Implement an installable Python CLI `iar`, pinned vLLM Docker service, AIPerf adapter and noninteractive Codex proposer. This package supplies contracts and instructions only. No executable or measured result is included. DECISIONS.md governs scientific semantics; INTERFACES.md governs wire/API meaning.

Three builders work in parallel after Agent 3 publishes v0.2 DTO/protocol scaffolding and fixtures. Agent 1 owns workloads/benchmark; Agent 2 runtime/evaluation; Agent 3 search/storage/CLI/integration. Use dependency injection and fakes, isolated branches/worktrees, and coordinated contract amendments. Only one real GPU lease is active. Do not run the optimization proposer locally on the measured GPU.

```text
src/inference_autoresearch/
  contracts.py           # Agent 3 shared scaffold
  workloads/ benchmark/  # Agent 1
  runtime/ evaluation/   # Agent 2
  search/ storage/ cli.py # Agent 3
deploy/                  # Agent 2
tests/                   # mirrors ownership; integration Agent 3
```

## M0 — contracts and mock path

Implement schemas and DTOs including workload cards, characterization, variable-length/natural-output scenarios, sensitivity reports, structured proposals and feedback. The three bundled schemas are starting contracts; DTOs defined in INTERFACES must also be validated by the implementation. Enforce cross-field rules in semantic validation. Add deterministic mock evidence for active/flat/noisy axes, mixed traffic, dependency-blocked requests, invalid clients, functional failure, overload and interruption.

Complete mock `doctor → characterize → prepare → baseline → pilot → search → report`, plus explicit `evaluate`. All mocked traffic/statistics/timings are labeled. Demonstrate a known Pareto set and restart without duplicate submissions. Mock pilot qualification must not unlock real mode.

## M1 — qualify hardware, dependencies and task

Doctor discovers exact GPU/UUID/compute capability/physical and free memory, CPU/RAM/disk, driver, Docker GPU support, competing processes and Codex availability/authentication. Pin image digest, vLLM/AIPerf/Codex versions, checkpoint/tokenizer revisions and template. Record current power/clocks without changing shared-machine settings. Resolve stock B0 defaults and canonicalize omitted/equivalent flags. B1 is optional and separately labeled.

Probe the exact model's supported parsers, native MTP, context bounds, cache/reset behavior and graph/compile features. TP1/BF16 and fixed KV precision; max_model_len=40960 provisional. Do not fit the model by changing task semantics. Reuse weights and compatible compilation caches, with sound cache keys. Missing hardware/auth/model is an external blocker, not a mock success.

Publish capabilities.json and an installed AIPerf text-input inventory. For every exposed text workload/load option record spelling/aliases, type/unit/default/constraints, conflict groups, translation to our spec, and used/deferred/not-applicable status. Verify installed help/config/export against source; web docs alone are insufficient. Do not guess cancellation, distributions, retry or conversation behavior.

## M2 — characterize sources and construct workloads

`characterize` audits source release/schema/license and computes streaming/batched statistics on bounded selected data, with source identity and coverage. First support local immutable JSONL/Parquet inputs; optional download paths must preserve revisions and hashes. Do not require downloading an entire multi-billion-request dataset. If raw data is inaccessible, implement miner/fixtures and publish blocked status; do not label literature summaries as our mining.

Compute joint lengths, traffic-count quantiles, complete session structure, tool gaps, context growth/mutations and prefix/reuse/cardinality statistics. Preserve known source limitations: missing text, tokenizer differences, week-local block IDs, provider timing and boundary-cut sessions. Split sessions/time/shared identities into search and evaluation data. Exclude held-out outcomes from proposer context. Keep source outputs separate from the converted target workload.

`prepare` produces workload cards and immutable payload/topology/dependency assets. Retain the twelve mechanical controls, but real search must additionally have a documented mixed contention pack, session/reuse pack and semantic content for MTP. Choose representative proportions from data, not candidate gains. Stress controls have a separate role. Each card compares source and constructed distributions and records transformations/limitations.

Choose one recorded/independent replay path for initial implementation; support session dependencies and static recorded histories without requiring live tools. Freeze initial-state/burn-in policy. Natural-output and live-history scenarios have explicit distinct protocols; implementing live adaptive tool execution is not required. Metadata-derived semantic text is labeled synthesized, with original content source recorded separately.

Preparation is two-pass: content and calibration traces first; final absolute schedules after baseline calibration. A prepared scenario can be pending rate validation. Real timed evaluation requires concrete hashes, supported output mode and observed tokenization/timing validation. Reuse AIPerf's generator if its version and semantics fit; do not duplicate it without reason.

## M3 — validate traffic and baseline

Run a small real cell proving request preservation, streaming, usage, output controls, cache initialization, dispatch accounting and export parsing. Validate actual tokenized input distributions after templates, actual output behavior, offered-versus-achieved timing, prefix topology and session dependencies. Save validation.json, source-versus-target comparison and per-request records. Client throttling cannot silently become a lower server load.

Warm execution on disjoint inputs, then reset/reinitialize cache. Prefix-only prewarm is for the defined warm diagnostic protocol; cold stream and representative burn-in are distinct. Verify reset on the actual hybrid model. Record all preparation and startup costs outside timed latency. Namespace/reset between cells without destroying intended within-cell reuse.

Baseline-only bounded calibration brackets and repeats a sustainable reference rate using completion, client lag and stationarity. Explicit tolerances and maximum steps/time must be set before running. For sessions name the rate unit and offered population; preserve dependencies. On failure stop with diagnostics. Freeze common screen load 80% and finalist ladder 60/80/100/120%; these are initial configurable policies. Materialize final schedules through Agent 1, not a second builder.

## M4 — sensitivity pilot and scientific gate

`pilot` runs an evaluator-owned plan fixed before adaptive search. Start with B0 repeats, then supported perturbations chosen from the mechanism map in UNDERSTANDING.md at ordinary and near-capacity load. Include inactive controls and a few justified 2×2 interactions (for example token budget × mixed prefill/decode conditions, and MTP depth × concurrency). Freeze the exact chosen contrasts; do not enumerate the full space.

Compare metric deltas against repeated-run noise/drift, inspect whether the relevant limit binds, and report effect uncertainty. Missing counters or sample-insufficient p99s can make a conclusion unresolved. No universal percentage threshold. Label axis×regime results sensitive, inactive-under-tested-conditions, unsupported or inconclusive. Report whether source-backed representative workloads and diagnostics agree or differ.

Write sensitivity-report.json and qualification-report.json. A sensitivity-qualified real search requires validated representative inputs, B0 evidence, at least one plausible reproducible parameter effect and a frozen domain/suite revision. It does not require a gain over B0 or every axis to matter. If flat/blocked/inconclusive, close the pilot honestly; recommend further evidence or a versioned domain/workload amendment. Do not silently manufacture a favorable workload. Low-level `evaluate` remains available for investigator probes while `search` enforces the gate.

## M5 — bounded hypothesis loop

Implement one schema-constrained Codex proposer, launched in a separate process with bounded timeout. Verify installed CLI/auth. Preserve final JSON separately from event logs; use argument vectors, no shell command proposals. No silent fallback from failed Codex to random. Explicit mocks are distinct.

Controller prepares frozen mission, workload cards, capability/qualification reports, domain, frontier, recent results and remaining budgets. Read-only evidence retrieval is allowlisted by artifact IDs/source snapshots, with retrieval audit and bounded context. Proposer may request diagnostics through a controller action; profiling has its own finite budget, GPU lock and separate run, never changes timed protocol or counts as a clean performance cell.

Each candidate proposal includes parameters, parent IDs, hypothesis/exploration, metric/diagnostic predictions, tradeoff, falsification and evidence IDs. Runtime validates domain/default equivalence; evaluator gates correctness and measures. Feedback combines validity, matched-load deltas/uncertainty, diagnostics, mechanism interpretation and frontier state. Agent chooses another candidate using feedback, not a hidden scalar score. Multiple parents and nondominated tradeoffs are supported.

Start with about 12 distinct proposals and at most 3 expanded finalists; those are budget controls, not a sample-complexity claim. Pick up to 3 predeclared sentinels from the qualified suite, including a representative mixed/session regime. Do not select only easy shapes. Screen 60–120s, expand approximately 120–180s on a predeclared compact bundle, then repeat finalists/B0 on common loads. No requirement to run all twelve mechanical controls at every stage. Budget reserve for B0 repeats, final confirmation and held-out evaluation.

Final tail target starts at 1000+ eligible requests and at least 3 windows but needs an explicit uncertainty criterion; neither count nor duration guarantees p99 precision. Specify max runtime and mark inconclusive when unmet. Independent seeds/windows estimate generalization; within each matched recorded replay compare identical assets. For live histories compare a common policy and disclose realized-stream differences.

## M6 — memory, confirmation and reporting

Store append-only events and queryable SQLite records for sources, cards, runs, proposals, retrieved evidence, feedback and lessons. Atomic state/checkpoints enable resume. Workload/domain amendments create new campaign versions; never overwrite scientific history. Preserve all failures and dominated points. Equivalence deduplicates resolved configurations; intentional repeats have distinct evaluation identities.

Stable procedural skill does not self-rewrite after every trial. Store candidate ideas in the ledger and promote only scoped, controlled findings to retrieved knowledge, retaining counterevidence and runtime validity. Freeze a small operational/reference packet for v1. Same-run memory is active; cross-run lessons and external mined insight cards are separately configured and logged for later ablations.

Confirmed reports include per-workload/common-load and matched-load fronts, per-class tails for mixtures, baseline curves, actual request/completion counts, offered/realized traffic, missing observations, censoring/overload, cache effects, hypothesis outcomes, cost and uncertainty. Use raw records for quantiles; never average p99s. Evaluate final frozen candidates on held-out packs without feeding those outcomes back into the search campaign. If someone continues tuning after viewing them, version a new search and obtain a new holdout.

## CLI to implement

```bash
iar doctor --campaign examples/campaign.json --backend mock
iar characterize --campaign examples/campaign.json --backend mock
iar prepare --campaign examples/campaign.json --backend mock
iar baseline --campaign examples/campaign.json --backend mock
iar pilot --campaign examples/campaign.json --backend mock
iar evaluate --campaign examples/campaign.json --candidate examples/proposal.json --stage pilot --backend mock
iar search --campaign examples/campaign.json --backend mock --max-proposals 12
iar report --campaign examples/campaign.json --backend mock
```

These commands are the proposed interface, not installed tools. Real mode uses `--backend real` after doctor/source/traffic qualification; unset pins and example-only artifacts must fail. Support `search --resume`, verified campaign hashes and explicit proposer mode independent of evaluator backend. No unbounded integration campaigns.

## Deliverables and cost control

Required: campaign.lock.json; capabilities and input inventory; source audit/statistics/splits; workload cards and immutable content/schedule/dependency assets; realization checks; B0 calibration; pilot/qualification reports; proposals/feedback/retrieval audit/lesson records; resolved argv/settings; server/profile/telemetry logs; raw request and cell results; ledger/checkpoints; provisional/confirmed fronts; final report and completion note.

Stream data, cache characterization by source/config hash, reuse servers across compatible cell bundles and fail unsupported candidates cheaply. Reusing a launch does not permit cache contamination. Avoid heavyweight profiling by default. Charge startup, preparation, measurement, drain, profiling and proposer cost separately; wall-clock/GPU budget bounds the whole process. Source, hardware or authentication blockers do not prevent independent mock implementation.
