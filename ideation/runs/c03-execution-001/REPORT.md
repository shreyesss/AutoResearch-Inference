# C03 execution result: stop after the median screen

C03 reached a valid, unfavorable screening result. The candidate exercised the intended smaller draft CUDA graphs, but median long-request ITL increased **1.8467%** and TTFT p99 increased **7.8332%**. The frozen reader returned **`screen_deferred_inconclusive`**. Do not promote this candidate, run the five-pair confirmation, or run the held-out burst under this execution plan.

This is one AB screening pair, not a confidence interval or statistical falsification of a ≥2% benefit. There is no demonstrated service speedup and no production qualification. The independent evaluator accepted the measurement, source identity, scoped prerequisites and final interpretation. See the [sealed paired result](screen-paired-result.json), [complete pair ledger](screen-pair-ledger.json), [independent review](evaluator-review.md), and [current-run prerequisite receipt](reviewed-gates-screen.json).

## What was built

The isolated three-file vLLM change sizes draft work from synchronized logical request counts instead of carrying target-graph padding into the draft path. It preserves the target descriptor capacity, capture grid, collective protocol, speculative width, sampler and verifier. DFlash and autoregressive draft paths clamp the relevant preparation/launch extent; bounds and the zero-count guard remain explicit. This implementation is preserved in [candidate.patch](/home/ubuntu/Deepseek_serve-c03/c03/candidate.patch), with [implementation handoff](/home/ubuntu/Deepseek_serve-c03/c03/CANDIDATE_HANDOFF.md) and [launch handoff](/home/ubuntu/Deepseek_serve-c03/c03/SCREEN_LAUNCH_HANDOFF.md).

Only these source files differ between A and B:

- `vllm/v1/worker/gpu/dp_utils.py`
- `vllm/v1/worker/gpu/spec_decode/dflash/speculator.py`
- `vllm/v1/worker/gpu/spec_decode/autoregressive/speculator.py`

They were mounted read-only into fresh containers. The existing installed vLLM/image packages and main environments were not edited. Exact A/B source hashes and image digest are bound in [screen-pair-fidelity.json](screen-pair-fidelity.json) and the ledger.

## Fixed setup

| Item | Actual execution |
| --- | --- |
| Node | This node only: `jl-vm-541077`, eight H200 GPUs; identical physical UUIDs for A/B |
| Profile | Original `/home/ubuntu/Deepseek_serve/serving/h200/vllm/profiles/latency-2xdep4-sla.yaml` |
| vLLM | `0.30.1rc1.dev493+gac9126e58`, source `ac9126e58aa7bbab1856ba6593ba4d5003fea516` |
| Container | `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c` |
| Model | DeepSeek-V4.1-Flash, revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027` |
| Replicas | Two TP1/DP4/EP4 replicas; GPUs 0–3 and 4–7; two API workers per replica |
| Routing | Original router code/environment, port 8000 → 8100/8101; connection limit 100, retries disabled |
| Batching | max sequences 64; max batched tokens 16,384; configured graph maximum 512 |
| Speculation | DSpark, five draft tokens, probabilistic drafting, block rejection, adaptive verification off |
| Memory/caching | FP8 KV; CLI block size 64; prefix caching on; bounded replay off; Engram CPU offload |
| Workload | Fixed Mooncake median trace, **0.5×**, 4,004 scheduled profiling requests |
| Client | Existing `.venv-aiperf`, AIPerf 0.13; client seed 42; workers maximum 256 |
| Sampling | Temperature 1, top-p 1, top-k 0, request seed unset, ignore EOS true, watermark true |
| Warmup/cache policy | Fresh containers/request caches per arm; existing shared compile cache; fresh private bytecode cache; fixed 120-second warmup |
| Observability | Original verbose service metrics/logging and client/telemetry collection retained; diagnostic probe **off** during both screen arms |

Actual argv, environments, device assignments, source mounts and worker process identities are preserved in the per-arm container/startup/post-run attestations. The screen scripts are [run-A-screen.sh](run-A-screen.sh) and [run-B-screen.sh](run-B-screen.sh); service scripts are [start-A-screen.sh](start-A-screen.sh) and [start-B-screen.sh](start-B-screen.sh). These are archival reproduction commands, not instructions to automatically rerun an unfavorable pair.

## Measured results

A is the **fresh matched control**, not the earlier supplied baseline. B is the frozen candidate. Percent changes below use B/A−1; lower is better for latency.

| Metric | A: fresh control | B: C03 | B versus A |
| --- | ---: | ---: | ---: |
| Long-output ITL p50, primary | 39.194800741 ms | 39.918618771 ms | **+1.8467% worse** |
| TTFT p99 | 11,815.256073 ms | 12,740.770988 ms | **+7.8332% worse** |
| Request latency p99 | 89,843.217656 ms | 85,054.602206 ms | −5.3300% better |
| Long-output ITL p90 | 126.750208000 ms | 131.567603719 ms | Descriptive |
| Long-output ITL p95 | 175.004047651 ms | 177.397036985 ms | Descriptive |
| Long-output ITL p99 | 305.543426972 ms | 260.626116114 ms | Descriptive |
| Output token throughput | 586.598801496 tok/s | 586.753925152 tok/s | Fixed offered load; no capacity claim |
| Long-output cohort | 1,692 | 1,692 | Outputs ≥50 tokens |
| Successful / attempted | 4,003 / 4,004 | 4,004 / 4,004 | A's one HTTP 502/reset retained |
| Error rate | 0.024975% | 0% | Both within fidelity gate |
| Replay scheduling lag p99 | 4.871086080 ms | 5.050462720 ms | Both within 500 ms gate |
| Replay degraded | false | false | Pass |
| Good-request fraction | 57.917083% | 57.217782% | Both below 95% |
| Long-output ≥30 tok/s attainment | 42.139480% | 42.375887% | Both below 95% |
| Existing service eligibility | Ineligible | Ineligible | Complete runs; latency/SLO failures |

The primary is the existing scorer's token-normalized **post-first-chunk ITL**, restricted to outputs ≥50 tokens. No endpoint or cohort was changed after observing B. The frozen screen requires a positive primary gain and both observed tail regressions ≤3%. B fails the primary and TTFT conditions. The E2E improvement cannot override them. There were **zero invalid-pair replacements** and no repeat-until-win.

| Arm | Run ID | Profiling interval, UTC | Final export completion, UTC |
| --- | --- | --- | --- |
| A | `20261020-183933` | 18:41:42.039–19:01:57.039 | 19:05:23.853847 |
| B | `20261020-192708` | 19:29:15.697–19:49:30.391 | 19:53:02.381849 |

All timestamps above are on 2026-10-20. Exact nanosecond boundaries are in [screen-A-phase.json](screen-A-phase.json) and [screen-B-phase.json](screen-B-phase.json). Each normal export took several minutes after the workload drained. Both wrapper exit codes are 1 because the unchanged scorer rejected service eligibility, not because export was incomplete. Completion receipts hash the required exports and attest that all client processes exited: [A](client-A-screen-completion.json), [B](client-B-screen-completion.json).

Full run directories:

- [A artifacts](/home/ubuntu/Deepseek_serve-c03/results/h200/vllm/c03/production/mooncake-median/c03-A-screen-median-0p5x/20261020-183933)
- [B artifacts](/home/ubuntu/Deepseek_serve-c03/results/h200/vllm/c03/production/mooncake-median/c03-B-screen-median-0p5x/20261020-192708)

The corrected supplied median baseline `20261020-145417` remains complete and retained: 4,001/4,004 successful, replay p99 4.334592 ms, long ITL p50 35.885356115 ms, TTFT p99 12,571.636821 ms, E2E p99 78,664.609965 ms. It is historical context and the client-identity reference; it is **not** substituted for fresh A. The supplied burst used different GPU UUIDs and remains contextual only. No local burst was run after this unfavorable screen.

## What the mechanism and correctness checks establish

The separate diagnostic runs confirmed the mechanism. A recorded 31,424 unique online replica/DP-step events and 2,469 smaller-bucket opportunities. B recorded 30,832 events and **1,941 opportunities, all selecting the predicted smaller draft graph**, with zero bucket, extent or target-synchronization violations. Conservative intervals wholly inside profiling retained 2,063 A opportunities and 1,350 B opportunities; warmup and trailing drain were excluded. These counts establish reduced selected/submitted draft graph capacity, not a direct kernel-time or instruction-count saving. Diagnostic latency was never used as the service comparison.

All eight workers retained exactly 41 target and 37 draft FULL graph descriptors, with target/draft maxima 384/320. Startup qualification also required completed captures, engine/API readiness and matching process/source identities; a list of attempted captures alone was insufficient.

Both arms passed common-input actual-function CPU checks, 170 GPU preparation cases per arm, controlled actual dense/sparse verifier checks with negative controls, and the prospectively frozen 20-request controlled integration matrix per arm. The integration checks include known token ownership, active width-five speculation, exact forced EOS, natural stop observations, cancellation witnesses, request-linked abort logs, recovery, and 13 strict all-eight-engine/router drains per arm.

This is bounded layout/row transport, verifier, distributed graph and controlled integration evidence. It does **not** certify unrestricted model-output equivalence, all KV cells or the full watermark distribution. Earlier free-form repeatability failures remain unresolved and retained; they were not relabeled as passing.

## Context and limitations preserved

The independent descriptive join found all 4,004 workload keys in both arms, with no invalid or duplicate keys. All 4,003 common successful requests have identical actual input/output/prompt lengths. The failed A key remains in the outer join. Both long cohorts have actual server first-chunk counts for every request, with no fallback, delayed-usage substitution or malformed chunks. Each long cohort has 1,691 first chunks containing one token and one larger first chunk; their actual counts are retained in the scorer.

Whole-run speculative totals (steps / proposed / accepted) are A **265,716 / 1,328,580 / 448,869**, B **265,882 / 1,329,410 / 448,689**. Common-success denominators are separately retained. Sixteen zero-step one-token outputs per arm omit optional per-step arrays; no arrays were fabricated. Width/histogram/per-step invariants passed. These measurements do not prove identical acceptance distributions.

The cache **policy** matched, while observed cache state differed. Warmup completed 52 requests in A and 53 in B under the same 120-second rule. Cached-prompt share was 27.797100% versus 28.259502%; 205 common requests had different cached-token counts (102 higher and 103 lower in B, net +159,936 B tokens). No adjustment or rerun was selected from these differences. Categorical KV configuration matched and all eight ranks had zero observed preemptions. This context limits a causal explanation for the unfavorable timing result; it does not change the frozen stop rule.

Primary independent telemetry had complete counter boundaries for all eight endpoint/rank identities with no observed resets. The separate AIPerf replica-1 counter export lacks an end boundary in both arms; that corroboration gap remains explicit. The primary collector and its boundary rule were fixed before the first screen client. Collection-loop sample means are descriptive, not time-weighted kernel measurements. See [paired context and denominators](SCREEN_PAIR_CONTEXT.md), [paired context JSON](screen-pair-context-comparison.json), and [full outer request join](screen-pair-requests-joined.csv).

## Triage retained without hiding failures

| Observation | Resolution and scope |
| --- | --- |
| Initial cold scheduler gauges absent | First lifecycle attempt sent zero requests; absent gauges were not treated as zero. Diagnostic workload initialized metrics before strict drains. |
| Free-form seeded T0 outputs differed after cancellation | Fixed-rank no-cancel control also differed in all four pairs. Exact-repeatability lane stopped; cancellation causality and unrestricted numerical equivalence remain unproven. |
| First controlled adapter expected abort success-counter increment | Actual pinned frontend removes requests before terminal success statistics. Failed receipt retained; independent designer froze V2's exact abort-log/live-rank/drain observable before B. New common V2 ran on A, then identically on B. |
| Large console replay warning during warmup | Corresponds to the separate concurrency-paced warmup timestamps. Actual profiling replay lag passes in both arms; the corrected historical baseline had the same warning. |
| Export continued after request completion | Normal aggregation/server-metric export completed. Artifact completion, fidelity and SLO eligibility were checked separately. |
| A screen HTTP 502/reset | Preserved as one failed profiling request; within predeclared error/completion gates. Its cause was not established and the pair was not rerun. |
| Unfavorable candidate timing | Retained as the only fixed screen pair. No confirmation or burst promotion. |

## Responsibilities, integrity and final node state

The orchestrator alone launched services, containers, clients and GPU checks. `c03_evaluator` owned design and independent qualification; `c03_evaluator_builder_review` implemented evaluator/probe/fixture/readers; `c03_dev_review` implemented isolated launch support and the optimization. The optimization developer did not author its evaluator. The evaluator designer did not implement either candidate or evaluator code.

Work remains in `/home/ubuntu/AutoResearch-Inference-c03` and `/home/ubuntu/Deepseek_serve-c03`. Final verification matched all **21 frozen input hashes**, all nine recorded original source/config hashes and both original environment package inventories (141 packages in `.venv`, 138 in `.venv-aiperf`). No installs/upgrades were performed. See [integrity receipt](final-integrity-check.json).

After full log archival and strict drain, task-owned B containers and the task-owned router were stopped. The node is back to its initial idle state: no serving containers; ports 8000/8100/8101 closed; all eight GPUs report zero allocated memory and zero utilization. Existing monitoring processes were preserved. See [cleanup receipt](final-node-cleanup.json), [A full-log attestation](screen-A-complete-log-attestation.json) and [B full-log attestation](screen-B-complete-log-attestation.json).

Any further C03 investigation needs a new prospectively documented question or implementation revision. This execution is complete at its frozen screening stop; it does not authorize tuning the evaluator or silently repeating the pair.
