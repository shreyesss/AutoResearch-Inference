# Judgments and experiment decisions — v0.2

Status: implementation specification; no target-hardware findings. Date: 17 October 2026. These decisions supersede v0.1. README is the executive summary; this file and INTERFACES are normative.

## Decision register

| ID | Decision and reason | Evidence required / revision trigger |
|---|---|---|
| D01 | Validate workload realism, realization and sensitivity before adaptive search. More diversity does not establish an interesting landscape. | Source audit, workload cards, observed traffic checks and mechanism pilot. Flatness remains reportable. |
| D02 | Initial interventions are supported vLLM serve settings. Expand observations immediately. | Add search axes only after compatible execution and plausible headroom are demonstrated; version the domain. |
| D03 | AIPerf benchmarks real vLLM on the target GPU. BLIS is deferred because predicted performance is not the target evidence. | A later surrogate must demonstrate useful target-system ranking/delta accuracy. |
| D04 | FreeInference/Mooncake are workload evidence, not optimization intervention labels. | Audit release schema/access/license and provenance. Structural metadata cannot recover original text or exact MTP acceptance. |
| D05 | Hyperloom is a methodology reference for state, retrieval, experimental authority and scoped knowledge. | Borrow specific mechanisms; do not import its full architecture or scalar adoption logic. |
| D06 | Retain the 12 mechanical packs as diagnostic controls. Construct representative mixed/session packs from trace evidence. | Data-based selection independent of candidate gains; stress cases labeled separately. |
| D07 | Primary objectives: throughput ↑, TTFT p99 ↓, TPOT p99 ↓. Both p50s mandatory. | Change objective policy only in a new campaign; no invented SLA or scalar weighting. |
| D08 | Fix common absolute traffic for comparisons. At underload throughput is demand-limited. | Baseline calibration freezes common load ladder; all finalists and B0 share it. |
| D09 | Store immutable observations, not just winning configurations. Separate hypotheses from evidence-backed lessons. | Knowledge entries reference trials, scope, uncertainty and counterevidence; invalidate on incompatible runtime. |
| D10 | Start with one proposer and deterministic execution authority. | Add roles only after a demonstrated need; builder parallelism is separate. |

## Fixed task and provisional feasibility

Target `Qwen/Qwen3.8-27B`, not Flash-Next. Treat checkpoint identity/architecture and parser support as facts to verify from the pinned model/runtime. Exact NVIDIA GPU, compute capability and physical/free memory are unknown. “RTX 86 GB” does not identify a product. TP=1, BF16 weights and fixed resolved KV precision; text-only behavior and endpoint semantics fixed. `max_model_len=40960` is provisional and must accommodate serialized input plus output. Do not change precision, truncate context or silently substitute a model to obtain feasibility.

Pin image digest, vLLM/AIPerf/Codex versions, model/tokenizer revisions and template hash. Fixed non-thinking mechanical probes coexist with separately specified semantic reasoning/tool probes. Operational parser settings in examples are proposed values, not validated compatibility. B0 is resolved stock performance defaults plus task requirements. B1, if included, is a separately labeled applicable recipe. Do not weaken B0 by disabling an optimization its defaults enable.

Proposed starting domain: `max_num_seqs` [8,16,32,64,128], `max_num_batched_tokens` [2048,4096,8192,16384], `gpu_memory_utilization` [.85,.90,.93], prefix cache off/on, native supported MTP depth [0,1,2,3,5]. Zero omits speculation. Conditional graph/eager and capture settings require a frozen compatible domain. These are probe candidates, not an asserted feasible Cartesian product or optimal range. Resolve aliases/defaults and retain all feasibility exclusions. Distinguish unsupported, inactive under tested conditions, inconclusive and measured-sensitive axes.

## Workload policy

The four exact diagnostic input/output shapes are 512/256, 2048/1024, 8192/1024 and 32768/512, with intended prefix fractions 0/.5/.75. Names identify mechanical shapes, not realistic task semantics. Prefix pool 64 is a diagnostic starting value, not an empirically derived population size. No requirement to benchmark all 12 at every stage.

Representative suite selection comes from documented deployment questions and trace characterization, before searching candidates. Required families for initial qualification: a mixed short-request/long-prefill/ongoing-decode pack; a session pack with observed context growth, tool gaps and reuse; and semantic prompts for content-sensitive speculation. Include ordinary and busy regimes, with actual proportions established from sources. Do not invent shares or presume every family activates every knob. A source-backed representative pack that is flat remains in the evaluation story; mechanism stress controls are separate.

Record joint input/output lengths, arrival counts at 1s/10s/1m, session/turn counts, context growth/mutations, reuse distances/popularity/cardinality, tool gaps and working-set proxies. Source timing is observed under the original provider and can include its service delay. Extract genuine think/tool time where possible; otherwise declare recorded-timing replay, not a causal reconstruction of live users. Preserve complete sessions and split by session/time and shared identities; namespace block IDs when their scope changes. Use train/search and untouched evaluation packs. No filtering based on discovered gains.

Freeze exact payloads/schedules for independent or recorded-history replay. For dependent live-history replay freeze initial prompts, incremental messages, dependencies, tool-delay assumptions, generation policy and seeds; actual future inputs/timestamps can vary with model output and service latency. Store realized histories and never claim identical streams. Do not merge these protocols into one frontier. AIPerf does not execute tools; scripted tool-result replay is not task-solving validation.

Do not call a constructed 75% shared prefix a 75% achieved hit rate. Account for tokenization/template alignment and the hybrid engine's supported reuse. FreeInference structural blocks use a different tokenizer from Qwen; reconstruct abstract sharing and revalidate target tokens, rather than pretending exact original Qwen KV identities were recovered. Metadata-only data requires separately sourced meaningful text for MTP. Forced-length and natural-EOS packs have different contracts. Never apply exact-output failure rules to natural EOS.

## Metrics, comparison and uncertainty

Objective vector at operating point (configuration, approved load): (output_tokens_per_s ↑, ttft_p99_ms ↓, tpot_p99_ms ↓). Primary archives group only the same workload/cache/execution/measurement protocol over a predefined common ladder. Conditional archives compare the exact same offered load. No averaging across workload types or p99 values. Also show per-class distributions for mixtures so long requests do not hide short-request regressions. Session completion time is supplementary for dependent workflows, not an unannounced replacement objective.

Baseline-only bounded calibration finds a sustainable reference rate using achieved dispatch, completion and stationarity evidence. Initial screens use 80%; finalist ladder uses 60/80/100/120% of that reference. These are initial policy choices, not universal production targets. If calibration fails, diagnose rather than fabricate capacity. Any extension of the common ladder follows an evaluator-owned predeclared rule for B0 and all compared finalists. Session traffic needs explicitly named session-start rate/user population; do not confuse it with per-turn RPS.

TTFT: actual dispatch to first relevant generated event; also retain scheduled-to-first-token and client lag. TPOT: request-level decode average with explicitly verified token/chunk denominator, not individual-token stall p99. Per-request speed and aggregate output throughput are distinct. Use server usage when available and count reasoning once. Undefined TPOT remains null with eligibility counts.

Canonical throughput is successful completed completion tokens divided by first planned benchmark dispatch through last terminal outcome (including drain/deadline). Also preserve active sending-window throughput, token/completion time slices and drain. This finite-run metric is not by itself sustainable capacity. Every planned request has a terminal or explicit not-dispatched/censored record. Do not hide timeouts or errors by showing successful-only quantiles without their counts.

Short screens are provisional. Confirm using matched repeated windows and raw-record statistics, with session/time-block uncertainty where appropriate. Minimum sample target (initially 1000 eligible requests) is a diagnostic floor, not a p99 precision guarantee. Specify desired interval precision and cost ceiling; report inconclusive tails when unmet. No arbitrary universal 5% gain requirement. Exact point-estimate nondominance and uncertainty-aware interpretation are separate views.

## Gate and learning policy

Implementation can proceed on mocks immediately. Real adaptive search requires a qualification report: workload provenance/realization, exact environment, B0 evidence, sensitivity classifications and a frozen active-domain revision. Pilot probes include negative controls and repeats; a few supported 2×2 interactions are permitted. At least one plausible mechanism must show a reproducible metric effect for a sensitivity-qualified campaign. Otherwise close as flat/inconclusive/blocked, preserve the evidence and recommend a versioned redesign. This gate does not require beating B0. No automatic selection of only easy-to-win workloads.

The proposer may read scoped artifacts, docs/source snapshots and prior outcomes, and request budgeted diagnostic observations. Evaluator owns workload, policy, runtime, measurements and validity. Observations are read-only; active profile requests go through the same exclusive GPU controller, are charged and kept separate from performance windows. The proposer cannot modify scoring, instructions, evaluation code or input manifests.

Every proposal records hypothesis or explicit exploration, predictions, tradeoffs, evidence IDs and a falsification condition. Feedback includes measured deltas, uncertainty, mechanism evidence availability, validity and frontier status. Mechanism interpretation can be supported, contradicted or unresolved; missing counters do not become evidence of absence. Adopt Pareto tradeoffs, not a single scalar incumbent. Preserve dominated and failed experiments.

Stable procedural skill is distinct from retrieved knowledge and raw ledger. Start with a small frozen operational/reference packet and an auditable same-run memory. External prior mining and cross-run memory are future controlled factors: compare the same search method with/without added priors, and compare search methods with comparable information/budgets. Public knowledge in base models prevents claims of truly knowledge-free agents. Held-out outcomes are never supplied during proposal generation.

## Scope expansion and non-goals

Observation comes first. Compatible prefill/scheduling, graph or backend controls can be admitted through evidence-backed domain amendments. Cache offload becomes a candidate when reuse beyond GPU residency is actually valuable. Source/scheduler/kernel edits need a new intervention and correctness contract. Quantization needs a separate quality-qualified branch. Multi-GPU routing/disaggregation, BLIS integration, training agents, full executable tools, web dashboards and BO superiority claims are outside initial delivery. These are sequencing choices, not permanent scientific restrictions.
