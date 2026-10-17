# OPS4 evaluation redesign: proposal for review

Status: design proposal, **not implemented**. Current authoritative campaign remains
`configs/campaign-ops4.json`; this note does not change its qualification or results.

## What the current evaluator actually does

The pinned AIPerf 0.13 adapter sends the exact JSONL request bodies and timestamps
with `--fixed-schedule --fixed-schedule-auto-offset --request-count N --random-seed 42`.
The source schedules came from seeded Poisson arrivals, but the search run replays
their captured realization. It does not resample prompts or interarrival gaps for
each configuration. The four streams contain 307 chat, 27 agent, 18 document, and
36 mixed requests. Each is a single-turn, independent, synthetic diagnostic.
Warmup is three distinct synthetic requests per cell; every task starts a fresh
vLLM process. Request accounting, output length, client schedule lag, queue and
drain checks determine validity. The twelve frontier coordinates are output
tokens/s, TTFT p99 and TPOT p99 for **each** stream. No SLA or confirmed capacity
is defined.

The controller has a one-scenario triage path, but `fixed-four-v1` explicitly
rejects a triage scenario and evaluates all four streams for every valid proposal.
The first candidate took 2744 s: 1350 s for four server starts, 1181 s of
benchmarks, 202 s of warmup, with small remainder. There is no automatic
matched-repeat or held-out confirmation gate. The `heldout_outcomes_visible_to_proposer`
policy field states an intention; no held-out task exists in this campaign yet.

The adapter computes TTFT p99 and TPOT p99 from **one value per successful
eligible request**, using linear interpolation of the sorted values. TPOT is each
request's average decode interval, not the distribution of individual token gaps.
For 18 requests, sample p99 is 83% of the maximum plus 17% of the second-largest
value; for 36, it is 65% of the maximum plus 35% of the second-largest. Even a
307-request chat p99 depends on roughly the slowest four requests. The chance of
seeing at least one event from a true 1% tail in `n` independent requests is
`1 - 0.99**n`: 17% at 18, 24% at 27, 30% at 36, 95% at 307.
Temporal correlation lowers the effective sample size. These figures illustrate
why one window's p99 is an observed quantile, not a reliable p99 SLA bound.

## Design choice: one main dev stream, stratified measurement

Use **one frozen mixed open-loop stream** as the cheap search/development task,
with each request tagged `chat`, `agent`, `document` or `code`. Freeze both bodies
and arrival credits before B0. The stream needs enough concurrent prefill/decode
interaction to activate the serving knobs and must be calibrated at a drainable
load. A single aggregate throughput/latency scalar is insufficient: a change can
help short chat while seriously harming document requests. Report aggregate
successful output throughput plus per-class counts, TTFT, TPOT, failures, queue
and drain. SLA-compliant goodput becomes meaningful only after SLA bounds exist.
Keep the four existing cells as mechanism diagnostics and regression checks, run
on finalists rather than on every candidate. Do not call the mixed stream
"production" until its class and arrival distributions are grounded in a trace.

One longer mixed benchmark can simplify the primary comparison, but it is not
automatically faster or statistically sufficient. At the current mixed source
rate of about 0.1 request/s, 300 requests would take about 50 minutes of
dispatch alone, before server startup and drain; it would still contain only
about 45 document requests at the engineered 15% weight. Raising the arrival
rate solely to collect more samples faster changes contention and may overload
the system. Therefore use the existing 36-request mix only as a coarse early
screen, then pay for longer/repeated dev and test windows on survivors.

**Dev:** version and publish the generated stream, fixed random seed, source
weights, schedule hash, tokenizer, prompt/token distributions, output policy,
endpoint options and calibration evidence. The agent sees its B0 and candidate
results. Use independent seeds/windows within dev for replication; a repeated
copy of the same requests adds run-to-run evidence but does not expand content
coverage. Pair B0/candidate runs on the same frozen stream and alternate run
order to reduce drift. Retain all raw per-request exports.

**Test:** separately generate/freeze an unseen mixed stream with different
content and arrival seeds (and ideally a qualified trace-derived stream), then
seal its payload, schedule and outcome paths away from the proposer mount. Keep
test class definitions and test protocol public so the objective is known. Run
test B0 and a small predeclared set of finalists once selection is frozen; repeat
only for a stated uncertainty decision. Publishing hidden test results to the
agent during search would turn it into another dev set. Existing four OPS4 task
bodies/schedules and B0 results are already visible to the agent, so they cannot
retroactively become an untouched held-out set. A future genuinely held-out
suite needs new assets and access controls, not just a JSON flag.

## Proposed gates and decision rules

| Gate | Work | Promotion rule | Evidence label |
| --- | --- | --- | --- |
| 0. Static | Domain, config compatibility, launcher validation, duplicate and resource checks | Invalid/duplicate stops before GPU | No performance claim |
| 1. Fast dev screen | One fresh-start mixed stream with fixed arrivals and per-class exports | Full accounting, no failures, acceptable lag/queue/drain; reject **clear material** degradation, with conservative margin set from B0 repeat noise | Provisional screen |
| 2. Dev repeat | Promising candidate and interleaved matched B0, on a second dev seed/window | Per-class effect and uncertainty reviewed; no class has a disqualifying regression | Replicated development finding |
| 3. Diagnostic suite | Existing chat, agent, document, mixed streams, selected for mechanism/regression evidence | All valid; compare all primary and diagnostic metrics; retain tradeoffs as separate Pareto points | Broader diagnostic finding |
| 4. Sealed test | Selected configuration(s) and matched B0 on unseen frozen test stream | Predeclared per-class constraints, complete accounting, bootstrap/paired uncertainty intervals and no disqualifying regression | Held-out result |

Start with Gate 1 on current frozen mixed task to prove implementation and time
cost: one measured cell took 800 s, including 356 s startup and 50 s warmup.
Its 36 requests are enough for a coarse smoke/large-regression filter, **not**
for tail promotion; the document stratum has only about five requests at the
declared mix weight, so per-class p99 cannot be a rejection rule at this gate.
A shorter clipped stream would require a new protocol and
matched B0; it must still exercise the target mechanisms. Saving three server
starts reduces the screening time from ~46 min to ~13 min on the recorded run.
Turning on the existing triage branch requires a **new campaign/protocol version**:
the present qualification hash and `fixed-four-v1` rule would reject an edited
campaign, and the triage branch requires its own matched B0 cell. It cannot
silently reuse the current `screen` B0 result.
Further real-GPU speedups require reducing measured startup work or an
explicitly different cache/restart protocol; reusing a live
server changes the comparison and may contaminate KV/cache state.
The most direct real-GPU follow-up is to test a **same-server four-task bundle**
with explicit cache reset, disjoint warmup, randomized task order, and a new
matched B0. Avoiding three of four measured starts could save roughly
17 minutes per finalist, but the current artifacts do not validate that
protocol and its results must not be pooled with fresh-server cells.

Set gate margins **after** measuring B0 repeat variation, not from the one B0
point. Use per-request distributions, run-to-run variability, and bootstrap
intervals at the run/window level when multiple windows exist. Do not pool
different classes into one p99 and call it evidence of all-class tail behavior;
do not average per-run p99 values as though each run were one request. For a
strict p99 SLA, choose an application threshold and a sample-size/confidence
protocol before running the test. AIPerf's sample p99 alone cannot certify it.

Keep offered load fixed for A/B causal comparison. If sustainable capacity under
TTFT/TPOT SLA is added as a separate objective, first declare numeric SLA bounds,
then search request rate/concurrency **inside** each finalist configuration with
AIPerf and confirm the discovered boundary on a fresh stream. Adaptive load
search changes the workload and therefore cannot directly replace the fixed-load
dev screen. Do not treat a planner's in-sample best point as a held-out capacity
measurement.

## What AIPerf simulates, and what it does not

AIPerf can synthesize token lengths, output caps, random/constant/gamma arrival
patterns, concurrency ceilings, and timestamped replay. It records request
metrics and server telemetry; adaptive search can tune load dimensions. Our
current adapter uses its **fixed schedule**, not its adaptive search. Synthetic
random text plus forced output length tests scheduling/decode behavior but does
not establish semantic answer quality, real user think time, dependent sessions,
production class frequencies, cache reuse, or business SLAs. The current
`cold_stream` protocol deliberately suppresses cross-request reuse.

The next implementation checkpoint is one versioned dev stream and matched B0
repeat policy, followed by a one-task gate wired into the controller. Measure its
wall time and false-rejection risk against known B0/candidate artifacts before
allowing it to discard configurations. Then create a physically isolated test
stream and run finalist confirmation.

## References

- [AIPerf timing modes](https://github.com/ai-dynamo/aiperf/blob/main/docs/benchmark-modes/timing-modes-reference.md): fixed schedule, request-rate, concurrency and sampling options.
- [AIPerf arrival patterns](https://github.com/ai-dynamo/aiperf/blob/main/docs/tutorials/arrival-patterns.md): Poisson/gamma/constant controls and fixed-schedule incompatibility.
- [AIPerf trace replay](https://github.com/ai-dynamo/aiperf/blob/main/docs/benchmark-modes/trace-replay.md): recorded timestamps and optional opt-out.
- [AIPerf metric definitions](https://github.com/ai-dynamo/aiperf/blob/main/docs/metrics-reference.md): request-level TTFT/ITL and aggregate output throughput.
- Pinned local source: `.venv/lib/python3.12/site-packages/aiperf/timing/strategies/fixed_schedule.py` and `aiperf/metrics/types/inter_token_latency_metric.py` (version 0.13.0).
- Recorded timing: `results/2026-10-17-ops4-first-search/candidate/evaluation-timings.json`.
