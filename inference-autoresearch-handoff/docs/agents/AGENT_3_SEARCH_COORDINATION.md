# Agent 3: search, persistence, CLI and integration — v0.2

Read the v0.2 execution requirements below together with the retained detailed implementation guidance. DECISIONS.md and INTERFACES.md are authoritative.

## v0.2 execution requirements: scientific gates and minimal learning loop

1. Scaffold v0.2 contracts first, including variable-length/session sources/cards, PilotPlan/SensitivityReport/QualificationReport, observation requests, feedback and knowledge. Publish typed fakes and amend all consumers together. Existing three JSON schemas are starter shapes, not the entire DTO implementation.
2. Add characterize and pilot commands; wire Agent 1/2 protocols instead of duplicating their logic. Search requires matching real qualification. Mock workflow includes deterministic active/flat/noisy axes. An honest closed gate is a valid report, not permission to auto-alter representative packs.
3. Context includes deployment/workload cards, domain/capability/qualification evidence, baseline/archive, recent results, uncertainties and budgets. Implement scoped EvidenceStore list/read and retrieval audit by IDs. No arbitrary proposer paths/commands or edits to inputs/evaluator. Optional bounded reference research is explicit and provenance-logged.
4. Proposal v0.2 includes hypothesis/exploration, predictions, falsification and requested observations. Route diagnostic requests through evaluator; charge profile cost and keep it separate from performance. The proposer may reason before proposing again; do not force every retrieval to spend GPU time.
5. Produce structured feedback per comparison: validity, actual matched-load metric effects/uncertainty, diagnostics/missingness, mechanism supported/contradicted/unresolved, frontier status and budget. No single weighted incumbent; keep multiple parents and exploratory coverage.
6. Implement three separate records: immutable trial ledger, stable procedural skill/reference version, and retrieved knowledge entries. Store every attempt; promote only validated scoped lessons with trial references, counterevidence and expiry/revalidation conditions. Failed attempts without a reusable inference remain raw history. Do not continuously self-edit scientific policy or silently rewrite the stable skill.
7. Freeze a small operational/reference packet and same-run memory for initial practical use. Configure external mined cards and cross-run memory separately for later ablation; log access and retrieval budget. Do not claim a no-added-prior model lacks public prior knowledge. Do not feed holdout outcomes back into the active campaign.
8. Report source coverage/fidelity, representative vs stress vs diagnostic results, sensitivity classifications, per-class mixed-workload tails, session metrics, actual vs intended traffic, hypothesis outcomes, memory provenance and all costs. BO comparison and training are future experiments under matched information/evaluator budgets.
9. Tests cover gate refusal (mock/stale/flat), retrieval scoping, knowledge vs hypothesis distinction, feedback with unsupported diagnostics, same-run resume, holdout isolation and natural/session protocol grouping, alongside Pareto/dedup/accounting below.

The current minimal execution path is doctor → characterize → prepare → baseline → pilot → search → report, with evaluate for explicit investigator trials. This is not a demand to stop parallel implementation at each gate; CPU work continues on fixtures. A real search starts only when evidence qualifies it.


## Assignment and boundaries

Implement the configuration-search coordinator for the inference autoresearch experiment. This is a build brief; none of its GPU results are already established. Read `DECISIONS.md`, `docs/INTERFACES.md`, and root-owned `contracts/` first. Those contracts are authoritative. If this brief and a contract conflict, stop the affected implementation, report the discrepancy to the integration owner, and continue independent work. Do not invent incompatible payloads or edit contracts unilaterally.

Own these paths:

- `src/inference_autoresearch/search/**`
- `src/inference_autoresearch/storage/**`
- `src/inference_autoresearch/cli.py`
- `pyproject.toml` and top-level package/entry-point wiring
- `tests/search/**`, `tests/storage/**`, `tests/integration/**`

Agent 1 owns workloads and benchmarking; Agent 2 owns runtime and evaluation. Import their protocols through the canonical interfaces. Implement local fakes conforming to those interfaces so your work does not wait for their implementations. Avoid installing a second local inference model: Codex proposes via its configured external execution environment; the real vLLM server is the only GPU workload.

## Scientific behavior to preserve

The configuration search changes supported serving flags only. Workloads, hardware, model precision, reasoning behavior, arrival schedules and evaluator policy are immutable during a campaign. The agent cannot improve a score by reducing offered load, modifying output lengths, or disabling a required response behavior.

Maintain a primary three-objective archive per workload/cache/protocol group across the evaluator-owned fixed common load ladder:

1. Maximize aggregate completed output tokens/second.
2. Minimize TTFT p99 in milliseconds.
3. Minimize TPOT p99 in milliseconds.

Report TTFT p50 and TPOT p50 on every result. A candidate dominates another when no objective is worse and at least one is strictly better. Do not replace this with arbitrary weighted latency/throughput scores. Do not collapse startup and decoding latency into one number. Export two-dimensional projections for inspection, clearly labeled as projections of the full three-dimensional frontier.

The initial fixed offered rate is baseline-derived and shared across candidates. Below saturation, completed throughput will be demand-limited and may barely differ; it is a completion guardrail, not proof of greater serving capacity. Finalists receive the evaluator's common absolute load ladder, including baseline-relative 60/80/100/120% points. Each point is identified by configuration and load scenario. Different loads remain explicit observations on the common operating curve; also maintain conditional archives within each exact load for matched-load comparisons. A configuration's outcome at 80% of its own capacity is not comparable with another at a different absolute rate.

Results are an empirical nondominated set among evaluated candidates, never a certified global optimum. Maintain a point-estimate archive and a separately qualified/confirmed archive. Insufficient samples, uncertain p99, or a short duration remain visible. Do not combine incompatible stages, budgets, cache protocols or datasets into one dominance comparison. Cross-load dominance belongs only to the predefined common ladder within a workload group; matched-load dominance has a separate view. The baseline curve is always retained in reports even when dominated; archive membership and baseline identity are separate fields.

## Core interfaces

Implement `Proposer.propose(context) -> CandidateProposal` and `SearchController.run(campaign) -> CampaignResult` according to `docs/INTERFACES.md`. Consume `Evaluator.evaluate(candidate, scenario_ids, stage) -> EvaluationResult`. Preserve canonical types and async/sync signatures as specified there.

A proposal contains allowed parameter changes, optional parent configuration references, hypothesis, expected tradeoff and evidence result IDs. Parents may be multiple archived candidates; do not implement a single-incumbent hill climber. The controller normalizes proposals into complete configurations against the frozen task settings before asking runtime/evaluation to resolve defaults.

A proposer context includes campaign identity, remaining wall-clock and trial budget, declared parameter domains, capabilities, baseline results, all current archives, recent failures, unresolved noisy results and concise diagnostics. Provide file references for detailed evidence rather than embedding huge traces or logs. Preserve enough history to reveal interactions without requiring an unbounded prompt.

The proposer cannot launch Docker, acquire the GPU, mutate contracts, or mark a run successful. The evaluator supplies correctness and measurement verdicts. The controller assigns the comparison/archive state from those verdicts and measurements. Proposal reasoning is evidence, not a measured result.

## Codex proposer adapter

Implement a configurable adapter that writes a versioned request JSON, invokes the installed Codex binary using the locally verified invocation, and parses a versioned response JSON. Check the binary's installed help/version during setup. Do not bake undocumented CLI switches into the project or claim an invocation has been tested before checking it. Put executable and argument templates in configuration; pass arguments without shell interpolation.

Validate output against the canonical candidate schema. Reject unknown flags, task overrides, unsupported values and malformed evidence references before consuming GPU time. Capture request, response, exit status and sanitized stderr. Use bounded timeouts, bounded context and a finite retry allowance for JSON repair. A repair retry is not an inference evaluation.

Provide explicit proposer modes such as `codex`, `mock`, and later `random`. Failure of the Codex adapter must produce an actionable failure/checkpoint; it must not silently switch to random search and label the resulting campaign an agent run. A random proposer is acceptable only when explicitly selected and identified in all campaign metadata. Bayesian optimization and equal-budget comparison are future extensions, not a dependency of this first build.

## Search scheduling and budgets

The controller performs the following state transitions:

1. Load or initialize the campaign, validate immutable hashes, and acquire the campaign coordinator lock.
2. Ensure baseline calibration and baseline evaluations exist with the required provenance. Never manufacture a rate when calibration fails.
3. Request, validate and normalize a proposal; reject duplicates before costly startup when possible.
4. Evaluate a candidate at the cheap stage using the evaluator's prescribed scenario bundle.
5. Promote promising tradeoffs, unresolved results near the frontier and a configured exploration allowance. Reject clear invalidity or large reproducible regressions.
6. Schedule expanded tests, repeats and held-out validation within the remaining budget.
7. Update archive views and persist the next controller state after every transition.
8. Stop cleanly on budget exhaustion, explicit interruption, unrecoverable environment failure, or a configured stopping policy; produce a partial report.

Use transparent configurable promotion rules. A small noisy p99 regression cannot permanently eliminate a configuration. Repeats may resolve uncertainty; a shorter-duration screen cannot be silently upgraded to confirmed. Preserve outcomes from all trials, including rejected and dominated candidates. Reserve budget for baseline repeats and finalist confirmation instead of spending everything on proposals. Check the remaining budget before scheduling an expensive promotion; acknowledge that server boot and graceful drain can exceed an estimate.

Do not let optional latency thresholds quietly alter the objective: if a campaign explicitly supplies thresholds, label feasible/infeasible separately and preserve raw metrics. Do not require hard SLA limits in the default frontier campaign.

## Durable storage and restart

Use an append-only experiment event ledger plus atomic materialized summaries, or a transactional database with exported JSONL. Whichever implementation is chosen, recover correctly after interruption between proposal, startup, measurement and archive update. Trial state must distinguish proposed, validated, starting, running, draining, completed, failed, interrupted and superseded measurements where the canonical schema allows them.

Compute a normalized resolved configuration hash after defaults and aliases have been resolved. Include immutable runtime identity separately: image digest, runtime version, model/tokenizer revision, GPU fingerprint and fixed-task settings. Deduplicate equivalent candidates using that resolved identity. A separate evaluation identity includes scenario hash, absolute schedule, stage/policy and repetition seed. Repeating a configuration deliberately is valid; accidentally rerunning the same trial after restart is not.

On restart, verify task and environment compatibility, reconcile incomplete trials with evaluator/runtime state, and record interrupted runs explicitly. Do not treat partial output as a successful result. Preserve raw request records through stable artifact paths and hashes. Store versioned schema IDs on records. Use atomic writes or transactions; never require reconstructing scientific provenance from an agent conversation.

Keep secrets out of logs and artifacts. Restrict subprocess environment forwarding and preserve only necessary configuration. Runtime owns the GPU lock; your coordinator lock prevents two search processes from issuing competing campaigns. A stale lock must be investigated or safely reconciled, not blindly deleted while an inference server still runs.

## Public CLI and artifacts

Wire the canonical commands:

- `doctor`: inspect hardware, runtime, permissions, installed versions, available flags and proposer availability; do not launch a performance campaign.
- `prepare`: validate campaign definitions and build/hash immutable workload assets through Agent 1.
- `baseline`: perform Agent 2's calibration policy, then measure B0 and feasible separately labeled B1.
- `evaluate`: run a specified candidate/scenario/stage through Agent 2 without invoking a proposer.
- `search`: run or resume the autonomous campaign with an explicit proposer and budget.
- `report`: rebuild archive views and human-readable reports entirely from durable evidence.

Support `--backend mock` for CPU-only end-to-end verification. Distinguish evaluator backend from proposer mode: a mock evaluator with a Codex proposer and a mock proposer with a real evaluator are different choices. Defaults must not accidentally spend GPU time in tests. CLI argument names beyond these agreed command names follow the canonical interfaces/configuration docs.

Export campaign metadata, proposals, normalized/resolved configurations, evaluation records and events as versioned JSON/JSONL; workload-group frontier tables and conditional per-load frontier tables as CSV/JSON; and a compact Markdown or HTML report. The report must show baseline, all candidate IDs, actual offered/admitted/completed work, failures/timeouts, raw artifact links, four latency summaries, throughput, uncertainty, repetition count and confirmation status. Explain any censored tail instead of printing an unjustified finite p99. Never average percentile values across trials; consume recomputed raw-record estimates from evaluation.

## Parallel integration sequence

First implement storage, dominance logic and the controller against fixtures supplied by canonical contracts. In parallel, build the CLI with injected fake workload/runtime/evaluator adapters. Publish the expected import points early to Agents 1 and 2. Request contract amendments from the integration owner when fields are missing.

Then replace fakes with Agent 1's prepared workload/benchmark artifacts and Agent 2's evaluator. The minimal real path is `doctor -> characterize -> prepare -> baseline -> pilot -> search -> report`, with `evaluate` for explicit candidate probes. All commands share a campaign directory and compatible hashes; the current path also includes characterize and pilot, with sensitivity qualification before search. Agent 2 remains responsible for lifecycle cleanup, GPU locking and verdict validity; Agent 1 remains responsible for request construction and metric extraction. Do not recreate their logic in the coordinator.

Finish CPU-only deterministic integration before a GPU smoke run. Mark real-hardware readiness as unverified until an actual target-machine run passes. The project may be implementation-complete while hardware/model feasibility is blocked; report those states separately.

## Acceptance checks

- Known dominated, nondominated, equal and invalid fixture observations yield correct workload-group and conditional per-load archives; throughput direction is maximization.
- A high-throughput configuration with dropped requests is rejected by evaluator constraints and never promoted as a winner.
- Incompatible stages/workload hashes never contaminate one another's archive; cross-load archives accept only the predefined common ladder and preserve load labels.
- Noisy short-run points remain provisional; a confirmed archive only contains appropriately repeated/qualified evidence.
- Multiple parent proposals work; baseline remains in reports after domination.
- Resolved default aliases deduplicate, while intentional repeats have separate evaluation identities.
- Interrupted campaign restart neither loses completed evidence nor double-submits an existing trial.
- Malformed Codex output and binary failure are explicit; no silent random fallback occurs.
- One CPU-only mock campaign runs all public commands and exports reproducible archives without Docker/GPU/API credentials.
- An optional real smoke campaign can use a tiny budget, stop safely, resume and regenerate its report.

## Paste-ready implementation prompt

Read and execute the v0.2 requirements at the top of this brief, not only the detailed module requirements.

> You are Agent 3 for the inference-autoresearch repository. Read DECISIONS.md, docs/INTERFACES.md and contracts/ first; implement this brief within the owned paths only. Implement durable state, a versioned structured Codex proposer adapter, conservative staged search, workload-group and conditional per-load empirical Pareto archives, CLI wiring and deterministic CPU-only integration. Use protocol fakes until Agents 1 and 2 are available. Do not edit contracts unilaterally, invent Codex flags, silently use random search, change frozen workloads or claim global Pareto optimality. Test restart, deduplication, validity constraints, load/stage separation and frontier logic. End with changed paths, checks performed, exact verified invocations and remaining hardware-dependent blockers.
