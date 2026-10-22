# Guided discovery — checkpoint 2

22 October 2026. **The loop remains active; no GPU work, serving change, model launch or training. No measured performance improvement.**

## What changed the next action

The strongest new source-specific lead is **AT03: reuse the gathered compressed-KV representation across source20's prefill consumers**. The pinned code already shares the stored source cache, but both inspected NVIDIA prefill backends reconstruct its BF16 representation repeatedly. That is a concrete additional operation to remove, rather than a new name for existing CED cache sharing.

The first lifetime design was too complicated and its fixture supplied an invalidation oracle. Delegated review found that source20 is also the decoder-replay entry. We revised the proposal: **fill a dedicated buffer unconditionally at source20 on every invocation, then reuse its compressed prefix only within that execution group.** Each consumer still gathers its own SWA tail and computes its original attention. Nothing is memoized across separate forwards.

The original fixture and proposal are preserved. The revision is a hypothesis, not a serving patch.

## Shortlist and metric relevance

| Direction | Evidence for a missing operation/choice | Next question | Metric pathway |
|---|---|---|---|
| **AT03 source20 materialization reuse** | Source20 supplies layers20–39; both FlashMLA and Mega prefill gather the shared compressed cache repeatedly | Exact chunk layout, write ownership, replay ordering and bounded persistent allocation | Prefill work/TTFT; possible interference reduction is unmeasured |
| **M01 distribution-informed MegaMoE tiles** | Current default tile heuristic ignores actual per-layer physical expert distribution | Best fixed layer/bucket tile, coupled scale-packing/kernel configuration and retained workload evidence | Decode/ITL and throughput, if the chosen tactic is actually faster |
| **S01 exact rendered-prefix tokenization repair** | Custom V4.1 frontend re-encodes rendered prompts | Certify the actual tokenizer/renderer; preserve rewritten suffixes and session isolation | Frontend CPU time/TTFT |
| **AT01 certified indexer head screening** | All index heads are evaluated in the inspected consumer scoring path | Conservative MXFP4/BF16 numerical certificate and useful survivor rate within the existing domain | Prefill/TTFT; direct decode benefit is unestablished |

This is a priority order for further information gathering, not a prediction of gains. If the objective is restricted to long-output ITL, M01 is more direct than the prefill directions. Neither a paper's speedup nor a constructed work-count saving establishes service ROI.

## AT03: precise opportunity and limits

At8192 positions, head dimension512 and BF16, the compressed representation is8MiB/request. A complete initial prefill's combined compressed-plus-SWA buffer is approximately16MiB/request before alignment and metadata. Actual chunked/replay shapes differ. Dedicated storage can increase peak HBM because other operations still use the shared scratch allocation.

Under an eligible identical-plan group, nineteen of twenty compressed materializations could be omitted. **That is a call-count upper bound, not a95% attention or latency improvement.** All SWA gathers, attention reads, source writes, projections and model work remain. A future performance comparison must charge extra memory and any fallback/validation overhead.

The original83-case fixture assumed supplied epoch/source-version signals and therefore could not establish runtime invalidation. The replacement239 comparisons exercise a Python source-entry protocol, including same-address content changes and fallbacks. These are symbolic comparisons. Separately, five branches of the actual AST-extracted `DecoderReplayLayers` wrapper were exercised with CPU callbacks; they enter the whole callback, whose20–39 layer range was inspected separately. This does not execute the model, CUDA graphs or GPU memory operations.

The follow-up used the actual chunk-plan method and gather/index write bounds. Source20's special replay SWA geometry is compatible for the inspected same-kept-batch path: for an8K sequence trimmed to128 query rows, source20 gathers255 SWA positions and consumers128, but both use prefix offset8192 and total width8447. Fresh per-layer indices exclude the leftover tail. This resolves that geometry objection; it does not execute a GPU kernel. Source writes inside the group invalidate the proposal, and persistent storage must preserve contiguous current row strides. See [round4 source review](round4/REPORT.md).

### PR triangulation changed the evidence

A fresh retained-corpus query, `compressed prefill reuse`, found **[SGLang PR #40421](https://github.com/sgl-project/sglang/pull/40421)**: the same reconstruction-reuse mechanism, with author-reported V4.1 Flash/8×B200 tests. Its scope is disaggregated context-parallel prefill and a64K-input workload, so its reported reductions cannot forecast our8K or aggregated deployment. The public PR remains open and displays failed CI checks; the current diff, dependencies and failure causes received delegated audit ([details](round4/PR40421_REVIEW.md)). This is a donor to investigate, not a validated transplant. It is the same AT03 direction and adds nothing to the yield denominator.

The current-head audit found an important qualification: `be9259983a47ecbe8d0dea073f24f4c12087d573` gates the inspected CP sparse-prefill entry on SM90 and disables it with Mega attention, while the PR body describes B200 measurements. That revision/path discrepancy is unresolved. Its focused GPU fixture mocks dequantization and attention, so it tests buffer/control behavior rather than the real kernels. These findings prevent treating the donor's headline as target evidence; they do not negate the repeated-gather observation independently found in our pinned vLLM.

The four local searches and matching opening records are retained in `round4-source20/pr-triangulation.json`. They used the existing `Store.search` implementation through a read-only connection while the publisher held the writer lock; no CLI command or additional API request is invented. Earlier source/prior checks did not substitute for this mechanism-specific PR search.

## Recent papers: selective reuse and rejection

- **[DoSA](https://arxiv.org/html/2610.13990v1):** retain the signed-head screening certificate; preserve the exact existing candidate domain and full original scoring of survivors. Its public FP8/TopK2048/131K-key path does not directly match MXFP4/BF16/TopK512. Actual target consumer compression ratio is1: an8K prompt can expose up to8192 positions. The author's131K guard does not prove zero8K opportunity. Numerical correctness and net work remain unresolved.
- **[PageWeaver](https://arxiv.org/html/2610.11201v1):** retain the idea of execution regrouping without changing attention support, but defer a port. Its grouping regresses at8K and its Blackwell comparisons do not establish a win over the best native order. Turning selected token IDs into whole pages would change support.
- **Herschel synchronization:** the inspected DSpark V2 runner already reuses target DP state for drafting. Reject the missing-feature premise. The remaining first-target synchronization is a different dependency problem.
- **Unfinished-prefill draft removal:** revise the initial blanket rejection, then defer implementation. Context-KV preparation and lagged parent-conditioned confidence are live dependencies; discarded draft token IDs do not imply that the whole query path is dead.
- **Expert-affinity regrouping:** moving requests within the same DP4/EP4 group in the same round preserves that group's expert union. Cross-group or temporal changes require an available signal and a separate routing/cache tradeoff.

## Yield without counting revisions as new ideas

| Cohort | Unique directions | Outcome at this checkpoint |
|---|---:|---|
| Frozen round1 | 11 | 2 accepted bounded CPU plans;1 duplicate;3 rejected direct applications;5 deferred/revise-deferred |
| Round2 runtime/MoE | 6 | 1 rejected;5 deferred; original and revised unfinished-prefill idea counted once |
| Round3 attention | 3 | 3 implementation-deferred; AT01/AT03 continue as recommended CPU/source investigations |
| **Total** | **20** | **2 formally accepted CPU plans;13 deferred;4 rejected;1 duplicate;0 service-qualified improvements** |

Round3 used three online OpenAlex tool calls,26 raw hits and22 distinct paper labels. Exact requests, receipts and the worker command journal are retained. The adaptive plan was written retrospectively; no unexecuted query-expansion command is claimed. Paper mirrors, repeated revisions and extra tests do not increase discovery yield.

## Tool/skill lesson verified on this case

The critic skill now explicitly checks whether a CPU fixture is given runtime facts that the implementation does not provide. That review found the missing generation signal, exposed the replay entry, and changed AT03's proposed design. The discovery skill now calls for renewed PR searches when code inspection reveals a more specific operation to remove; this step found the donor above. These are observed cases, **not a controlled claim of general skill improvement**. Both skill format validators passed; the prior research-code baseline had248 passing tests. No research application code was changed in this continuation.

## Retention and continuation

Round1 is in canonical memory and has a verified S3 publication receipt: [publication-checkpoint1.json](publication-checkpoint1.json). Later cohorts require their own import/publication readback; see [STATE.md](STATE.md). S3 publication does not prove VM restore.

Worker material is retained externally under `~/.local/share/autoresearch-reviews/guided-discovery-20261022-001/`. Compact round2/round3 reports accompany this checkpoint; relative references inside copied worker reports refer to their retained workspace. Live source20 geometry work continues in a new round4 folder so frozen import inputs cannot drift.
