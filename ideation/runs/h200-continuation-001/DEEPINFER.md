# DeepInfer: released mechanisms, proposed PRs and local implications

The released source remains pinned at
`774ce244b87cc0eb8d4b94ab9f5de2ab22049f01`. This scan collected 95 PR opening
records and retained deeper pages/patches for 14. The
[disposition ledger](DEEPINFER_DISPOSITIONS.csv) distinguishes reviewed leads
from deferred openings. No DeepInfer model, extension or kernel was executed.

## Released mechanisms

The released engine implements confidence-scheduled variable verification,
asynchronous scheduling, shared sparse-indexer/attention metadata, fused compute
paths, expert load balancing and optional bounded replay. Its complete serving
stack is not included. Mainline NVIDIA support is SM100; the newer Hopper work
below is a proposed port, not a change in the pinned release's support boundary.
The prior [mechanism comparison](../deepinfer-comparison-001/REPORT.md) remains
useful, with the following source-level refinements.

The installed vLLM AV objective **already adds draft cost to verification cost**.
The useful question is whether its request-indexed draft-cost table represents
the actual draft graph selected after the target budget changes. DeepInfer's
controller additionally corrects its startup forward curve using recent runtime
observations and sampler time. Transferring that controller wholesale is not
justified; first measure the relevant total-cost mismatch and its decision impact.
The [synthetic CPU probe](av-cost-counterexample.json) demonstrates possible
decision sensitivity, not a local runtime or service gain.

## Changes worth separating

| Source | What it actually proposes | Implication for our program |
| --- | --- | --- |
| [#92 Hopper port](https://github.com/deepseek-ai/DeepInfer/pull/92) | Broad SM90 path with attention/indexer kernels, FP8 linears, native resident FP4 experts, Humming/fallback paths and vendor patches. Author reports H20 results. | Replaces the earlier belief that only a Hopper RFC exists. It is an expensive alternative-engine/port lane; isolate reusable mechanisms before considering full integration. |
| [#47](https://github.com/deepseek-ai/DeepInfer/pull/47), [#88](https://github.com/deepseek-ai/DeepInfer/pull/88), [#91](https://github.com/deepseek-ai/DeepInfer/pull/91), [#101](https://github.com/deepseek-ai/DeepInfer/pull/101) | RFC, throughput helper and FP4→FP8 conversion/loading pieces. | These are not independently complete Hopper support. The conversion lane changes weight representation and memory, unlike #92's resident-FP4 path. |
| [#54 host overhead](https://github.com/deepseek-ai/DeepInfer/pull/54) | Gate profiler scopes, pool timing events, reuse the sample-end event and avoid repeated structured-output/empty-output work. | Useful patterns; establish an equivalent active vLLM cost before proposing a port. Its headline saving is not a measurement on our service. |
| [#111 queue/output work](https://github.com/deepseek-ai/DeepInfer/pull/111) | Reduce waiting-queue scans, cancellation lookup and output conversion. | Reported fixtures involve very large queues. First establish queue-size distribution and exposed host time for seq64/EP4. |
| [#99 NVLink Engram](https://github.com/deepseek-ai/DeepInfer/pull/99) | An optional single-node Engram path without NCCL GIN, with extra collective work and scale storage. | Primarily compatibility. Current vLLM shared-host Engram is a different path; this is not automatically a faster replacement. |
| [#107 EPLB history](https://github.com/deepseek-ai/DeepInfer/pull/107) | Attribute historical counts to logical experts when recorded, preserving meaning across remaps. | A correctness prerequisite if adopting dynamic remapping; EPLB is off in our recorded baseline. Measure skew and memory tradeoffs before activation. |
| [#35 resource accounting](https://github.com/deepseek-ai/DeepInfer/pull/35), [#108 chunk sizing](https://github.com/deepseek-ai/DeepInfer/pull/108) | Repair KV capacity/reservations/reclamation and chunk-checkpoint/lookahead invariants. | Strong negative-control ideas for evaluator design. They do not prove matching bugs in installed vLLM. |
| [#100](https://github.com/deepseek-ai/DeepInfer/pull/100), [#102](https://github.com/deepseek-ai/DeepInfer/pull/102), [#112](https://github.com/deepseek-ai/DeepInfer/pull/112) | Reject mixed replay modes, invalid synthetic acceptance probabilities and configuration conflicts hidden by deduplication. | Keep evaluation configuration identity and real sampling explicit before comparing any engine frontier. |

## Transfer limits that matter

The H20 port's author-reported TTFT and random-token decode benchmarks do not
match our H200 arrival replay, profile or primary ITL cohort. Its stated GSM8K
procedure uses the first eight test questions as demonstrations while scoring all
1,319; that is not a clean held-out quality check for our proposed deployment.
The broad patch also changes many paths at once, so its aggregate result cannot
attribute a gain to one kernel. Preserve it as an engineering lead and qualify
individual components or a separately scoped matched engine control.

The [PR discussion](https://github.com/deepseek-ai/DeepInfer/pull/92#issuecomment-6297307116)
also states that the port will not be merged and can be maintained separately.
That increases the integration/maintenance burden; it is not a reason to treat
the proposed kernels as disproved. The retained
[visible discussion extracts](sources/visible-discussions.json) also record
merge-conflict notices on the vLLM sampler PR and implementation revisions on
the router PR. Opening-body summaries alone missed this information.

Likewise, the released DSpark Q&A's variable-verification results concern a
different topology/load and include an unfavorable low-concurrency point. They
support a workload-dependent cost model, not a universal AV win. Current C24
timing is instrumentation-inconclusive. Its descriptive target-occupied time
cannot be treated as removable verification time.

The most useful cross-repository lead for the existing baseline is an isolated
probabilistic DSpark sampler fusion from
[vLLM #61869](https://github.com/vllm-project/vllm/pull/61869). The upstream model
interface gates it behind `specialized_decode_requested`, and the sampler gates
exclude AV, top-k drafting and watermarks. A portable unsharded H200 path would
therefore be a deliberate port with its own sampling/logit-cache checks, not an
existing easy activation or evidence that a whole SM100 engine can run on H200.

See [extracted evidence](combined-evidence.json),
[updated C24 evidence](evidence-update/packet.json), and
[retained proposed patches](sources/primary-manifest.json). All quoted source
claims remain distinct from our measured results and transfer hypotheses.
