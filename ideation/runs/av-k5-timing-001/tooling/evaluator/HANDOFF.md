# AV-off k5 timing tools

These new tools are evaluator-owned. The orchestrator alone executes profile RPCs or clients. They do not modify the runner, scorer, environments, candidate, or sealed C03 artifacts. The independent designer owns `ideation/runs/av-k5-timing-001/EVALUATION_CONTRACT.md` in the research worktree.

## Observation and launch

`../observation-manifest.json` binds two new source copies to their original image sources. `prepare_observation.py` independently removes exactly the three added `record_function` scopes and checks AST equality with the originals. The reviewed copies are read-only. Do not regenerate or modify mounted sources during a run. `../render_launch.py` is developer-owned and renders the baseline arguments plus these two read-only mounts, fresh bytecode cache and exact profiler configuration.

The three scopes are target forward, the complete draft proposal, and the draft execution composite. The FULL draft graph includes context preparation, model and sampling. It cannot be described as pure draft model time. There are no new CUDA events, synchronization, tensor reads, or collectives. Startup capture profiling is disabled.

## Root-only control

Start the ordinary fixed prefix workload. Use the timestamp of the live `Phase profiling (profiling) started` NOTICE after the 120-second warmup as the declared scheduling anchor. This timestamp has UTC millisecond precision; it is not the exact lifecycle `start_ns`. The exact lifecycle value appears in `PhaseRecordsStats` at completion. Preserve both values and reconcile them afterward. Invoke this before phase +90 seconds:

```bash
/home/ubuntu/Deepseek_serve/.venv/bin/python /home/ubuntu/Deepseek_serve-c03/av-k5/evaluator/capture_windows.py \
  --backend-url http://127.0.0.1:8100 --backend-url http://127.0.0.1:8101 \
  --profiling-start-ns DECLARED_NOTICE_ANCHOR_NS \
  --identity-receipt ABSOLUTE_ROOT_RUNTIME_IDENTITY_JSON \
  --output ABSOLUTE_FRESH_CONTROL_JSON
```

The controller dispatches empty-body start POSTs to both replicas at +90/+210 seconds, then stop POSTs at each scheduled offset +15 seconds. Each HTTP call has a ten-second timeout. The installed worker schedule (warmup1, active20, max20) is the recording bound; the explicit stop is cleanup. A late wakeup over one second fails without catch-up. A failed/partial start always attempts stop on both, then suppresses the second episode. It never retries. Keep the receipt and separately inspect worker traces/logs: HTTP200 alone is not trace coverage. Root should retain ordinary load outcomes even if control fails.

## Offline summary after load/export completion

Collect every trace and worker log before selecting the eligible sixteen files; retain extras/partials. Build a small JSON manifest with:

- `identity_receipt`, `identity_sha256` for root's runtime/worker/container/GPU/source attestation.
- `phase_receipt`, `phase_receipt_sha256` for root's phase and workload evidence.
- `control_receipt`, `control_receipt_sha256` for the control output above.
- `observation_manifest`, `observation_manifest_sha256` for the exact mounted source inventory.
- `profiling_start_ns`, the declared NOTICE anchor exactly matching the control receipt. The phase receipt must also retain exact final lifecycle `start_ns`, anchor precision/source and their delta. Independent review requires absolute anchor−exact delta <=1s and each actual backend start-dispatch relative to exact phase+offset within±1s; failure is inconclusive, never a catch-up/retry.
- `traces`: exactly sixteen entries: `offset_s`90 or210, `replica`0 or1, `rank`0..3, absolute `path`, raw-file `sha256`, actual `worker_pid`, physical `gpu_uuid`, full `container_id`.

Paths are explicit and existing files are hash checked. The independently reviewed runtime receipt must establish actual rank/physical-GPU/container mapping; the parser does not infer it from a filename. The reviewer must bind each trace to its declared episode and phase using control times, trace clock metadata and worker logs, and check dropped-activity/truncation warnings. These external checks remain pending in a successful parser receipt.

```bash
/home/ubuntu/Deepseek_serve/.venv/bin/python /home/ubuntu/Deepseek_serve-c03/av-k5/evaluator/trace_summary.py \
  --manifest ABSOLUTE_TRACE_MANIFEST_JSON --output ABSOLUTE_FRESH_SUMMARY_JSON
```

The parser reads one file at a time, with a 512MiB decompressed bound per trace. It uses unique CUDA runtime/driver correlation IDs and CPU scope nesting. A kernel name or temporal proximity never determines ownership. Missing/ambiguous graph associations remain unknown. Each complete decode cycle needs native context0/generation>0, one observed proposal/execution and an observed following target with attributable GPU activity. The final boundary step is excluded. No FULL mode or padded graph descriptor is invented from token counts.

Cycle boundaries are current and next target's first attributable GPU activity, on one device. All GPU activities are clipped to that finite half-open interval; unions, target/draft intersections, kernel/copy/memset, other work and idle-without-observed-activity are separate. Draft execution is a subset of draft proposal. CPU range times and full stage GPU spans are reported separately. Whole-trace distributions are context; complete-cycle columns supply the reviewed materiality inventory. No cross-device sum is wall time, and no interval union is exposed service delay. The parser always leaves `exposed_critical_path_established=false` and makes no AV decision.

At least ten complete eligible decode cycles are required per rank/episode. Unattributed GPU work is conservatively flagged for review, including required graph coverage; the tool never uses a small unknown fraction to excuse a missing required graph. All sixteen identities are mandatory. `occupied_measurements_ready_external_review_pending` means only parser-level completeness; source/phase/control/trace-warning/attribution and diagnostic workload fidelity still require independent acceptance.

## Offline validation

`test_timing_tools.py` exercises union/overlap/clipping, finite following-target boundaries, missing and ambiguous launch correlation, prefill exclusion, invalid timing/correlation, missing rank failure receipt, partial-start cleanup, and late-wakeup rejection. These are CPU-only synthetic fixtures. They do not prove the installed profiler emits adequate graph correlations. Actual traces may therefore produce an instrumentation-inconclusive result without any rerun or backend fallback.

## Prepared prefix and client

The research run directory contains `subset-receipt.json`, `client-dryrun.json`, `client-dryrun-check.json` and root-only `run-client.sh`. The subset contains exactly original lines1–986, with byte-preserved raw rows. Its SHA256 is `3d8575ab10687f431695c9467e50425a934086bec10e9111a41e816cd88cb4b1`; the ordinary runner's scaled0.5x output is `ee5c7a0b9a6458becb06ce112f952549e023cdc03728deaa8539e74ed7e1b8d9`. Relative arrivals span299.232 seconds. The generated AIPerf command differs from the reviewed A screen only in artifact directory and input trace path; environment is identical. Existing runner duration settings are unchanged because the hashed input prefix, not `--duration`, bounds fixed-schedule arrivals. Root invokes the script only after readiness/source/capture review.

To discover the live scheduling anchor, inspect the new run's `console.log` for exactly one `Phase profiling (profiling) started` NOTICE (not `AIPerf System is PROFILING`, which precedes warmup). Parse its `HH:MM:SS.mmm` as UTC on the observed run date and convert it to integer Unix nanoseconds. Save the exact notice line, line number, UTC date, anchor value and a hash of the log prefix through that line in root's phase-anchor receipt. Use that integer in the controller command before +90s. At completion compare against the exact `PhaseRecordsStats(phase=CreditPhase.PROFILING, ... start_ns=...)` value under the one-second reconciliation rule above. No source logging change is needed.

The existing frozen `c03/evaluator/startup_inventory.py` can read the new two raw backend logs with unchanged `expected-captures.json`. Use fresh `--identity` and `--output` paths. It checks all eight targetq6/draftq5 FULL capture inventories as attempts only; root's fresh worker PID/start/GPU/source binding and health establish readiness separately.
