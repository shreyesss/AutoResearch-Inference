# Understanding and experiment design — v0.2

## Question and current evidence

Can a Codex research loop discover reproducible workload-specific serving tradeoffs over normal vLLM defaults on one GPU? Before asking that, establish that the workload is plausible, its realization is faithful, and the allowed settings can affect observable bottlenecks. This handoff specifies the apparatus and decision rules. No raw traces were mined and no GPU results were measured during its preparation.

The target is `Qwen/Qwen3.8-27B` on an unidentified NVIDIA GPU described as “RTX 86 GB.” Verify the exact checkpoint, architecture, runtime and hardware. Do not import Flash-Next MoE settings. BF16 feasibility, hybrid cache behavior and native MTP support remain empirical qualification tasks.

## Components in plain terms

| Component | Meaning | Role in this experiment |
|---|---|---|
| vLLM | Inference engine serving the actual model | Executes candidate configurations |
| AIPerf | Client that generates/replays requests and measures responses | Real-hardware evaluation transport |
| Trace | Recorded requests and their temporal/session relationships | Evidence for realistic input construction |
| Mooncake trace format | Timing/length/prefix-block description, optionally richer messages | Structural replay through AIPerf |
| FreeInference | Released serving/session metadata and separate telemetry datasets | Characterize realistic traffic, context changes and locality |
| BLIS/inference-sim | Discrete-event serving simulation with modeled execution costs | Deferred; predictions are not target GPU measurements |
| Hyperloom | Agent harness spanning inference framework and kernel optimization | Reference for experiment state, retrieval and evidence-backed lessons |
| Our harness | Controlled execution around a proposer | Builds packs, runs trials, judges validity and maintains empirical fronts |

A served agent's task trajectory is not an optimizer's intervention trajectory. FreeInference can reveal session structure without identifying which serving flag would help. Missing original text prevents exact semantic reconstruction. AIPerf is capable of synthetic traffic and session replay, but does not execute tools or prove task success. BLIS can vary supported modeled deployments/hardware/workloads without running the model per trial; it needs suitable cost support and cannot independently predict speculative acceptance. It is unnecessary for the first real-hardware campaign.

## Three validity questions

1. **Realism:** What deployment and source population does the input represent? Published source findings are not our own measured statistics.
2. **Realization:** Do the actual formatted/tokenized requests, dispatch timing and context reuse match our intended construction?
3. **Sensitivity:** Does changing an allowed setting activate a mechanism and produce effects distinguishable from noise?

Answer separately. A well-replayed synthetic stress test is not proof of production prevalence. A realistic pack can have no tuning headroom. A large improvement can be an artifact or an already-known disabled-default control. Do not certify interest or novelty from parameter count alone.

## Workload construction from evidence

Choose a deployment question first: e.g. shared coding-agent sessions, a document/chat endpoint, or independent short chats. Audit source schema, license, availability, model/hardware population, time span and missing data. Compute bounded-batch statistics on accessible data; if unavailable, ship the miner and mark characterization pending. Never invent empirical proportions to complete a card.

Characterize joint input/output lengths (including conditional distributions), arrival counts over 1s/10s/1m, overlap, session turns, tool/think gaps, context growth and mutations, prefix cardinality/popularity/reuse distance, cancellations/retries if available, and context/working-set proxies. Reuse distance means intervening traffic before a prefix returns. It is not just elapsed time or shared fraction. A context prefix mutated early may invalidate a long downstream suffix even if most words remain similar.

Extract complete sessions and representative ordinary/busy/tail windows. Pack sizes are chosen from measured evaluation cost and statistical precision, not a mandatory 5K–20K count. Preserve correlations instead of independently sampling input length, output length, gaps and reuse. Split search and held-out data by complete sessions and time, checking prefix/account identities and source-specific hash namespaces. Record exclusions and compare source versus selected pack distributions. Do not pick packs based on which candidate wins.

Source observations include original provider timing and caching. Distinguish recorded arrivals from tool delays, and preserve dependencies where known. If service and think time cannot be disentangled, declare a recorded-timing protocol. FreeInference uses structural block tokenization distinct from Qwen: reconstruct abstract prefix topology, target-tokenize text and validate achieved boundaries. Do not reinterpret source block IDs as exact Qwen KV blocks.

Every target adaptation is documented: length capping/filtering, tokenization, content substitution, arrival rescaling, session selection and precision/context feasibility. Prefer filtering or explicitly designed alternate regimes to silent truncation. Time compression changes cache eviction and concurrency; it is a transformed workload. Record absolute time and a separate independent-session superposition experiment if used.

## Suite composition

| Family | Purpose | Initial status |
|---|---|---|
| Four exact shapes × intended prefix fractions 0/.5/.75 | Attribution, accounting and mechanism controls | Construction templates, not empirical representative packs |
| Mixed short requests plus long prefills with active decodes | Plausible contention/scheduling test | Source proportions and exact assets pending |
| Session growth with tool gaps and reuse | Retention/working-set behavior | Trace-derived card and validation pending |
| Real semantic chat/code/document prompts | Content-sensitive generation and MTP | Source/license and natural/forced protocols pending |
| Deliberate stress controls | Boundary behavior and failure diagnosis | Labeled separately; not weighted as typical production |

Exact diagnostic input/output sizes: 512/256, 2048/1024, 8192/1024 and 32768/512 total server-tokenized tokens. Prefix pool 64 is an initial control, not a real-user estimate. Template tokens can create unavoidable common beginnings in the nominal 0% case. Explain them. No arbitrary 10/30/60% mixture is designated realistic before source analysis.

A workload card records scenario, source revision/hash/license, selection/split, source-versus-pack statistics, transformations, content provenance, timing/dependency/output policy, prefix topology and gaps, expected mechanisms/controls, actual realization, limitations and readiness. Representative, diagnostic and stress are separate suite roles.

## Mechanism map and pilot

| Control | Activation condition | Useful observations | Expected flat region |
|---|---|---|---|
| Sequence cap | Concurrent work reaches the limit | Running/waiting requests and realized batch | All concurrency below the smallest cap |
| Token budget/prefill controls | Prefill and decode compete for scheduled work | Prefill/decode tokens per step, queue and stalls | Token budget seldom binds |
| GPU memory fraction | Useful active/reusable state is capacity constrained | Cache usage, preemption/recomputation and memory | Working set comfortably fits |
| Prefix caching | Exact reusable prefixes survive until reuse | Cache reads/saved prefill, cardinality/gaps | Unique, evicted or unsupported reuse |
| Native MTP/depth | Accepted progress offsets draft/verify overhead | Accepted tokens/step, acceptance, batch/memory | Low acceptance or adverse saturated batching |
| Graph/capture behavior | Coverage, launch cost or reservations matter | Actual execution/capture/fallback and memory | Defaults already cover useful shapes |

These directions are hypotheses, not monotonic guarantees. Long-prefill traffic may delay decode; a smaller token budget may improve TPOT while worsening TTFT/capacity. Prefix caching can reduce prefill demand so token-budget changes become inactive. MTP and concurrency can interact. Probe a few mechanism-justified 2×2 combinations rather than only single knobs or the entire Cartesian product.

Baseline repeats estimate drift/noise. Run supported perturbations in ordinary and near-capacity regimes; verify actual resolved settings and binding counters. Include an underloaded/inactive control where appropriate. Classify each axis/regime as sensitive, inactive-under-tested-conditions, unsupported, or inconclusive. Record metric effect intervals, diagnostics and costs. Missing counters imply uncertainty, not a zero bottleneck. A small pilot cannot prove global flatness. Adaptive search is qualified only when the report supports a plausible reproducible effect; otherwise publish findings and version a redesign. Beating B0 is not a pilot gate.

## AIPerf input map and realization contract

The following is the text-serving control map to implement. Agent 1 must expand it into a version-specific inventory from installed help/config schemas, covering every exposed text input/load option and marking used/deferred/not-applicable. This table is not an exhaustive validated CLI listing.

| Family | Documented interfaces to verify | What to freeze and check |
|---|---|---|
| Endpoint/tokenization | model, URL, endpoint type, streaming, tokenizer/revision, template, extra inputs | Exact request body and server token totals |
| Content | input file, dataset type, prompt corpus, system prompt | Content source/license, no unintended regeneration |
| Lengths | input/output mean/stddev, `--seq-dist`, range/distribution options | Joint ISL/OSL and exact versus ceiling behavior |
| Prefixes | prefix length/pool, shared system/user context, cache-bust controls | Full formatted token LCP and intended reuse graph |
| Independent arrivals | request rate, constant/Poisson/Gamma, smoothness, ramps/series | Actual schedule, burst counts and dispatch lag |
| Client limits | concurrency, prefill concurrency, workers/connections | Whether the client suppresses offered demand |
| Timestamp replay | fixed schedule and trace synthesis transforms | Explicit time origin, scaling and session semantics |
| Conversations | turns, delays, user populations and live/recorded history | Dependency edges, context growth and realized input |
| Output/lifecycle | output cap, supported minimum/ignore-EOS extras, cancellations, timeouts | Enforced-length versus natural EOS; terminal accounting |
| Preparation | execution warmup, cache reset hooks, prewarm | Hook order and actual cache starting state |
| Reproducibility | seed, repeated-run/sweep seed settings, dataset sampling/wrap | Saved assets, actual seed scopes and no accidental recycling |
| Evidence | per-request exports, server metrics, telemetry/profile hooks | Verified fields/units, raw sources and missingness |

Independent synthetic and recorded-history replays can use immutable payloads and timestamps. Dependent live histories instead freeze initial/incremental inputs and dependency/delay policy; generated content and later dispatches may vary. Save the realized stream. A fixed-concurrency session benchmark is different from open-loop external arrivals. Session-start RPS is not turn RPS. Configure these explicitly and never silently substitute one for another.

Seed content, topology and arrivals separately. Save generated assets and hashes instead of assuming regeneration survives software changes. AIPerf's generation seed does not fix server sampling; even fixed server sampling does not promise deterministic timing. `max_tokens` alone is a ceiling. Mechanical packs require validated fixed-output controls; semantic natural-output packs require EOS-aware analysis. AIPerf's agentic generator is worth reusing after auditing its assumptions against traces; its defaults are not empirical truth for our deployment.

## Preparation, observations and objective semantics

Warm compilation/execution on disjoint content, then reset/reinitialize cache. For prewarmed controls, populate only intended prefixes; for cold streams, let reuse develop naturally. Representative steady streams require a documented burn-in/initial-state policy. Record preparation cost separately. Cache-off sees the same opportunities and preparation sequence; lower hits are not invalid. Validate hybrid cache/reset behavior rather than assuming classical attention rules.

Primary objective vector: output_tokens_per_s maximize, TTFT p99 and TPOT p99 minimize. Report both p50s. TTFT starts at actual dispatch; scheduled-to-first-token exposes client queueing. TPOT is request-level decode elapsed/tokens after the first relevant chunk under an explicitly qualified counting rule. It is not raw token-gap p99. Preserve undefined/missing cases and eligibility counts. Aggregate throughput differs from reciprocal request TPOT.

Canonical effective throughput includes the full finite run through terminal drain/deadline; retain active-window throughput and time slices separately. Stationarity/backlog determine whether capacity is sustainable. At underload throughput is demand-limited, so latency may be the only visible gain. Common baseline-derived 60/80/100/120% loads reveal curves; cheap 80% is a starting policy. Do not compare private candidate-relative loads. Dependent workflows also report session completion time, realized turn rate and request-class breakdowns.

Every planned request is accounted for; successful-only latency quantiles always carry error/censoring counts. Overload, client throttling, startup failure, valid regression and measurement failure are distinct. No averaging p99s. Repeats and time/session-block uncertainty qualify final tails; 2–3 minutes is a screen, not a tail guarantee. No certified global Pareto optimum or agent-vs-BO superiority claim follows from v1.

## Minimal agent and accumulated knowledge

Give one proposer a frozen mission, workload cards, active domain, resolved environment, baseline/frontier and remaining budget. Provide read-only retrieval of raw/summary evidence, failures, profiles and pinned references. Controlled profiling uses a separate controller action and budget, never contaminates a timed cell. Maintain bounded context and an append-only audit of what evidence was available and retrieved.

A proposal states hypothesis or explicit exploration, mechanism, changed settings, expected metric/diagnostic effects, tradeoff, evidence IDs and falsification condition. Feedback reports validity, measured changes/uncertainty, diagnostic availability and frontier membership. Interpret the mechanism as supported/contradicted/unresolved. Do not require invented causal stories for exploratory coverage. Multiple Pareto parents are allowed.

Separate stable procedural skill, immutable ledger and curated retrieved lessons. Store all attempts; promote only evidence-backed scoped findings to knowledge. A lesson records hardware/model/version/workload/load applicability, trial IDs, result and uncertainty, counterevidence and revalidation conditions. Historical failures are contextual evidence, not permanent blacklists. Hyperloom's persisted state, contextual evidence tools and measured promotion provide patterns; do not import its single-best selection into our Pareto objective.

Practical default: frozen small operational/reference packet plus same-run memory. Later ablate external insight cards and cross-run memory separately, with equalized search-method information/budgets and untouched evaluation outcomes. Base models already contain public knowledge; “without added priors” is the accurate label. Generated lessons need not rewrite the stable SKILL file during every trial.
