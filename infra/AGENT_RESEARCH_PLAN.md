# Agent research design for the upgraded evaluator

Status: implementation proposal for review, **not an active campaign change**. The
measured `qwen38-27b-ops4-v1` campaign, its B0 and candidate remain intact. Build
this under a new campaign and protocol version after the evaluator design is
approved. See `OPS4_EVALUATION_REDESIGN.md` and `SEARCH_SPACE_EXPANSION.md`.

## Mission and evidence the agent receives

One Codex CLI research agent proposes **vLLM serving changes** for the pinned
Qwen3.8-27B, BF16, TP1, 40,960-context, single RTX PRO 6000 Blackwell setup.
The controller alone applies configs, launches vLLM, schedules AIPerf and decides
gate promotion. The agent does not choose the traffic rate for an A/B comparison,
change frozen inputs, alter the evaluator or see sealed test outcomes. AIPerf's
adaptive planner chooses *benchmark-side load points* for a separate capacity
study on B0 and finalists, not server settings.

Before its first proposal, the agent receives the **new protocol's matched B0**:
resolved launch settings and image/model/GPU pins; frozen dev workload card,
payload/schedule hashes, class counts and offered/realized rates; each valid B0
window's raw request ledger, server/GPU metrics, validity checks, startup/warmup
timings and p50/p90/p99 TTFT and per-request TPOT. It also receives the current
domain, budget, all prior proposals, valid and invalid results, feedback and
point-estimate frontiers. The older OPS4 four-task B0 stays available as clearly
labelled background evidence, **never as a matched B0 for the new protocol**.

Expose a compact `evaluation-index.json` at each attempt. Each entry names the
configuration, workload/protocol/hash, gate, exact matched B0, evidence grade,
run/window IDs, objective values, uncertainty, reasons for invalidity, and
paths with checksums to complete raw files. Include per-class counts and
TTFT/TPOT p50/p90/p99, output tokens/s, completions/errors/censoring,
configured and realized request rate, client dispatch lag, server queue and
drain, KV/cache, GPU memory/utilization, and MTP acceptance when applicable.
Missing counters must be `unavailable`, never zero. Keep diagnostics available
for the agent to inspect with shell tools; do not stuff every log into the
prompt. Include the AIPerf native `search_history.json` and per-trial exports
for capacity studies, **including invalid and overloaded points**. The agent
gets plotted load curves and underlying point tables; plots alone are not data.

The current `agent/SKILL.md` already uses a path-only prompt and instructs
inspection of `context.json`, `research-index.json`, `measurements-index.json`,
hash-checked evidence, and `history/`. `search/proposer.py` stages recent and
frontier cells, including B0, with explicit file limits. It does **not** stage
adaptive history or all older cells by default. The planned index extends this
mechanism without forced long-context injection or hiding the source records.

## Research method and promotion authority

1. Read B0 and the latest gate evidence. State a specific mechanism, the
   relevant server setting and an observation that would falsify it. Cite the
   exact cell IDs, scope and, when needed, pinned runtime references. A config
   can be a justified exploration even if the direction is unknown.
2. Propose one interpretable setting or a justified interaction, with a typed
   domain-valid override, predicted direction by workload class, likely
   tradeoff, and needed existing diagnostics. No invented percentage gains or
   SLO thresholds. Duplicate/invalid configs stop before GPU use. Prefix-cache
   and MTP settings remain fixed in v2 unless the dedicated token-exact reuse,
   acceptance and semantic-quality gates in the serving-domain plan pass.
3. Controller runs the frozen fast dev screen. A result with full accounting
   but only 36 mixed requests is a **coarse regression screen**: it cannot prove
   p99 improvement or certify any class's SLA. A clear failure may stop here;
   a plausible result advances to matched B0/candidate repeats on independent
   dev windows. Define material-regression thresholds from observed B0 repeat
   variation before automated promotion, and log the policy version.
4. Controller runs the four diagnostic shapes only for survivors, preserving
   per-class tradeoffs and all points. Load exploration is separate: AIPerf may
   sample rates for B0/finalists before a numeric SLO, with results labelled
   exploratory. After an application SLO exists, it can seek an SLA boundary;
   the selected load is confirmed on a fresh fixed schedule. The planner's
   selected in-sample point is not a capacity result.
5. Freeze a small finalist set and rules **before** sealed test. Give the agent
   only the test workload definition and protocol, not hidden payloads or
   outcomes. Matched B0/finalist test results go to the operator and archive
   after search closes. Test outcomes cannot feed another proposal in that
   campaign. If they do, start a new test version.

Ranking should retain configuration and load/protocol scopes. p50/p90 and
profile counters help explain mechanisms and regressions; do not make every
diagnostic a Pareto objective. Primary frontier axes remain predeclared and
uncertainty annotated. Once real TTFT/TPOT/error SLOs are supplied, report
SLO-compliant goodput and the independently confirmed feasible load separately
from fixed-load throughput/latency. No SLO is inferred from B0's observed p99.

The agent reads the remaining **GPU minutes, proposal count and gate costs**
from context. Spend cheap gates on broad hypotheses; spend matched repeats,
longer dev windows and load search on plausible contenders. A failed gate and
its diagnostic reason are useful evidence, not silent omissions. An outer
Optuna Bayesian/TPE baseline can propose serving settings under the
same domain and GPU budget, with random/local-search baselines; the agent is
most useful for mechanism research and proposing conditional domain changes.
Do not claim agent superiority without this budget-matched comparison.
Assess reuse of [InseeFrLab auto-tuning-vllm](AUTO_TUNING_VLLM_REUSE.md) as the
outer study/controller through an adapter before building a separate search
loop; its default local vLLM/GuideLLM trial protocol differs from our
Docker/AIPerf baseline.

## Memory, observability and execution environment

Keep one writable `notes.md` per attempt for concise durable findings:
mechanism, affected workload/class, supporting and contradicting cell IDs,
unresolved questions, source URL/date and next contrast. The controller
snapshots prior notes, proposal JSON, receipt, Codex event JSONL, stderr,
validation decisions, evaluator artifacts and ledger entries. Retain all
adaptive trial points and B0 repeats, not just the optimizer's selected best.
The current note snapshots cover the latest 12 attempts and are campaign-local;
cross-campaign lessons are **not implemented**. Add a curated, versioned
cross-campaign lesson file only after provenance and applicability rules exist.
No vector memory or forced context injection is needed.

The proposer currently runs in an isolated Docker image with read-only staged
inputs and auth, a writable attempt folder, no GPU or Docker socket, and
Docker `bridge` networking. The campaign sets Codex model
(`gpt-6-astra`), reasoning effort (`high`), and web search (`live`); the
controller passes these to Codex. `configs/campaign-ops4.json` also declares
`container_network`, but `deploy/codex-isolated` currently hard-codes
`--network bridge`; make that campaign field validated and effective if network
mode is meant to be configurable. Internet and model access must be verified by
an isolated-container smoke, not inferred from config. The agent's source
research should favor pinned vLLM/AIPerf documentation and distinguish web
claims from measured GPU evidence.

## Concrete build changes and inspection gates

| Area | Planned implementation | Human inspection checkpoint |
| --- | --- | --- |
| Campaign and skill | Version new protocol/domain; update `agent/SKILL.md` and `reference.md` with dev/test boundary, gate grades, class-specific interpretation, real SLO policy and capacity-study authority. | Read exact mission, domain and B0 packet before first proposal. |
| Evidence staging | Extend `src/inference_autoresearch/search/proposer.py` to stage indexed B0 repeats, gate results, all load-search trials, profiler receipts and reason-coded omissions without exposing held-out files. | Open one attempt folder and trace every summary value to raw records. |
| Controller | Extend `search/controller.py` with static/fast/repeat/diagnostic/capacity/test states, matched-B0 selection, policy versioning and explicit promotion/stop reasons; do not reuse old OPS4 qualification. | Review a dry-run state trace and one real B0/candidate gate trace. |
| Profiling | Have `evaluation/observations.py` distinguish ordinary telemetry from a separately budgeted, controller-run targeted profile. Until that exists, retain `targeted_profile: not_executed`. | Inspect receipts and raw counter coverage for every claimed mechanism. |
| Reporting | Extend `search/report.py` with every adaptive point, fixed-load and load-curve plots, per-class p50/p90/p99, validity flags, repeats/uncertainty and frontier provenance. | Reproduce a plotted point from native AIPerf exports. |
| Agent budget comparison | Run equal-GPU-budget agent, outer optimizer and simple baselines on the same dev protocol; seal test during selection. | Compare confirmed frontier progress and GPU minutes, not proposal count alone. |

The first build validation is **one versioned dev B0 repeat and one candidate
through the fast gate**, with complete request accounting and readable agent
packet. Only after its measured time and noise are known should we enable
automatic promotion or adaptive capacity search. BLIS is outside this build.
