# Round69 — runtime role reassignment in fused MoE execution

**Outcome: one retained N03-family refinement, zero new hypothesis identities, no implementation promotion.** The recent mKernel paper supplies a more specific control mechanism than the original launch-time N03 selector: measure progress and task costs, then change compute/communication roles at task boundaries within an invocation. The selected released donor MoE implementations do not establish this controller's implementation, and pinned target MegaMoE does not expose a compatible scalar role-switch knob. Retain the component and its precise integration boundary; do not substitute donor headline gains for target ITL evidence.

Source plan: `DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`, `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, `vllm-project/DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`, planned B200 TP1/DP4/EP4. This is not a live backend, graph, route histogram or timing attestation. No GPU/native/model import, build, serving operation, canonical write, cloud action or Git mutation occurred.

## 1. Adaptive retrieval and coverage

Before retrieval, read the complete **145-card compact inventory** over two pages with a matching inventory hash. Also searched standalone canonical reports for compiler, persistent execution, specialization, register/instruction work, combine, reduction and synchronization; these are bounded lexical searches, not semantic coverage certification. Read round53 compiler/rollback and round55 overlap reports in depth. Later read the full original N03 card and round52's dedup/ready-source findings when PR vocabulary led back there. The original N03 card/baseline/status remains unchanged; new Flash1017 source observations are an applicability refinement, not a rewrite of its older Flash profile.

- Query1: September1 inclusive–October23 exclusive, GPU/CUDA + inference/MoE + compiler/warp-specialization/persistent/register terms. Twelve abstracts returned. Several were astrophysics/neurosymbolic uses of “inference”; this domain noise motivated a new query rather than a hidden provider relaxation.
- Query2: same dates, explicit LLM/language-model/MoE anchor plus instruction-cache/warp-specialization/register/control terms. Two abstracts returned: deterministic arithmetic and Linux scheduler control. Neither supplied a new immediate target GPU component. Existing source-library lookup showed the arithmetic paper already appeared in earlier campaign screens.
- Selected [mKernel2609.13585v1](https://arxiv.org/html/2609.13585v1) from query1. Exact retained-library lookup found no mKernel copy before the fulltext fetch. Read the mechanism, comparator limitations and adaptive evaluation sections, especially3.2,5.3,5.5. One version-pinned fulltext request succeeded.
- The paper linked `uccl-project/mKernel`. Explicit public GitHub commit/tree requests pinned the current inspected source to `ef6225fdde493f4119f519c99bfa4ad9234e323b`; this is a retrieved implementation revision, not a claim it matches every paper experiment. Two code-only `investigate` calls retained six files: README, three API headers and two actual dispatch kernel bodies. No code ran.
- Seven bounded read-only PR searches changed vocabulary from dynamic SM allocation to warp roles, MegaMoE and controllers. Most hits were unrelated host/PD control or other kernels. Three opening records were selected through production `import-corpus`, then `pr-search` replayed that isolated subset. This is not a second full-corpus scan or new PR refresh. No donor PR diff or CI was newly verified here.

**Denominators:** two successful online paper queries,14 hits/14 identities,14 abstract screens, one selectively read fulltext, six donor files, three retained PR opening records, four component dispositions. Zero new formal cards or native experiments. All rejected/off-topic entries remain in `paper-dispositions.json` and `screens.json`.

## 2. Useful component: progress-sensitive changes within an invocation

mKernel §3.2 describes blocks checking a shared communication-block target between compute or communication tasks. An on-GPU controller estimates per-task costs from cycle counters and remaining work. Its target is proportional to remaining communication work times estimated communication cost, divided by the sum of remaining compute and communication costs. When communication supplies inputs, a waiting compute block may temporarily help communication.

This component does not require changing neural weights or adopting the paper's host proxy/network transport. It is narrower than “replace MegaMoE with mKernel,” and a potential refinement of N03:

| Existing proposal | Additional component here |
|---|---|
| N03 chooses a legal launch-time SM/CTA allocation from routing volume | Revisit allocation during an invocation using measured progress and remaining tasks |
| M01 selects GEMM tiles at fixed resource allocation | No proposed tile selection or weight/scale-layout change |
| RD01/WP38 localize or packetize weights | No proposed weight relocation or packing |
| A52-02 starts work before all source ranks are ready | This component changes resources after execution begins; it does not itself remove the target's all-rank admission dependency |

The paper's experiments cannot predict our service benefit. Its adaptive sweep is single-node H100; the illustrated MoE run has128K total tokens. Its two-node H200/EFA dispatch headline explicitly includes benefits from expert computation organization because the unfused comparator does not group expert GEMMs. These are different controls and regimes. The paper's reported adaptive improvement over its measured static configurations is neither a c455/B200 result nor a long-output ITL result.

## 3. Released source narrows the transfer

[Inspected donor Blackwell kernel](https://github.com/uccl-project/mKernel/blob/ef6225fdde493f4119f519c99bfa4ad9234e323b/src/dispatch_gemm_blackwell.cu)336–355 divides CTAs by `blockIdx.x < G.num_dispatch_sms`. Dispatch walks slices with that fixed stride; other CTAs run GEMM with fixed `num_gemm_sms`. The corresponding header requires BF16 activations and BF16 `[E,H,I]` weights, positive dispatch/GEMM counts and a sum within the device's SM count. Reading this source does not invoke its hardware checks.

The selected ordinary [dispatch kernel](https://github.com/uccl-project/mKernel/blob/ef6225fdde493f4119f519c99bfa4ad9234e323b/src/dispatch_gemm.cu)453–480 likewise uses fixed send/copy/dispatch/compute ranges. It includes useful phase ordering and cleanup but does not exhibit the paper's measured-cost controller in that inspected body. We did not search every branch/file/release and do **not** claim repository-wide absence. A controller implementation and exact task-claim protocol remain unresolved evidence requirements.

A direct Blackwell donor port would also replace the target's quantized two-layer routed/shared pipeline with a different BF16 dispatch/GEMM boundary. That is not a mere allocation change. Changed arithmetic is not automatically forbidden, but this task has not authorized an unscoped new precision/model comparison. The inference-only controller principle remains worth retaining without silently adopting the whole package.

## 4. Exact target: roles are coupled inside CTAs

The actual target [MegaMoE implementation](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/impls/sm100_fp8_fp4_mega_moe.cuh) uses dispatch, activation/scale producer, weight producer, MMA, scheduler and epilogue warp roles within each CTA. Key source constraints:

- Compile-time dispatch/non-epilogue/epilogue thread counts determine shared storage, barriers and register budgets. The register configuration around332–338 gives distinct budgets and statically limits the total. A whole CTA is not simply an interchangeable compute or communication worker.
- The heuristic requires the full configured GPU because work is distributed across locality domains. Reducing the launched grid to reserve a new controller is not an existing supported switch.
- Dispatch and epilogue synchronize with explicit `kNumDispatchThreads + kNumEpilogueThreads` participant counts before overlapping phases and again before cleanup. Epilogue completion also participates in a grid synchronization over `kNumSMs` before publishing remote combine readiness.
- Separate producer/MMA/epilogue roles consume scheduler tasks and ring generations. The activation producer waits for the expected token-arrival count; later work depends on L2 readiness and ring reclamation. Taking a worker away at a “tile boundary” must preserve all these consumers and their phase progress, not merely decrement a count.
- **Phase reuse already exists:** epilogue warps perform token combine after their GEMM work. “Use idle epilogue resources for combine” is not a newly absent optimization.

These facts reject a **scalar target-count transplant** and a claim of no existing phase reuse. They do not prove dynamic role reassignment is impossible. A viable adaptation needs a new legal switch boundary, complete ownership/barrier protocol and compatible register/shared-memory resources. Keeping the grid and original roles while adding feedback could first inform a future fixed configuration, but that returns to N03's existing launch-time scope and is not another hypothesis.

## 5. PR triangulation and stopped branches

FI#5148's retained opening body describes EP16/SM103a BF16-activation/MXFP8-weight execution with immutable routing and CUDA graph capture unsupported. Its role budgets, direct output return and per-owner dispatch grouping are useful specific components; its API conditions are not our EP4 MXFP4 dynamic-routing path. A generated closure does not make it a drop-in replacement.

FI#4688 exposed destination fan-out and folded producer roles; DeepGEMM#409 describes shared-expert integration for a separate NVFP4 path. Reading their bodies does not establish new absent target work. The fan-out lead was checked against round52 **before being counted**: D52-01 already audits repeated native pulls, carrier ownership and a closely related donor's null full-layer result; grouped combine also regressed there. This round does not reopen it from fewer logical reads alone. Native routed/shared phase support is already in the inspected target. No fresh PR head/diff or benchmark is claimed.

## 6. Self-critique and next decision

**Strongest support:** runtime balance can change within a sufficiently long invocation; recent primary evidence describes a concrete measured-progress controller. Source inspection identifies that current target roles are fixed, so the abstract research question is real.

**Strongest objections:** no compatible safe switching boundary or inspected released adaptive MoE implementation; target already has fine-grained fused overlap and phase reuse; the paper's large invocation regime may not expose useful adaptation time during actual long-output decode. Controller counters, queue contention, register pressure and altered scheduling can cost more than any recovered slack. No per-layer/rank wait profile, task-cost sequence or controller overhead is known here.

**Cheapest informative next step:** locate the exact donor adaptive implementation and prove an actual target task-boundary transition that preserves existing pipeline ownership, register budgets, named barrier participation, ring generation and all-rank progress. Enumerate zero-work/empty-rank and final-cleanup transitions from source. A simulator supplied with ideal task costs or switch events would not prove that the native events exist; none was run. If no tractable boundary emerges, stop this refinement rather than substitute a large runtime rewrite.

Only after that contract and separate execution authorization would a future comparison distinguish baseline, observation-only bookkeeping, static allocation using the same observations, and true within-invocation changes. Existing Mooncake and agent-p75 remain the serving evaluators with long-output ITL and separate TTFT/tail guards; role/progress instrumentation is needed to attribute a mechanism. Do not invent a synthetic workload or transfer the paper's128K-token improvement to standard decode. No numerical ROI estimate or new serving benchmark is justified now.

**Disposition:** existing N03-family research refinement, deferred below narrower source-work-removal opportunities such as PJ01. Four screens retained, zero new identities. No source or timing evidence changes the campaign's accepted implementation count.

## 7. Tool-use limitations and durability

Initial `init` incorrectly included `--defer-snapshot`, which the CLI rejected before mutation; the subsequent expand/search consequently rejected the uninitialized state. Retried initialization without that flag, then ran the declared research commands successfully. An attempted read of a nonexistent round56 source-manifest was unused; the saved round52 source manifest supplied verified target hashes. Some broad displays were truncated and then replaced with bounded reads; saved receipts retain complete outputs. These are agent command/inspection errors, not provider failures or target behavior.

The exact clauses and pins are retained in `claims.json`/`source-manifest.json`; seven quotes were checked as exact substrings. Quote/hash checks are evidence integrity, not an execution experiment. The isolated source export has provider records, historical revisions and query edges. The command journal and explicit donor pin/tree requests retain provenance. Snapshots/publication remain deferred, and no S3/VM sync is claimed.

Final durability check caught four manually added target source records not committed by the preparation script before close. The explicit isolated commit was added; preparation and all source/hash/quote readbacks then passed before this packet was frozen. Exported scientific content was unchanged. This was a packet-preparation error, not a canonical data loss or tool importer failure.
