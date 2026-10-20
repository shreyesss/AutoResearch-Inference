# Generic performance candidates rescued from `auto`

## What was actually inspected

Scanned all 5,532 CSV rows with a bounded generic-performance filter: `action` containing `auto`, serving-path keywords, and optimization/performance words. This yielded 46 rows. Read complete stored opening bodies for nine selected PRs and checked seven primary GitHub PR objects through the existing cache. `generic-auto-scan.json`, `source-records.json`, `current-prs.json` preserve the work. This does **not** mean all 5,532 bodies were reviewed.

Ranking concerns usefulness to the current serving system, not publication novelty. No GPU experiments, source patches, builds or deployments were executed.

## Ranked inspection queue

| Priority | PR | What is worth testing | Mandatory gate / reason for restraint |
|---|---|---|---|
| 1 | [#52464](https://github.com/vllm-project/vllm/pull/52464) | Internal DP tie-break prefix affinity; diagnose API2 map fragmentation | Actual DP selection implementation and final-rank trace; source A/B is mixed, not a general speedup |
| 2 | [#51199](https://github.com/vllm-project/vllm/pull/51199) | Coordinate large prefills across DP ranks using asynchronous coordinator releases | Draft; demonstrate cross-rank prefill skew and compatibility with current DSpark/scheduler |
| 3 | [#61834](https://github.com/vllm-project/vllm/pull/61834) | Alternative alignment with protected decode steps and synchronous collective | Draft; adds collective cost and TTFT risk; not an additional independent optimization to stack immediately |
| 4 | [#51333](https://github.com/vllm-project/vllm/pull/51333) | Reduce repeated prefix-cache CPU bookkeeping if the exact path is active | Closed unmerged draft; source workload is Qwen3.5 fine-grained cache, narrower diff has no demonstrated throughput gain |
| 5 | [#54345](https://github.com/vllm-project/vllm/pull/54345) | Avoid first-real-shape sparse-MLA metadata JIT stalls | Verify current FlashMLA DSV41 call path; distinguish cold/new-shape tail from already-warmed throughput |

**Best first investigation:** #52464 and the #51199/#61834 family. They directly address the two-level DP/frontend topology; the remaining two are conditional profile-driven leads. These are three mechanism families plus a startup-tail lead, not five proven B200 wins.

## Current deployment facts that change ranking

The audited serving repo is `2e6fa287d90adf7318ad314de27aa2f595aac821`; its configured vLLM source is `ac9126e58aa7bbab1856ba6593ba4d5003fea516`. CSV claims based on v0.32/B300 are not inclusion proof.

In `../evaluation/snapshot/lib/serve_recipe.py`, line243 selects `deepseek_v41` tokenizer mode; lines295–305 choose `FLASHMLA_MEGA_ATTN_DSV41` and `deep_gemm_mega_moe` for the normal EP path. R7b is two DP4/EP4 groups, API2 per group, with a seq128 override. Runtime image and flags remain to be attested.

The **external** router already bounds session-hash placement at 1.1× in-flight load through latency-helper overrides. Therefore adding bounded endpoint affinity is not itself a new baseline delta. Internal rank affinity and coordination across the four ranks are distinct.

## 1. Internal DP tie-break affinity: useful diagnosis, cautious port

[#52464](https://github.com/vllm-project/vllm/pull/52464) remembers first-block prefix ownership and favors the owner only on tied load scores; lower load still wins. The author explicitly identifies frontend-local maps as a limitation under multiple API processes. That maps closely to our API2 deployment.

Its H100/DeepSeek-V4-Flash A/B shows the largest cache recovery at concurrency1; other points are mixed or negative. The author attributes one large regression to variance, but those measurements cannot establish no regression for us. This is why the first experiment should expose rank locality, not assume it.

**Experiment:** inspect the running `get_core_engine_for_request` and whether the tie-break change/equivalent is already present. Trace identical session/prefix requests through replica → API PID → final DP rank. Compare current routing against only the tie-break patch using existing native prefix workloads and Mooncake cache-heavy. An API1 diagnostic arm isolates frontend-local map fragmentation; keep API2 as the production comparison. Record actual reused tokens, prefill work, queue delay and SLO goodput. A cache-hit-only win is insufficient. Use existing session driver for locality; it does not validate real tool-role encoding.

## 2. Cross-DP prefill coordination: one family, two alternatives

[#51199](https://github.com/vllm-project/vllm/pull/51199) asynchronously coordinates releases with bounded fail-open behavior. Its described DeepSeek-V4 setup is DP8, no prefix caching and a 2K budget; ours is DP4 per group, prefix-enabled and nominal16K. The PR is a draft and does not provide a measured B200 throughput result.

[#61834](https://github.com/vllm-project/vllm/pull/61834) instead aligns per-step state with a CPU collective and protects decode steps after prefill. Its headline measurements use MI355X/DeepSeek-V4-Pro on an earlier development branch, with single runs and node/recipe caveats. The upstream branch explicitly lacks GPU validation. The tradeoff includes higher TTFT, not just faster decode.

**Experiment:** first measure whether one rank's prefill stalls the other ranks. Keep existing E1 agent-f75 and E2 Mooncake burst/load sweeps. Compare baseline and strongest static budget/interval against #51199 and #61834 separately; do not combine them initially. Instrument per-rank phase counts, cross-rank waiting, mixed-step frequency, controller acknowledgments/collective latency, oldest prefill age and actual emitted tokens per engine step. DSpark makes “10 protected steps” different from “10 output tokens.” Require improved existing-SLO-qualified goodput or matched-load latency without starvation. Test wave reset, dummy/pause participation, cancellation and fail-open before long runs; #61834 cannot be combined with `prefill_schedule_interval` as-is.

No new load harness is necessary. Protocol state assertions and iteration instrumentation are the missing parts.

## 3. Prefix bookkeeping: inspect before spending GPU time

[#51333](https://github.com/vllm-project/vllm/pull/51333) memoizes unchanged partial-tail registration and skips empty evictable-block scans. Its motivating profile is on B200, but with Qwen3.5 and fine-grained prefix caching. The author carefully distinguishes a broader variant's roughly1% throughput effect from this narrower diff; the isolated scan optimization was inside noise.

**Experiment only if applicable:** prove repeated `cache_partial_block` work exists on the actual DeepSeek manager path, then compare memo and empty-scan changes separately using existing high-concurrency synthetic and cache-heavy replay. Validate block ownership/hash promotion, preemption/reallocation and release invalidation. CPU savings are diagnostic; the frontier criterion remains serving latency/goodput. Closed-unmerged status is a maintenance warning, not evidence the idea is invalid.

## 4. Runtime JIT: a different measurement window, not a different load generator

[#54345](https://github.com/vllm-project/vllm/pull/54345) targets sparse-MLA metadata specialization and the distinction between compile-only warmup and the first real kernel launch. Its implementation/backend evidence includes RTX PRO6000 Blackwell and B12X-related configuration, which do not establish reachability on our EP FlashMLA backend.

**Experiment:** inspect the actual call graph and existing fix. If reachable, retain existing workload generators and exercise first unseen32K/128K prefill shapes while recording compilation events and TTFT. Separate cold-cache/startup results from steady results after120s warmup. A lifecycle timestamp wrapper is sufficient; a new benchmark stack is unnecessary.

## Additional full-body checks that should not become unconditional shortlists

- [#47583 incremental encoding](https://github.com/vllm-project/vllm/pull/47583): promising long-conversation CPU optimization, but expressly scoped to HF fast tokenizer paths. Our launcher uses custom `deepseek_v41`; inspect renderer/cache entrypoint before activation. If eligible, use existing session load plus a narrow full-versus-incremental token-ID fixture for adversarial/tool boundaries. Do not assume its reported Spark result transfers.
- [#52657 FlashInfer MLA prefill sync](https://github.com/vllm-project/vllm/pull/52657): retains host query offsets to avoid planner synchronization. Our current EP backend is FlashMLA DSV41, so establish that it calls this generic FlashInfer planner. Draft, with GPU tests skipped; backend mismatch is a gate.
- [#60779 expert-map lookup sync](https://github.com/vllm-project/vllm/pull/60779): source explicitly measures layerwise weight reloading/RL updates. Exclude from current steady, fixed-model serving queue; revisit only when reload latency is an explicit objective.
- [#58169 DCP sequence-length sync](https://github.com/vllm-project/vllm/pull/58169): TP1/DP4/EP4 profile does not configure DCP. Inspect actual DCP/helper reachability before considering this; a merged status or GSM8K smoke is not a current performance benefit.

## Reusable evaluation contract

Use `../evaluation/EVALUATION_CAPABILITIES.md` and the root's consolidated thresholds. Preserve original synthetic/Mooncake scorer definitions, warmup, output lengths, model/image/source and request hashes. At1× replay goodput may already sit near offered load; use matched-load latency or existing timestamp-speedup capacity comparisons rather than an impossible fixed-offer goodput target. Run cold/first-shape results in a separate evidence class. No performance-only result can discharge sampling, tokenizer or kernel correctness requirements.

`candidates.json` contains per-item source quotes, state/draft/head SHA, baseline gates, metric requirements and experiment descriptions. Rankings are inspection priorities, not cherry-pick authorization or predicted gains.
