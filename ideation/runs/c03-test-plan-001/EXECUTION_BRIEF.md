# C03 execution brief — logical request counts for DSpark drafting

**Approved execution contract.** The user authorized execution on 20 October 2026. Live progress and evidence are recorded in [c03-execution-001/status.json](../c03-execution-001/status.json). The sections below preserve the reviewed plan and its original planning snapshot. This is the concrete sequence to execute after the plan is reviewed. Use **this node only (`jl-vm-541077`, 223)**, the existing **`latency-2xdep4-sla.yaml`** profile, and **Mooncake trace replay speed 0.5× in every arm**. Earlier references to host 219 or changing the offered rate do not apply.

## The corrected baseline is complete

The local median run `20261020-145417` is the supplied baseline: its eight GPU UUIDs match this node. **4,001/4,004 requests succeeded**, with three errors (0.075%), p99 replay lag **4.335 ms**, and no degraded replay. It passes the existing completion/error/replay fidelity checks. Its long-output ITL p50 is **35.885 ms**, TTFT p99 **12.572 s**, and end-to-end latency p99 **78.665 s**.

Its `eligible: false` means the service misses the configured latency/output-speed SLOs; it does **not** mean the corrected benchmark failed to finish. Keep this result. A useful C03 improvement can still miss those SLOs, and must be reported that way. A new paired A run is needed to control drift and match the treatment launch, not to erase or “repair” the completed baseline.

The corrected burst run `20261020-145708` completed all 4,220 requests, but all eight GPU UUIDs differ. It is contextual evidence, not this node's control. The held-out burst A/B will therefore be collected **on this node** at 0.5×. The earlier failed 1× runs are superseded for this experiment. [Full baseline audit](baseline-audit.md) records counts, errors, hashes, client configuration, GPU identity and limitations.

## Exactly what stays fixed

| Item | Frozen choice |
|---|---|
| Host | Current local node only; all A/B arms use its same eight GPUs |
| Profile | `/home/ubuntu/Deepseek_serve/serving/h200/vllm/profiles/latency-2xdep4-sla.yaml`, SHA256 `edb4c68cb4ee72415abe65c077683a8f88942bfcc8fff5833270ba05cdddcab8` |
| Layout | Two TP1/DP4/EP4 replicas, two API workers per replica, max sequences 64, max batched tokens 16,384 |
| Speculation | DSpark k5, probabilistic/block rejection, adaptive verification off |
| Other serving settings | Same model/tokenizer revision, FP8 KV/block size 64, prefix caching, Engram, graph captures, observability and router behavior |
| Serving environment | Existing `/home/ubuntu/Deepseek_serve/.venv` launcher plus the existing pinned vLLM container and binary dependencies; no installs or upgrades |
| vLLM identity observed | `0.30.1rc1.dev493+gac9126e58`; image `sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`; reattest before execution |
| Benchmark client | Existing `/home/ubuntu/Deepseek_serve/.venv-aiperf`, AIPerf 0.13; this is what the corrected run used, not a newly created environment |
| Workload | Exact existing Mooncake median/scaled/0p5x trace, then the fixed burst/scaled/0p5x; fixed schedule, workers 256, 120 s warmup, complete drain |
| Evaluator | Existing runner/analyzer/campaign, `common.log_level: info`, unchanged SLO definitions; explicit `--no-sync` |
| Service sampling | Preserve observed temperature 1, top_p 1, top_k 0, unset request seed, ignore_eos true and watermarking true; client seed is not server RNG seed |

The `.venv` is a launcher environment; vLLM itself executes inside the existing container. Preserve both that environment and the separate already-used AIPerf client. Do not pip-install vLLM into the host environment or replace the container with upstream main.

The latest read-only check, **20 October 2026 at 21:12 IST (15:42 UTC)**, found no running serving containers and no listeners on ports 8000/8100/8101. None was stopped or started by this planning work. Earlier source/capture observations remain documented, but the execution phase must restore/attest the chosen baseline before requests. If the old router executable cannot be established, explicitly freeze the restored A router and use it identically in B; the old run then remains historical context rather than proof of identical runtime. A router change is not part of C03.

## Agent responsibilities and boundaries

| Role | Agent and responsibility | Must not do |
|---|---|---|
| Orchestrator | Root: freeze this scope, review handoffs, schedule one arm at a time, verify artifacts and report the verdict | Write the optimization and then judge it using its own invented oracle |
| Evaluator designer | `c03_evaluator`: define independent expected behavior, metrics, gates, coverage and falsification rules | Implement the candidate or evaluator; revise thresholds after seeing B |
| Evaluator builder | `c03_evaluator_builder_review` for planning, then the separate evaluator-builder role: implement only the frozen fixtures, observation probe and comparison/reporting; reuse existing runner/scorer | Change the optimization, workload, SLOs or designer's expected answers |
| Optimization builder | `c03_dev_review`: adapt the final upstream semantics, isolate Python files and prepare reversible backend launch commands | Edit evaluator tests, expected values, scorer, thresholds or measurement exclusions |
| Baseline auditor | `c03_baseline_audit`: independent provenance and baseline-data review | Treat SLO failure as missing data, pool hosts, or certify candidate performance |

Evaluator code and optimization code remain separate patches with separate ownership. An observation hook in a vLLM file still belongs to the evaluator builder and is applied identically to diagnostic A/B. The optimization builder does not author the expected test result. The designer reviews the evaluator implementation before B results are unblinded. The orchestrator checks that candidate diffs cannot silently modify the evaluator or profile.

## The hypothesis, in operational terms

The existing DP synchronization already knows the maximum **real** request count. In a target FULL-graph path, the installed code replaces that value with target graph capacity. DSpark inherits DFlash's drafting path, which then uses that capacity to size the drafter and can round up again to a draft graph bucket.

The **final** #58984 change gives `DPSyncState.num_reqs` the logical DP-wide maximum, keeps graph capacity in `BatchExecutionDescriptor`, and makes online dummy inputs/metadata consistent with the logical bound. Do not implement the earlier intermediate `num_reqs_unpadded` field or blindly cherry-pick a patch against a different version.

The planned optimization touches three installed Python source files: `dp_utils.py`, `spec_decode/dflash/speculator.py`, and the installed `spec_decode/autoregressive/speculator.py` compatibility path. No sampler/kernel/dependency change, new collective, graph-bucket tuning or smaller startup allocation is part of C03. [Implementation review](/home/ubuntu/Deepseek_serve-c03/C03_IMPLEMENTATION_REVIEW.md) traces the actual call sites and exact source hashes.

Observed capture tables distinguish target width 6 from draft width 5. A source-derived positive case is logical DP maximum 5: target capacity 6 makes current drafting select capacity 7, or 35 draft rows; the treatment should select capacity 5, or 25 rows. Logical maximum 9 selects 50 rows in both arms. These are test expectations, not measured speedups. The real traffic must actually hit useful boundaries.

## Execution order and falsification checks

| Step | Concrete action and required artifact | Stop/decision |
|---|---|---|
| **0. Freeze the control** | Record local UUIDs, restored/current image and source hashes, actual router executable/settings, full launch arguments, graph tables, evaluator/profile/trace/client hashes and idle/drained state. Match the selected baseline revision. | Different host/config/dependencies, unexplained runtime drift or incomplete identity: do not compare arms. Equivalent logical-count behavior already present: not applicable. |
| **1. Build the evaluator first** | Independent builder reuses existing AIPerf/scorer and adds only the missing bounded dispatch observation and focused fixtures. Designer reviews the reference and deliberately wrong negative controls. No optimization yet. | If the reference calls the patched helper to compute its expected answer, or a bad-count control passes, evaluator is not ready. |
| **2. Prove baseline exposure** | Diagnostic A on median 0.5×; capture local real counts, DP maximum, target capacity, draft requested/executed rows, selected graph and dummy/startup state across all ranks. Use burst 0.5× only if median lacks useful exposure. | Require >=1,000 online dispatches total, >=100 per replica, all ranks observed; mechanism falsification additionally needs >=100 opportunities for a smaller executed bucket, >=20 per replica. Count a replica/DP step once, with its four rank records as evidence. No useful exposure: inactive in that workload. Missing ranks/rare events: inconclusive. If only burst exposes the mechanism, retain that lead and defer service confirmation to a separately declared burst-primary test; median remains the primary here. |
| **3. Build only the scoped treatment** | Builder adapts the final three-file semantics against byte-identical installed originals. Review the diff and shared call sites. Use read-only per-file mounts into fresh containers using the same image; prepare plain baseline/rollback commands. | Any unrelated change, source/hash mismatch, changed dependencies or startup graph inventory blocks handoff. No live package editing. |
| **4. Pass independent correctness** | Exercise real/dummy/empty ranks, every graph boundary, cold capture, replay, input/slot/KV metadata, cancellation/wake and unchanged rejection semantics. Run the same fixtures on A/B; verify independent positive and negative controls. | Wrong valid row, probability/RNG ownership, bounds error, deadlock, corrupt KV or lost/cross-request token: reject/repair before service timing. Startup max target 384 / draft 320 capacity must remain intact. |
| **5. Show the mechanism and screen service value** | Separate diagnostic A/B proves fewer **executed** draft rows on eligible events, then one unprofiled median A/B pair at 0.5× with matched startup/cache/warmup. No simultaneous arms or background campaign. | No row reduction despite useful opportunities falsifies the mechanism. Promote only a valid pair with positive primary point gain and neither observed tail regression >3%. An unfavorable valid screen is deferred/inconclusive; do not repeat it until it wins. |
| **6. Confirm a promising result** | Five full median A/B blocks in AB/BA/AB/BA/AB order, paired client seeds 101–105 and unique IDs; preserve service RNG defaults. Then a fresh untuned local burst A/B at 0.5×. | Apply the predeclared rules below. Do not tune against burst or stop repeatedly as soon as a favorable p-value appears. |

If burst was used for the exposure diagnostic, it is no longer wholly unobserved; its service endpoints remain held out, and neither workload nor thresholds may be tuned from that diagnostic.

The launch-only source-mount and backend-handover support may be prepared before Stage 2 so the evaluator-owned probe runs in an isolated container. Review that support independently; it contains no C03 semantic change. The optimization port still waits for useful baseline exposure.

Stage 2 uses diagnostic-only probes. Service measurements disable them in both arms, unless identical negligible overhead is independently established. A stopped-short exposure run is never a service result. Save raw failures as well as successes; sampling acceptance alone is not a correctness test. No new load generator, broad benchmarking framework or mandatory profiler setup is required.

## What will count as success or falsification

**Primary endpoint:** the existing scorer's long-output (>=50 tokens) median ITL on **Mooncake median 0.5×**. It is AIPerf's token-normalized latency after the first content chunk, not raw SSE spacing. Keep its exact definition and first-chunk/fallback coverage visible; changed chunk packing cannot be credited as less draft work.

The practical 2% gain and 3% guard thresholds are chosen for this experiment from the fresh evaluation design; they do not replace the production SLOs. A useful confirmed C03 result requires all of the following:

1. Correctness and measurement fidelity pass, and useful exposure yields fewer actual draft rows.
2. Paired run-level ITL improvement has a 95% interval whose lower bound is at least **2%**.
3. The upper paired 95% bounds on TTFT p99 and end-to-end p99 regressions are at most **3%**; failures/replay do not worsen past the existing fidelity limits.
4. Local burst shows no new correctness/fidelity failure or >3% observed tail regression in its screening pair. One burst pair is a regression screen, not a precise burst improvement claim.

Intervals use **whole paired runs**, not requests or ranks: gain per block is `100*(1-B/A)`, using the mean paired percent gain, 10,000 paired-block bootstrap resamples, Python random seed 20261020 and linearly interpolated percentile bounds. The tail intervals use the same sampled blocks; these are per-endpoint intervals. Five pairs are a minimum, not guaranteed statistical power. The decision occurs once after the five valid blocks. An invalid pair retains both arms and its reason; after an identified external cause is resolved, at most two whole-pair replacements are allowed with the same seed/order and new IDs. A third invalid pair stops confirmation as inconclusive. Candidate correctness failures are stops, not replaceable noise. If the upper interval is below 2% despite valid exposure/correctness, reject a useful service gain for this scope while retaining the row-saving result. If the interval crosses 2%, report inconclusive. If correctness fails, stop irrespective of a faster time. If service SLOs still fail, an improvement remains **SLO-ineligible**; do not promote it as production-qualified or silently relax the scorer.

Existing fidelity bounds stay completion >=99.5%, error <=0.1%, nondegraded replay and replay-lag p99 <=500 ms, complete artifacts and adequate server-token/rank coverage. The existing scorer separately requires at least 100 total attempts and at least 100 long-output records. Report exact request failures, all latency distributions, qualified goodput, output lengths, acceptance, cache hits, KV/preemption and graph/runtime changes. No maximum-capacity claim can come from one fixed offered rate. Existing $36/hour cost fields are excluded from conclusions.

## Worktrees, commands and record keeping

Already created:

- `/home/ubuntu/AutoResearch-Inference-c03`, branch `experiment/c03-plan`: brief, frozen evaluator design, baseline audit, triage and evidence receipts.
- `/home/ubuntu/Deepseek_serve-c03`, branch `experiment/c03-logical-draft`, baseline commit `cc479a4`: isolated future optimization/launch work. Its runner, analyzer, campaign and profile match the corrected baseline hashes. The original checkout's unrelated uncommitted delivery-default change remains untouched; use explicit `--no-sync`.

Use the exact command template in [evaluator-design.md](evaluator-design.md), from the serving worktree with the **absolute existing client interpreter and binary**. It supplies the original profile path, `--trace-speedup 0.5`, workers 256, warmup 120 s, all three metrics URLs and a separate C03 results root. The documented command includes `--dry-run`; it has **not** been executed. Each arm gets a unique directory; old baseline results are never overwritten. No worktree environment or symlink is needed.

The bounded correctness matrix and intentionally failing controls are specified in [evaluator-design.md](evaluator-design.md) and mapped to reusable tooling in [evaluator-builder-review.md](evaluator-builder-review.md). CPU checks cover logical maxima 0–64; GPU checks target six maxima and distinct preparation branches. Exact row/metadata/RNG ownership is required. No generic numerical tolerance or broad sampler certification is introduced.

Before execution, keep one small manifest with the control/treatment file hashes, reviewer-owned evaluator hash, exact commands, profile/trace/client/image/router identities, arm/order/seed/cache state, and expected output directory. Each stage appends a row to `TRIAGE.md` and a machine-readable verdict record pointing to raw evidence. Record applicability, activation, correctness, mechanism, service and SLO verdicts separately. A scorer exit 1 for an SLO-ineligible completed run is not automatically a client crash; inspect its artifacts.

Rollback removes only the treatment source mounts on the next baseline-container launch, keeping the same image and explicit backend arguments. Keep or restore the separately attested router unchanged. Verify baseline file hashes, graph inventory and health before subsequent traffic. The shared `.venv`, installed image and original checkout are not reverse-patched because they are never modified.

## Time budget and first authorized action

At 0.5×, a 600-second source window becomes approximately **1,200 seconds of arrivals**. One full diagnostic costs about 22 minutes plus drain; the median screening pair costs 44 minutes plus drain/startup. Five median pairs cost **220 minutes** of arrivals and warmup before drain/startups; one burst pair adds 44 minutes. Correctness and server cold starts are additional. Stop cheaply at source/exposure gates if the mechanism is absent.

This planning stage has performed read-only inspection, created worktrees and written documents. **No experiment, source adaptation, package change or service launch has run.** After this brief is reviewed, the implementation phase begins with the independent evaluator/probe and frozen reference, then the baseline exposure check. The optimization builder starts the C03 semantic source adaptation only after useful exposure is established; launch-only isolation can be prepared first for the independent diagnostic.
