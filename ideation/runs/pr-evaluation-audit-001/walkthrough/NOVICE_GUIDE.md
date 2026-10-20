# Plain-language guide to the B200 experiment queue

This guide explains the **hypotheses** in the [experiment index](../EXPERIMENT_INDEX.md). It is a discussion aid, not a new experiment result or a change to the frozen plans. No GPU performance experiment from this audit has run. The order is an inspection order, not a predicted ranking by speedup. The configured source/image is historical evidence; the running server must be attested before any patch decision.

## A request's path

1. A request reaches a server and a data-parallel (DP) rank. The server checks whether it can reuse the beginning of the prompt from the KV cache.
2. **Prefill** processes prompt tokens that were not reused. During **decode**, DSpark proposes five possible next tokens and the target model verifies them. This cycle repeats until the response ends.
3. GPU workers coordinate DP and expert-parallel (EP) work. CUDA graphs replay captured GPU batch shapes when one matches. Engram tables may be read from host memory. Each part can introduce work, waiting, memory pressure or a correctness failure.

The audited latency profile uses eight B200 GPUs as two four-GPU replicas, each TP1/DP4/EP4, with DSpark k5 and adaptive verification off. The profile defaults to 64 maximum sequences per rank; the historical latency comparison uses a `lat-seqs-128` override. The profile's 512 graph value is a **token capture ceiling**, not 512 requests. Resolve the actual launcher arguments and occupancy before using any capacity arithmetic.

**Vocabulary:** KV cache = stored attention state; prefix hit = reuse of that state for a shared prompt beginning; CUDA graph = recorded GPU execution shape; eager = ordinary launches without a matching FULL graph; acceptance = number of proposed draft tokens the target keeps; TTFT = time to first token; TPOT = time per output token; qualified goodput = completed requests passing the run's service limits.

The plans' **E1 synthetic** and **E2 Mooncake** are the two existing *evaluation workloads*. Their names are separate from **E01/E02**, the proposed changes. Mooncake traffic replay does not imply an enabled Mooncake or other KV-offload connector.

## Each performance proposal

| Plan | Suspected unnecessary work or delay | First observation that decides whether to test |
|---|---|---|
| [E01](../experiments/E01.md) | Candidate selection spans a maximum-context buffer even for short live contexts. | The running indexer uses that selection path and it consumes meaningful decode time. [Detailed walkthrough](E01.md). |
| [E02](../experiments/E02.md) | Target graph padding enlarges DSpark's draft dispatch. | Real DP request count is below target graph capacity and draft rows grow from the latter with adaptive verification off. [Detailed walkthrough](E02.md). |
| [E03](../experiments/E03.md) | Occupied decode/draft shapes lack compatible FULL graphs. | Runtime dispatch logs show useful shapes falling back; test configuration coverage before code changes. [Detailed walkthrough](E03.md). |
| [E04](../experiments/E04.md) | Small CPU coordination messages delay the next GPU step. | DP metadata collective time is on the critical path of the actual single-node DP groups. |
| [E05](../experiments/E05.md) | First-use kernel compilation stalls the first real request. | A missing specialization compiles after readiness; measure startup cost and first-request TTFT separately. |
| [E06](../experiments/E06.md) | The selected top-k algorithm is slow for actual batch shapes. | Identify the current backend and find a qualifying shape where an alternative is faster and index-correct. |
| [E07](../experiments/E07.md) | The scheduler reserves target token budget for separate draft work. | At the existing 16K budget, admission is actually blocked while this reservation leaves capacity unused. |
| [E08](../experiments/E08.md) | Adjacent GPU operations repack activations or positions repeatedly. | The conversions occur on the deployed TP1 path and occupy material GPU time; preserve numerical behavior. |
| [E09](../experiments/E09.md) | Attention misses a useful B200-specific pipeline. | The exact head shape, precision, KV layout and prefill/decode leg match the proposed kernel. |
| [E10](../experiments/E10.md) | Host Engram storage causes avoidable lookup, registration or NUMA cost. | Identify the active shared/sharded backing branch and measure that branch; listed fixes target different branches. |
| [E11](../experiments/E11.md) | Draft-group or prefix bookkeeping loses reusable KV hits or exposes invalid draft context. | Observe a group-specific prefix loss or acceptance collapse after cache hits, then select the matching fix. |
| [E12](../experiments/E12.md) | Python scheduler bookkeeping repeatedly scans long cache tables. | Scheduler CPU spans show a bottleneck under your prompt lengths and request turnover. |
| [E13](../experiments/E13.md) | A rank's long prefill stalls other ranks' decode steps. | Cross-rank traces show prefill/decode skew on the critical path; compare coordination cost and TTFT tradeoff. |
| [E14](../experiments/E14.md) | Related requests reach different internal DP ranks and lose prefix locality. | Same-session requests scatter across final ranks despite endpoint routing, causing measurable cache misses. |
| [E15](../experiments/E15.md) | Separate Engram/mHC operations add launches and memory traffic. | The TP1 shape is eligible and a fused implementation passes numerical checks before serving A/B. |
| [E16](../experiments/E16.md) | Recomputing evicted KV might cost more than fetching it from another tier. | An explicitly enabled offload connector has enough useful hits to repay transfer and storage cost. |
| [E17](../experiments/E17.md) | Very long context degrades drafter acceptance. | Acceptance falls with context after ruling out prefix restoration and workload effects. Adaptive-policy work waits while that feature is off. |
| [E18](../experiments/E18.md) | Another precision, layout, kernel or topology could yield a better serving point. | One compatible route shows a plausible benefit with quality, KV capacity and dependency costs accounted for. |

## The five correctness gates

These are scoped checks, not throughput predictions.

| Gate | Failure to rule out |
|---|---|
| [G01](../experiments/G01.md) | DSpark block verification reuses random draws and biases the output distribution. |
| [G02](../experiments/G02.md) | Graph dispatch, sliding-window cache or sparse indices read stale/invalid data and silently corrupt output. |
| [G03](../experiments/G03.md) | Persistent GPU kernels reuse synchronization state across graph replays and return wrong results or hang. |
| [G04](../experiments/G04.md) | Tool-turn tokenization or parsing changes prompt meaning and cache keys; a throughput comparison then measures different work. |
| [G05](../experiments/G05.md) | DP workers hang after idle, or restart uses wrong cached draft compilation state. |

## How to use the queue

For each idea, ask in order: **Does the running image contain the alleged old behavior? Does the relevant workload activate it? Is the wasted work large enough to matter? Can the proposed change preserve correctness? Does it improve completed requests under the same service contract?** A failed applicability check means *not applicable*, not a failed optimization. A faster kernel without a serving gain remains a kernel result.

Start with a short mechanism diagnostic, then compare an unchanged control and one treatment with identical model, topology, requests, arrival pattern, cache preparation and numerical mode unless the idea intentionally changes one of those. Use the existing synthetic and Mooncake evaluations for request-level latency, failure rates and SLO-qualified goodput. Keep profiling separate from scored runs; confirm promising changes on held-out traffic. See the [common protocol](../PROTOCOL.md) for replication, thresholds and raw-artifact requirements.
