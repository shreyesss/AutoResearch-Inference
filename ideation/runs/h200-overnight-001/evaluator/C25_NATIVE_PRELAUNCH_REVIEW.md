# C25 native pilot: independent prelaunch acceptance

2026-10-20 UTC. **Release one bounded `native-pair-001` allocation using `native-root/launch-native-pair-001-v2.json` and the hashes below.** The positive component result justifies this native integration pilot. No native or service result exists at this signature. No full service attempt is consumed by this scoped allocation; two remain. Root executes; builder/developer/evaluator roles remain separate.

The governing prospective contract is `C25_NATIVE_PILOT_CONTRACT.md`, SHA256 `3df4f0fc47b02fa648afe6815c0e0cae27717513b1d0f5023ea70b4f85cc176a`. Its appended clarifications were all written before native output. Fixed logical inputs, actual descriptor witnesses, exact original-sampler native oracle, 960 samples per rank, fresh controlled lifecycle inventory, exploratory statistics, pending-versus-failed integration distinction and resource caps are frozen.

## Exact accepted inputs

| Input | SHA256 |
|---|---|
| launch-native-pair-001-v2.json | `40ff6d3b2af7b67930f25bfe1d5155f80b0000558e1ff0a3692bf14dec1d7342` |
| native-root/controller.py | `8305ed51e193fba4b295ed4cefacb388fa4e56ef83bfbc599429ec27fbfed42d` |
| native-root/watchdog.py | `8783bf8580e25f269b7d699cd6cc52e9132cdaa5a5e1098080c8451cf4683583` |
| native-root/render.py | `fe36fe96a675edface4fc258a81fb65e12960e5a28a594247ca0bfb4e960f335` |
| tooling/native/manifest.json | `299edc492416c6d1d5d720520727e86249f3dbe6ad39eb9cdbab111890425ae4` |
| tooling/native/traffic-manifest.json | `55c94bbc43b704fbfa09b04d32aba01ca426b33b150be8e7741b2f969c3c42c6` |
| c25_native_observer.py | `1e1cf05feb11390361cf1f67f749cb36a13d1e6b3a21ff7e4e6e712b45c99740` |
| parse_native.py | `67cf3ec72c51692e777b0867ec0211bdd875d32aa21464ae82574313f7edff21` |
| tooling-evidence/native/build-receipt.json | `d14bbab7f00bc13cac1bf172f558d7f99e86582682fe5327a6661a1543a5bcb9` |

I independently verified every hash in the builder receipt and all 35 final launch inputs, parsed the Python sources, reviewed the observer, oracle, reader, traffic adapter, renderer, controller and watchdog, and checked source interfaces against the pinned installed image. The treatment core remains `7536fcf28dee55a963bb2bc01b50eb0f2ac2e088d83142f088c8f625ac0ba8e9`; the original sampler oracle remains `97bcfaa655c6d4a5ecdfb17ab87b80547e8216b9d15a91c341798ebbb558f146`.

The shared model-runner overlay is `5a9af8a16a353f083a185a004f8932431a3125d909e48cab3c7e127de4a403c1`. Baseline DSpark plus observation is `70d83f1a54980af75bb9f21110a37dc023615f43aaf2272264b51455045f7815`; candidate DSpark plus observation is `1a211062a845ed21f883408c10a8540f264607d0e92278a0705d5fa7fd350ad1`. I independently removed the identical capture observer from both modules and recovered the exact installed A source and already reviewed B treatment source. No second DSpark mount collision is silently accepted.

## Measurement and correctness review

The observer excludes temporary `capture_model(profile_only=True)` capture entirely, retaining no throwaway-pool tensors. The final capture observer records the actual five baseline `_sample_logits` or candidate `sample_step` calls and restores Python wrappers immediately. It adds no captured GPU kernel, and binds the final captured head tensor and branch to the actual replay graph object/descriptor. Native events use the installed collector and current device/stream, without the failed C24 CPU/GPU timestamp association method.

The untimed oracle invokes the original installed sampler directly on the actual replay-produced head activations and unchanged prepared state. Finite writes replacing NaN cache sentinels, exact active tokens/BF16 cache against two reference executions, inactive bytes, valid indices and zero fused counters are required before and after timing. State restoration includes modified request/sampling/UVA/input buffers and collector metadata; original null-block warmup reset is source-supported. Capture observation and retained references are disabled/cleared afterward. This verifies the controlled native integration domain, not all production workloads.

The reader validates all fixed cells and order, all rank/shape descriptors and streams, source hashes, common run identity, eight unique physical GPUs and their pinned per-rank A/B mapping. Its thirty-round ratio-of-means bootstrap matches the prospective statistic. Both target-control drift scales are diagnostic; neither is subtracted. Every shape, replica and rank remains visible, with per-cell exploratory intervals and no familywise or independent-start confidence claim.

The retained builder test receipt reports **30 passing CPU controls**, including missing/duplicate samples, wrong schedule/head/capture step/mapping, nonfinite durations, unrestored state, wrong source/run/GPU, duplicate GPU, profiling-capture exclusion, wrapper restoration, post-traffic missing metrics, unexpected rank activity, wrong tokens/k5 and false cancellation. Receipt SHA256 is `8848bf80e72a4ac30d6cdc60bcb4fddf6e43e6dc8d1beddab81b691d234b44a2`. These tests exercise rejection behavior; they are not native GPU validation.

The traffic manifest preserves the existing expected-token and cancellation oracle functions and the exact twenty-request inventory. First ten initialize fresh lazy metrics; initial absence remains unknown. Actual metrics source eagerly creates all finish-reason labels per configured engine, so required used-rank counters are justified. All eight post-traffic running/waiting gauges and router active counts must be present and drain strictly. Cancellation still requires independent retained runtime-log acceptance; unconstrained natural length remains inconclusive. Neither pending lane becomes complete integration by receiving a zero driver exit code.

## Runtime envelope and retained revisions

The controller enforces 40 minutes per arm for startup/native work, five minutes for controlled traffic, each active observer's eight-minute deadline, and shared 85-minute work / 90-minute hard allocation limits. An independent watchdog addresses controller death and deadline failures, verifies PID/start-tick/process-group ownership before terminating children, attempts all owned containers, and is disarmed only after verified idle GPU/container/owned-child state. Root's CPU watchdog test includes early parent death and a deliberately wrong process identity; SHA256 `1b63fe8c22753134dd67d0fbe81ddf7eb313802569e8c583e3e6559b89ec7070`.

The controller checks exact GPU inventory, hashes, final native status/oracle/capture/restoration/sample count and physical rank GPU identities, and rechecks live worker PID/start ticks before traffic. It binds unique outputs, closes and hashes foreground container logs after cleanup, and allows a bounded independent A log review before B according to the prospective pending-versus-observed-failure rule. Any actual correctness, EOS/recovery, drain, activation or restoration failure stops B. No expensive trace is authorized by this review.

The actual-image read-only mount/hash/AST preflight passed for A's four and B's six mounts; receipt SHA256 `4060e1e8f4d33eaee062a6f35be46d9bd8d539b663f3e9bd1b157a0edd3ddeec`. Its original launch manifest is retained. The final v2 revision only repairs controller watchdog disarming and allows the renderer a new manifest path; I independently confirmed identical arm commands, mounts, router and GPU inventory. Revision receipt SHA256 `3c8328e72e485cf158ed3f19c55d0d23173e73cec3b773f01ca8cd422c895861`. This preflight validates mount/source plumbing and syntax, not model execution.

Root may now run the accepted controller with `--manifest native-root/launch-native-pair-001-v2.json --review evaluator/C25_NATIVE_PRELAUNCH_REVIEW.md`, from this run directory or with absolute paths. Freeze every bound input during allocation. Keep raw partial results, errors and cost on any failure. The primary new claim remains **controlled padded native draft-proposal performance**, with real lifecycle correctness evaluated separately; no production draft percentage, accepted-token ITL or confirmed service improvement may be inferred from this pilot alone.
