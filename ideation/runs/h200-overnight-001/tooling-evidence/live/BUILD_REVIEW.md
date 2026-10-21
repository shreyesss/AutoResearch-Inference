# C25 live proposal observer: implementation review

This is a new diagnostic instrument. Frozen native002/native-v2/B003 scientific and lifecycle files are unchanged. No builder GPU, service, container or traffic execution occurred. The live allocation and one-device engineering preflight require separate root/evaluator release.

## Actual execution and exact ownership

The generated model_runner overlay starts from the already reviewed identical native observation overlay. It adds CPU batch-state snapshots immediately after target dispatch and wraps only the actual non-dummy sample_tokens -> speculator.propose call with two events on the existing current stream. Native startup qualification completes before live pool initialization. Profile-only capture cannot initialize the pool. The DFlash overlay saves the raw actual executed descriptor; it performs no formatting, readback, logging or CUDA operation. Both arms receive identical observation additions.

The fixed pool owns exactly65,536 event pairs/rank. Every pair is created and recorded once before readiness. Initialization reports wall time, process max RSS, PyTorch allocator memory and CUDA device free/total memory; event resources may lie outside the PyTorch allocator. No event query, D2H copy or new synchronization occurs inside real traffic. Overflow stops admission and makes the result incomplete. Call-index gaps are resolved by exact completed indices, never by list position. Flush synchronizes only the last completed event, copies CPU records under the output-callback lock, writes all raw data and disables observation. Missing outputs, unfinished calls, errors and overflow remain explicit incomplete receipts.

The AsyncOutput callback executes after the existing get_output synchronization and CPU list construction, inside the worker process/thread before IPC serialization. It copies IDs/counts before downstream mutation. Current returned counts are prior verification results, so the records explicitly leave yield attribution unjoined/unknown. No generation-aware yield model is invented.

Primary FULL/FULL graph timing is a main-stream proposal span including preparation, replay and intervening waits/idle. DFlash returns a tensor view immediately after replay; graph launch ordering covers captured side-stream work joining the graph. Eager/mixed exposure remains separately labeled main-stream span. No global-device fence, kernel-only time, complete useful decode cycle or unprofiled ITL claim is made.

## Request phases, real metric readiness and fixed traffic

The unchanged source byte prefix contains480 records, relative arrival span146.562seconds, SHA256 aebcfacdd261c5eb214c9430aaacc51c6e63cfb34fe9ec852919976bd938bd70. The client argv changes only its input and unique artifact paths from the frozen prior AIPerf argv. Seed42,120second warmup,300second maximum grace, payload defaults and all export/telemetry flags remain.

Before AIPerf, exactly eight independent existing singleton fixtures run, one per replica/rank using row=rank, caps17/19/23/29. The already reviewed native-v2 Harness and token checker are reused. Actual terminal length count1 on every rank, router4 per replica and three strict observed all-eight idle snapshots are required. Valid missing gauges remain typed not-ready and reset the consecutive-zero counter within60seconds. No missing gauge/counter becomes zero. Primers, warmup, profiling, drain and flush share the root600second traffic cap.

Chat raw SSE IDs match exported X-Request-ID. Pinned InputProcessor.assign_request_id appends eight hex characters to the external ID. Pinned completion/serving.py141/177 adds the completion choice suffix '-0' before that internal suffix. Primer cmpl IDs are read from retained exact request records and labeled metric_primer; they never enter the primary profiling cohort. Unknown and mixed phases remain visible, never assigned by timestamp proximity.

After all480 profiling requests and every warmup request complete, the same strict all-eight/router drain precedes two backend flush RPCs. DP utility dispatch awaits all engines even where only its first return value is surfaced; the driver requires all eight final atomic rank receipts. Native/live PID, start ticks and UUID must match; candidate activation and native fused-capture witnesses are required for B. Any failed client, partial cohort, missing flush, overflow or unbound receipt exits2.

## Reader and validation

The reader freezes profiling real pure-decode FULL/FULL primary cells by replica/rank, actual target/draft capacities and CPU context-upper-bound bins <8192,8192–32767,>=32768. It reports the entire common/unmatched inventory, coverage and chronological10second blocks anchored to the first matched profiling call. The standardized comparison uses A call-count weights over common cells. There is no event bootstrap, independent-step inference, winning-cell acceptance rule or native round pairing. Summed concurrent GPU exposure per client-committed token is explicitly a resource-time ratio, excluding dummy EP support, not wall latency.

Retained tests.txt reports41 passing CPU tests: exact-index event gaps, callback ownership/copy, duplicate/missing outputs, overflow/unfinished/hash/run/device/nonce failures, native B activation/capture, exact chat/completion suffixes, primer phase exclusion/counters, whole synthetic eight-rank reader, context bins and fixed standardization. A separate previous native-v2 suite retains18 saved-regression/readiness controls. All observation overlays are syntactically parsed and exactly reversible to their input source. Build/source hashes and input manifests are retained for independent review.
