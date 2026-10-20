# Why C03 did not earn another run

**C03 fixed a real padding inefficiency, but we never established that it was an expensive bottleneck on this workload.** The implementation changed the intended graph selection. The complete service screen did not improve. The exact cause of the observed latency regression remains unmeasured.

This is a read-only explanation using retained evidence, dated 2026-10-21 (Asia/Calcutta). No new service, profiler, benchmark or correctness experiment ran. The [original result](../c03-execution-001/REPORT.md) and its sealed verdict remain unchanged. The independent evaluator recounted the saved histograms; [ACCOUNTING.json](ACCOUNTING.json) preserves counts, denominators and input hashes.

## The concrete mechanism

The target model checks proposed tokens. The drafter proposes the next block. CUDA graphs use a finite set of captured shapes, so a live batch can be padded to a larger capacity. The old code passed the target's padded request capacity into draft sizing. The draft graph then padded it again.

This is the actual common affected case in the B diagnostic:

| Quantity | Original rule | C03 |
| --- | ---: | ---: |
| Maximum logical requests across the four ranks | 5 | 5 |
| Target graph request capacity | 6 | 6 |
| Request count passed to draft sizing | 6 | 5 |
| Draft query rows requested, at width 5 | 30 | 25 |
| Selected draft graph rows | 35 | 25 |

The patch separates logical requests from target capacity and keeps dummy-rank input/metadata extents coherent. The target graph, speculative width, sampler and verifier are preserved. It does not stop verifying low-value draft positions, make real tokens cheaper, or remove target-model prefill work. See the [actual patch](/home/ubuntu/Deepseek_serve-c03/c03/candidate.patch).

## How much of the run benefited

| Diagnostic observation | Count | What it means |
| --- | ---: | --- |
| Unique online replica/step events | 30,832 | Warmup plus profiling, startup excluded; ranks are not summed as independent events |
| Supported uniform FULL-target events | 29,277 | Denominator for the graph-capacity calculation below |
| Events selecting a smaller draft graph | 1,941 | **6.30% of all recorded online events** |
| Common reduction: 35 → 25 draft rows | 1,848 | 28.57% fewer rows for this affected launch only |
| Other reduction: 75 → 65 draft rows | 93 | A smaller reduction for another boundary shape |
| Target padding existed, but draft bucket did not change | 431 | Removing logical padding does not always change executed graph capacity |
| Other supported FULL events with unchanged draft bucket | 26,905 | No graph-capacity saving from this mechanism |
| Eager/piecewise-target events outside this accounting | 1,555 | Not reader failures; actual unsupported-failure count is zero |

Applying the old padding rule to the **same B shapes** gives 502,000 supported FULL draft rows. The candidate selected 482,590: **19,410 fewer, or 3.87%**. This is descriptor-capacity accounting, not an A/B GPU-time comparison. It excludes target work and the 1,555 other events. All four ranks participate; multiplying both row totals by four would leave the percentage unchanged.

The separate strict-profiling receipt establishes 1,350 smaller-graph opportunities inside profiling. It does not convert the warmup-inclusive histogram totals into exact profiling-only time weights.

## Where the performance argument was incomplete

The full claim needed four links:

1. The installed code unnecessarily inflates draft graph size. **Established.**
2. The change selects a smaller graph on real workload events without violating the scoped checks. **Established.**
3. Those smaller graphs save a material amount of exposed time per step. **Not measured.**
4. That saving improves the service objective under actual arrivals. **Not demonstrated; the fixed screen was unfavorable.**

The activation floor proved enough events to observe the mechanism; it was not an ROI test. We advanced without measuring the time contribution that would connect row savings to a plausible service gain. That is the selection weakness to correct before spending another attempt.

Rows are not milliseconds. The pinned Marlin expert path chooses blocks from 8/16/32/48/64 rows, and routing then pads each expert to its block size. Removing some draft rows can therefore leave expert block counts unchanged. The all-gather payload can shrink, but collective count and five sequential draft sampling rounds remain fixed. These source-level effects explain why proportional savings cannot be assumed; they were not measured as the cause of this result. Source: [pinned Marlin expert implementation](https://github.com/vllm-project/vllm/blob/ac9126e58aa7bbab1856ba6593ba4d5003fea516/vllm/model_executor/layers/fused_moe/experts/marlin_moe.py), [expert row alignment](https://github.com/vllm-project/vllm/blob/ac9126e58aa7bbab1856ba6593ba4d5003fea516/vllm/model_executor/layers/fused_moe/moe_align_block_size.py). Kernel tiling, weight traffic, collectives, overlap and synchronization can make graph runtime nonlinear in row count. Most service work was unchanged. As an illustration only, if precisely this draft component consumed 20% of step time and its runtime scaled linearly with rows, a 3.87% reduction there would save roughly 0.77% of total step time. **Neither the 20% share nor linear scaling was measured.** This is not a speedup estimate or bound.

The candidate's one AB screen measured ITL +1.85%, TTFT p99 +7.83% and E2E p99 −5.33%. That is sufficient to stop under the frozen rule. It does not explain the regression: realized cache counts differed, warmup completed 52 versus 53 requests, and acceptance/scheduling varied. Some differences may themselves result from the change. We cannot choose one as the cause, declare them external noise, or dismiss the valid screen. See [paired context](../c03-execution-001/SCREEN_PAIR_CONTEXT.md).

## Consequence for the remaining two attempts

The next candidate needs an observed expensive operation, a concrete way to remove or shorten it, and a same-shape component measurement showing that the saving can matter after overhead. A PR, another engine's implementation, or a reviewer score cannot supply that evidence. A short baseline profile is diagnostic preparation; it must be budgeted explicitly and kept separate from unprofiled service results.

DeepInfer is useful source evidence, but its released NVIDIA engine targets SM100 and does not provide a drop-in H200 service. Its confidence-budgeted verification is relevant because it can trim **target verification** work; that is a broader cost than C03's occasional draft padding. Our pinned vLLM already contains an adaptive-verification manager, so an engine port is not required to investigate this mechanism. It remains a conditional lead, not a measured high-ROI choice. Verify cost-table calibration, confidence handling, variable-length graph/backend support, sampling correctness and runtime overhead before assigning a service attempt. A high rejection fraction alone does not establish the best draft budget.

The cheap C02 planner-sharing port is also not automatically a good use of the remaining budget: its upstream higher-concurrency result was about 0.6% lower ITL on H20 with synthetic acceptance, not a demonstrated ≥2% win on our workload. Humming's grouped result is reported poor on node 219; the user confirmed that location, but its raw results are not present here. Treat it as external caution, not a matched measurement on this node.

Sources inspected for the selection discussion: [DeepInfer README](https://github.com/deepseek-ai/DeepInfer), [pinned budget controller](https://github.com/deepseek-ai/DeepInfer/blob/774ce244b87cc0eb8d4b94ab9f5de2ab22049f01/csrc/engine/mtp_varlen.hpp), [local comparison](../../../../AutoResearch-Inference/ideation/runs/deepinfer-comparison-001/REPORT.md), [vLLM adaptive-verification explanation](https://github.com/vllm-project/vllm-project.github.io/blob/main/_posts/2026-08-14-dspark-adaptive-verification.md), [C02 upstream test](https://github.com/vllm-project/vllm/pull/58818). The local comparison's C01 failure-audit link is unavailable on this node.

The next full experiment is **not selected for execution by this note**. The leading mechanism to qualify is adaptive verification at the existing k5; choosing another winner from the catalog before measuring its cost would repeat the same mistake.
