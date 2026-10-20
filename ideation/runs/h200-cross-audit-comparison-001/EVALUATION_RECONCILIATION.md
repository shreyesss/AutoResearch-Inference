# One evaluation contract for comparing the proposals

The two independent investigations agree on many mechanisms. They do **not** share an executed H200 benchmark, and their frozen evaluation contracts differ. Preserve both originals; use this reconciliation when preparing a new test. Nothing here starts a GPU test or changes a service.

## 1. Match the actual control

Both H200 snapshots describe the same image/model and two TP1/DP4/EP4 groups, API2, seq64, MBT16384, cap512, FP8 KV/block64, DSpark k5 with probabilistic/block rejection and AV off. They are different physical hosts: earlier audit inspected219; fresh research is on 223.

The earlier controller serving checkout is2e6fa287; the fresh serving checkout is11c249d2. The former is a controller/config snapshot, not proof of the exact launcher/router source executing on 219. Freeze actual router source/settings, CPU/NUMA affinity, clocks/power, logging, telemetry, client version/location, workload hashes and model/drafter/tokenizer revisions for a new experiment. Image equality does not prove equal scheduling or end-to-end routing.

Use a **within-host paired A/B** first. Running A on 219 and B on 223 once confounds treatment with host placement, caches and load generation. If using both hosts to accelerate confirmation, cross over treatment assignments, include host/block effects and retain within-host controls. Neither host's frozen startup/readiness state is a performance measurement.

## 2. Resolve the workload disagreement explicitly

| Topic | Earlier H200 audit | Fresh H200 run | Combined execution decision |
|---|---|---|---|
| Native E1 | Capacity discovery8/16/32/64/128, extend256 | Preserves historical c256/384/512 at seq64 | Calibrate from low load upward, then include historical higher points if feasible. Freeze an identical A/B grid; failed/overloaded points remain recorded. Historical points and newly selected frontier points get separate labels. |
| Mooncake | Includes slower0.5/0.75× if H200 cannot sustain1× | Starts1/1.25/1.5/2× | Use timestamp-only scaling to bracket a passing/failing rate, including slower points if needed. Freeze the shared grid before confirmation. |
| Cheap synthetic diagnostic | Existing clients; extensions per mechanism | Prepared attach-only 1K/1K,512 warmup and 2048 measured requests | Useful diagnostic if hashes/client semantics match. It does not reproduce agent-f75 or establish arrival-driven capacity. |
| Native cache layout |8192 input/1024 exact output;6144 shared prefix; Zipf64 | Same native semantics | Keep it. AIPerf synthetic prose and 1K/1K are distinct workloads. Nominal prefix fraction is not measured cache hit rate. |
| AIPerf | Catalog describes0.13 features; installation not established | Installed0.11 versus docs0.13 recorded | Pin an isolated client environment; validate actual plugin/export support before using new features. Do not upgrade the live service environment implicitly. |
| Native launcher | B200 paths hardcoded in inspected helper | Separate attach-only H200 evaluator exists on 223 | Audit that existing adapter first. It may address the launch gap, but this comparison did not validate or commit its unrelated dirty implementation. No blind old sweep invocation. |
| Sampling and streaming | Acceptance/correctness distinguished | Explicit token-based TPOT and all-rank coverage | Adopt both: server-accounted tokens, real rejection, target/draft separation, all-rank deltas and reset detection. |
| Practical threshold | Proposed3% capacity or 5% latency,95% paired interval | Provisional2% improvement /3% secondary guard | Neither is a scientific constant or production SLO. Freeze one task-specific threshold before each experiment; do not pick whichever passes afterward. |

### Required timing definitions

- TTFT: request start to first emitted token, with a consistent client/server timing boundary.
- Request TPOT: `(last_token_time - first_token_time)/(server_output_tokens - 1)` for outputs longer than one token. One-token cases are undefined.
- SSE chunk gaps are **not** token ITL under speculative bursts. Report true per-token timings only if instrumentation genuinely provides them.
- Keep the existing Mooncake length-aware scorer separate from AIPerf's native goodput and the manual diagnostic's TTFT≤2s/TPOT≤50ms. Those diagnostic limits are not an approved production SLA.
- At fixed open-loop arrivals, an arrival-limited run cannot demonstrate higher capacity. Compare latency/failures there; increase arrival rate to measure sustainable qualified goodput.

## 3. Six verdicts per experiment

1. **Applicable:** missing behavior exists in the actual architecture/backend/shape/dependency path.
2. **Activated:** changed-path calls divided by eligible opportunities, across every rank and both model roles. Zero calls without meaningful opportunities is inconclusive, not a disproved optimization.
3. **Correct:** independent numerical/reference, distribution, lifetime and distributed tests pass for the changed scope.
4. **Mechanism improved:** the expected work/bytes/wait time decrease, with an alternative explanation tested.
5. **Service improved:** unprofiled, paired E1/E2 results improve a predeclared useful endpoint without unacceptable quality/tail/capacity regression.
6. **Practical:** integration, startup, memory/KV, rollback and maintenance cost are justified.

A source patch applying proves none of steps2–6. A critic score such as76/100 is a policy judgment, not a probability, an observed gain, or permission to bypass applicability.

## 4. Cheap first block and honest duration

First inspect C01–C04 independently. A source/configuration check can stop an ineligible idea without GPU work. If eligible, qualify the narrowly relevant correctness fixtures, take one unprofiled screening pair, and collect a short separate mechanism trace only when needed. C05 gets a low-row exposure check; C09 gets a long-context exposure check.

For promising small gains, use at least five paired full-run blocks, alternating/randomizing A/B, same workload/cache states within pairs, new seeds/windows across blocks. Bootstrap blocks, not correlated requests or ranks. Five pairs are a floor, not a power guarantee. Hold out a second workload/window and do not tune on it.

**Budget arithmetic matters:** five pairs of 600s Mooncake windows require at least100 minutes of measurement, before warmup/drain/builds. Five pairs of native120s warmup +150s measurement require45 minutes at one load point. A20-minute component diagnostic cannot replace this confirmation. Multi-host parallel execution changes wall time, not total node time, and needs balanced assignments.

If measured variability makes a1% improvement indistinguishable from drift, either budget the needed repeats or retain inconclusive. Do not demand a3% threshold mechanically from a low-cost1% patch; choose and freeze the practical threshold based on actual engineering value before confirmation.

## 5. Why microbenchmarks can mislead

As a diagnostic intuition, if a non-overlapped critical-path component takes fraction f of time and becomes s times faster, the serial model predicts speedup `1/(1-f+f/s)`. A component occupying10% of that path and becoming2× faster gives only about 5.3% total speedup. These numbers are illustrative, not measurements of this deployment. Queueing, overlap and SLO boundaries require actual service tests.

For shape-gated changes, account for exposure too: an optimization eligible on only a small fraction of calls may have negligible whole-service value. Do not add overlapping kernel durations as if all were exposed serial time. A faster mHC kernel at one request and a faster long-context indexer address different operating points; keep separate frontier lanes.

## 6. Minimal extra tests

Reuse E1 and Mooncake unless a specific claim is unobservable there:

- Shared plans: upstream live-length/mask/lifetime/graph reference fixtures.
- MoE backend/precision: both observed E384/top6/local96 and E128/top3/local32 geometries, routing/scales/clamp10, empty ranks, graph replay and appropriate quality tests. Confirm role ownership in traces.
- Stochastic verification: analytical/reference distribution tests; acceptance rate is not correctness.
- Prefix/connector changes: unaligned siblings, eviction/restore/cancel cases absent from ordinary traces.
- Long-context indexer: inspect trace histogram first; extend lengths using an existing client only when coverage is insufficient.
- API2 lifecycle: idle/pause/resume and cached restart fixtures on a test deployment.
- Tool/engine/encoding changes: actual assistant/tool-role golden tokens and streamed argument assembly.

Nsight Systems and CPU spans are diagnostic; profiled runs do not enter the frontier. Nsight Compute is reserved for a demonstrated hot kernel. Preserve existing verbose logging and metrics across arms; changing them is a separate optimization.

## 7. Cost and persistent evidence

Use the whole eight-GPU node. With hourly price P and qualified request rate q, cost per million qualified requests is `1e6*P/(3600*q)`. Until P is supplied, report normalized node-seconds/request or relative cost. Per-output-token cost is a different denominator and must be labelled;1,000-request and 1,000,000-request costs differ by1000×. No B200$36/hour substitution.

Keep run-local IDs namespaced (B:E02, A:H02, F:H04), source hashes, parent links and all original verdicts. [CROSSWALK.csv](CROSSWALK.csv) records correspondence; matching mechanisms are not duplicate experimental results. Git synchronizes immutable research artifacts, not live SQLite databases. Do not overwrite or union independently evolving memory databases by copying a backup. A future executor should register a new comparison-specific test referencing the chosen original identities and its newly attested baseline.
