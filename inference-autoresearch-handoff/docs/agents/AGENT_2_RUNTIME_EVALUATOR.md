# Agent 2 — Runtime and evaluator implementation assignment — v0.2

Read the v0.2 execution requirements below together with the retained detailed implementation guidance. DECISIONS.md and INTERFACES.md are authoritative.

Read `DECISIONS.md`, `docs/INTERFACES.md`, and `contracts/` before implementation. Frozen decisions and root-owned contracts take precedence over examples here. This is an implementation brief, not evidence that the model, flags, container, or hardware have already been validated. Build the execution and measurement authority that allows the search agent to experiment without redefining success.

## v0.2 execution requirements: observability and sensitivity qualification

1. Implement Evaluator.pilot and Evaluator.observe in INTERFACES. A pilot is evaluator-owned and predeclared; adaptive search cannot redefine its workload or choose favorable loads. Use fake characterization/cards/adapter results to build independently of Agent 1.
2. Extend capabilities with available resolved defaults, queue/running/batch metrics, prefill/decode scheduled-token summaries, memory/cache/preemption/recomputation, graph behavior and speculation acceptance/progress. Record source, unit, frequency and availability. Never fabricate per-step counters from coarse aggregates.
3. Observe kinds include read-only summaries from saved evidence and optional targeted profiling. Profile only under the runtime GPU lease, outside timed cells, with budget/overhead/logs and a verified tool/backend. Missing profiler support does not invent a zero-overhead profile or block ordinary measurements.
4. Pilot B0 repeats and supported parameter contrasts across ordinary/near-capacity representative regimes plus inactive diagnostic controls. Add a small number of justified 2×2 interactions. Record actual config change, binding evidence, metric delta/interval, sample sufficiency, drift and cost. Do not impose an arbitrary 5% threshold.
5. Classify axis×regime sensitive, inactive-under-tested-conditions, unsupported or inconclusive. A flat small pilot is not global proof. Search qualification requires real workload/source/realization/B0 evidence and at least one plausible reproducible parameter effect; it does not require beating defaults. Flat/inconclusive/blocked results produce a report and versioned recommendations, never an automatically harder input.
6. Coordinate WorkloadCard validation and QualificationReport with Agents 1/3. Reject mismatched environment/domain/suite or mock qualification in real search. `evaluate --stage pilot` remains available to investigate a failed gate. Do not confuse software implementation-complete with sensitivity-qualified.
7. Forced output and natural EOS have different checks. Dependent traffic records eligibility/ready times and realized histories, session-start load units and supplementary session completion. Support cold, prefix-prewarm and representative burn-in protocols with explicit reset and cost.
8. Add tests for inactive counters, insufficient evidence, false qualification from mock/stale reports, flat pilots, valid improvements/tradeoffs, profiler separation, natural outputs and session delays. Preserve the lifecycle/accounting checks below.

Deliver capabilities, realized configuration evidence, telemetry dictionary, sensitivity/qualification reports and exact run costs. Agent 3 owns nondominance and structured feedback; you supply measurements, validity and mechanism evidence availability.


## Ownership and boundaries

Own `src/inference_autoresearch/runtime/**`, `src/inference_autoresearch/evaluation/**`, `deploy/**`, `tests/runtime/**`, and `tests/evaluation/**`. Do not edit another agent's modules, shared DTOs, schemas, `pyproject.toml`, or integration wiring without coordination. Propose contract amendments to Agent 3, the integration owner, before implementing divergent signatures. Provide dependency requirements to Agent 3.

Agent 1 owns immutable workloads and the AIPerf adapter. Agent 3 owns candidate generation, persistence, CLI, reports, and campaign orchestration. You own process lifecycle, exclusive GPU access, feasibility checks, baseline calibration, evaluation staging, correctness/measurement decisions, and evidence returned to the archive. Codex proposes experiments; your evaluator decides what their results mean. The evaluator must never allow a proposed candidate to modify workload definitions, arrival schedules, task settings, or validation rules.

Implement these public APIs exactly as specified in `docs/INTERFACES.md`:

- `RuntimeManager.inspect_hardware() -> HardwareManifest`
- `RuntimeManager.start(config, output_dir) -> ServerHandle`
- `RuntimeManager.stop(handle)`
- `Evaluator.evaluate(candidate, scenario_ids, stage) -> EvaluationResult`

Consume Agent 1's `BenchmarkAdapter.run_cell(...) -> CellResult`; preserve its raw artifacts rather than replacing them with summaries. Use root-defined DTOs and schema versions. This brief does not establish alternative field names or return types.

## Build order and independent development

First implement mock lifecycle, validation, evaluator states, and artifact capture. Next implement the Docker backend and hardware doctor. Then connect the AIPerf adapter, calibration, staged promotion, and paired confirmation. Work against a local fake implementing the shared benchmark protocol until Agent 1's adapter is ready. Agent 3 should be able to call your mock evaluator before Docker or GPU access exists.

The fake adapter must support configurable outcomes: healthy completion, slow but valid service, startup failure, wrong token lengths, client dispatch lag, timeout/censoring, and an intentional cache-off candidate with zero cache hits. It must write contract-compatible raw request records and return a `CellResult`. Use deterministic fixture values, not artificial claims of inference performance. Keep fixtures inside your test paths; return real DTOs at the boundary.

## Hardware doctor and immutable execution environment

The target is one NVIDIA GPU described only as approximately 86 GB available. Do not infer its model, architecture, or FP8 support from that figure. Doctor records GPU name, UUID, compute capability, physical and available memory, MIG status when applicable, driver, container runtime, Docker GPU support, and competing GPU processes. Record host RAM and free artifact/weight-cache disk space. Emit actionable diagnoses without automatically killing another process or changing the machine's driver.

The model is `Qwen/Qwen3.8-27B`, a dense hybrid-attention target. It is not Flash-Next. Pin and record the actual vLLM image digest, package/commit, CUDA runtime, model revision, tokenizer revision, and template hash. A supplied model or image reference must resolve successfully before a real run; never substitute a similar checkpoint silently. Discover CLI/config support from the pinned image rather than assuming current documentation matches it. AIPerf is an external traffic driver, not a hardware simulator.

Create a configurable Docker launch template under `deploy/`. Use explicit model/cache/artifact mounts, configurable host port and shared-memory settings, and deterministic environment capture. Grant only required GPU access. Keep credentials out of saved commands and logs. Pin dependencies; do not install latest packages during every launch. Model downloads and compilation caches persist across candidates. Their identities belong in the execution manifest.

## Baseline and feasibility

B0 is normal vLLM performance defaults plus the fixed task requirements from `DECISIONS.md`. Do not turn a hand-tuned configuration into the default baseline. B1, if requested, is an independently labeled applicable 27B recipe configuration; unsupported settings produce a diagnosis rather than an invented equivalent. Resolve implicit defaults and canonicalize configuration aliases so Agent 3 can deduplicate equivalent candidates.

TP stays 1. Initial weights and KV precision remain fixed. Fix text/reasoning/parser behavior and the provisional total context limit of 40,960. Verify that the document case counts 32,768 total input tokens including the template, plus 512 output tokens within the supported limit. Never truncate workloads, lower context length, change quantization, or disable requested semantics to make a candidate start.

Preflight each declared serving parameter against the pinned image and model. Validate numeric domains, conditional speculative settings, graph capture compatibility, and any known memory constraints. MTP values are conditional on actual support; zero omits speculative configuration. Reject unsupported combinations with evidence. If a domain is only partially feasible, publish the exclusions and effective domain before search; do not silently skip candidates or remove failed dimensions from reports. Distinguish an unsupported setting from insufficient memory on this hardware and an unexplained launch failure.

## Transactional GPU lifecycle

One controller owns the GPU at a time. Acquire a process-safe GPU lock keyed by GPU UUID before starting a server or beginning calibration. The lock records campaign/run identity, host, PID, heartbeat, and owned container IDs. Startup is transactional: reserve ownership, create labeled container, capture logs, wait for readiness with a bounded timeout, run smoke tests, then return a healthy handle. Any failure captures evidence and cleans up owned resources before releasing ownership.

Do not use broad `docker stop` patterns. Stop only the container/process identified by the handle and ownership record. Stop is idempotent. Graceful shutdown has a deadline followed by owned-process termination and verification that allocations are released. Handle SIGINT, SIGTERM, evaluator exceptions, and benchmark failure through the same cleanup path. Keep a heartbeat while a long benchmark runs. Do not steal a lock solely because a short heartbeat delay elapsed: check process/container identity and liveness, and record stale-lock recovery.

On resume, reconcile persisted intent with live processes. Reuse a surviving server only after verifying configuration hash, model/runtime identity, readiness, and cache reset protocol. Otherwise clean up owned stale resources and relaunch. Never treat an interrupted cell as completed. Unowned GPU use blocks measurement with a diagnostic. Retain cleanup failures explicitly; do not launch a second candidate into uncertain GPU state.

Capture the requested command, sanitized environment, normalized resolved configuration, startup duration, memory after loading, server logs, and software/hardware fingerprint for every launch. A CLI command alone is insufficient evidence because runtime defaults can differ.

## Functional and quality gates

Before performance measurement, test readiness and streaming; reconcile output controls with actual generated token counts; probe required parser/tool/reasoning formats using a separate semantic smoke workload. A valid tool call with empty ordinary content is not an empty response. Mechanical performance tests use the frozen non-thinking behavior. Semantic reasoning probes must use enough output budget to complete their expected structure.

Reject crashes, corruption, malformed required fields, unexpected empty responses, and incorrect enforced output lengths. CUDA graph fallback or explicitly selected eager execution is performance behavior unless graph execution is an explicit campaign requirement. Do not label every fallback a correctness failure. Log graph overflow/crash signatures separately.

A short smoke test cannot establish model-quality equivalence. V1 freezes precision and functional settings. A new precision/backend branch requires a larger qualification suite before eligibility; coordinate the quality-suite contract with Agent 3. Cache qualification results by the relevant runtime/model/precision identity, while retaining launch smoke checks. Never claim that passing parser probes proves semantic quality.

## Cell execution and cache preparation

Launch once per candidate and amortize startup across its assigned bundle. Warm compilation/execution with disjoint prompts. Then ask the adapter to reset cache state and execute the prescribed cold or warm prefix protocol. For warm scenarios, prewarm only intended shared prefix groups; never warm complete timed requests. Recorded/independent traffic must match its immutable payloads and absolute schedule. Dependent traffic must follow its frozen dependency policy and retain realized histories/times. Adapter ownership includes tokenization, namespace/group construction, reset validation, and exact request replay; runtime supplies supported reset/restart capability and captures overhead.

This model has hybrid recurrent state, so do not assume classical full-attention prefix behavior. If reset is unsupported, use a verified restart/reinitialization path and record its cost outside measured latency. A cache-off candidate may legitimately achieve fewer hits on the same workload. Mark contamination or incorrect construction invalid; keep genuine cache-capacity/policy disadvantages as valid performance observations.

Collect server-side metrics for memory, cache usage/hits, scheduling/preemptions, graph behavior, and speculative acceptance when supported. Annotate unavailable metrics explicitly. Missing optional telemetry is not a silently fabricated zero. Keep lightweight telemetry on normal screens; targeted profiling is a bounded optional diagnostic action when needed, separate from timed performance cells; unsupported profilers are reported.

## Measurement authority and staged budgets

Return distinct states/reasons for functional failure, unsupported/infeasible configuration, interrupted run, measurement failure, valid overload/regression, provisional result, and confirmed result using the root contract. The evaluator controls eligibility and measurement status. Search/archive code computes nondominance; do not conflate a valid result with a winner. The primary three-dimensional archive groups a fixed workload/cache/protocol across the evaluator-owned common load ladder; each operating point is (configuration, load scenario). Return exact load identity so reports can also make conditional comparisons at identical offered load. The agent cannot invent a lower load to obtain a better latency point.

Cheap screens use the declared 60–120-second budget and fixed representative scenarios. Expanded screens cover the designated suite. Finalists receive repeated confirmation and the common load ladder. Respect campaign wall-clock/GPU budgets before starting a stage; return budget exhaustion with completed evidence rather than silently shortening the evaluation. Reuse launches where allowed, not measurement records whose scenario/runtime identity differs.

TTFT/TPOT p50 and p99 and aggregate output tokens/s are mandatory. Consume the pinned adapter's documented token/chunk accounting; verify server counts and record accounting limitations. TPOT p99 is across per-request averages, not individual token gaps. Keep scheduled-to-first-token, actual-dispatch TTFT, schedule lag, offered/admitted/completed requests, errors, and backlog so client delays cannot disappear. Do not average percentiles across repetitions. Preserve raw records for pooled estimates and per-run values; correlated uncertainty requires time-block/session-aware resampling.

Duration-limited runs require an explicit drain/deadline. Account for every dispatched request: completed, error, timeout, canceled as prescribed, or censored. Pending slow requests must not vanish from latency metrics. If tails are not identifiable because of censoring, label them accordingly; do not present successful-request p99 as an unconditional tail guarantee. Low sample count makes p99 provisional even if the point estimate looks favorable.

## Calibration, load curves, and confirmation

Implement baseline-only calibration with predefined bracketing, repeated durations, completion/stability criteria, and queue-growth checks. The policy comes from immutable campaign settings. Stop with diagnostics if sustainable baseline capacity cannot be identified; do not invent a rate. Freeze absolute schedules after calibration. Initial cheap search uses 80% of the scenario's baseline capacity; finalists receive the same 60/80/100/120% baseline-relative ladder. Coordinate any mixed-workload calibration and scenario mapping explicitly rather than applying one request rate to unrelated length distributions without definition.

At 80% load, throughput can be demand-limited and nearly equal across candidates. That is expected: latency improvement remains measurable. Full operating curves identify capacity differences later. At 120%, growing queue/dropped work may represent valid overload, while a saturated load generator is a measurement problem. Distinguish these using schedule lag, achieved dispatch, server backlog, and completion accounting.

Confirm promising configurations with repeated incumbent/candidate or baseline/candidate blocks under identical scenario/cache protocols. Alternate order where feasible, retain per-run records, and report drift. Borderline p99 changes require more evidence, not arbitrary weighted scores. Root owns frontier representation and uncertainty reporting; supply the required evidence and reproducibility status.

## Acceptance criteria and handoff

CPU-only tests must prove exclusivity; idempotent cleanup; stale-run recovery; resolved-default capture; early infeasibility diagnosis; output validation; correct cache preparation ordering; legitimate zero-hit cache-off handling; valid overload versus client failure; request accounting with censoring; provisional p99 handling; budget stops; and fixed-rate calibration outputs. A mock paired comparison must demonstrate identical traffic identities on both sides.

Real-backend acceptance requires doctor output, pinned launch evidence, B0 smoke success, one complete benchmark cell with raw records, verified cleanup, and a calibration attempt with either measured results or an explicit blocker. Never describe CPU mock success as GPU readiness. Supply Agent 3 a short integration note listing public APIs, dependency additions, required environment/config values, mock invocation, real smoke procedure, and unresolved hardware/model compatibility. The complete experimental setup must fail visibly and diagnostically whenever a required capability is unavailable.


## Paste-ready implementation prompt

Read and execute the v0.2 requirements at the top of this brief, not only the detailed module requirements.

> Implement Agent 2 using this complete brief and canonical DECISIONS.md, docs/INTERFACES.md and contracts/. Own Docker runtime, hardware/flag qualification, GPU lifecycle, telemetry and evaluator only. Use the injected mock benchmark adapter until Agent 1 is ready. Implement feasibility, functional gates, cache preparation coordination, full request accounting, baseline calibration, staged evaluation and repeated confirmation. Do not change fixed workloads or task semantics. Keep one GPU lease, clean up owned servers, preserve all outcomes and provide mock/real acceptance evidence for Agent 3.
