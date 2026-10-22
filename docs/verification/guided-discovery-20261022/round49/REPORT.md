# Round49 — restrict the draft head's rows, not the target vocabulary

**Decision: retain a deferred alternative in the draft-head investigation family; no new accepted implementation or service claim.** Static vocabulary restriction has a credible operation-removal mechanism that differs from QH45 precision reduction. The current target has no configured keep set, representative held-out token coverage or exposed head timing in this packet. Those missing measurements prevent a numerical ROI forecast. Do not implement a dynamic per-step vocabulary search merely because it produces fewer candidates.

## 1. Actual discovery and adaptation

Two dated arXiv searches covered August1 through October22 inclusive. The first exact pruning/restriction/selection query returned zero. An explicit observation object recorded that failure; the next query retained speculative/vocabulary/date anchors and relaxed only the operation phrase. It returned six identities. Six abstracts were read; FlexEE's method and relevant appendix were inspected in newly fetched v1 full text. HyCo's previously retained full text was reused. No claim of an exhaustive literature search or complete visual/figure review.

| Source | Selected component / disposition |
|---|---|
| [HyCo, October](https://arxiv.org/abs/2610.21436v2) | Its static restricted drafter vocabulary is separable from mobile placement, QAT, context restriction and approximate acceptance. Preserve exact target verification; its mobile timing is not ours. |
| [FlexEE, September](https://arxiv.org/abs/2609.17008v1) | Local candidate rows can be reused across exit layers. Full method trains early-exit representations and trades accuracy. Its repeated exit heads differ from our one batched DSpark head call. Keep the row-selection concept, reject a direct speedup transfer. |
| Multi-Access SPIN2608.29618 | Abstract: uplink/downlink full-distribution transfer is the problem; this single-node layout does not establish that bottleneck. |
| Osprey2609.09338 | Abstract: pretrained, pruned, adapted/distilled drafters; not a frozen-weight drop-in. |
| Tool transactions2609.15397 | Abstract: agent/tool state semantics; outside the inference mechanism investigated here. |
| Certified Splitting2610.08854 | Abstract: tokenizer-boundary contract, not draft output-head work. |

HyCo explicitly cites [FR-Spec, ACL2025](https://aclanthology.org/2025.acl-long.198/). Following that citation is an intentional exception to the recent-discovery window. The primary PDF was fetched once through the existing cached source reader, with explicit PDF locator, and its method/comparator sections inspected. FR-Spec constructs a frequency-ranked subset and crops draft output rows without retraining, while retaining full target verification. Its EAGLE/Llama measurements and corpus proportions do not predict V4.1 performance. This is prior work, not a newly invented algorithm.

Three readonly local searches returned18/30/1 records. The30-result draft/vocabulary query is capped. Five opening bodies were inspected in detail: vLLM24343/29334/61152 and SGLang28856/29943. They are supporting history and failure examples, not freshly inspected head diffs. An earlier root CLI query mistakenly included literal OR; the search tool treats it as a term. Its pending receipt is not counted as scientific coverage. The corrected calls use explicit match=all. Original command/error chronology remains retained.

## 2. What the pinned implementation actually does

Baseline: callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883`, planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, TP1/DP4/EP4 groups. These are source-profile pins, not live deployment attestation.

- `models/deepseek_v41/nvidia/dspark.py` aliases the full target head, uses identity draft-to-target token mapping and retains full parent-token Markov embeddings.
- `DSparkSpeculator._sample_sequential` computes the base head once for **all request×five-position rows**, then applies parent-conditioned Markov bias sequentially. This is not five separately loaded full base heads per request.
- `_sample_sequential_topk` still computes full base logits before TopK, then masks and applies gathered Markov correction. It does not avoid the full base projection. The pinned configuration explicitly limits `dspark_draft_topk` to Qwen3/Qwen3Omni DSpark; native V4.1 also lacks that gathered-bias hook. It is not an available V4.1 tuning switch.
- The shared speculator already has an optional reduced-vocabulary scatter interface. It interprets `draft_id_to_target_id` as **offsets**: target columns are `arange(K)+d2t`, not raw keep-set IDs. It scatters into persistent full-target-width negative-infinity scratch before probabilistic sampling/cache writes. This interface is not currently enabled by the V4.1 model.

This existing interface is useful: a conservative initial adapter can reduce the base-head projection while leaving full-width sampler/rejection buffers intact. That sacrifices some potential sampler saving but avoids conflating a narrower vocabulary implementation with a new native rejection kernel.

## 3. Proposed isolated component and hard boundaries

Choose a fixed target-token ID set S using an independent representative output corpus, include required special/byte/control tokens, and freeze the selection before held-out evaluation. Create a **separate** immutable selected-row head for the draft. Preserve every target weight and the target full head; retain full input/Markov parent embedding support so a correction or bonus outside S remains usable.

Initially compute the existing full Markov bias and gather its S columns, rather than simultaneously inventing a narrower Markov implementation. Add those values to the selected base logits and use the audited full-width scatter/cache path. This isolates one operation: fewer base-head output rows. It does not promise fewer Markov GEMMs, sampler scans or rejection buffers. Weight-row gathering at initialization is a derived copy, not neural retraining, but costs additional HBM and needs reload/ownership rules.

For selected IDs `[3,8]`, the offset map must be `[3,7]`; supplying `[3,8]` as offsets would scatter to `[3,9]`. Require unique/in-range IDs and exact correspondence between selected weights, bias columns, sample IDs and cached q. A frozen S keeps outside columns negative infinity across rounds; changing S in place without clearing old columns is unsafe. Dynamic keep sets are excluded from the initial arm.

No epsilon-relaxed acceptance. For ordinary one-token rejection, acceptance is `sum_v min(p(v),q_S(v)) <= p(S)` and target residual recovery restores full support. This mathematical identity is not proof of the native block verifier. Validate its distribution, temperature/watermark/grammar/bonus/EOS and multi-round graph contracts separately. Cached q must be the actual restricted, normalized proposal, not the original unrestricted q.

## 4. Why two attractive shortcuts do not qualify

**FlexEE-style dynamic selection:** it pays for a full head at one exit and reuses a shortlist at later exits for the same token. Our existing DSpark computes all five future rows in a batched head. Selecting from the first row still reads the full weight matrix at least once, introduces serial dependency/TopK/gather work and does not establish coverage of later positions. It can reduce some arithmetic yet lose weight reuse. No head tiling/traffic trace supports this variant; park it.

**Keep the most common25% and assume95% acceptance:** aggregate corpus frequency is not conditional target mass. A rare-code/Unicode request can put almost all mass outside S even when global coverage is high. Per-step support mass is not five-step committed progress; adaptive confidence and block verification change the relationship. Do not transplant FR-Spec's subset or HyCo's86,089-token set to the V4.1 tokenizer.

## 5. PR triangulation and prior overlap

vLLM29334 replaces24343 and reports only one/two samples on A100/Llama/EAGLE. Its own body calls out extra head memory from breaking target/draft aliasing. This supports a capacity warning, not a reliable target effect estimate. SGLang28856/29943 describe reduced-head graph/shared-buffer width mismatches: graph-buffer shape must follow actual selected head output or explicitly retained full-width scatter contract. vLLM61152 describes a narrow-draft rejection support/stride repair, including block recovery. We have not proved that change's inclusion in the pin; the proposed first arm deliberately retains full-width cached q and still requires native correctness checks.

Prior round25 concerned **target** head/rejection work and found the default no-copy fast path; that finding remains valid. C025 concerns full-vocabulary Markov sampler fusion; this component initially leaves those scans unchanged. QH45 reduces draft-head precision while retaining every output row; this alternative removes rows, keeps original selected weight precision, and trades acceptance plus extra memory. They share the same unknown target head exposure. Keep them separate experimental arms under one head investigation family, not additive forecasts or renamed discoveries.

## 6. ROI screen and the next decision-changing evidence

With V=129280,H=5120,BF16, the aliased original head occupies1,323,827,200 logical weight bytes. It remains required. A fraction f selected-row draft copy adds approximately `f*1,323,827,200` bytes before alignment, mappings/workspace and transients. At f=.25 that is330,956,800 additional bytes per TP1 rank. Projection arithmetic ideally scales with f; elapsed time need not. Full bias, full-width scatter/cache/sampling and all target work remain in this first arm.

Let original round time T, committed progress G, exposed head time Ht, retained progress ratio r and new overhead O. An optimistic upper saving is `(1-f)*Ht-O`; actual reduced-head timing can differ. Net progress/time improves only if `r > T_new/T`. All target values are unknown. In particular, a lower accepted length is allowed if time falls more; a faster head is insufficient when committed progress falls more.

The next useful CPU step is **not another invented probability fixture**. First inventory already-retained exact-baseline head timing and output token IDs/tokenizer revision. If available, construct S on request-disjoint training outputs and measure held-out per-domain token coverage, outside-S transitions/burst lengths and capacity feasibility. Such frequency evidence screens disastrous sets but cannot estimate counterfactual conditional acceptance or native runtime. Existing source-profile reports did not supply these artifacts; this round did not exhaustively search every remote archive. If no representative outputs/exposure exist, leave deferred for later authorized capture.

Future authorized comparison: original full head; full vocabulary FP8(QH45); BF16 selected rows; only then a factorial combination if each earns it. Fix workloads and evaluate actual committed tokens per round, head/bias/scatter/cache durations, long-output ITL and separate TTFT/tails/goodput/memory guards. Standard Mooncake and agent75 are still the service objectives. Additional multilingual/code/rare-token correctness and stress probes are necessary because aggregate throughput does not reveal support-mapping bugs or domain-specific acceptance collapse. They are diagnostic cells, not a substituted benchmark objective.

## 7. Honest yield

Six recent hits, two recent fulltexts used (one newly fetched, one reused), one older cited fulltext fetched, five selected PR opening bodies, four pinned source files inspected. One component is retained as a deferred draft-head alternative; the direct dynamic policy and plug-in flag interpretation are not qualified. **Zero new formal hypothesis IDs, zero implementation promotions, zero GPU experiments and zero measured service wins.** Independent review is pending at author freeze. Full-text availability and source plausibility are progress in evidence, not a performance result.
