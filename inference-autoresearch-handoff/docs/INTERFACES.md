# Shared interfaces and data contract v0.2

Integration owner: Agent 3. All builders implement these contracts before adapting external APIs. The JSON files here are application contracts, not AIPerf configuration files. Amendments need a version change and coordinated example/test updates.

## Types and public APIs

Python package: `inference_autoresearch`. Place shared typed DTOs/protocols in `contracts.py` (Agent 3 scaffold); serialize versioned JSON with the names in this document and starter schemas. DTOs may use dataclasses/Pydantic, but the wire shape must remain stable. Path arguments are `pathlib.Path`; IDs are strings; timings in metric fields are milliseconds unless a `_s` suffix says otherwise. Adapter methods are synchronous at the public boundary; internals may use asyncio.

```python
class TraceCharacterizer:
    def characterize(self, spec: SourceSpec, output_dir: Path) -> CharacterizationReport: ...

class WorkloadBuilder:
    def build(self, spec: WorkloadSpec, output_dir: Path) -> ScenarioManifest: ...

class BenchmarkAdapter:
    def run_cell(self, server: ServerHandle, scenario: ScenarioManifest,
                 policy: MeasurementPolicy, output_dir: Path) -> CellResult: ...

class RuntimeManager:
    def inspect_hardware(self) -> HardwareManifest: ...
    def start(self, config: ResolvedServeConfig, output_dir: Path) -> ServerHandle: ...
    def stop(self, handle: ServerHandle) -> None: ...

class Evaluator:
    def pilot(self, plan: PilotPlan, output_dir: Path) -> SensitivityReport: ...
    def observe(self, request: ObservationRequest, output_dir: Path) -> ObservationResult: ...
    def evaluate(self, candidate: CandidateProposal, scenario_ids: list[str],
                 stage: str) -> EvaluationResult: ...

class Proposer:
    def propose(self, context: ProposalContext) -> CandidateProposal: ...

class SearchController:
    def run(self, campaign: CampaignSpec) -> CampaignResult: ...
```

Concrete evaluator implementations receive injected runtime, benchmark, ledger, frozen campaign and output-root dependencies at construction. They resolve scenario IDs through the prepared registry; proposals cannot supply paths or benchmark overrides. Agent 1 and 2 use contract-valid fakes rather than blocking on each other. Agent 3 owns dispatch and dependency wiring.

## DTO responsibilities

| DTO | Mandatory meaning |
|---|---|
| `CampaignSpec` | Frozen experiment ID, runtime/model/tokenizer pins, fixed task policy, search domain, baseline selection, workloads, evaluator load policy, budgets and proposer driver. Example is `examples/campaign.json`; unresolved pins are forbidden in real mode. |
| `HardwareManifest` | Device ID/UUID, name, compute capability, total/available memory, driver/CUDA/runtime versions, CPU/RAM, power/clock observations, Docker/GPU access and support probes. Unknown facts remain null with reasons. |
| `WorkloadSpec` | Source/card/suite role, joint lengths and output mode, prefix/session construction, seeds, tokenizer/template identity, cache protocol, traffic mode and immutable schedule or dependency policy. It is not a serving config. |
| `ScenarioManifest` | Content-addressed pack/schedule-or-dependency identity, workload card and source manifest, group key, explicit load unit/mode, expected counts, output/accounting policy and preparation instructions; see starter schema. Scalar lengths may be null for distributions. |
| `CandidateProposal` | Only allowed parameter overrides, parent IDs, hypothesis/exploration, predictions, falsification condition and evidence. No free shell command, model/precision replacement or workload mutation. See schema. |
| `ResolvedServeConfig` | Validated proposal plus fixed task policy plus concrete image defaults; exact argument vector, env allowlist, model pins, effective settings, config ID, feasibility evidence and restart cache identity. Never hash secrets. |
| `ServerHandle` | Runtime/session/container IDs, GPU lease ID, origin URL, config ID, log/metrics locations, readiness evidence. Does not contain credentials. |
| `MeasurementPolicy` | Stage, replicate, measurement window, drain/deadline, minimum eligible count, fixed-output expectations, cache preparation, allowed lag/completion tolerances and early-stop rules. Evaluator supplies it. |
| `CellResult` | One measured scenario/config/replicate with status, raw artifacts, complete counts, latency/throughput vector and diagnostics. See schema. |
| `EvaluationResult` | evaluation_id, config_id, stage, cell result paths/IDs, total startup/warm/measure/drain seconds, overall status, failure reasons, promotion recommendation and confirmation evidence. Functional failure may legitimately have zero measured cells. |
| `ProposalContext` | Frozen mission and compatible search domain, baseline/qualification and archive summaries, workload cards, past results/failure packets, structured feedback, uncertainty, budget, scoped lessons and available evidence references. No claim of hidden chain-of-thought logging. |
| `CampaignResult` | Campaign ID, stop reason, tested/proposed counts, baseline IDs, archive paths, pending/failed runs and reproducibility manifest. |

## Raw request record

One JSONL/Parquet row per planned request (or explicit not-dispatched terminal row) with: request_id, session_id if any, config/scenario/run/replicate IDs; scheduled arrival, actual dispatch, first relevant token, final relevant token and request-terminal times; timing origin/clock and nullable missing timestamps; input/total completion/reasoning/first-chunk token counts and counting source; finish reason; terminal state; HTTP/error/cancellation detail; cache-read tokens if available; output checksum; source raw-record pointer. Token counts must not double-count reasoning when usage completion already includes it.

Token/chunk correction follows verified support in the pinned AIPerf/server. Primary TTFT uses the first relevant content/reasoning event. TPOT numerator ends at the final relevant event; denominator excludes tokens in the first content chunk. If exact first-chunk count is unavailable, store `single_token_first_chunk_assumption` and retain a cross-check against full-response duration/usage. All-in-first-chunk outputs have no useful post-first-token TPOT: mark null and report eligibility. Reject an unqualified mismatch between timing interval and completion count rather than invent a denominator.

For independent/recorded open-loop replay, planned arrival timestamps are relative to one monotonic run start. For dependent traffic also retain predecessor IDs, ready-after-completion/delay timestamps, source timing, session/class/turn identifiers and dependency-blocked reasons; do not label policy-determined arrivals immutable timestamps. Client dispatch lag is diagnostic; export scheduled-to-first-token latency as well. Persist UTC run anchors for trace alignment, never subtract clocks on different machines as if synchronized.

## Throughput and counting

The canonical `output_tokens_per_s` is successful completed completion tokens (including reasoning once) divided by elapsed seconds from the declared benchmark start/first planned dispatch instant to the last terminal outcome among planned/dispatched requests, including drain/deadline elapsed. This is an effective finite-run measure. Also retain AIPerf active-window throughput, dispatch duration, drain duration, offered RPS, successful request/s and time-slice counters; do not swap denominators silently. Fixed common schedule and policy make this comparable; capacity/stationarity checks separately inspect the sending interval.

At normal final completion: planned = dispatched + not_dispatched; dispatched = completed + failed + timed_out + canceled. Completed excludes malformed and wrong-length records; preserve their token work diagnostically instead of inflating successful throughput. Intentionally canceled requests occur only in explicitly declared cancellation-specific scenarios. Natural-EOS completion is successful if the output-policy contract is met; exact-length checks apply only to forced mode. All counts nonnegative and checked, never silently inferred as zero. A stopped run may use `incomplete` with explicit missing outcomes; no confirmed frontier entry.

Latency percentiles use successful eligible requests; always disclose eligible/completed/failed counts. Nonzero failure or censoring requires a validity/overload verdict and cannot silently improve the frontier. By default primary unconstrained frontier admits only fully accounted, clean completed runs; valid overloaded but failed/censored points remain in the operating-curve report as infeasible points. Queue-growing finite overload observations are labeled non-sustainable even when all requests drain; do not use them to claim sustainable capacity.

## State and outcomes

- Persistent lifecycle: proposed → validated → starting → smoke → warming → measuring → draining → recorded. Failures and interrupted states terminate with an explicit reason. Persist transitions before external side effects where possible.
- `CellResult.status`: `valid`, `functional_failed`, `measurement_failed`, `incomplete`, `canceled`. Validity is not goodness; a slow configuration can be valid.
- `behavior`: `normal`, `overload`, `unknown`. Overload is server behavior, not automatically a measurement fault.
- `evidence_grade`: `provisional`, `confirmed`, `ineligible`.
- Run reason codes include unsupported_flag, incompatible_config, startup_oom, runtime_cuda_fault, invalid_response, wrong_output_length, client_lag, cache_contamination, request_accounting, insufficient_samples, timeout_censoring and interrupted. Preserve the original diagnostic.
- A `confirmed` grade belongs to an aggregated point backed by repeated cell results; a single cell does not become confirmed merely because it ran for a long time. Starter examples use provisional cells.

## Identity and frontier eligibility

Canonical JSON serialization (sorted keys, normalized numeric representations, no timestamps) plus SHA256 identifies effective serving configs; include fixed task settings/runtime/model pins. Omitted flags equal to resolved defaults must canonicalize to the same ID. Preserve both original override and normalized effective config.

Scenario IDs include request/schedule-or-dependency hashes, source/card/split, output/history mode and timing policy. For live-history protocols the identity is the fixed initial input/generation/dependency policy; realized stream hashes belong to the result and can differ across configurations. Workload-group IDs omit the common load-level factor but include workload content family/cache preparation/measurement protocol, so approved common-ladder points can share one primary archive. Different seed realizations can be combined only as declared replicates of the same fixed sampling protocol; retain constituent hashes.

Never combine cheap 60s and final 600s estimates without a protocol key. Exports include per-exact-load conditional frontier and approved cross-load primary frontier, with stage/grade filters. Ties retain provenance. Exact mathematical point-estimate dominance is implemented without arbitrary epsilon; optional practical-equivalence tolerance must be separately named/configured and may not overwrite the exact archive. Uncertainty-aware confirmation is a separate decision.

## Driver invocation

Version-pin Codex CLI and validate its installed help/schema support. The documented `codex exec --output-schema <schema> --output-last-message <file> -` pattern accepts a prompt on stdin; event JSONL is distinct from the final proposal JSON. Use an argument list in subprocess, a timeout and explicit exit-code/error handling. Never parse human prose into serving flags or silently replace unavailable Codex with random search. The mock/explicit random proposer is separate and clearly labeled. No proposer process starts/stops the inference server; only `Evaluator` can do that.


## v0.2 source, pilot and learning contracts

The implementation must define/validate these additional DTOs before parallel consumers use them. They do not imply additional files shipped in this starter package.

| DTO | Required fields and semantics |
|---|---|
| `SourceSpec` | source_id, release/URI/local paths, format/license/access status, hashes, selected time/session scope, tokenizer/block namespace, selection seed, missingness and field mapping |
| `CharacterizationReport` | report_id, status (mock/complete/partial/blocked), source hashes/coverage, reproducible query/config, joint-length/session/arrival/reuse/mutation/gap summaries, exclusions, split map/hash, limitations and raw summary artifact refs |
| `WorkloadCard` | card_id/hash, deployment question, suite_role, source/selection/split, source-vs-pack fidelity summaries, transformations/content provenance, output/history/arrival policy, expected mechanisms, realization report, limitations and readiness |
| `PilotPlan` | plan_id/hash, campaign/environment, workload IDs, fixed contrasts and negative controls, ordinary/near-capacity absolute loads, repeat/order/randomization rules, diagnostic requests, uncertainty interpretation, budget and stop rules |
| `SensitivityReport` | report_id/hash, plan/run IDs, axis×regime contrasts, resolved config differences, metric effect/uncertainty, binding evidence availability, classification, cost and limitations |
| `QualificationReport` | campaign/suite/domain/environment hashes, provenance/realization/baseline/sensitivity gate results, exact blocked/inconclusive reasons, active/inactive/unsupported axes, search_allowed boolean and evidence IDs |
| `ObservationRequest` | request_id, originating proposal/context ID, allowlisted observation kind, scoped run/config IDs and bounded requested cost. No arbitrary shell command or policy override |
| `ObservationResult` | request ID, status, measured/not-supported reason, artifact refs, overhead/cost and separate diagnostic-run identity |
| `ExperimentFeedback` | proposal/config/evaluation IDs, comparison scope, validity/reasons, per-scenario raw metric deltas and intervals, diagnostic observations/missingness, mechanism interpretation, archive membership, remaining budget and evidence IDs |
| `KnowledgeEntry` | lesson ID, hypothesis vs validated finding, claim, source trial IDs, hardware/model/runtime/workload/load scope, measured effect/uncertainty, counterevidence, validation status and revalidation/invalidation triggers |

`ObservationRequest.kind` initial allowlist: resolved_config, queue_batch_summary, token_budget_summary, cache_memory_summary, speculation_summary, graph_summary, targeted_profile. The controller can satisfy summary requests from existing artifacts without another run. Unknown/unsupported observations return an explicit reason. `targeted_profile` is optional capability, serialized through runtime with a separate finite diagnostic budget. It cannot silently replace a performance measurement.

Read-only evidence API: `EvidenceStore.list(context_id, filters) -> list[EvidenceRef]`, `EvidenceStore.read(evidence_id, max_bytes) -> EvidencePacket`. Scope by campaign/source permissions; preserve source revision/hash, evidence type and mock/real label. Do not accept arbitrary filesystem paths from proposals. Proposer context and controller audit retain retrieved IDs, packet version and permitted source snapshot. If online reference research is enabled, log URLs/revisions/content hashes and charge its budget; it is not implicit unlimited access.

`CandidateProposal` v0.2 retains hypothesis and expected_tradeoff strings and adds `experiment_kind` (hypothesis/exploration), `predictions` (short named metric/diagnostic expectations), `falsification_condition` and `requested_observations`. Predictions are testable expectations, not percentages claimed as fact. Exploration can use an explicit coverage rationale and an unresolved mechanism. All fields are final structured output; no private reasoning trace is required.

`CellResult` adds workload_class_summaries artifact, realized_stream artifact and mechanism_evidence rows: observation name/value/unit, availability (measured/unsupported/not_collected), artifact ID and interpretation scope. Per-class percentile aggregation is recomputed from raw requests. Keep optional sampling frequency/overhead in telemetry artifacts. An unavailable counter is null plus reason, not zero.

`ScenarioManifest` supports exact mechanical scalars or nulls with distribution files referenced in the card/payload. `output_policy` is forced_length or natural_eos; `traffic_mode` independent_open_loop, recorded_timing, or dependent_sessions; `history_mode` single_turn, recorded, or live. `offered_rps` is null for dependent scheduling unless explicitly defined as external request arrivals. `offered_load` plus `load_unit` (requests_per_s/session_starts_per_s/active_users) is the canonical load declaration. Dependency schedules preserve DAG edges and delays; all realized request bodies/times are saved. `cache_protocol` includes cold_stream, prefix_prewarmed and representative_burn_in with a prescribed policy.

Semantic validation beyond JSON types: forced_length requires length expectations in scalar/payload; natural_eos does not use wrong_output_length for early EOS; variable lengths require validated payload/card distribution; warm/burn-in requires preparation instructions; dependent_sessions requires session/dependency assets and a declared offered population/rate; source and card hashes/pins must be concrete in real mode. A validated traffic manifest is not by itself a sensitivity qualification. Search refuses absent/mismatched real qualification; low-level evaluate permits labeled pilot investigation.

## CLI extension and gate statuses

Public commands: doctor, characterize, prepare, baseline, pilot, evaluate, search, report. `characterize` and `pilot` are additions to v0.1. `evaluate --stage pilot` produces mechanism evidence without requiring search qualification. Stages remain separate in result/archive identity. Only search requires `QualificationReport.search_allowed=true`; real mode also verifies actual hashes/environment/backend. Never use a mock report to unlock it.

Campaign states: draft → sources_characterized → packs_prepared → traffic_validated → baseline_characterized → pilot_completed → sensitivity_qualified → searching → reported. These are evidence statuses, not a requirement to stop unrelated implementation work. Blocked/inconclusive/flat pilots can transition directly to a report. Real baseline and validation preparation may interleave under the two-pass schedule protocol. A report can state no gains without being a failed software delivery.

## Backward compatibility

This is a coordinated v0.2 amendment, not an instruction to accept v0.1 JSON silently. Migration must add explicit suite/source/output/traffic semantics and preserve originals; unresolved meaning remains pending. Effective config IDs need not change solely because the proposal adds explanation fields, but evaluation/campaign identities include every changed scientific policy. Never reinterpret an old result's protocol in place.
