# Independent review of the real-request proposal instrument

Reviewed on 2026-10-20 UTC before B003 candidate results or live execution. **Accept the frozen implementation for the declared scoped diagnostic.** This is not a release of the full live allocation: completed B003 native/lifecycle review, event-pool engineering result, exact launch and mount preflight, and the cumulative cost check remain required. Root owns execution.

I read the observer, overlays, traffic driver, reader and source receipts, independently verified the build/traffic/pool source hashes with no drift, and reran all 41 CPU controls successfully. Controls cover exact event-index gaps, callback copy ownership, overflow and incomplete outputs, wrong run/device/nonce/hash, native fused activation, exact chat/completion suffixes, fixed primers, unknown/mixed phase exclusion, the eight-rank reader, context bins and A-weighted standardization. These are source and CPU checks, not a fabricated runtime qualification.

The observation additions reverse exactly to the reviewed native observation or pinned installed source. They retain the qualified candidate and native oracle. Live initialization follows final capture and native qualification. CPU request metadata is saved outside the event span; two existing-stream events bracket only the real sample_tokens proposal call. The draft descriptor assignment retains its raw object and formats it after the end event. Dummy proposal calls follow the separate installed path and are counted separately. The FULL endpoint includes proposal preparation, graph replay and intervening waits/idle, as explained in `C25_LIVE_ENDPOINT_SOURCE_REVIEW.md`; it is not a pure kernel sum, useful decode cycle or ITL.

The pool owns 65,536 event pairs per worker, initialized before traffic. Flush uses each completed record's exact call index, takes a deep CPU snapshot under the output callback lock, synchronizes the last completed event, and retains every admitted record. Output callbacks run after the original copy synchronization, in the owning worker, without new D2H or per-step synchronization. Overflow, unfinished calls, missing outputs and duplicate callbacks remain incomplete. Device free-memory readings supplement PyTorch allocator and process-RSS readings because CUDA events may consume resources outside that allocator.

Eight fixed exact-token primers use one request per replica/rank before AIPerf. The existing reviewed readiness helper requires actual counters and three all-engine/router zero snapshots; missing valid publication remains unknown. The client then uses the frozen 480-row prefix and original seed, defaults, 120-second warmup and 300-second maximum grace. All phases, drain and flush share the 600-second cap. Exact response/internal-ID construction distinguishes chat requests from completion choice-0 primers. Primers, warmup, unknown and mixed phases do not enter the primary profiling matrix. The driver requires all eight bound flush files and completed client records before B admission.

The reader preserves every common and unmatched stratum, context exposure and chronological block. Its A-call-weighted common-stratum comparison is descriptive. Returned token counts remain prior-verification data with unknown per-proposal yield; there is no false same-call yield attribution. Summed concurrent GPU time per committed output is explicitly a resource-time ratio, not wall latency. B's activation and native fused capture witness must match the final worker receipt.

The reviewed root controller/watchdog/renderer preserve identity repair and native qualification, use distinct 70/75-minute work/hard deadlines, include 600-second traffic and cleanup reserves, and bind prior cost receipts against the 22-GPU-hour ceiling. Admission of B depends on correctness, completeness and remaining budget, not A's timing direction. Final rendered source/mount/command hashes still require the separate prelaunch review.

## Frozen implementation inputs

- Observation manifest: `e6e5855889c1152f4da385dfb28740057cd951a0c07eaac38f3cbf8403f68cee`.
- Traffic manifest: `56f01141217c351ec65ae9e8cd9accc03df7d0afba3ca4ac6628738bbf5130e7`.
- Observer: `a09d9cbdfd5eb02a26df4468865286fc8bf2837ce1df1532d3113a924d4c9dbd`.
- Reader: `5f8c59f9b7a8573147e7a8f6ea851af7e79b73c93a9c7a3fc4c3097c7d946fb2`.
- Traffic driver: `e0cb50fa7fa6297c2a40c303148f0da0c1eaaa585d28e4bed8e92ff6e45c3d17`.
- Build receipt: `b79a371e5a497683f7aa7399f6c005d0eaad7d4787fc89c0ae2752475fc135d4`.
- Retained 41-test output: `2ed58df6235f121f5a362d2fc9d8d5ed58e9464289ca1c1d2c2d14f82f8cce2c`.
- Source audit: `a70cb572348b885dae02692761632dcd225bb76602a01dcbd222715f2d8a8f40`.

## Bounded event-pool engineering release

After B003 cleanup and an idle-node ownership check, release one GPU0 engineering preflight in the pinned image, with no model mount, network, service or client traffic. Bind physical UUID `GPU-fc81ee05-2051-5148-0563-47bdb726dbc4`. The exact inner command is:

```text
python3 /work/tooling/live/pool_preflight.py --output /out/pool-preflight.json
```

The existing root wrapper supplies the python3 entrypoint, so its positional command begins with the script path. Mount the run at `/work` read-only and a unique new output at `/out`. Preserve all output and before/after hashes. Use a process timeout no greater than 90 seconds, reserving cleanup within the declared 120-second overall engineering ceiling. Root supervises the overall ceiling; any timeout or non-idle cleanup remains a failed/incomplete preflight, not permission to repeat automatically.

The preflight uses the exact production pool helper, initializes all pairs, records all pairs again and resolves the complete fixed inventory with one final synchronization. Finite nonnegative empty-span durations are valid here; actual live proposal durations must be positive. No performance threshold is imposed. Report initialization/flush time, process RSS, device free memory, exact UUID and helper hashes. One-device success establishes resource feasibility only, not equal eight-worker overhead or candidate speedup.

- Pool manifest: `66b6e6227675aa922a9fa2df47e8a3053874b31c6e6e3831bdaf0fdd9293f88f`.
- Pool script: `94a09b758ee400f7e7de029b6c24b577eec1f37a6634161554399aa1e2eb034d`.
- Existing root_component_v3 wrapper: `4cf0348ca6694239427e94287513283f2a45246f63537fe319c485f44197fc47`.

No current native003 source or verdict is changed by this review.

## Exact pool supervisor acceptance

The new `live-root/run_pool_preflight.py` and `pool_watchdog.py` are accepted for this one engineering allocation. They bind the existing runner to a 60-second component work timeout, GPU0, no model mount and the reviewed script command. The independent watchdog verifies PID/start-tick/process-group ownership, intervenes at 90 seconds, reserves container cleanup at 105 seconds and retains the 120-second hard action. I requested and verified the correction that container removal is bounded by the remaining absolute deadline with a 10-second cap and three-second reserve; the earlier 35-second blocking timeout could overrun the hard action. The owned-group wait is also bounded by the absolute deadline. The supervisor disarms only after observed GPU/container idle and reports the full supervised duration; exceeding the ceiling is not accepted as success.

Bound supervisor SHA256: `f028386eb8cb31b023140c40e2b53a11cac9abe02d603c508d0386e5206ff8c6`. Bound watchdog SHA256: `d7d3dabcde0287b7f443bb4ca17d4b0e7b09b5b9c95207a5592af6119625819a`. This acceptance remains conditional on B003 cleanup and node ownership, and does not release the full live pilot.
