# Shared experiment and decision protocol

## Target and baseline identity

The objective is improved **SLO-qualified serving cost/throughput and latency**, on one eight-B200 node serving the existing DeepSeek-V4.1-Flash checkpoint. Publication novelty has zero weight. Known fixes, upstream ports and configuration improvements are eligible.

The inspected serving checkout is `sofia-gpu-mumbai:/home/ubuntu/shreyas/skunk-work/Deepseek_serve`, clean commit `2e6fa287d90adf7318ad314de27aa2f595aac821`. Its default image is `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`, mapped to vLLM `ac9126e58aa7bbab1856ba6593ba4d5003fea516`.

This is a **configured baseline, not attestation of a running host**. Before applying a patch, save runtime image digest, `vllm.__version__`, installed source identity and dirty patches, GPU model/count, driver/CUDA/PyTorch, vendored dependency versions, model/draft/tokenizer revisions and resolved server arguments. Check both ancestry and equivalent behavior: a cherry-picked fix may lack upstream ancestry. An upstream merge date cannot establish presence in the image.

Reference performance profile: two replicas, four GPUs each, TP1/DP4/EP4 per replica, API2, DSpark k5, adaptive verification off, prefix caching on, Engram host offload on, HICache off, MBT16384, graph cap512, maximum context1,048,576. Profile default is seq64; the measured R7b comparison requires explicit `lat-seqs-128`. The actual launcher selects `FLASHMLA_MEGA_ATTN_DSV41` and `deep_gemm_mega_moe` for this normal EP path. See the [source audit](evaluation/EVALUATION_CAPABILITIES.md) for file/line references and snapshots.

Preserve router helper overrides: bounded endpoint/session hashing1.1×, pool4096, retries. Endpoint locality already exists; internal DP-rank locality is not the same mechanism. Preserve CPU affinity, NUMA placement, API process count and load-generator placement.

## Ranking and filter policy

Ranking is an explicit engineering inspection order, not a prediction of percent improvement:

1. Is the code path active on the real B200/Flash/TP1/DP4 deployment? An inactive path is conditional, regardless of vendor speedup.
2. Does the mechanism affect repeated work or capacity under the actual synthetic/Mooncake load? Cold-start effects get a separate objective.
3. How strong is the primary mechanism evidence, including shape restrictions and contradictory results? B300, different model and simulation results are supporting clues, not B200 results.
4. Can we isolate the change and measure its mechanism cheaply? Large dependency upgrades or new integrations rank behind narrow changes.
5. What correctness, maintenance, KV-capacity or tail-latency risk does it introduce?

Correctness gates G01–G05 are not given a fake throughput rank. Performance rank E01–E18 orders families; `RANKED_PRS.csv` orders PRs by family, with IDs as deterministic ties. Ties are not measured superiority. Source-level priorities and limits remain in each specialist review. Conditional alternatives and dependencies remain visible, rather than being represented as 64 independent predicted wins.

All5,532 input identities are conserved in `PR_DISPOSITIONS.csv`. Rule-based screening, inherited catalog rationale and primary-source review are separate `review_depth` values. `deferred_source_review` explicitly preserves ambiguity. A family assignment for a backlog row is a **review destination**, not permission to cherry-pick every row into that experiment. Each promoted row needs source eligibility review first. Original `already in v0.32` labels are reclassified as membership checks because the B200 source is different.

## E1: retain the actual native synthetic evaluation

Use native `agent-f75`:8,192 input/1,024 exact output, 6,144-token shared-prefix component, Zipf pool64, thinking/tools request, separate warmup/measurement seeds and unique requests. AIPerf's synthetic agent is not a replacement for this cache layout.

Use the verified generic sweep command from the source audit with `lat-seqs-128`; it **starts/restarts the server**. Discovery: c256/384/512,120s warmup and150s measurement. Use an isolated candidate output name and the existing campaign analyzer/SLO tiers. Extra input lengths, cache fractions or occupancy points are **existing workload parameter extensions**, not a second benchmark implementation.

Record raw and SLO-qualified RPS, output tokens/s, TTFT/TPOT/E2E distributions, all failures, actual input/output counts, observed prefix hits and rank imbalance. The nominal75% prefix construction is not an observed hit rate.

## E2: retain Mooncake replay and its existing scorer

Keep the source trace revision/hash and original median, burst and cache-heavy600s windows. Use the existing `ops_aiperf.runner` with fixed schedule and `--trace-speedup`; this scales timestamps only. Do not replace it with a closed-loop concurrency driver. A smaller prepared window is a separately labelled workload and cannot silently replace historical results.

At1×, raw goodput can already be capped by arrivals. Primary fixed-load outcome is latency/SLO failures; a throughput claim requires capacity exploration, e.g. timestamp speedups1,1.25,1.5,2, extending or refining a bracket only after the initial results. Keep both arms on the same tested grid. Report **highest tested passing load**, not interpolated capacity or a single flattering point. If the trace's structure produces no saturation in that grid, record the bound and extend deliberately.

Retain the existing analyzer: completion≥99.5%, errors≤0.1%, qualified fraction≥95%,≥100 requests, replay not degraded, replay lagp99≤500ms, authoritative server token counts; output-speed gates on the≥50-token cohort. Its latency gates use p99 and workload/length-aware rules. Preserve both custom qualified goodput and AIPerf goodput as different columns. Do not rename one to the other. Missing replay-validity fields fail closed.

At the assumed node price$36/hour, cost per million qualified requests is `1e6*36/(3600*qualified_rps) = 10000/qualified_rps`. Store this price as a scenario, not a verified current quote. Keep all eight GPUs in cost accounting even for a smaller topology. Zero goodput gives undefined/infinite cost, not zero. Report tokens/s and useful requests/s separately.

## Staged execution, replication and thresholds

1. **Applicability before GPU spend:** inspect source/image, backend/shape, feature flags, equivalent implementations and dependency versions. No active path → hold with reason. Missing behavior → an eligible experiment, not an automatic patch recommendation.
2. **Correctness:** relevant existing/upstream unit, numerical, replay or tokenizer tests; existing smoke; narrow fixtures only where the source audit establishes a gap. Do not require unrelated research benchmarks for every CPU optimization.
3. **One discovery pair:** one control/treatment pair on the relevant E1 point and E2 window, with mechanism counters. Record this as exploratory, not a validated improvement. Avoid a full sweep for a clearly inactive or regressing mechanism.
4. **Confirmation:** freeze chosen configuration before held-out evaluation. Run at least five paired blocks, alternating/randomizing A/B order with matched datasets/seeds within blocks and new seeds/windows between blocks. Fresh process/cache states must be matched and recorded. Use existing runner repetitions/phases; external ordering is sufficient, no orchestration service needed.
5. **Final frontier:** confirm selected load points plus held-out Mooncake window and the other existing evaluation. Plot nondominated cost vs latency using qualifying runs only, preserving failed points in the raw results.

Proposed task-specific promotion target:≥3% relative qualified-capacity improvement **or**≥5% reduction in the preregistered matched-load latency metric, with a95% run-level paired bootstrap interval excluding zero, the relevant mechanism moving as predicted, and no existing SLO/correctness failure. These are editable experiment targets, not hardcoded ideation policy. Record the primary endpoint and allowed tradeoff before runs. A latency reduction must not trade away required capacity; a capacity improvement must pass existing tail gates. For non-SLO regression guardrails, propose at most3% worse held-out throughput/latency with uncertainty reported; if noise exceeds the margin, increase repeats or mark inconclusive.

Resample **paired run blocks**, not individual requests or correlated GPU ranks. Five pairs are a minimum screening confirmation, not guaranteed statistical power. If intervals straddle the practical threshold, retain inconclusive and estimate the needed repeats; do not claim “no effect.” Small wins such as casts may need more data than this budget justifies. Multiple explored configurations require final held-out confirmation; do not select the best noisy discovery value.

For G01–G05 the primary contract is scoped correctness/reliability, not the3% performance target. For sampling, preregister categorical distributions, independent seeds, sample counts, an effect-size tolerance and multiple-comparison treatment across temperatures/rounds. Use an analytical/reference sampler; exact sequence equality is not required between valid stochastic implementations. For kernel tests, declare dtype-appropriate tolerances and changed-input graph replay coverage before execution. Zero observed failures is bounded evidence, not universal safety.

## What additional evaluation is justified

| Missing claim | Why E1/E2 cannot establish it | Minimal addition |
|---|---|---|
| Sampling distribution | Successful streaming and token counts do not test probability laws | Reuse upstream sampler regression/reference fixture; extend cases only for missing rounds/parameters |
| Kernel/graph numerical correctness | HTTP success does not detect corrupted outputs | Upstream kernel/reference or changed-input replay reproducer; instrument bounds/NaNs |
| Actual tool encoding | Smoke lacks argument assertions; session driver strips tools and appends faux tool results as user text | Reference token-ID and tool-schema fixtures for actual assistant/tool-role messages |
| New precision's task quality | Fixed output length and arithmetic smoke do not measure task utility | Pinned held-out quality suite appropriate to changed math; threshold fixed before runs |
| Cold-start latency | Standard warmup omits launch/first-use cost | Readiness timestamps and isolated cache manifest around existing launcher/requests |
| Idle wake-up if trace lacks idle interval | Existing traffic may never activate the bug | Small idle→burst schedule using the existing client |

Ordinary kernel/routing/scheduler/graph improvements use E1/E2 plus counters. An auxiliary microbenchmark diagnoses mechanism; it never replaces whole-server validation. No new performance harness was built for this audit.

## Fork → immutable image → existing deployment path

1. Create a branch from the **attested** vLLM baseline. Record fork remote and branch. Check each selected PR's current head/merge SHA, diff, dependencies and license; keep each change as a separate commit. Open/draft branches can move; use the recorded SHA.
2. Put necessary correctness changes into a qualified control image C1, with C0→C1 correctness/regression evidence. Compare each performance change independently against C1. If two changes interact, first isolate each, then test the interaction explicitly. Do not stack the shortlist and attribute a combined gain to individual PRs.
3. Reconcile overlapping alternatives: #62535/#59986 address different graph layers; #51199/#61834 are competing coordination designs; prefix-group fixes overlap; #59923's DP-sharded tables and #62359's shared backing are different branches. DeepGEMM/FlashMLA upgrades change APIs/layouts and require their own control arm.
4. Build using the chosen fork's actual supported Dockerfile and pinned toolchain/dependencies. The audited serving repo has a specialized NVFP4 Dockerfile, not a verified generic fork-build pipeline. Save build log, source/patch hashes and immutable image digest; do not invent a known-working build command before inspecting that fork.
5. Existing launcher accepts `VLLM_IMAGE=registry/image@sha256:DIGEST` and profile/experiment overrides. Validate and dry-run first, then deploy to the designated test host when executing. Preserve original image/config for rollback and verify the runtime digest after launch. The current controller lacks the launcher's expected `.venv`; provision the benchmark host first.
6. Persist run manifests, per-request records, server metrics/logs, diagnostic traces, scorer revision, workload hashes, selected policy and verdict. Connect them to the specific hypothesis/test ID. A manifest environment value is not runtime image attestation.

No fork, image build, deployment or GPU experiment was performed by this audit.
