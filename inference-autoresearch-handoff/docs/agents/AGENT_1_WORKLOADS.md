# Agent 1: immutable workloads and AIPerf benchmark adapter — v0.2

Read the v0.2 execution requirements below together with the retained detailed implementation guidance. DECISIONS.md and INTERFACES.md are authoritative.

## v0.2 execution requirements: source evidence and input realization

1. Implement TraceCharacterizer and source mapping for bounded local JSONL/Parquet slices, including FreeInference-style sessions and Mooncake-style traffic. Emit source audit, exact selection/hash, license/access, missingness, block namespace/tokenizer caveats and reproducible aggregate statistics. No mandatory full-corpus download. Unknown fields and blocked access remain explicit.
2. Compute joint lengths, 1s/10s/1m arrival-count summaries, session lengths/overlap, context growth/mutations, tool gaps and prefix reuse/popularity/cardinality proxies. Preserve dependence and document what cannot be recovered from metadata. Source provider timings are not automatically target think times.
3. Implement WorkloadCard and source-vs-selected-vs-target distribution comparison. Split complete sessions/time/shared identities into search/holdout; no tuning against held-out outcomes. Support suite_role representative/diagnostic/stress, distribution lengths, forced/natural output and independent/recorded/dependent traffic. Scalar shape fields can be null under the v0.2 contract.
4. Retain 12 mechanical construction controls. Build compact mixed prefill/decode and growing-session packs with data-backed proportions before real search; do not invent “representative” shares. Provide semantic content from a licensed documented source before declaring MTP transfer. Metadata-derived synthetic text is not recovered original content.
5. Inventory every installed text input/load control from AIPerf help/config schemas: exact name/aliases, type/default/unit, constraints/conflicts, our mapping and used/deferred/not-applicable. Include endpoints/templates/extras, content/length distributions, prefixes, arrivals, concurrency/worker limits, replay/synthesis transforms, sessions/users/delays/history, EOS, cancellations, warmup/reset, seeds and exports. Mark any unsupported retry/Weibull/dependency facility rather than inventing a flag. Review the built-in agentic-code generator first; validate assumptions before adoption.
6. Save content/topology/schedule-or-dependency assets and policy hashes. For live histories preserve the actual realized stream and do not promise identical future prompts. Initial delivery can implement recorded histories with dependency-aware timing; no actual tool execution required.
7. Realization checks compare actual post-template input/output behavior, LCP/reuse topology, arrival counts, achieved dispatch/lag and dependency timing against the card. A seed alone is insufficient. Expose source-mined, pack-built and traffic-validated as distinct readiness states.
8. Add tests for blocked/partial source ingestion, correlated fixture distributions, namespace collisions, split leakage, time-compression disclosure, natural EOS, dependent ready times, client caps and realized-stream changes. Keep detailed transport/counting tests below.

Deliver source audit/statistics, workload cards, installed AIPerf inventory/compatibility note, tiny immutable fixtures and realization reports to Agents 2/3. Request root DTO amendments through Agent 3. `characterize` may finish blocked on data while all mock/build work proceeds. Do not label mock statistics as empirical findings.


## Mission and boundaries

Implement the inputs and measurement transport for a serving-parameter autoresearch experiment. AIPerf sends traffic to an actual vLLM server; it is not a hardware simulator. Target one NVIDIA GPU, Qwen/Qwen3.8-27B, fixed BF16 behavior, and a pinned runtime. Your output must let other agents evaluate identical requests and arrival schedules against different serving configurations without accidentally changing the problem.

Read `DECISIONS.md`, `docs/INTERFACES.md`, and the root-owned versioned contracts before implementation. Their names, field definitions and units override illustrative names here. Implement these public interfaces exactly:

- `WorkloadBuilder.build(spec, output_dir) -> ScenarioManifest`
- `BenchmarkAdapter.run_cell(server, scenario, policy, output_dir) -> CellResult`

You own `src/inference_autoresearch/workloads/**`, `src/inference_autoresearch/benchmark/**`, `tests/workloads/**`, and `tests/benchmark/**`. Do not edit runtime, evaluation, search, storage, top-level CLI, deployment configuration or root contracts unilaterally. Agent 2 launches servers and judges validity; Agent 3 wires commands and persists/searches results. Submit required dependency additions to Agent 3. Propose contract amendments to the integration owner before using them.

All public DTOs are versioned and JSON serializable. Persist raw artifacts separately and reference them using paths and content hashes. No live clients, NumPy scalars or Python-specific objects in public records. Both APIs must work against CPU mock implementations immediately; do not wait for GPU access or another agent's implementation.

## Freeze inputs before evaluating candidates

For independent/recorded replay, implement immutable payload records plus immutable relative scheduled timestamps. For dependent sessions freeze incremental inputs/history mode, dependencies and delay policy; retain realized messages and timestamps separately. Candidate parameters must never affect pack construction. Seeds control input generation and schedules, not GPU execution determinism. Use separate seeds for content, prefix assignment and arrival generation. Persist generator version and tokenizer/model/template revisions.

The diagnostic mechanical shapes use exact total server-tokenized inputs and exact completion lengths. They are retained controls, not the finalized representative suite:

| Shape | Input tokens | Completion tokens |
| --- | ---: | ---: |
| Chat | 512 | 256 |
| Code | 2,048 | 1,024 |
| Agent | 8,192 | 1,024 |
| Document | 32,768 | 512 |

Produce each shape at intended prefix fractions 0, 0.50 and 0.75. These are twelve construction scenarios, not twelve guaranteed cache-hit measurements. Total inputs include message template and special tokens; do not append a template after counting. Fix thinking off for these mechanical packs. Endpoint, parsers, sampling, precision policy and output controls remain fixed across candidates. Use exact-output controls supported by the pinned endpoint, and validate actual completion lengths. `max_tokens` by itself is only a ceiling.

Mechanical random-text packs measure shapes, not realistic speculative-decoding acceptance. Also define a separate versioned semantic pack format for actual code, agent-style messages and documents. Preserve licenses/provenance and target shapes without asserting that arbitrary padding remains semantically representative. MTP finalists must be evaluated on those packs under their own group identities; do not merge their metrics with mechanical packs.

The provisional model limit is 40,960 total tokens. Check the actual serialized prompt plus completion allowance against this limit. Reject infeasible packs instead of truncating. Builder failure must identify the requested size, actual tokenizer result and revision. A tokenizer round-trip does not guarantee the serving template agrees; implement an integration check using the pinned server tokenizer interface or an equivalent documented runtime path. If unavailable, mark token-count verification pending and require Agent 2 to block real evaluation until validated.

Build enough unique requests for the full duration, largest scheduled rate, warmup and repetitions. Do not cycle a short prompt list when a run outlasts it. If exhausted, stop with a structured failure. Keep execution warmup inputs disjoint from all measured inputs.

## Prefix construction and cache preparation

Use an initial pool of 64 prefix groups for nonzero sharing. Persist each request's intended prefix group and expected common token count. Construct common prefixes and unique suffixes at token boundaries; validate actual longest common token prefixes after full formatting. Required template tokens impose a small unavoidable common beginning even for the 0% case: report that structural sharing and prevent additional intentional reuse rather than claiming literally zero identical tokens.

An intended fraction is a construction target; explain alignment and template effects in the manifest. Verify no unintended longer shared prefix appears within or between groups. Unique suffixes must differ early enough to avoid complete-prompt reuse, not just by a trailing request ID. A run/cell namespace must prevent prior cells leaking reusable prefixes. Preserve intended within-cell groups while changing namespaces for independent repetitions. Do not rely on adding an identifier after the shared portion to invalidate earlier cached prefixes.

Support two explicit cache protocols, never an implicit generic warmup:

1. Warm execution/compilation with disjoint inputs. Reset prefix state after that warmup. Prewarm only the intended prefix groups, then dispatch measured unique-suffix requests. Report prefix-prewarm traffic separately from measured traffic.
2. Warm execution, reset prefix state, then dispatch the measured stream with no prefix prewarm. Cache reuse develops naturally from that stream.

Coordinate reset/restart with Agent 2 through the interface contract. Verify that reset actually applies to this hybrid model's cache/state implementation. If reliable reset is unsupported, request a fresh server lifecycle and record that cost; do not assume a reset endpoint works because ordinary attention models support it. Prefix-only prewarm must use the same token prefix as the subsequent requests, with endpoint-required continuation handled and reported. Prove this using tokenized payloads. If exact prefix-only prewarm cannot be constructed, block that protocol rather than silently warming full measured prompts.

Cache-disabled candidates receive the same reuse opportunities and preparation request sequence. Lower achieved hits are a legitimate candidate outcome. Collect measured hits when exposed, but do not impose 50% or 75% achieved-hit equality as a validity rule.

## Arrival schedules and pack identity

For independent mechanical/recorded traffic, create a fixed open-loop schedule: request dispatch deadlines are prescribed independently of previous completion. Maintain absolute order/timestamps relative to cell start. Do not implement a fixed-concurrency loop as an unnoticed substitute. Max outstanding requests is a generator safety limit; reaching it must be visible as dispatch lag or missed dispatches, not suppressed demand.

Baseline-only capacity calibration supplies absolute rates. You generate schedules at those rates; neither the agent nor a candidate chooses its own rate. Initial cheap screens use one fixed baseline-derived rate per scenario. Finalists use common 60/80/100/120% baseline-rate schedules. Overload at 120% is expected evidence, not an automatic measurement failure. The evaluator decides the distinction between system overload and an inadequate load generator.

Support deterministic fixed spacing first and seeded Poisson arrivals as the first stochastic extension. Explicit schedules can represent bursts and recorded tool pauses; dependent sessions require dependency policies rather than only absolute timestamps. Do not claim every pattern is a built-in AIPerf flag. Save all actual timestamps, rather than only saving a seed and rate. Source manifests must distinguish single independent requests from dependent sessions; dependent recorded-history session replay is required; live adaptive tools are not.

Preserve both a workload-group identity and an exact load-scenario identity. A group fixes payload distribution, cache protocol and measurement protocol; the predefined load ladder supplies distinct scenarios within it. Agent 3 builds the primary throughput/TTFT-p99/TPOT-p99 operating frontier across that common ladder and conditional archives at each matched load. Your records must carry both identities. Never pool unrelated shapes, cache protocols or execution protocols into that frontier. At the cheap 80% point throughput may be demand-limited; report it faithfully rather than inventing an artificial capacity estimate.

A `ScenarioManifest` references versioned payload and schedule files, hashes, request counts, expected token lengths, prefix groups/cardinality, cache protocol, seed components, tokenizer/template identity and generation provenance. Its hash changes when any evaluator-relevant input changes. Prepared artifacts cannot be regenerated differently under an existing identity.

## AIPerf adapter: verify before assuming APIs

Pin the installed AIPerf version/commit in the shared environment and inspect its actual help, supported dataset format and source. Raw request-body replay, timestamped replay, cache hooks and metric export are documented API candidates to verify, not invented guaranteed method names. Write `benchmark/COMPATIBILITY.md` documenting the tested commit/version, exact supported invocation, request format, schedule semantics, metric fields, timeout behavior and any wrapper required. Avoid undocumented private internals when a stable CLI exists.

AIPerf must preserve request bodies, including message/tool fields and exact-output controls. Confirm that it does not silently regenerate prompts, reapply a different template, resample lengths, override arrival timing or recycle input records. If the pinned version cannot replay a required schedule exactly, implement a narrow supported scheduling adapter or report an unsupported capability. Do not approximate while labeling results identical. Capture argv, tool version, stdout/stderr, exit status and raw exports for every cell. Use argument arrays without shell interpolation.

Do not write a second performance client as the default while calling it AIPerf. A custom fake SSE server is appropriate for testing adapter behavior. If minimal instrumentation around the generator is needed for dispatch accounting, document its measurement effects and retain raw records.

## Measurement normalization and complete accounting

Normalize time units to milliseconds and throughput to output tokens per second. Preserve original fields/units. TTFT begins at actual request dispatch and ends at the first relevant generated token; also export scheduled-to-first-token and dispatch-minus-scheduled lag. Record transport/connection timing separately where available. Define how reasoning tokens count and how metadata-only events are excluded. Mechanical tests disable thinking; separate parser probes must recognize reasoning-only and valid tool-call responses rather than declaring every empty `content` invalid.

TPOT is a per-request average decode interval, not a percentile across individual token gaps. Use `(last relevant token time - first relevant token time) / (output tokens after the first streamed chunk)` when first-chunk token counts are available. Cross-check AIPerf's pinned definition and handle speculative multi-token chunks explicitly. If the only supported denominator is completion tokens minus one, preserve that metric under its precise definition, flag the chunk-count limitation and avoid fabricating per-token timestamps. For one-token outputs, TPOT is undefined, not zero. Prefer server token counts; record tokenizer fallbacks and possible mismatch.

Keep per-request raw records sufficient to recompute TTFT/TPOT p50/p99 without averaging run percentiles. Include scheduled, dispatch, first/last relevant output and terminal times; expected/actual token counts; success/error type; terminal status; prefix/session identifiers; server usage; and censoring evidence where supported. Use monotonic local time for durations and an explicit origin for cross-artifact timestamps. Never subtract unsynchronized host clocks.

Report offered, dispatched, completed and failed counts separately, with output-token sums and the fixed offered measurement-window duration. Export completions/output tokens during measurement and total after drain separately; do not label drained tokens divided by offered-window duration sustainable throughput. Retain unfinished-at-window-end, backlog, drain duration, timeouts, cancellations and retries. Require bounded drain/deadlines, and identify pending work at shutdown. AIPerf silently omitting pending requests from percentiles must not conceal them from `CellResult`. Quantiles over successful completions are conditional metrics accompanied by failure/censoring counts; Agent 2 makes the verdict.

GPU memory, cache-hit measurements, speculation acceptance, graph fallback and preemptions are diagnostics from server/telemetry artifacts. Agent 2 owns collection mechanisms; accept references or normalize supplied records. Unsupported telemetry is null with a reason, never zero.

## Parallel implementation, tests and acceptance

Create deterministic unit fixtures with a fake tokenizer and a fake AIPerf process/export. Create a small local SSE endpoint to test actual installed AIPerf streaming and accounting without a GPU; tests must not depend on public networking or a downloaded model. Use a contract-valid fake server descriptor from root examples until Agent 2 is ready. Tests should cover:

- All twelve packs, full-template token accounting, prefix boundaries, suffix uniqueness, hash stability and exhaustion.
- Arrival reproducibility, no completion-dependent throttling, schedule lag and missed dispatches.
- Cache-preparation order, no generic full-prompt warmup, reset failure and fresh-lifecycle requirement.
- Partial chunks, multiple tokens per chunk, reasoning/tool events, one-token TPOT and absent usage.
- Mixed successes/errors, delayed stragglers, drain timeout, censoring and complete request conservation.
- Known raw-record quantiles/units, immutable replay, AIPerf nonzero exit and malformed exports.

Run `pytest -q tests/workloads tests/benchmark`. Coordinate public `prepare --backend mock` and `evaluate --backend mock` smoke commands with Agent 3; final CLI syntax belongs to `docs/INTERFACES.md`. Provide an opt-in installed-AIPerf/local-SSE integration test and an opt-in real-server acceptance test. Neither requires a GPU by default.

Done means another agent can prepare immutable scenarios, run a cell against mock or actual pinned AIPerf, obtain contract-valid artifacts with full request accounting, and identify exactly what is measured versus unsupported. Deliver source, tests, compatibility note, sample tiny packs, artifact examples and concise integration instructions. Do not claim real GPU performance, exact cache support or a quality guarantee until those checks actually run.


## Paste-ready implementation prompt

Read and execute the v0.2 requirements at the top of this brief, not only the detailed module requirements.

> Implement Agent 1 using this complete brief and the canonical DECISIONS.md, docs/INTERFACES.md and contracts/. Own workload generation, immutable traffic packs, AIPerf adapter and metric normalization only. Build against contract-valid runtime mocks so parallel work is unblocked. Verify actual installed AIPerf interfaces and total server-tokenized lengths before real use. Prepare content/calibration schedules first; final common-load schedules are materialized after baseline capacity is measured. Produce source, tests, compatibility note and integration examples. Report actual tests and any real-hardware limitations.
