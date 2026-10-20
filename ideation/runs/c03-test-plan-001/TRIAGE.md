# C03 triage ledger

Planning snapshot, 20 October 2026. All future stages use this local node, the exact latency-2xdep4-sla profile and 0.5× trace speed. No experiment has run under this plan.

| Gate | Current status | Evidence / consequence |
|---|---|---|
| User scope | Fixed | Current node 223; same profile; 0.5× all arms; plan before execution |
| Isolated work | Ready | Research and serving worktrees created; serving worktree fast-forwarded to current committed `cc479a4`; unrelated original edits preserved |
| Corrected local baseline fidelity | Pass for supplied run | Median 145417: 4,001/4,004 successes, 3 errors, 4.335 ms replay p99, UUID match; baseline-audit.json |
| Supplied baseline service SLO | Fail, retained | Existing score remains ineligible; this does not invalidate fidelity or prohibit a scoped latency comparison |
| Saved burst as local control | Not usable | All 8 GPU UUIDs differ; fresh local burst pair required for holdout |
| Source behavior | Missing C03 observed | Earlier live source hash/call-path inspection and final archived #58984 semantics; reattest on future launch |
| Live service at final planning check | Stopped/absent | 21:12 IST: Docker process list empty and no listeners on 8000/8100/8101; no stop/start performed by planning agents |
| Exact actual router identity for experiment | Pending fresh attestation | Keep existing environment; do not silently change Python/runtime. Freeze restored A router and preserve in B |
| Evaluator design | Contract finalized for user review | evaluator-design.md; separate designer and builder ownership |
| Evaluator-builder feasibility | Reviewed independently | Existing runner/scorer retained; bounded probe/fixtures/report reader; coverage and statistical rules resolved in evaluator-design.md |
| Evaluator implementation/probe | Not started | Existing artifacts lack the joined logical/target/draft-row triplet; minimal independent observation/fixtures planned |
| Useful removable rows on 0.5× traffic | Unknown | Source-derived M=5 positive / M=9 same-bucket examples are not observed workload activation |
| Optimization implementation | Not started | Planned narrow three-file adaptation; no package/image update |
| Correctness | Not run | Independent metadata/dummy/distributed/graph/sampling fixtures required |
| Mechanism measurement | Not run | Need changed executed rows and coherent ranks; smaller requested count insufficient |
| Screening/confirmation | Not run | Conditional on earlier gates; unique sequential runs and full-run paired inference |
| GPU experiments / service mutations by this task | Zero | No benchmarks, model generation, candidate launch, restart or dependency installation |

For each future stage append timestamp, actor/role, input hashes, actual command, artifact paths, decision and reason. Do not overwrite this planning state, raw failures or prior verdicts. No passing performance result may substitute for a failed correctness gate.

## Execution authorized

On 20 October 2026 the user approved execution ("ok go ahead"). Implementation and experiment receipts now live in [c03-execution-001](../c03-execution-001/status.json). The planning snapshot above is retained. Initial recheck found no serving containers/listeners and all eight GPUs idle. Separate evaluator builder and launch-isolation developer have started; C03 semantic adaptation waits for useful exposure.

## Execution checkpoint — 2026-10-20T16:21:29.385165+00:00

Control identity and read-only source mounts pass attestation. Original environments preserved. Independent production CPU A checks pass within their documented controlled-double scope. Diagnostic A model loading is active on all eight workers; no requests or semantic port yet. Read-only process sampling finds continued checkpoint page faults, ample RAM and no OOM/reclaim. Prior same-profile archived startup took approximately 21 minutes, so this interval alone is not evidence of deadlock. GPU/integration/capture/exposure gates remain open. See [execution evidence](../c03-execution-001/README.md).

## Execution checkpoint — 20 October 2026, Gate 2

Diagnostic run `20261020-163428` completed 4,003/4,004 requests with profiling replay p99 5.862 ms and replay_degraded=0. Normal exports are complete; service SLO remains ineligible. The apparent 104-second replay warning belongs exactly to concurrency-paced warmup, as also observed in the retained corrected baseline. All eight rank/source/capture invariants pass. The strict in-profiling lower bound is 21,396 unique dispatches and 2,063 useful smaller-bucket opportunities. Independent review authorizes the narrow three-file port. Baseline lifecycle cancellation/drain succeeds, but the exact seeded T0 reference differs in reasoning/token count; this failure remains open for evaluator-only diagnosis before judging B. No candidate runtime or performance test has started. See [live execution record](../c03-execution-001/README.md).

### 2026-10-20T17:11:37.805724+00:00 — Baseline fixed-rank control

The prospective eight-request no-cancellation control failed exact repeatability in all four pairs (replicas 0/1 × internal ranks 0/2). All eight router/engine routing attestations and all nine strict drains passed. Completion-token pairs were 33/15, 64/15, 22/34, and 22/31. This invalidates the baseline deterministic-output prerequisite; it does not establish a cancellation defect. Original failed receipts remain. The exact-output lane is stopped with no retries or tolerance, and no B runtime has launched. The separate evaluator designer is assessing a controlled integration alternative; the optimization remains frozen. Evidence: ../c03-execution-001/service-rank-control-A.json and A-rank-control-summary.json.

### 2026-10-20T18:19:07.205405+00:00 — B composite correctness accepted; service screen next

The common controlled V2 alternative was prospectively designed and validated on A before B. Both arms passed its fixed 20-request matrix and independent request-linked abort review, alongside actual CPU/GPU row-transport/verifier fixtures, startup inventories and coherent diagnostic graphs. Earlier free-form repeatability failures remain stopped and retained; no unrestricted numerical-equivalence claim is made. B diagnostic exports are complete (4,003/4,004, replay p99 5.004 ms, degraded false), with SLO ineligibility retained. All 1,941 stronger B opportunities select the predicted smaller draft graph; the strict profiling lower bound is 1,350. Independent evaluator accepted the composite gate and authorized the frozen fresh, probe-off A/B median screen. No service performance result exists yet. See ../c03-execution-001/evaluator-review.md.

### 2026-10-20T19:59:45.549350+00:00 — Execution complete at unfavorable fixed screen

Fresh probe-off A/B median0.5x screen completed with accepted measurement/source/process identity and all six independently reviewed prerequisites in the documented bounded correctness scope. A4003/4004 and B4004/4004, replay p994.871/5.050ms, no degraded replay; both are complete but SLO-ineligible. Frozen paired reader reports `screen_deferred_inconclusive`: primary long-output ITL39.1948→39.9186ms (+1.8467%), TTFTp9911.8153→12.7408s (+7.8332%), E2Ep9989.8432→85.0546s (−5.3300%). The valid unfavorable screen stops promotion; zero invalid-pair replacements and no confirmation/burst. This single pair does not statistically falsify a ≥2% effect. Cache policy matched; observed52/53warmup and different cache counts remain context. Original environments/source/configs and all21 frozen pins reverified; own servers/router stopped and all8GPUs idle. Full result, all prior failures, evidence and scope: [execution report](../c03-execution-001/REPORT.md).
