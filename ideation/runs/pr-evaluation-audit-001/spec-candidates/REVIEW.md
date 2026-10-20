# B200 serving audit: speculation, graphs, scheduling, caching and API

## Scope and evidence

This audit starts from **all 5,532 CSV rows and all their fields**, not a search for B200 in titles. A broad family pass retained 1,899 rows for the areas assigned to this branch. The complete 2,222-line Markdown file was parsed for candidate provenance; relevant detailed tables and selected PR bodies were then inspected. **This does not claim that 5,532 complete PR bodies were reviewed.** The parent audit combines this with the other families.

Artifacts:

- `catalog-family-scan.json`: input hashes, every broad family row, selection method.
- `candidates.json`: **28 ranked PRs**, source quotes and hashes, latest known states, dependencies, eligibility gates, and existing evaluation requirements; 15 explicit exclusions/delegations.
- `source-*.json`: 41 stored opening records plus separately available children. Bodies do not imply complete discussion coverage.
- `current-pr-*.json`: 12 bounded cached/live GitHub REST checks.
- `pinned-*.json`: four complete source files from exact historical vLLM SHA `ac9126e58aa7bbab1856ba6593ba4d5003fea516`.

No GPU execution, deployment, source modification, new evaluator or hypothesis-memory registration was performed. The following priorities are **inspection priorities**, not instructions to cherry-pick blindly and not predicted speedups.

## Baseline is a prerequisite, not a release label

The supplied catalog targets a **B300 v0.32.0 fork**, while our objective is **eight B200 GPUs**, the existing synthetic `agent-f75` campaign and Mooncake replay. `deepseek_serve` revision `2e6fa287…` is not a vLLM revision. The historical vLLM image pin is `ac9126e58aa7…`; the actual benchmark runtime may carry a dirty patch. “Already in v0.32” therefore neither establishes presence nor excludes value.

Resolve image digest, actual vLLM SHA and patch, checkpoint/drafter/tokenizer revisions, k5 verification mode, per-rank sequence limits, graph descriptors, prefix-cache settings, and whether a KV connector exists. R7b's profile requests DSpark k5, adaptive verification off, prefix caching and API2; its seq128 overlay overrides the profile's seq64. The contradictory CSV DSpark label must not determine eligibility.

**Mooncake workload replay is not the Mooncake KV connector.** CPU/filesystem offload PRs are gated on the actual connector; running the named workload alone does not activate those paths.

## Ranked shortlist

### Correctness and liveness before performance attribution

| Rank | PR | Why it matters | Required qualifier |
|---:|---|---|---|
| 1 | [#61161](https://github.com/vllm-project/vllm/pull/61161) | Fresh random draws across block-verification rounds; matches probabilistic DSpark/block sampling | Check actual sampler. Toy distribution tests matter; aggregate accuracy or golden NLL alone cannot prove unbiased generation |
| 2 | [#62535](https://github.com/vllm-project/vllm/pull/62535) | Keep prefill-bearing batches out of FULL decode graphs | Open; SM120 evidence. Trace actual B200 dispatch and compare mixed-load outputs with eager reference |
| 3 | [#61174](https://github.com/vllm-project/vllm/pull/61174) | Clear stale shared block-table rows when batches shrink | H20/GLM validation; verify DSv4.1 path and shrinking/draining batches |
| 4 | [#59559](https://github.com/vllm-project/vllm/pull/59559) | API2/DP wake-up race can leave idle or paused ranks hanging | Frontend and engines must move together; this is a 12-file protocol change, not a tiny local patch |
| 5 | [#60767](https://github.com/vllm-project/vllm/pull/60767) | Mask freed SWA pages that can leak NaNs through tiled attention | MRV2 SlidingWindowSpec, no CP; validate the null block and actual group types |
| 6 | [#62199](https://github.com/vllm-project/vllm/pull/62199) | Correct tool-result turn encoding and preserved reasoning | Changes prompt token IDs and cache keys. Establish a new encoding baseline, not a misleading same-input speedup |

These are prerequisites for trustworthy experiments; a correctness repair need not increase throughput to be valuable.

### Highest-value performance inspections

| Rank | PR | Mechanism | What would make it worth an existing serving A/B |
|---:|---|---|---|
| 7 | [#58984](https://github.com/vllm-project/vllm/pull/58984) | Use logical DP request count for draft graph dispatch | Trace target-capacity inflation of draft rows. Author H20 measurements used adaptive verification **on**; our off configuration needs separate eligibility proof |
| 8 | [#62040](https://github.com/vllm-project/vllm/pull/62040) | Retain a FULL graph for the largest uniform draft batch | Enumerate q6 target and q5 draft descriptors. GB200 seq72 proof does not establish that seq128 has the same hole |
| 9 | [#59468](https://github.com/vllm-project/vllm/pull/59468) | Stop charging separate draft work against the target token budget | Show budget-bound mixed steps at actual 16K. At 128 requests, removing four charges each frees at most 512 target-budget tokens, not the author's 512-budget regime |
| 10 | [#61767](https://github.com/vllm-project/vllm/pull/61767) | Faster tiny CPU collectives for DP metadata | CPU sync must be on the critical path; reported collective microbench speedups are not end-to-end serving gains |
| 11 | [#48459](https://github.com/vllm-project/vllm/pull/48459) | Prevent a draft group's zero hit from vetoing GPU prefix reuse | **Current PR annotates only `model_version == deepseek_v4`.** DSv4.1 applicability needs adaptation/inspection, not a catalog “yes” |
| 12 | [#47926](https://github.com/vllm-project/vllm/pull/47926) | Hide restored-but-unwritten draft context from draft attention | Show cache-hit-dependent acceptance collapse. B200 evidence is GLM5.2 k7; validate DeepSeek k5 and unaligned boundaries |
| 13 | [#61455](https://github.com/vllm-project/vllm/pull/61455) | Explicit draft-layer ownership for prefix groups | Inspect actual flags and downstream junction semantics; correct ownership does not itself guarantee a gain |
| 14 | [#62278](https://github.com/vllm-project/vllm/pull/62278) | Preserve both reachable shared-prefix junction positions | Conditional on dropping draft groups and retention behavior; alternative to narrower #62206 |
| 15 | [#57110](https://github.com/vllm-project/vllm/pull/57110) | Stop unintended DSpark tail-block drop | **Also changes heterogeneous page allocation and admission.** Do not treat its title as a one-flag patch |
| 16 | [#59986](https://github.com/vllm-project/vllm/pull/59986) | DSv4.1 graph capability restrictions for safe mixed prefill | Conditional safety work, especially before adaptive verification; CPU tests only, no author B300 end-to-end run |

### Conditional families; keep these separate from the present baseline

| Rank | PR | Eligibility and evaluation need |
|---:|---|---|
| 17 | [#47891](https://github.com/vllm-project/vllm/pull/47891) | OffloadingConnector prefix-veto counterpart to #48459; active connector and model annotation must be confirmed |
| 18 | [#62041](https://github.com/vllm-project/vllm/pull/62041) | Collect KV transfer results before drafting; trace actual load-notification delay; no PR serving measurement |
| 19 | [#59096](https://github.com/vllm-project/vllm/pull/59096) | Filesystem-tier disconnect/load race; fault probe and engine survival, not a throughput claim |
| 20 | [#59140](https://github.com/vllm-project/vllm/pull/59140) | Correct secondary-tier store drop fraction under pressure; affects optional writes, **not request admission** |
| 21 | [#61375](https://github.com/vllm-project/vllm/pull/61375) | Persist a loaded partial-tail chunk; requires observed partial-tail stalls with the configured groups |
| 22 | [#61961](https://github.com/vllm-project/vllm/pull/61961) | Optional synchronous small CPU-tier hits; measure step delay saved against whole-batch copy blocking |
| 23 | [#61724](https://github.com/vllm-project/vllm/pull/61724) | Skip null SWA block-table head in Python; useful mainly with long contexts and high turnover, not assumed for 8K native traffic |
| 24 | [#61261](https://github.com/vllm-project/vllm/pull/61261) | Bound draft context if acceptance collapses beyond its training range; Kimi/B300 evidence does not prove DeepSeek applicability |
| 25 | [#62062](https://github.com/vllm-project/vllm/pull/62062) | Preserve replica identity in draft compile caches; inspect independent-instance cache layout before warm-restart testing |
| 26 | [#62259](https://github.com/vllm-project/vllm/pull/62259) | Valid truncated DSML JSON and incremental argument streaming; existing tool-conformance workload, not random-token throughput |
| 27 | [#62206](https://github.com/vllm-project/vllm/pull/62206) | Narrow SWA shared-prefix junction fix; compare against broader #62278, do not stack automatically |
| 28 | [#54077](https://github.com/vllm-project/vllm/pull/54077) | Schedulable mixed-tail profiling; **deferred while adaptive verification is off**. Both calibration arms must share the same qualified adaptive-on configuration |

## Configuration experiment: audit graph coverage before increasing caps

For 128 active requests per rank and k5, a uniform target verification batch can require **768 rows**. An anchor-sampling DSpark draft pass can require **640 rows**. A true 512-row capture ceiling cannot cover those full batches; confirm effective limits and actual scheduler shapes first.

A “g1024” candidate should provide valid target and draft descriptor coverage, not merely a scalar cap. **1024 is not divisible by six**; the largest multiple of six below it is 1020. A target q6 ladder need not produce the desired q5 draft full-batch descriptor, which is why #62040 is a separate inspection. Capture-memory growth can reduce KV capacity and reverse the end-to-end benefit. Use the existing concurrency sweeps and Mooncake replay; retain graph fallback, padded rows and KV bytes in the result.

## Exact historical source findings

Four files were retrieved at `ac9126e58aa7bbab1856ba6593ba4d5003fea516`, with complete bodies/hashes preserved:

1. `vllm/config/speculative.py`, lines 1882–1914: DSpark's table says K−1 additional slots; the parallel-drafting return retains K−1. This supports checking #59468 against the historical pin. At lines 1944–1946, DSpark remains in the EAGLE block-drop predicate. No `draft_context_window` field appears.
2. `vllm/v1/worker/gpu/cudagraph_utils.py`, lines 314–322: rounded token counts are skipped when they exceed the request cap; there is no #62040-style clamp in that loop. There is no `allow_full` argument in this file. `_is_compatible` at lines 103–130 treats a descriptor with unconstrained query length as compatible; the call chain still needs inspection before declaring the #62535 failure reachable.
3. `vllm/v1/core/kv_cache_utils.py`: no `eagle_group_is_veto_exempt` identifier and no old `_annotate_eagle_groups_deepseek_v4` helper. The proposed #48459 port therefore needs a path-aware adaptation, not an assumption of clean applicability.
4. `vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py`, lines 547–569: a request seed and token position feed `tl_rand32(seed, pos, ...)`; no `step_seed` helper appears in this file. This is a strong reason to inspect the round-seeding call path, but a symbol absence alone is not a proof of the end-to-end sampling bug.

These observations establish differences in the **historical source**, not the identity of a running server or benchmark binary.

## Catalog corrections and excluded lookalikes

- **#61827:** its primary repair is `StandaloneARSpeculator` with `method=draft_model`, not DSpark. Its DSpark/DFlash change affects unused dynamic-SD capture tiers. Fixed k5 does not justify including the large patch for an inferred performance gain.
- **#61911:** explicitly leaves DFlash/DSpark block-drop behavior unchanged. Its GLM Mamba MTP result cannot be assigned to our system.
- **#61589:** EAGLE lookahead hashing has restrictive eligibility and no rerun of split-PR GPU benchmarks; investigate only if the actual DSpark method qualifies. Do not generalize its title to every prefix cache.
- **#56734:** AR/MTP dummy decoding and stale-row logic provide a regression reference, not automatic DSpark applicability.
- **#61807 and #61153:** alternate/superseded fixes; prefer reviewing canonical #58984 and #61161 rather than counting duplicates as independent opportunities.
- **#56966, #56611, #57281:** explicitly exclude speculative layouts or require incompatible TP/DP/cache modes. Broad relevance of the model name is insufficient.
- **#61553/#61555:** PCP paths are outside the current TP1 DEP setup.
- **#62200:** Rust frontend counterpart, not the Python encoder change.
- **#60468/#61039:** relevant warmup/indexer candidates owned by the kernel branch; delegated, not dismissed.

## Dependencies and requirements for the existing evaluator

1. **Correctness bundle:** #61161 plus graph dispatch/capability coverage (#62535/#59986), stale rows #61174 and conditional stale SWA columns #60767. Evaluate overlapping changes as a reviewed set with regression isolation; none is a claimed speedup.
2. **Graph/budget family:** graph coverage configuration, #62040, #58984, #59468. First show the specific padding, fallback or admission bottleneck. Keep k5, precision, topology and cache state unchanged within each A/B.
3. **Prefix family:** actual group flags/validity first; #48459/#47891 architecture gating, #47926 restored-context handling, #61455 ownership and #62206/#62278 junction alternatives. Do not maximize cache-hit rate at the expense of invalid draft state.
4. **API/encoding family:** #59559 liveness, #62199 prompt semantics, #62259 parser behavior. Encoding changes require explicit new goldens and token counts; a shorter or different prompt is not a same-workload kernel improvement.
5. **Tier family:** only when the current serving configuration really uses CPU/fs offload. Load completion, aborts, cache namespace and restored token correctness must accompany TTFT.

Bind these to the existing native synthetic runner and AIPerf/Mooncake tooling. Request-level timestamps, fixed tokenizer, successful SLO goodput, both currently used scorers, output-length cohorts, offered-rate/capacity behavior and queue growth must remain visible. At a fixed arrival rate already fully served, measure tail improvement rather than demanding impossible extra goodput. Existing replay alone does not prove unbiased sampling, correct tool rendering or fault recovery; those require the corresponding existing correctness/fault checks or an explicit evaluator gap.

## Freshness and limitations

Twelve PR API checks plus four pinned file reads fit the 20-call proof budget. API reads use the app's existing cache. #58984 was merged on **October 20 at 00:06:58 UTC**; #59986 remains open with an updated **October 20 03:33:07 UTC** head. #62535/#62040/#61827 remain open. #61161, #59559, #59468 and #62199 are merged; this does not establish inclusion in `ac912…` or the actual server. Remaining records are timestamped local snapshots, not claimed freshly verified states.

All benchmark numbers in source records are **author/reporter claims**. B300/GB300, GB200, H20, H100 and SM120 evidence can motivate a mechanism inspection, but none is substituted for eight-B200 measurements. No findings here claim a measured improvement on our deployment.
