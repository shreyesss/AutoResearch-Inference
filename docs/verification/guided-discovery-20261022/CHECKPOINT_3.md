# Guided discovery — checkpoint3

22 October2026. Active CPU/source-only loop. **No GPU work, runtime patch or measured inference improvement.** This checkpoint extends, rather than overwrites, earlier decisions.

## What the latest review changed

**RD01: physical MegaMoE weight localization** is a new, decode-oriented candidate. The dependency already contains domain-aware scheduling, so that is not the proposed delta. Pinned vLLM allocates ordinary weight tensors; the proposal is to place completed weight slices in the physical memory domains used by the existing schedule.

A naive parameter replacement breaks expert-leading layouts. Independent review found a narrower adapter: expose every contiguous domain slice as an expert-weight component to the existing EPLB interface. Subsequent source tracing found that the ordinary model post-load hook runs twice. The proposed finalization boundary is after the loader returns and before drafter/EPLB views and registrations are captured. Existing reload needs an adapter or an explicitly scoped early refusal. This is a feasible design direction with unresolved environment and runtime gates, not an instruction to flip a switch.

**AT03: source20 reconstructed-KV reuse** now has an external-reader audit at the default pinned FlashMLA source. Selected kernels read BF16 KV and write separate output. The existing index wrapper clears all padding to-1 each layer; this must remain because valid padded indices into NaN data can contaminate output. WorkspaceManager isolates ubatches/lanes but not arbitrary streams, and new resources cannot be allocated after capture lock. A bounded, prewarmed, single-chunk resource with fallback is the current design.

## Priority by objective

| Direction | Why still worth investigating | Missing decisive evidence | Metric relevance |
|---|---|---|---|
| **RD01 physical weight localization** | Actual absent allocation step and plausible small EPLB adapter | MLOPart/B200 eligibility, useful physical affinity, memory and numerical/registration behavior | Decode ITL/TPOT if expert weight access is exposed |
| **M01 distribution-informed MegaMoE tiles** | Current default heuristic omits actual per-expert distribution | Retained target distribution and coupled scale/kernel tactic behavior | Decode/verify cost and throughput |
| **AT03 compressed materialization reuse** | Repeated reconstruction of the same within-forward source cache | Bounded resource implementation, graph/lane correctness and exposed gather cost | Prefill TTFT; mixed-load ITL benefit unmeasured |
| **AT01 certified indexer screening** | Selectively skip provably irrelevant score work | Conservative target numerical certificate and useful survivor rate | Primarily prefill; no decode forecast |
| **S01 exact rendered-prefix repair** | Repeated frontend tokenization | Exact tokenizer/renderer repair correctness and CPU exposure | Frontend TTFT |

The rows rank the next evidence-gathering effort; none promises a gain. RD02 host dispatch caching remains lower priority: graph replay may remove the Python overhead entirely. H200 support is not established for RD01's audited Blackwell MXFP4 path.

## Cheap checks and what they prove

- RD01's102 byte-layout mappings reconstruct expert payloads/scales; five negative controls catch missing components, unsafe swaps, stale views and truncated mixed-schema copies. This is a CPU representation test, not PyTorch/CUDA/NIXL validation.
- AT03 executed selected WorkspaceManager Python methods with object factories: slot isolation and lock behavior pass. This does not validate GPU stream races or graph pointers.
- RD01's estimated1.13GB largest temporary payload and AT03's illustrative544.5MiB worst-bound buffer per slot are allocation arithmetic, not observed peaks. Neither is free memory or a gain estimate.
- Existing Mooncake and agent-75 replays remain the eventual service comparisons. Add mechanism instrumentation and exact correctness checks; no new workload is justified merely because a kernel is changed.

## Yield, with an honest denominator

Through round5: **22 unique directions:2 accepted bounded CPU plans,15 deferred,4 rejected,1 duplicate;0 service-qualified improvements.** Round4/6 refine AT03 and round7 refines RD01, so they do not inflate the count. Round5's19 screening entries are source/lead dispositions, not19 hypotheses. Round8 evaluated research/evaluator components and adds zero serving hypotheses.

Round5 ran2 online paper queries and inspected original code/PRs. Round8 ran1 additional bounded OpenAlex query:8 results,2 selected full texts,2 failed citation expansions. Its selected components inform cost/state and workload checks; they do not produce a measured deployment win. Root web discovery was separate and is documented separately.

## Tools improved from observed failures

Restored hypothesis artifact references now resolve with hash verification and immutable retry identity. Local missing-source/revision errors now explain coverage and recovery in CLI/MCP without implicit network fetch. **258 research tests and bootstrap dry-run passed.** See [tool evidence](TOOL_IMPROVEMENTS.md).

## Artifacts and ongoing work

- [Round5 candidates and rationale](round5/REPORT.md)
- [AT03 external readers and workspace](round6-reader-contract/REPORT.md)
- [RD01 load/rebalance/ownership design](round7-localization-lifecycle/REPORT.md)
- [Recent evaluator literature and limitations](round8-modeling/REPORT.md)
- [Verified persistence state](STATE.md)

Source pins are not live-binary attestations. Canonical imports, S3 publication and VM restore are reported independently. Research continues into exact Engram paths and recent mechanism-specific evidence; no GPU experiments are authorized.
