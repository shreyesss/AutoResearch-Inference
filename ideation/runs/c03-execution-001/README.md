# C03 execution evidence

User-authorized execution of the frozen [brief](../c03-test-plan-001/EXECUTION_BRIEF.md), local node only, unchanged latency-2xdep4-sla profile and Mooncake 0.5×. The current state is in [status.json](status.json); append-only actions are in [events.jsonl](events.jsonl). The corrected supplied baseline remains complete and retained.

## Final result

**Execution complete: `screen_deferred_inconclusive`.** The valid probe-off median screen did not meet promotion: primary long-output ITL worsened 1.8467%, TTFT p99 worsened 7.8332%, and E2E p99 improved 5.3300%. No confirmation or burst follows. One pair does not statistically falsify a ≥2% effect. The original environments remain unchanged and the node has returned to its initial idle state.

Read [REPORT.md](REPORT.md) for the complete setup, result table, mechanism evidence, bounded correctness, retained failures and cleanup. The [sealed paired result](screen-paired-result.json), [independent review](evaluator-review.md), [paired context](SCREEN_PAIR_CONTEXT.md), [integrity receipt](final-integrity-check.json) and [cleanup receipt](final-node-cleanup.json) are authoritative final evidence.

## Earlier diagnostic and screening milestones

Diagnostic A completed in run `20261020-163428`: 4,003/4,004 profiling requests succeeded (one client disconnect), replay lag p99 5.86175488 ms, replay_degraded=0. Required raw/aggregate/telemetry artifacts exist. The unchanged scorer is SLO-ineligible; this is not a fidelity failure. It is a diagnostic run, not an unprofiled performance control.

| Gate | Result | Evidence |
|---|---|---|
| Source/image/profile/router identity | Pass | diagnostic-A-container-attestation.json; startup-A-readiness-identity.json |
| Cold capture inventories and readiness | Pass on all eight ranks | 41 target/37 draft FULL descriptors each; maximum target/draft tokens 384/320; startup-A-inventory.json |
| Production CPU adapters on A | Pass in declared controlled scope | 3,072 rank calls; final caller/AR/launch/microbatch receipts |
| Actual GPU preparation and verifier on A | Pass in bounded scope | 170 preparation cases; controlled dense/sparse real verifier with watermarking and negative controls |
| Closed diagnostic exposure | Pass | 31,424 unique replica/DP-step events; 2,469 smaller-bucket opportunities; exposure-A.json |
| Strict interval inside profiling | Pass | Conservative 21,396 events and 2,063 opportunities (1,232/831); profiling-exposure-A.json |
| Baseline free-form repeatability | Failed; lane stopped | Original cancellation reference and all four fixed-rank no-cancel pairs differ. All failed receipts remain. |
| Baseline controlled integration | Independently accepted | Corrected common V2 completed20 requests; exact known token/EOS/ownership checks, active speculation,13 drains and both exact request-linked aborts verified. No unrestricted numerical-equivalence claim. |
| Optimization port | Complete and independently reviewed | Frozen three-file candidate and matching diagnostic copies; no speedup claim |
| Candidate runtime identity and CPU fixtures | Pass in declared scope | Both pinned containers/four readonly files and all eight worker identities reattested; same five actual-function CPU adapters pass |
| Candidate startup and GPU fixtures | Independently accepted in declared scope | All eight capture inventories retained; 170 GPU preparation cases and controlled actual verifier outcomes pass |
| Candidate diagnostic mechanism | Independently accepted | 30,832 unique online events; all 1,941 stronger opportunities execute fewer draft rows; zero bucket/extent/synchronization violations |
| Candidate strict profiling interval | Readers pass | Conservative lower bounds: 19,623 events and 1,350 stronger opportunities (577/773 per replica); warmup and trailing drain excluded |
| Candidate controlled integration | Independently accepted | Exact common V2: 20 requests, 13 strict drains, 165 raw metric hashes, both positive DP0 cancellation witnesses and exact request-linked abort logs verified; controlled token/EOS/recovery checks pass |
| Probe-off service comparison | Complete; valid unfavorable screen, independently accepted | A/B run IDs `20261020-183933` / `20261020-192708`; primary ITL +1.8467%, TTFT p99 +7.8332%, E2E p99 −5.3300%. Both complete and SLO-ineligible. Zero replacements; no confirmation/burst. See REPORT.md. |

The initial lifecycle attempt sent zero requests because never-set scheduler gauges had no samples. The fixed Mooncake workload naturally initialized them. The subsequent strict all-eight-engine/router drain passed, and `A-exposure-final-snapshots` was archived before lifecycle traffic. No exposure count includes those later correctness requests.

The console's alarming ~104-second replay warning exactly describes the 52 concurrency-paced warmup requests, which retain trace timestamps. Both independent reviews reconstructed actual profiling dispatches; the unchanged final scorer confirms 5.862 ms p99 and no degraded replay. The supplied corrected baseline emitted the same unlabelled warmup warning. The server-metrics RPC timeout also did not mean incomplete output: the normal export completed after processing 11.55 million rows. See [client triage](A-client-runtime-triage.md).

All earlier failures, original scripts and receipts are retained. [status.json](status.json) and [events.jsonl](events.jsonl) track later decisions. The original environments, installed image packages, main checkout and profile are unchanged.

## Role separation

- Root: orchestration, evidence manifests, service/client/GPU execution and gate enforcement.
- c03_evaluator: frozen expectations and independent review; no implementation.
- c03_evaluator_builder_review: evaluator/probe/fixture implementation; no optimization.
- c03_dev_review: isolated launch support and later gated optimization; no evaluator changes.

## Important interpretation

Observed synchronized counts are unpadded scheduler request counts. Online dummy participation may contribute a synthetic request on a rank with no client request. Keep the dummy flag when interpreting them; do not label every observed entry a live client. Startup events are excluded with an explicit activation marker. Diagnostic timing is never a service benchmark result.
