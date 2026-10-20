# Routing, prefix reuse and scheduling exploration

## Outcome and scope

Two falsifiable directions are prepared for B200 R7b. They are **untested experiment designs**, not measured optimizations. Baseline evidence is the existing B200 report and launch-profile snapshot; profiles do not establish which features the running deployment actually has. The companion `experiments.json` contains controls, treatment arms, instrumentation, thresholds, budgets, and stop conditions.

1. **Preserve prefix locality to the final DP rank, with an escape for overloaded warm prefixes.**
2. **Adapt the aggregate prefill budget to pressure while bounding prefill starvation.**

Scientific novelty is disabled in the task brief. Each proposal must improve the existing deployment and beat a strong existing comparator.

## How this track explored

The subagent used three different reasoning directions:

- **Deployment-first:** R7b comprises two DP4/EP4 engines with API2 per replica. Ask whether apparent endpoint affinity survives the second load-balancing level and separate frontend processes.
- **Seeded cross-product search:** seed `20261020`; shuffle pairs from `prefix/chunked/scheduler/routing` × `cache/latency/balance/prefill`; combine four sampled searches with four directed searches. Require all terms, filter `updated_at >= 2026-08-01`, inspect top eight BM25 results. Two undated searches deliberately recover older implementations/counterevidence. Date is a filter, not a recency score. `search-results.json` preserves all ten exact calls and results.
- **Counterexample-first literature reading:** read full papers about cases where better cache hit rate does not improve capacity and where reducing decode interference worsens TTFT. This prevents selecting a proxy metric as the objective.

All GitHub searches operated against the VM's actual local corpus using the application's tool registry. Selected bodies were read using `github.get`. Three papers were fetched and cached with `research.read`. Two PR-head source files were fetched with `github.code` at exact SHAs. No Serper requests were used by this track. Web discovery queries used the available browser search, then primary arXiv text was fetched into the application's corpus.

## Baseline that motivates the tests

The existing [B200 report](../../../../b200-bench-analysis/PARETO_FINDINGS.md) identifies R7b as the two-engine configuration with DSpark k5, prefix cache and the seq128 override. At closed-loop concurrency 384 it reports 27.69 req/s and E2E p95 18.30 s; at 512, 33.76 req/s and E2E p95 19.49 s. These are throughput and latency observations, **not SLO goodput**. The 75% prefix setting is a cacheability target, not measured cache hits.

The shared `../BASELINE_AUDIT.md` and `../EVALUATION_PROTOCOL.md` take precedence for scorer semantics and workload definitions. In particular, custom length-aware goodput and AIPerf goodput differ. Whole-trace streamed inter-token gaps and TPOT are different quantities. At 1× replay goodput is already close to offered load; a capacity claim requires increasing offered load, while a fixed-load comparison can show a tail-latency benefit.

## R1 — rank-aware prefix locality with warm-hit load escape

**Conditional hypothesis.** If requests with reusable prefixes reach different final DP ranks, some prefill work can be recovered. If prefix popularity is skewed, unconditional stickiness can turn that recovery into a queue hotspot. Preserve exact-prefix locality across both routing levels, but escape even on predicted cache hits when excess queue delay outweighs saved prefill time.

### Grounding and concrete implementation delta

- [vLLM PR #43483](https://github.com/vllm-project/vllm/pull/43483), open and labelled `needs-rebase` in this snapshot, proposes internal/local DP prefix-aware routing. Its opening body explicitly limits scope; it is not a cross-replica KV migration system.
- Exact [router source at b4baf2d](https://github.com/vllm-project/vllm/blob/b4baf2df26b25c3ab39c5590656d3937c9ac6fb0/vllm/v1/engine/dp_prefix_cache_router.py) was fetched. `route()` invokes `_pick_balanced_miss_rank` only under `_would_miss`. The inspected implementation has a load-imbalance ratio, but **that miss-reroute gate does not implement a queue-cost escape for every warm sticky hit**. That is a concrete candidate extension, subject to comparison with the actual deployed router.
- [PR #58757](https://github.com/vllm-project/vllm/pull/58757) describes routing to individual DP engines with vLLM Router. It is documentation, not proof that our deployment exposes or uses this path.
- [CacheRoute, August 2026](https://arxiv.org/html/2608.19677v1), provides direct counterevidence to blanket affinity: some tested configurations gained cache hits but lost capacity because residual skew dominated. Its studied fleet/model differ from our two-replica B200 system. This motivates workload-specific shadow measurements rather than importing its reported gains.

### Minimal discriminating experiment

First trace `request → replica → frontend process → DP rank`, measuring executed prefill tokens, served cached tokens and queue delay. If there are no recoverable misses, stop this branch. Compare original and best load-only routing against endpoint-only affinity, rank-aware affinity, and rank-aware affinity plus warm-hit queue escape. Hold engine settings constant. Endpoint-only affinity is an intentional negative/control arm: it diagnoses whether locality is lost inside DP4.

Use cold-prefix, many-key reuse, one-hot-prefix skew and held-out burst traces. A cache-hit increase alone cannot pass. The accepted result must improve matched-load latency or sustainable SLO capacity without starvation, errors or correctness regressions. Only then consider combining routing with scheduler changes.

## R2 — pressure-adaptive aggregate prefill admission

**Conditional hypothesis.** Under R7b's nominal 16K token budget, uncached prefill bursts may delay decode steps. Temporarily cap aggregate prefill admission when decode is active and multiple prefills queue, then restore the large budget under low pressure. Bound oldest-prefill wait so improved ITL cannot hide admission starvation.

### Grounding and competing explanations

- [RFC #52906](https://github.com/vllm-project/vllm/issues/52906), updated October 12, describes a concrete policy: prefill cap 2K when at least two prefills are pending/running and decode is active; otherwise 16K. It leaves the global token budget unchanged. The linked [P-PAS paper](https://arxiv.org/html/2608.15171v1) and [implementation repository](https://github.com/TimoSaemann/ppas-vllm) make this a practical reuse/port candidate. Compatibility with our actual B200/DeepSeek/DSpark build is unverified.
- [PR #56848](https://github.com/vllm-project/vllm/pull/56848) is explicit about decode-priority cadence sacrificing prefill throughput/TTFT. Its reported workload is not our deployment. Exact scheduler source was fetched at `f2fe7307a504ee1c40ca127523a667bf1fda5ab2`; it computes cadence from engine steps and tests for a pure-decode request. DSpark emits multiple tokens per step, so step cadence is not a token deadline.
- [SLOWeave, September 2026](https://arxiv.org/html/2609.07883v1), motivates deadline-aware chunk selection, but its assumptions and finite calibration envelope require scrutiny. It does not establish a ready drop-in B200 DP/EP controller. Start with the cheaper pressure rule; attempt a predictor only if the pilot establishes a problem that static controls cannot solve.

### Minimal discriminating experiment

Measure per-iteration prefill/decode/verification tokens, GPU iteration time, graph mode, accepted speculative tokens, KV preemption and request age. If prefill admission is not correlated with decode stalls, prune. Compare the adaptive controller against **the best of fixed 2K/4K/8K/16K**, not just 16K. Include an age guard and a held-out long-prefill burst. A lower ITL paired with worse length-aware goodput or E2E is a failed tradeoff, not success.

## Evaluation contracts and resources

`experiments.json` contains machine-readable plans with all thresholds explicitly marked as chosen rules. Suggested support is ≥5% sustainable SLO-capacity improvement with a paired interval excluding zero, or ≥5% p95 E2E reduction at fixed offered load with throughput/error/correctness guardrails. These are screening choices, not production SLOs; use the actual frozen scorer to define eligibility.

Stage budgets per direction: CPU presence check; 30 minutes on eight GPUs for a mechanism pilot; 90 minutes for screening; at most two hours for a promising finalist. At the report's assumed $36/hour, these are $18/$54/$72 scenarios. They are caps, not claims that all matrix cells fit. Reduce exploratory cells before reducing required repetitions, and report a right-censored capacity if the load knee is not reached.

No GPU job, baseline modification, serving rollout or measured improvement occurred in this exploration. Generated proposals and reviews are separate from these engineering designs; their exact accepted/deferred/rejected decisions are retained in `hypotheses/decision.md` and persistent memory.

## Actual system decision

The evidence extractor produced 11 quote-validated claims from seven primary records. The hypothesis runner generated two cards; both scored 68/100 and were **deferred**, not rejected or accepted. Its task-generated rubric requires the deployment delta to be established, so the unresolved runtime-presence check is a mandatory unknown. The priority threshold also exceeds 68. The full rubric, critique and reasons are retained. This is an honest inspection queue, not a claim of two validated improvements.

Both designs are registered as planned tests with a CPU presence gate first. No test was started and no experimental outcome was recorded.

- Hypothesis `hypothesis:cc9105999256646dbaa47c4f6b615bfa412fd3674c30bdafc5fd8787e38dd075`; planned test `test:010eae591cc308f30c2ae343a96c19f5a399335b55ca06871da9edb2ed53a7d6`.

- Hypothesis `hypothesis:60c092dce5cb28eec640ec26cf51b69b80dabd4666094baf8b005bad34f75ac9`; planned test `test:abf2bf0e063aa6c3ad7be3992c6026db0e8398608cbf953a3a69d416f8de0eda`.

### Refinement and consolidation boundary

The warm-hit escape extension was identified by the subagent after fetching the PR-head code. It is an engineering refinement of the generated routing card, **not a claim that the model critic reviewed that exact extension**. The registered plan includes the exact code source and delta. Keep that distinction when creating a revised hypothesis or evaluating the extension.

The per-track plans were registered before the shared protocol was finalized. Their 5% guardrail and 90-minute screening suggestions are preliminary. The shared protocol uses stricter 2% guardrails and a 45-minute screening budget; use the consolidated, versioned evaluation contract before execution. Preserve these initial plans as provenance rather than silently mutating them.
