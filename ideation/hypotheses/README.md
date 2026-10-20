# Hypothesis register

Start here for the hypothesis, where it came from, what was tested, the result, and the detailed logs. **Plain Markdown: one record per family, one history row per execution.** Updated 2026-10-21 (Asia/Calcutta).

Current coverage: **36 records** (the original 33 consolidated families plus C24 adaptive verification, C25 sampler fusion and C26 router eligibility; 26 performance ideas, 6 held/different-scope ideas, 4 correctness prerequisites), **66 original audit cards**, and **56 saved builder/review proposal instances across 22 batches**. Raw proposals and revisions are not counted as unique mechanisms. C03 has a complete local execution record; C01 has an external grouped-arm result notice from node 219 without raw artifacts here. C24 has a completed baseline timing diagnostic with an instrumentation-inconclusive verdict. C24 also has CPU cost/dispatch work and bounded instrument probes; C25 has a positive exact sampler-component result with native integration pending; C26 is inapplicable to the frozen BF16-weight baseline. None establishes a new service gain.

[Execution / analysis / meta-learning](../records/README.md) · [How to maintain this](WORKFLOW.md) · [New record template](TEMPLATE.md) · [All builder generations / research inputs](GENERATIONS.md) · [Original card → family mapping](SOURCE_MAP.md)

| ID | Hypothesis / sources / detailed record | Current status | Key local result |
| --- | --- | --- | --- |
| C01 | [Humming: backend first, then indexed versus grouped](C01.md) | Grouped arm on hold; indexed untested | Poor grouped result reported on node 219; raw results unavailable here |
| C02 | [Share compatible FlashMLA planning metadata](C02.md) | Proposed; untested | No execution linked |
| C03 | [Use logical requests rather than target padding for drafting](C03.md) | Screen deferred; no promotion | ITL +1.85%, TTFT p99 +7.83%, E2E p99 −5.33%; [report](../runs/c03-execution-001/REPORT.md) |
| C04 | [Reduce CPU DP metadata synchronization overhead](C04.md) | Proposed; untested | No execution linked |
| C05 | [Tune SM90 mHC for actual one-to-eight-row launches](C05.md) | Proposed; untested | No execution linked |
| C06 | [Repair demonstrated prefix-cache/draft interactions](C06.md) | Proposed; untested | No execution linked |
| C07 | [Remove repeated scheduler cache work](C07.md) | Proposed; untested | No execution linked |
| C08 | [Hopper selector integration and length-aware block selection](C08.md) | Proposed; untested | No execution linked |
| C09 | [Candidate-only long-context decode scoring](C09.md) | Proposed; untested | No execution linked |
| C10 | [Preserve cache affinity at the final DP rank](C10.md) | Proposed; untested | No execution linked |
| C11 | [Bound coordinated DP prefill release](C11.md) | Proposed; untested | No execution linked |
| C12 | [Contiguous prefill MQA epilogue](C12.md) | Proposed; untested | No execution linked |
| C13 | [Per-token FP8 Humming activation](C13.md) | Proposed; untested | No execution linked |
| C14 | [Fuse top-k with physical KV-slot mapping](C14.md) | Proposed; untested | No execution linked |
| C15 | [Shared Engram placement and exposed lookup cost](C15.md) | Proposed; untested | No execution linked |
| C16 | [Scheduler budget reserved for separate drafts](C16.md) | Proposed; untested | No execution linked |
| C17 | [Unreachable draft graph buckets](C17.md) | Proposed; untested | No execution linked |
| C18 | [Bound drafter context if long-context acceptance collapses](C18.md) | Proposed; untested | No execution linked |
| C19 | [Native MXFP4 SM90 fused expert backend](C19.md) | Proposed; untested | No execution linked |
| C20 | [DeepEP activation, then triple-buffer dispatch](C20.md) | Proposed; untested | No execution linked |
| C21 | [SM90 mHC coefficient overlap](C21.md) | Proposed; untested | No execution linked |
| C22 | [KV offload as a separate capacity configuration](C22.md) | Proposed; untested | No execution linked |
| C23 | [Matched SGLang control](C23.md) | Proposed; untested | No execution linked |
| C24 | [Adaptive target verification at existing k5](C24.md) | Timing diagnostic inconclusive | 986/986 successes; timing coverage/association gate failed. AV unqualified; [report](../runs/av-k5-timing-001/REPORT.md) |
| C25 | [Isolated unsharded DSpark sampler fusion](C25.md) | Positive component; native pilot planned | Exact parity; 25–40% component gain across eight shapes; service benefit unknown |
| C26 | [Conditional SM90 FP32-weight router kernel](C26.md) | Inapplicable to frozen baseline | All43 weights BF16; installed load/dispatch confirms excluded FP32 branch; no GPU run |
| D01 | [Private Engram exact allocation: inactive](D01.md) | Research hold; untested | No execution linked |
| D02 | [TP4 Marlin alignment alternative](D02.md) | Research hold; untested | No execution linked |
| D03 | [Small-head sparse attention alternative](D03.md) | Research hold; untested | No execution linked |
| D04 | [TP-sharded fused prefill projection](D04.md) | Research hold; untested | No execution linked |
| D05 | [Blackwell MegaMoE warmup and activation repacking](D05.md) | Research hold; untested | No execution linked |
| D06 | [B200 FlashMLA pipeline and Engram/mHC fusion](D06.md) | Research hold; untested | No execution linked |
| Q01 | [Sampling distribution qualification](Q01.md) | Correctness prerequisite; untested | No execution linked |
| Q02 | [Index/graph bounds and mHC lifetime qualification](Q02.md) | Correctness prerequisite; untested | No execution linked |
| Q03 | [API2 liveness and restart identity](Q03.md) | Correctness prerequisite; untested | No execution linked |
| Q04 | [Tool encoding, parser and changed-math quality](Q04.md) | Correctness prerequisite; untested | No execution linked |

Each record links the original builder/review identity, PR/issue/paper citations, saved research evidence when available, and original audit design. C03 additionally links implementation, evaluator, scores/raw exports, full logs, triage, independent review and environment cleanup. The original register consolidated retained snapshots. C24–C26 now also link the [deeper continuation scan](../runs/h200-continuation-001/REPORT.md), new primary-source evidence and explicit research/cheap-check outcomes.

An upstream result is not a local measurement. Research selection scores are not speedups. Completed but SLO-ineligible runs remain complete; failed and inconclusive attempts stay linked. The original audit cards and sealed experiment artifacts are preserved.
