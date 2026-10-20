# H200 experiment protocol

## Objective and adaptive ranking

Improve the existing **SLO-qualified cost/throughput and latency frontier** for the user-selected live eight-H200 DP4/EP4 deployment. Scientific novelty has zero weight. Existing fixes, configurations and upstream ports are eligible. [BASELINE.md](BASELINE.md) fixes the actual target; the B200 timings are workload/provenance context, never a numerical H200 baseline.

Priority is an engineering test order, not a fabricated speedup score:

1. Active hardware/model/backend/shape path and missing behavior.
2. Repeated work or binding capacity under our actual workloads.
3. Primary evidence strength, including negative results and unmatched source hardware.
4. Cost of isolating the mechanism and making a decisive measurement.
5. Correctness, tail latency, capacity and integration risk.

H01 is first because a real backend choice is observed and it is cheap to isolate. H02/H03 follow because DP speculation and synchronization are active repeated paths. H07 waits for a qualified Humming baseline. Long-context H08, new-extension H09 and large-integration X02 have substantial eligibility/dependency gates. Correctness Q01–Q04 precede any affected comparison and are not ranked as speedups. TP-only T01–T03 are outside the user-selected layout.

The full5532-row ledger is a reproducible mechanical reclassification with explicit source-review overrides. A prior family assignment was often just a review destination, not a reviewed candidate. Deferred records are unresolved; they have not been disproven or fully source-reviewed. The73 refreshed primary snapshots include context, alternatives and negative evidence;27 have complete changed-file lists at retrieval. Existing generic source reviews are labelled inherited.

## E1: native synthetic workload

Retain native `agent-f75`:8192 input tokens,1024 exact output tokens,6144 shared-prefix tokens, Zipf pool64, temperature0/ignore-EOS behavior and existing request semantics. Preserve eight client shards and separate warmup/measurement seeds. Nominal75% prefix construction is not observed cache hit rate. Use120s warmup and150s measurement for comparable discovery cells; extend if uncertainty or request-count gates require it.

H200 discovery starts at total client concurrency8/16/32/64/128; extend256 only if capacity and tails allow. Low-load H06 uses1/2/8 as a labelled extension. Freeze the same selected points for A/B confirmation. Do not import the B200 seq128 override or its c256/384/512 grid without H200 measurements. Server seq64 is per engine, not total-node client concurrency.

## E2: existing Mooncake replay

Keep trace revision/hash, original600s median/burst/cache-heavy windows, original prefix relationships and the existing custom analyzer. Scale **timestamps only** through the existing trace-speedup setting. At1× offered load may cap throughput; use latency as the matched-load endpoint. Bracket capacity with0.5/0.75/1/1.25/1.5/2× as needed, retaining exactly matched A/B points. Report highest tested passing rate and bounds; never infer capacity from arrival-limited throughput.

Preserve existing gates: completion≥99.5%, errors≤0.1%, qualified fraction≥95%, ≥100 requests, replay not degraded, replay-lag p99≤500ms and authoritative server token counts. Keep existing workload/length-aware tail gates and the≥50-output-token speed cohort (30tok/s qualification with the existing scorer's required fraction). Missing validity fields fail closed. AIPerf native goodput and our custom qualified goodput remain different columns.

## Launch integration gate found during this audit

`Deepseek_serve/ops_latency/lib/common.sh` hardcodes B200 profile/image/experiment paths, B200 result roots and `make serve-b200-vllm`. **Do not run the old native sweep command against the H200 host as-is.** A profile name alone does not make it an H200 launcher.

Before GPU execution, parameterize that small launch/path adapter or launch the H200 manifest explicitly and reuse the existing native client in external-server mode where supported. Save and inspect the dry-run resolved command. `ops_aiperf.runner` supports an explicit profile path and external base URL; that provides the Mooncake route after a separately verified H200 launch. Do not silently substitute AIPerf synthetic text for native agent-f75 cache construction. No adapter was changed or test service launched in this audit.

Observed startup is not ready yet; endpoint health and model identity must pass before any traffic. The checked-in H200 balanced profile is TP4/DSpark-off/MBT4096, different from the selected live DP4/k5/MBT16384 launch. Freeze the **observed arguments**, not that balanced profile.

## Measurement and decision

1. Resolve actual installed implementation and equivalent fixes. Capture model/draft/tokenizer revisions, image digest, patch hashes, dependencies, resolved flags, topology, clocks/power, router behavior and load-generator location. Current source snapshot only attests inspected files.
2. Qualify relevant upstream unit/numerical/distributed tests. Necessary fixes form common control C1; save original C0→C1 correctness/regression evidence. Compare each performance patch independently against C1. An activation/layout/dependency change is its own arm.
3. One exploratory paired run at an eligible E1 point and E2 window, with matched cache/warmup states. Measure predicted mechanism. Stop spending on an inactive path or clear regression.
4. Freeze the chosen arm and preregister one primary endpoint. Run at least five paired blocks, alternating/randomizing order, identical seeds/workloads within each pair and fresh blocks between pairs. Bootstrap paired run blocks, not correlated requests/ranks. Five pairs are a minimum, not guaranteed power.
5. Proposed, editable promotion target: ≥3% qualified-capacity improvement **or** ≥5% lower preregistered matched-load latency, with95% paired interval excluding zero, mechanism improvement, no existing SLO/quality failure, and no unacceptable held-out regression. Specify allowed tradeoffs before runs; a default3% non-SLO guardrail is a proposal, not universal policy. Borderline/noisy results remain inconclusive.
6. Confirm on held-out Mooncake window and the other existing workload. Publish qualifying frontier points plus failures. Do not select the best noisy exploratory result and call it validated.

Use short, separate Nsight Systems/CPU traces to explain launch gaps, expert/attention time, EP synchronization, host lookup and overlap. DCGM/Prometheus counters can accompany load tests if overhead is checked and held constant. A profiled run is not a timing confirmation cell; Nsight Compute is only for a demonstrated hot kernel. Keep existing verbose output logging and metric settings fixed across initial A/B arms; logging-off tuning would be a separate explicit experiment.

H200 node price is unknown. With price P dollars/node-hour and qualified request rate q, cost per million qualified requests is `1e6*P/(3600*q)`. Until P is supplied, report normalized node-seconds per request and relative cost, not the old B200 $36/hour scenario. Count the whole eight-GPU node for this deployment.

## Minimal extra evaluation, only for a demonstrated gap

| Claim | Why E1/E2 alone fail | Smallest addition |
|---|---|---|
| Changed kernel/precision correctness | Successful HTTP and token counts do not establish equivalent math | Upstream reference/tail/graph tests; pinned held-out task quality only when math changes |
| Probabilistic DSpark validity | E1 temperature0 cannot reveal sampling bias | Upstream analytical sampler fixture with nonzero temperature, independent seeds, effect tolerance and multiple-comparison policy |
| Draft acceptance across content domains | Synthetic/replayed prompt construction may not represent real prose/code/math entropy | Cached SPEEDBench/SpecBench data through the existing AIPerf interface, only after version/format support check |
| Long-context candidate work | E1 is8K and a trace may have too few long examples | Inspect length histogram; extend existing client lengths only if needed; preserve failure/OOM results |
| Prefix boundary/restore correctness | Ordinary warm hits may never exercise unaligned siblings/eviction | Small upstream/two-turn fixtures with the same client |
| API idle/restart reliability | Warm steady traffic omits lifecycle transitions | Bounded idle→burst and cold/cached-start fixtures on a test deployment |
| Actual tool semantics | Text replay does not cover assistant/tool-role tokenization | Upstream golden token-ID/streamed-argument fixtures |

AIPerf feature/version details and known reporting caveats are in [the existing evaluator inventory](../pr-evaluation-audit-001/evaluation/EVALUATION_PLAN.md#4-aiperf-and-supporting-tool-inventory). Do not claim all these options are installed and working from a repository audit. Detailed per-request speculation is enabled in the server command, but successful payload collection remains unverified until ready.

## Fork, image and persistent memory

Start the fork branch at the attested baseline, port one pinned patch and its minimal dependencies, build an immutable H200-compatible image, then record actual deployed digest. The exact fork build command must be validated against that fork; this audit does not invent a working image pipeline. Preserve a rollback manifest. No image/deployment change has been made here.

Each plan has a hypothesis identity, baseline/task/policy/source edges, a planned test and a documented parent B200 hypothesis when derived. Keep selection (`deferred`/`accepted`/`rejected`) distinct from test execution (`planned`/started/completed) and outcome (validated/invalidated/inconclusive with artifacts). These26 plans are conditional and untested; no fabricated outcomes are registered. No persistent autonomous agent or scheduler was started by this audit.
