# Exposure audit — can retained measurements qualify RD01, M01 or AT03?

## Finding

**No compatible measured component-exposure record was found in the bounded retained-artifact audit.** We cannot currently estimate a defensible numeric ITL/TPOT gain for physical weight localization (RD01), route-histogram MoE tactics (M01), or compressed-KV gather reuse (AT03) from these records.

This is a specific evidence gap, not a conclusion that the ideas cannot help. Existing records remain useful for workload choice, metric definitions, correctness controls, topology comparisons and failure-aware evaluator design.

Target comparison contract: `deepseek-ai/DeepSeek-V4.1-Flash-1017`, revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, planned two independent TP1/DP4/EP4 groups, native MegaMoE, DSpark5, vLLM `c4557869393db4d75c483d92edd02a5125500883`. The source plan is not a verified live deployment.

## Compatibility matrix

Detailed model/revision/layout/source/workload/metric fields and individual dispositions are in `compatibility-matrix.csv` and `.json`.

| Retained evidence | Model/runtime/hardware relationship | What it actually measures | Permitted use; why it cannot forecast these ideas |
|---|---|---|---|
| B200 R7b two-DEP4 agent-75 | Closest topology match; **unsuffixed Flash**, older configuration revision `2cba9e…`, source snapshot default `ac9126e…`; exact per-run installed image not independently attested | Closed-loop service latency/throughput at 8K input/1K output and prefix target75%; e.g. C256=21.67req/s | Historical workload/concurrency choices. No exclusive MoE or gather time; model/runtime changed. |
| B200 R7b Mooncake | Same older model context and two-DEP4 label; client manifest pins tokenizer `2cba9e…`, serving checkout `7562145…` **dirty**, `selected_image` empty | Arrival-driven median1x service metrics:6.65req/s, E2Ep50=1.36s, p95=5.54s | Trace/metric and load-design reference. Tokenizer revision and serving Git commit do not attest server model/runtime. |
| Other B200/public points | TP4, DP8, differing DSpark/precision variants; public endpoint hardware/model revision unknown | Aggregate cost/latency operating points | Keep as separate controls. Do not pool layouts or transfer fractions; public cost/topology not established. |
| H200 C01 grouped-Humming | H200, earlier Flash revision/image `3d17635…`/vLLM `ac9126e…`; candidate/baseline median span different hosts | Poor grouped-backend service outcome; mean server decode interval9.45→21.78s | Dispatch/precision/host-identity lessons. Request decode time is not exclusive MoE GPU execution; not current MegaMoE. |
| H200 AV-k5 trace diagnostic | Earlier unsuffixed Flash `2cba9e…`, image `3d17635…`, two-DEP4 DSpark5 AVoff, instrumented source |986 completed requests; only11/16 adequate trace cells;647 chronology flags; one cell4cycles vs10 required | Instrumentation and coverage design only. Final verdict explicitly says **exposed service time not established**; target intervals include NCCL/waiting. |
| H200 C25 sampler component | One H200, real earlier Flash sampler weights, isolated unsharded sampler |108 correctness fixtures;30paired timing blocks per shape;45–83µs saved at common small shapes per **complete five-step call** | Valid scoped sampler evidence and timing methodology. Not MoE or gather, not full-model exposure, not B200/1017/c455. |
| H200 C03 service | Earlier Flash/runtime, two-DEP4, draft-padding intervention |ITLp50+1.8467%, TTFTp99+7.8332%, E2Ep99−5.3300%; failed frozen gates | Shows why work removal and event counts do not predict service gains. Different intervention and implementation. |
| Current source/CPU envelopes | Correct Flash-1017 config and c455 source, but no device execution |Requested-length-derived counts, compressed-byte/capacity arithmetic | Shapes/eligibility/memory bounds only. Requested length is not actual uncached prefill work, graph/cardinality distribution, overlap or elapsed time. |

## Exact incompatibilities matter

### Older B200 data are useful but not an exposure trace

The B200 config snapshot maps default image `3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c` to source `ac9126e58aa7bbab1856ba6593ba4d5003fea516`. The R7b base profile has two independent TP1/DP4/EP4 engines and DSpark5; the measured campaign also applies a sequence-count override. Thus it is wrong to dismiss all old B200 data merely as a different topology. **Its topology can match; its exact model/runtime and component exposure do not.**

The downloaded benchmark analysis explicitly retains aggregates, configs, score/manifests rather than the full roughly119GB S3 inventory of logs/telemetry/caches. We did not query S3, download additional archives or inspect a node. An aggregate ITL value cannot tell us how much critical-path time is spent in MegaMoE or repeated compressed-cache gathers.

### H200 timings cannot be repurposed into a MegaMoE fraction

The AV diagnostic's preserved final verdict is `instrumentation_inconclusive`. Its16-cell prerequisite failed even after a separately reviewed parser correction. GPU annotation/correlation anomalies were not resolved, and target-owned intervals include communication/waiting. Reprocessing those fractions as “MoE opportunity” would bypass both the original adequacy gate and the missing component attribution. No giant trace reprocessing was attempted.

C25 is a real positive component result. Its environment reports NVIDIA H200, Torch2.13/cu130, Triton3.7.1 and installed sampler source hashes. It covers five-step sampler calls with real earlier-checkpoint weights. Multiplying its percentage by whole-request latency, multiplying its savings by five again, or using it to set MoE/gather exposure would be invalid.

C25 native candidate continuation was interrupted before usable candidate traffic. Prepared subsequent profiling plans are **not** executed exposure measurements. The canonical experiment registry has only three recovered experiment records here: C25 component validated, C24 short probe inconclusive, C25 native003 error. No newly measured Flash-1017/c455 component experiment is present in that registry.

## What remains unknown for each current idea

| Idea | Missing exposure numerator and denominator | Retained data can still provide |
|---|---|---|
| RD01 physical weight locality |Actual MXFP4 MegaMoE duration and exposed fraction of decode cycle; useful locality map; power/clock/traffic bottleneck; unaffected communication/attention fraction |Representative workload labels, H200 failure cautions, exact source/adapter contract. No speed percentage. |
| M01 histogram-conditioned tactics |Actual per-expert routed-row histograms, dispatched legal tactics, per-rank imbalance and exposed MoE cost at fixed SM allocation |Model dimensions, earlier shape/control ideas. Synthetic histogram differences establish decision sensitivity, not runtime benefit. |
| AT03 source20 gather reuse |Actual eligible single-chunk prefill frequency after prefix caching, repeated gather/dequant duration, overlap and retained-buffer memory cost |Saved requested-length distributions, 8K agent shape, source-derived compressed ratios and workspace bounds. Primarily TTFT/prefill work; frozen long-output ITL effect unknown. |

An Amdahl-style estimate needs both the current **exposed** component fraction and a supported component improvement. Neither is established for these interventions. Byte counts, kernel launch counts, clock claims and old request intervals cannot fill those variables by assumption.

## Scope and reproducibility

- Read metadata/reports/manifests from the current AutoResearch repo, historical skunk-work recovery/C01 artifacts, restored-evidence filename inventory, current read-only experiment registry and this research batch.
- Searched explicit model revision/source identifiers and selected runtime/profiler/component manifests; source hashes and identity excerpts are retained in `source-manifest.json` and `identity-excerpts.json`.
- Ten evidence groups are classified, including the current plan and CPU envelopes. They are not ten experiments or ten new hypotheses.
- No GPU/model/profiler/node availability calls, network calls, new hypotheses, canonical writes or giant raw dataset/trace reprocessing occurred.
- This does not assert that no usable trace exists anywhere in the119GB S3 archive or on a lost/unexamined machine. It states that the inspected retained evidence does not provide one.

**Disposition:** keep RD01/M01/AT03 evidence status unchanged. The next research output can specify the missing exposure fields and future bounded measurement, but cannot report a numeric serving gain from the recovered records.
