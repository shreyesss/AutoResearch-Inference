# Adaptive evaluation plan for the Qwen serving study

**Status: v2 screen, Optuna search, and exploratory adaptive CLI implemented;
real v2 B0 and adaptive pilot are still being measured/validated.** The v2
artifacts are `configs/campaign-v2.json` and
`configs/evaluation-protocol-v2.json`. The older `configs/campaign-ops4.json`
retains its separate `fixed-four-v1` evidence. BLIS is outside this phase.

## Objective and measured starting point

Find reproducible throughput/latency tradeoffs for each vLLM configuration on
the pinned Qwen3.8-27B, single RTX PRO 6000, vLLM 0.28 environment. The agent
may inspect every development result and raw record. The evaluator alone owns
the offered load, frozen inputs, validity decisions, sealed test, and GPU lease.

Current evaluation runs all four fixed tasks on fresh servers for each valid
candidate. One recorded candidate took **2744 s (45.7 min)**: 1350 s starting
four servers, 1181 s benchmarking, 202 s warming up. The mixed cell alone took
**800 s (13.3 min)**: 356 s startup, 50 s warmup, 392 s benchmark. Its 36
requests (17 chat, 8 agent, 5 document, 6 code) can detect large regressions;
they cannot estimate per-class p99 or a service SLA. The current search has no
automatic repeat, sealed test, or adaptive load capacity evaluator.

The fixed four tasks and all measured B0/candidate records remain valid
exploratory evidence. The new campaign must acquire its own matching B0 for
each new workload, gate, and restart/cache protocol.

## What AIPerf 0.13 gives us, and what it does not

| Native control | Use in our protocol | Limit |
| --- | --- | --- |
| `--request-count`, `--benchmark-duration` | Set request budget or timed window per trial; record actual sent/completed counts | Neither chooses statistically sufficient samples. Duration and low rate may yield too few observations; count and low rate may run for a long time. |
| `--num-profile-runs` (1–10) | Repeat each adaptive point; preserve each trial, its order, and spread | Repeats multiply GPU work. Mean per-trial p99 is not a pooled p99 or confidence bound. |
| `--search-percentile-pooling pooled` with record export | Pooled per-request percentile for a percentile search objective | Still a point estimate; it requires raw records and does not correct dependent requests or biased load selection. |
| `--search-max-iterations`, convergence and 1D planners | Limit probes, find a likely SLA boundary using fewer rates than a dense grid | Iteration-level convergence is optimization stopping, not SLA certification; per-trial `--convergence-metric` cannot be combined with adaptive search. |
| `--search-sla`, TTFT/TPOT/error filters | Mark measured points feasible after real SLOs are declared | An observed percentile at a tiny sample can flip pass/fail through noise. The recipe TTFT and TPOT flags default to **p95**; use explicit `--search-sla` to select another percentile. |
| `search_history.json`, native trial exports | Audit every proposed load, outcome, selected point, and reason for stopping | The chosen in-sample best point is not a held-out capacity result. |

AIPerf searches **client traffic fields**, such as rate and concurrency. It does
not alter or optimize vLLM launch settings. A rate search uses a rate-controlled
arrival process; it cannot simply rescale our exact fixed-schedule OPS4 JSONL.
Keep fixed-schedule replay for causal B0/candidate comparisons and use adaptive
search as a separate inner load experiment on B0 and finalists. The observed
12-request smoke had client throttling/dispatch distortion, so no capacity
claim follows from its selected best rate.

**Request count is set by our protocol, not searched by the planner.** We use
different predeclared counts across stages: 36 requests for the existing mixed
screen, more requests and independent windows for development confirmation,
and a separately sized test. Within one rate sweep, every sampled rate gets
the same request count and workload distribution, with separately labelled
repeats near a possible boundary. Store planned, sent, completed, and
metric-eligible counts for each point; a duration cap may cause these to differ.

## Workloads, split, and sample policy

1. **Development screen:** the existing frozen 36-request mixed stream, with
   exact payloads and arrivals. It is a mechanism smoke and large-regression
   filter only. Its B0 must be repeated under the same new gate protocol. Report
   each shape, even where the count only allows a descriptive median.
2. **Development replication:** independent content and arrival seeds/windows
   from the same documented class and length recipe. Pair each candidate with
   B0 at the same offered load, interleave order, and retain independent windows
   as units for run-level uncertainty. A repeated copy of the same 36 requests
   measures runtime repeatability, not new content coverage.
3. **Diagnostic suite:** existing chat, agent, document, mixed fixed tasks for
   finalists and for mechanism-specific regressions. Retain per-task results;
   do not collapse a blend into one tail percentile.
4. **Sealed test:** a separately generated/frozen content and arrival seed,
   ideally followed by a qualified trace-derived stream. Publish its class
   definitions and acceptance rule, but do not mount its payloads or outcomes
   into the proposer container. Existing OPS4 streams are already visible and
   cannot retrospectively become untouched test data.

The statistical unit for a service-level percentile is an eligible completed
request in a defined class and measurement window. Save sent, completed,
failed, timed out, canceled, and metric-eligible denominators separately.
Predeclare the minimum **per-class** samples and window count from the SLO
percentile/confidence rule before a pass/fail claim. For example, with zero
violations, approximately **299 independent requests** are needed merely to
place a one-sided 95% upper bound of 1% on violation probability
(`log(0.05)/log(0.99)`, rounded up). Correlation/bursts demand independent
windows and may require more. This is a lower-bound illustration, **not** a
universal p99 sample target or a guarantee from 299 requests. AIPerf does not
perform this choice for us. At the current 0.1 request/s mixed rate, 300
requests require about 50 minutes of dispatch before startup/drain; raising
rate just to acquire samples changes the tested load.

## Staged evaluator and decisions

| Gate | Evidence and promotion decision | Time implication |
| --- | --- | --- |
| 0. Static | Validate typed server knobs, compatibility, hashes, duplicate candidate, resource feasibility. Save rejection reason without GPU run. | Seconds, to measure. |
| 1. Fast fixed-load screen | Fresh-start B0-matched 36-request mixed stream. Require complete accounting; no error; valid open-loop dispatch, queue and drain. Reject only a material regression larger than measured B0 run-to-run variation. Do not promote on p99 here. | Measured cell 13.3 min versus 45.7 min for four cells. |
| 2. Replicated development | Candidate and B0 on same load across independent dev windows, alternating order. Compare per-class p50/p90, throughput, errors and uncertainty. Escalate ambiguous effects instead of forcing a winner. | Cost scales with number/duration of selected windows. |
| 3. Mechanism diagnostics | Four fixed OPS4 tasks (or justified subset plus full suite before finalist). Report per-task p50/p90/p99 and full records. Check long prefill, chat decode, mixed interference separately. | Current full fresh-server reference: 45.7 min. |
| 4. Adaptive load curve/capacity | On B0 and finalists, map the open-loop rate curve under declared bounds; keep concurrency ceiling nonbinding. Without numeric SLOs, label it exploratory. With SLOs, use `smooth_isotonic` for a noisy, approximately monotone boundary; compare `monotonic_sla` and BO/TPE on the same B0 budget. Preserve all points. | Every iteration sends real requests. Startup can be amortized within one server run; total may exceed 45 min for enough points/repeats. Measure it. |
| 5. Sealed fixed-schedule test | Freeze selected configuration(s) before exposing test outcomes. Run matched B0 and candidates at predeclared load(s), independent content/arrival windows and sample budget. Enforce SLO, error, validity and uncertainty rules. | Paid for a small finalist set, not every proposal. |

Gate 1 is implemented for the separate `fast-gate-v2` campaign. Stage 4 has
an exploratory `iar adaptive` command: one fresh server, disjoint warmup,
AIPerf rate probes, full native history, per-point validation, and report
plots. It has **not passed a real GPU pilot** and cannot claim an SLA boundary.
Stages 2 and 5 are not implemented because independent development and sealed
test manifests are not yet frozen. A same-server four-task bundle
could avoid three starts (roughly 17 min of the recorded 22.5 min startup), but
must be experimentally validated for cache residue, order and warmup effects;
do not pool its values with fresh-server cells.

Set screen margins from multiple B0 runs, not an arbitrary percentage. An
invalid/overloaded trial is neither a win nor a zero-latency sample. Near an
SLO boundary, repeat the same load in distinct windows and confirm with a
fresh frozen schedule. If a result cannot resolve a decision within budget,
mark it **inconclusive** rather than declaring a pass.

## Metrics and profiling made visible to the agent

Every cell and adaptive point must expose: server/config hashes; workload and
seed; configured and realized rate; sent/completed/error/censored counts;
scheduled-vs-actual dispatch lag; warmup, dispatch and drain durations; request
and output-token throughput; TTFT and per-request TPOT p50/p90/p99; per-class
counts/quantiles; queue peak and timeline; GPU memory/utilization and available
vLLM metrics; raw per-request exports; client/server logs; validity reasons.
Label absent telemetry as absent. TPOT is one average decode interval per
request, not fleet output tokens/s and not an individual-token tail.

For each candidate, show its **matched B0 delta** and evidence grade. For load
search, ingest every `search_history.json` iteration and native trial export,
including infeasible/failed points. Plot configured and realized rate against
throughput, TTFT p50/p90/p99, TPOT p50/p90/p99, errors and queue/drain; mark
SLO feasibility and repeated-point variation. Draw Pareto fronts only from
valid, comparable points with the same workload/protocol, and display
uncertainty rather than treating a noisy nondominated point as an established
improvement. Preserve all dominated points for diagnosis.

Use p50 and p90 to understand typical latency and mechanisms; p99 remains a
visible tail diagnostic. Adding all quantiles to one high-dimensional frontier
would make many points trivially nondominated. Choose declared service
constraints and capacity/goodput objectives separately. Define goodput only
after the per-request service deadlines and denominator are settled.

## SLA contract to fill from product needs and B0 feasibility

Do not copy B0 observed percentiles into an SLA. The owner supplies acceptable
TTFT and TPOT deadlines and the percentile for each meaningful class, an error
limit, offered load/time horizon and output-length context. B0 p50/p90/p99 and
load curves show whether those limits are feasible on this model/GPU. Chat and
long-document prompts need distinct requirements. The mixed aggregate alone
cannot certify either class. AIPerf's convenience `--ttft-sla-ms` and
`--tpot-sla-ms` are p95 filters; when our contract says p90 or p99, wire the
exact percentile with generic `--search-sla` and verify the normalized
per-request calculation.

Suggested versioned contract fields, with values pending the owner:

| Class | Offered RPS/window | TTFT percentile and deadline | TPOT percentile and deadline | Error limit | Minimum samples/windows |
| --- | --- | --- | --- | --- | --- |
| Chat | TBD | TBD | TBD | TBD | Derived from chosen confidence rule |
| Agent/code | TBD | TBD | TBD | TBD | Derived from chosen confidence rule |
| Document | TBD | TBD | TBD | TBD | Derived from chosen confidence rule |

Until these values exist, run throughput/latency **exploration** and label all
adaptive points as observed, not SLA-compliant capacity. An exploratory rate
curve may identify a knee, but neither the knee nor the planner-selected best
rate becomes an SLA boundary without an actual service contract and fresh
confirmation.

## Implementation acceptance and inspection checkpoints

1. **Protocol and B0:** check the frozen dev/test manifests, disjoint mounts,
   planned sample counts, fixed-load B0 repeats and measured repeat noise. Show
   the user these assets before allowing candidate rejection by Gate 1.
2. **Fast gate:** execute known B0 and the existing candidate with new matched
   rules. Show validity, per-class metrics, raw paths, decision reason, wall
   time, and whether the coarse gate would falsely reject a plausible finalist.
3. **Adaptive pilot:** on a stable B0 server, run a bounded one-dimensional
   search with explicit request count or window, disjoint warmup, sufficient
   client concurrency, full record export and at least two trials near the
   boundary. Inspect dispatch lag and all points before accepting the planner.
   The prior 12-request smoke is a negative control for this validity check.
4. **Reliability comparison:** repeat B0/candidate at matched rates and unseen
   windows. Report total GPU minutes per decision, point-to-point variation,
   interval widths, and agreement with the full fixed suite. Only then claim
   the upgraded process is faster or more reliable.

### Primary sources and local evidence

- [AIPerf 0.13 adaptive search reference](https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/sweeping/bayesian-optimization.md): search controls, repeated trials, percentile pooling, SLA filters, planners, search history.
- [AIPerf 0.13 timing modes](https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/benchmark-modes/timing-modes-reference.md): request count, duration, fixed schedule, rate modes and warmup.
- Local installed flag definitions: `.venv/lib/python3.12/site-packages/aiperf/config/flags/cli_config.py`.
- Local measured time: `results/2026-10-17-ops4-first-search/candidate/evaluation-timings.json`.
- Local adaptive smoke: `infra/AIPERF_ADAPTIVE_FINDINGS.md`.
