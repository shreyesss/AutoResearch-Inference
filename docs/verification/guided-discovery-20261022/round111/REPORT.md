# Round 111 — historical exposed-time audit

## Decision

**No compatible exposed-time bound found for FV86 or PJ01. No new hypothesis or promotion.** A distinct recovered native timing artifact exists, so the result is not “no historical timings.” Its declared and implemented scope excludes the measurements needed here. Stop this bounded search; repeating acceptance aggregates would not resolve the gap.

This audit read local historical files and stdlib JSON/source only. It did not execute a kernel, profiler, model, server, event API, network request or device query. Original artifacts remain unchanged.

## What was actually recovered

The repository checkout lacks the native A002 rank JSON files, but the recovery report declares their restored location. All eight were found under the exact `recovery/restored-evidence/h200-overnight-001/native-baseline-002/.../native-pair-002/A/observations/` path, verified against `baseline-native-002-frozen.json`, and retained here. An absent checkout file was therefore not treated as global absence.

There are 960 samples per rank and 7,680 recorded samples across eight receipts. These are repeated controlled cycles, not 7,680 independent workloads or startups. Their exact scope is:

> controlled padded native draft-proposal proxy; excludes rejection, accepted-token progress, production context, queueing and ITL

The bound observer source calls `_dummy_run` with `context_len=0`, uniform six-row target decode and five-row draft graph per logical request. The overlay brackets whole target forward and whole draft proposal with events. Dummy proposal inputs set sampled counts to ones and rejected counts to zeros. It does not exercise actual rejection. The receipts enable the no-AV and no-real-requests guards.

The identity receipt binds H200-era unsuffixed `deepseek-ai/DeepSeek-V4.1-Flash@2cba9e42aa026125f3ed06c6d98c1db82f7ca027`, image `sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`, TP1/DP4/EP, DSpark five, AV disabled. It is not the planned B200 Flash-1017/c455/d464 configuration. This audit does not infer a serving source commit from benchmark Git or old image identity.

## Measurement compatibility

| Existing artifact | Actual measurement or evidence | Permitted use | Cannot establish |
|---|---|---|---|
| C025 component-002 result and hash-matched harness | CUDA-event duration of the complete five-step draft Markov sampling call, including five bias GEMMs, for a whole batch | Historical component result and correct timing units | Target rejection/residual time, current ITL, PJ01 target projection exposure |
| Recovered A002 eight rank receipts | Whole target forward and whole draft proposal in controlled padded dummy calls | Historical native graph/path evidence; scope and instrumentation design | Real-request sampler exposure, accepted-token progress, effective joint full-pass frequency, current target bound |
| Event-pool resource review | Empty event spans and allocation feasibility | Historical observer resource planning | Per-call instrumentation overhead or proposal latency |
| Real-request-stage design | Proposed event placement and request/proposal-to-verification joining | Future instrumentation requirements | Executed real-request timing |
| Historical status/interruption reviews | Live stage prepared, not executed; candidate startup interrupted before telemetry | Limits of the historical comparison | A paired production speedup |

The proposed real-request observer explicitly distinguishes rank-summed resource time from wall time. Its design is not a recovered measurement. The bounded inspection did not find an actual compatible request-stage span or isolated residual/projection timing; this is a statement about inspected artifacts, not every possible machine or cache.

## Five-step unit correction

`c25_component.py` loops over `STEPS=5` inside both measured functions. CUDA graphs capture the entire function, and elapsed time is divided by 100 graph replays. Thus each value below is **microseconds per complete five-step call for the entire batch**. It is not per token, per request, per accepted token, or client ITL.

| Batch | Baseline µs/call | Candidate µs/call | Difference µs/call |
|---:|---:|---:|---:|
| 1 | 181.480 | 136.135 | 45.346 |
| 2 | 206.086 | 138.961 | 67.125 |
| 4 | 215.749 | 145.294 | 70.455 |
| 5 | 226.090 | 149.538 | 76.553 |
| 7 | 239.984 | 156.740 | 83.244 |
| 16 | 309.809 | 186.735 | 123.074 |
| 32 | 331.703 | 227.966 | 103.736 |
| 64 | 484.137 | 330.474 | 153.662 |

The audit recomputed these means from the retained 30 paired blocks per shape. It did not rerun the historical 108 fixtures, bootstrap uncertainty, graph replays, or component implementation. Do not multiply these savings by five again or by eight ranks to forecast wall time. The result's own status is `component_complete_integration_not_qualified`.

## Remaining evidence, precisely

FV86 needs time attributable to the eligible residual/rejection path on the actual current request stream, joined with effective post-AV capacities and the same round's full-pass event. C025 measures a different operation; the dummy native path explicitly excludes rejection. Aggregate acceptance cannot recover that joint exposure.

PJ01 needs attributable dead-row query projection/norm work and its backend/capture shape on actual context rows, together with critical-path overlap. The dummy `forward_ms` is an entire historical forward at context zero. It cannot isolate the removable work or establish a current upper bound.

No new measurement is authorized or performed here. A later compatible trace could supply those fields; current numerical upper bounds remain null. Historical files can inform event placement and controls, not promotion of FV86 or PJ01.

## Reproduction and limits

Executed stdlib readback:

```sh
python3 /Users/shreyas/.local/share/autoresearch-reviews/guided-discovery-20261022-001/round111-historical-exposed-time/readback.py
```

Result: 13 initial source copies; eight native receipts verified; 7,680 recorded native samples inspected; eight component timing rows recomputed; current exposed bound null. Exact identity and all eight rank receipts were subsequently copied for portability and listed in `retained-native-receipts.json`. `inputs.json` describes the initial 13-copy stage; the final manifest covers the complete packet.

Initial broad text-search output was truncated; subsequent reads used explicit known paths. `bounded-inventory.json` records immediate-directory inspection, not an exhaustive recursive census. No new paper query, repeated round91 acceptance search, or canonical state mutation occurred.
