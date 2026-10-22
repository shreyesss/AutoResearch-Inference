# Round 88: recent execution search, transport observability, and a graph-readiness dependency

## Decision

**Zero new performance hypotheses.** The recent paper's instrumentation does not observe the planned MegaMoE transport. The useful follow-up is a concrete correctness dependency: open DeepGEMM PR451 resets combine readiness before the pull barrier, while the pinned a7a FP8/FP4 implementation lacks that reset. This deserves a bounded future changed-input graph check before interpreting MegaMoE optimization results. We have not reproduced a device failure, applied the patch, or measured a benefit.

The original folder name reflects a memory-translation direction stopped by prior recall. The task then pivoted to recent persistent execution and scheduling papers. All branch outcomes remain below.

Target remains frozen Flash1017 checkpoint 1bae0e1088993b9b82de08f59de5be5a34e42170, callgideon/vllm c4557869393db4d75c483d92edd02a5125500883, vllm-project/DeepGEMM a7a927731b109fdfec770df7c2a5be5d7e2216b5, planned B200 TP1/DP4/EP4 groups. These are source-plan facts, not live attestation. No GPU/native/model imports, build, serving patch, canonical mutation, cloud action, or Git change occurred.

## 1. Adaptive discovery and coverage

1. Full compact recall covered 149 cards over two pages, with a matching inventory hash. Read-only report search found round44's BOOST/Elastic-KV work; the initial hardware-page-placement lane stopped before any online query. Compact-card silence was not treated as semantic novelty.
2. One OpenAlex search, September 1 through October 22 inclusive, returned ten papers. mKernel and Herschel were already investigated; several results concern code-generation agents rather than a removable target operation. OpenAlex dates are provider publication dates: the kernel-generation survey has a January arXiv identity despite a September publication record.
3. A narrower explicit arXiv query for GPU inference plus persistent execution/work stealing/work queues returned twelve papers. No automatic relaxation occurred. mKernel appears in both receipts, so **22 returned references represent 21 explicit paper identities**. SigmaTrace had prior abstract metadata but no retrieved full text in the bounded retained-source lookup. One normal `investigate` fetched versioned 2610.24328v1.
4. Read SigmaTrace Sections V, VI-D/E, VIII, with introduction/interface context. Its exact mechanism changed the decision: low-overhead GPU instrumentation here means NIC doorbell interception, not arbitrary remote GPU-memory tracing.
5. Read-only PR FTS found zero SigmaTrace PRs, five MegaMoE/barrier matches and five RDMA/profile matches. Two selected PR records were imported into the isolated state. Actual `pr-search` replayed that subset; it is not another full-corpus search. PR451 warranted current API, complete three-file diff, comments/reviews, and two exact head code reads. PR36657 is a distinct SM-reservation/liveness issue, not bundled into this change.
6. The first readiness report search accidentally used the Store default `match=any`; its broad matches did not contain the exact claim. A recorded `match=all` follow-up found no report for gridid or 451 plus readiness. Two existing reports mention combine readiness generally. This is bounded indexed-report evidence, not proof no human ever considered the bug.

See `paper-dispositions.json`, `tool-use.json`, normal command journal, and raw receipts. The final closure plan records why further querying would not change the present decision.

## 2. SigmaTrace: retain the interface lesson, reject the direct instrumentation port

[SigmaTrace 2610.24328v1](https://arxiv.org/html/2610.24328v1) replaces Mellanox NIC UAR mappings with monitored host pages, forwards observed doorbells, and reconstructs queue entries. The paper distinguishes these GPU-initiated traces from its MoE case: the latter uses **host NCCL**, DeepSeek-V3-0324, 16 H200s over four nodes. Its 2.13× node egress imbalance is an observation, not a serving speedup or a target result. The persistent BFS GPU case reports 11.5% tracing overhead; low overhead is not universal.

The pinned MegaMoE adapter obtains one symmetric buffer for the EP group and launches its fused kernel. The selected kernel writes source indices/counts through `sym_buffer.map`, executes an explicit `comm::nvlink_barrier`, publishes completion with system-release stores and reads it with system-acquire loads. These inspected operations are direct peer-memory signals; they do not ring an RDMA UAR. Installing SigmaTrace would not observe them merely because the model uses EP. This does not claim the entire serving process has no NIC traffic: control traffic, KV transfer, or another deployment can use different transports.

**Disposition:** reject direct SigmaTrace profiling of this intra-node MegaMoE data plane. Retain the diagnostic principle of mapping a trace to its actual transport and separating byte skew from exposed wait. Do not replace the transport or add a host proxy to make a profiler applicable. A future multi-node/RDMA baseline would be a changed premise. No immediate service optimization follows from this paper, and no speedup is forecast.

## 3. PR451: missing readiness reset in the pinned implementation

Current [PR451](https://github.com/deepseek-ai/DeepGEMM/pull/451) is open/unmerged; inspected head **7e924a8c4be7458d5f18175bf00da8644be17c04**, base **78b69000794d0937b47ae3387eff7663410264d1**, fork foreverrookie/DeepGEMM. Complete patch changes the FP8/FP4 and BF16 kernels plus their layout comment. Only FP8/FP4 and layout full bodies were fetched and read; BF16 evidence is the retained complete diff and author comment.

### Exact source delta

- Target layout says grid indices are unique per launch, so no reset is needed.
- Target dispatch pushes `get_grid_idx()+1` to peers, then enters the pull barrier. It does not clear local combine-ready flags there.
- Target epilogue publishes peer readiness after local L2 writes and waits for `ld_acq_sys(peer_ready_ptr) == grid_idx` before reading selected routed results. Shared-first/top-k ordering remains separately important.
- The inspected end cleanup clears expert counts, task counters and ring state, not these ready tags. The vLLM symmetric-buffer cache persists the workspace; its inspected forward stages activation/routing inputs, not a ready-tag reset.
- Donor adds a local system-release zero store for each peer flag immediately before publishing grid IDs and before the existing pull barrier. It does not replace the scheduling/communication algorithm.

[Target kernel](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/impls/sm100_fp8_fp4_mega_moe.cuh), [target layout](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/layout/mega_moe.cuh), [donor kernel](https://github.com/foreverrookie/DeepGEMM/blob/7e924a8c4be7458d5f18175bf00da8644be17c04/deep_gemm/include/deep_gemm/impls/sm100_fp8_fp4_mega_moe.cuh).

### Evidence and limitations

PR author reports changed-input graph replay failures on B300, repaired by the reset; this is externally reported, not executed here. The automated review comment is an additional source explanation, not independent hardware evidence. Official [PTX gridid documentation](https://docs.nvidia.com/cuda/parallel-thread-execution/#special-registers-gridid) describes a temporal grid identifier and debugging use; the inspected section does not explicitly settle reuse across graph replays. Therefore the current record establishes **a code difference and a credible conditional failure mechanism**, not an observed bug on our target runtime.

If the same nonzero tag remains from an older invocation and is reused, equality alone admits a read before the current peer publishes. Resetting before the existing all-rank pull barrier is intended to separate old completion from the new one. Correctness still depends on the actual barrier and system-memory ordering: all ranks must perform the reset; no prior publication may arrive afterward; current completion must be ordered after the barrier; the consumer must not race with its own reset. Concurrent invocation/workspace aliasing, zero-token ranks, full tag width/wraparound and native graph lifecycle remain explicit checks. We did not prove these with scalar arithmetic.

`source_contract_check.py` executes only stdlib source-string checks and four equality cases with **assumed** reused/distinct tags. It verifies donor reset placement relative to the call rather than its enum declaration, old reset absence, and the unchanged wait predicate. It is not a CUDA or concurrency simulator. An initial check selected the enum declaration and failed; the corrected check anchors on the actual pull-barrier call. The failed diagnostic is recorded in tool-use history.

### Disposition and smallest next check

Retain as a **correctness prerequisite/refinement for future MegaMoE work**, including A52/N03/EC79-style experiments, not a new performance identity or measured gain. It does not supersede those scientific mechanisms. No baseline, hypothesis status or accepted count is changed.

The smallest future authorized device check is repeated changed-input graph replay of the exact dependency and adapter, comparing eager and captured outputs under identical policy, including balanced, unequal and empty source ranks. Record actual ready-tag values and workspace reuse. Compare original versus exact reset patch only after reviewing memory-order/lifecycle obligations. A runtime that demonstrably supplies fresh tags or an equivalent reset may close the concern without adding this patch. Keep any fixed correctness baseline identical across subsequent performance arms; never call stale or partially written results a speedup. This check is **not authorized now**.

Existing agent-75/Mooncake service metrics do not certify synchronization correctness. A small changed-input replay diagnostic is justified because stale completion can be invisible to aggregate latency. No new broad workload or profiling campaign is proposed. The work is correctness-first; direct ITL ROI is unknown and not its claim.

## 4. Other screens and useful search lessons

- Hardware translation/VMM: prior round44, stopped as duplicate, not rejected by a new experiment.
- mKernel/Weave/Herschel: already investigated component families; no new evidence changed their dispositions.
- FlowTT: abstract describes TT-core contractions and prefix-shared index flows. No such TT embedding representation was established in frozen target weights; no trained/compressed representation transplant or ungrounded work-stealing card was proposed. No full text read claimed.
- AGP/A-GHOST: packet-to-inference pipelines; no corresponding packet parser or small IDS execution graph was identified on this target. Abstract-only screens, not blanket rejection of GPU-driven execution.
- KVMem: query-dependent history virtualization changes the context policy; no exact target-cache or quality contract was established here. Abstract-only, deferred outside this lane.
- KernelOPT/D2K/AlphaCu: possible research-process background; no specific target operation delta obtained. No workflow-quality improvement claim from retrieving them.

The concrete useful outcome came from recent-paper interface scrutiny followed by local PR triangulation. The broad query itself had low direct mechanism yield. A closure-plan schema error (observations omitted provider) was repaired explicitly; it made no network call and did not alter accepted statuses. No new tool feature is justified solely by this one caller mistake.
