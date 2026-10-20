# Kernel, memory and communication exploration

## Method actually used

A source-first implementation-delta search, followed by counterexample search and recent-paper mechanism transfer. `explore.py` permutes eight predeclared engineering queries with random seed **20261020**; this randomizes order, not an unbiased sample of all optimization space. `search.json` retains queries, full returned records, dates and ranking. Searches used the local GitHub tool, all-token matching, updated_at >=2026-08-01, six results per query. Thus an old PR with a recent discussion can appear. No Serper calls. Read full bodies of twelve selected PRs, fetched pinned code and fulltext of September2026 paper arXiv:2609.07536. `selected-sources.json` identifies the frozen evidence selection; execution.log records actual runner progress. Agent prompts emphasize backend eligibility, measured counterexamples and operator-to-serving transfer, unlike generic novel-idea brainstorming.

## Baseline and goal

Build on the existing B200 native agent-f75 frontier: R7b two DEP4 replicas at concurrency256/384/512, and R10 DEP8 at1024, keeping eight GPUs and the same workload. The previous source report is an aggregate benchmark, not a kernel trace. Refreshing a YAML profile does not establish the flags used by an archived run. In particular, archived dspark_config=off conflicts with current k5 profile; engine image, exact commit, backend and real flags must be established before starting any comparison. Parent exploration's shared protocol further distinguishes custom goodput from strict AIPerf goodput and wholetrace ITL from long-output-only cohorts. No GPU experiments were executed in this exploration.

## Candidate K1: decode-capacity workspace for FlashInfer CuTeDSL MegaMoE

**Mechanism:** when actual decode/verification token count is much smaller than prefill capacity, use the upstream decode-sized workspace rather than the prefill-sized workspace. The causal claim to test is reduced capacity-dependent work or memory traffic—not a guaranteed arithmetic speedup. The new allocation may reduce KV capacity enough to hurt overall goodput.

**Grounding:** [PR62073](https://github.com/vllm-project/vllm/pull/62073) directly describes a second workspace and global rank agreement. Its quoted contract is “since peer buffer offsets depend on the capacity.” The PR's Beam prefill result is a different model/hardware/workload and is not evidence of a DeepSeek decode gain. This path requires nightly FlashInfer APIs. Source also admits real nightly MegaMoE paths lack complete validation on that head. Pinned head `86a5bbe75a7971275952477bb1ce03e715bcc339`; the modular expert adapter delegates to `FlashInferMoeEp`. At the historical baseline pin, both guessed adapter paths returned404, so **feature absence is unresolved**, not established.

**Experiment:** backend and inclusion audit first. If active DeepSeek uses native DeepGEMM MegaMoE rather than FlashInfer CuTeDSL, this is not a direct patch: defer, or separately compare backend changes without attributing their effect to workspace sizing. On an eligible path, isolate workspace selection behind one switch, preserve weights/GEMMs/routing, and require globally consistent capacity. DSpark k5 can make verification input up to six tokens per sequence, so a decode-only one-token capacity is unsafe. Test empty ranks, skew, exact boundary and overflow fallback; ensure no new hot-path host synchronization. Measure allocated bytes, dispatch/compute/combine time, HBM traffic, graph replay, preemptions and KV blocks. A kernel gain that is erased by cache pressure or tail latency fails the serving objective.

## Candidate K2: contention-aware communication resource choice

**Mechanism transfer:** choose a small, capture-compatible resource partition for communication and shared-expert computation using routed-tile counts and residency rather than always maximizing communication CTAs. This targets contention inside overlap; merely turning on asynchronous combine is not the proposed treatment.

**Grounding:** [September2026 paper](https://arxiv.org/abs/2609.07536) models launch-time resource contention and tests on four A100s in COMET/FLUX. Its implementation and measured gains are not B200/vLLM results. [PR52781](https://github.com/vllm-project/vllm/pull/52781) supplies a concrete vLLM shared-expert/combine overlap boundary and a useful causal ablation: wait-before-shared-experts versus delayed device-side join. It also disables this overlap under DBO. A B200 backend with an integrated MegaMoE kernel may not expose a safe independent communication-resource control. This is **research-stage conditional**, and should be deferred if no legal knob or measured contention exists. Additional pinned adapter inspection (performed after evidence extraction) finds `can_overlap_shared_experts` returns `False` at lines404–405 of head86a5bbe75a7971275952477bb1ce03e715bcc339. Thus this is not directly applicable to that CuTeDSL path; do not silently change the backend and attribute the resulting effect to resource selection. The frozen model packet includes the expert wrapper but not this subsequently fetched adapter; this is a documented post-run engineering eligibility check.

**Experiment:** read the active backend and collect one overlap trace before implementation. Hold GEMM tactics, weight precision, routing and topology fixed. Compare synchronous control, async fixed partition, resource-selected partition, and async-with-early-wait ablation. Freeze a small permitted partition set with fixed pointer/buffer ownership; include selector/dispatch overhead in timing. Measure actual communication-compute overlap, SM residency, serialized intervals, per-rank tail and request goodput. No online exploratory kernel execution within request handling. Autoresearch may fit an offline table on training traces, but must use held-out bursts for evaluation.

## Leads not promoted as direct B200 improvements

| Lead | Why retain it / why not claim a win |
|---|---|
| [61962 pre-dispatch MXFP8](https://github.com/vllm-project/vllm/pull/61962) | Attractive quantize-once mechanism, but AMD MoRI/AITER operand contract; B200 adapter quantizes dynamically inside its megakernel. Requires verified scale transport and kernel consumption. |
| [54683 scale correctness](https://github.com/vllm-project/vllm/pull/54683) | Counterexample: rank-local dynamic per-tensor scales cannot simply be gathered and consumed as one global scale. Quantize-before-dispatch can be wrong. |
| [57604 staging/gather](https://github.com/vllm-project/vllm/pull/57604) | Merged Sep18; may already be present. Strong prefill microkernel improvement does not imply decode win; PR's paired decode full-model effect is only0.14%. Use as a negative control and inclusion audit. |
| [62430 DBO real-row staging](https://github.com/vllm-project/vllm/pull/62430) | Specific NIXL/MRV2/single-token eligibility; DSpark multi-token verification unsupported without additional work. Current head CPU tests do not validate CUDA/multi-rank serving. |
| [57204 remove intermediate padding](https://github.com/vllm-project/vllm/pull/57204) | Good known implementation check; not a fresh frontier claim until pinned baseline's width/fusion are inspected. |

See `experiments.json` for machine-readable proposed contracts and `hypotheses/decision.md` for the actual generated rubric decision. “Accepted” means prioritized for evaluation, never measured support. All numeric stop/advance thresholds in the experiment contract are design choices, not historical gains.

## Additional exact implementation inspection

`pinned-adapter.json` stores the complete adapter at head86a5bbe75a7971275952477bb1ce03e715bcc339. Lines389–400 gate secondary workspace on CuTeDSL, PCP=1 and create_workspace, with capacity ceil(max_num_seqs*(1+speculative_tokens)/SPsize). Lines419–438 select only when all DP ranks fit; lines513–518 allocate and warm it before use. Inspect the use of existing CPU DP metadata and ensure the serving integration does not add synchronization. This resolves implementation existence on the PR head, not deployment inclusion.

## Actual runner result and retained memory

Two proposals were persisted; neither was selected by the generated rubric. H1 (K1) scored67 and was rejected: reviewer flagged ambiguous wording (no reported measurement versus a measured zero gain), missing deployment eligibility, and the automatically generated rubric required a fulltext paper for every candidate. That paper requirement is unnecessarily broad for a concrete engineering port; it is a surfaced rubric limitation, not evidence the idea is experimentally false. H2 (K2) scored66 and was deferred because backend eligibility and a legal resource knob are unknown. Neither has been GPU-tested. A later review should correct the wording, include pinned-adapter.json and use an engineering-specific rubric; preserve this earlier rejection.

- K1: `hypothesis:e4f2843d5a7873fb39c4533c1eeb4d18758ebadc01bff67d8fc4cfc9235693fd` — rejected.
- K2: `hypothesis:d6a6e253d7a287c7e1d05febf6ddd4c5bce5e576bb03685997c73ede6f53e78d` — deferred.

Experiment JSON uses the shared protocol: strict AIPerf goodput primary, custom scorer separate, arrival-rate capacity sweep and matched-load tails;5% promotion target is a proposed engineering threshold. GPU-hour budgets explicitly assume eightGPUs (15min=2GPUhours,30min=4GPUhours). No test plans are registered by this subagent; the parent consolidates them.

## Executed factual repair under the same rubric

A follow-up corrected H1's ambiguous wording to say there is no controlled DeepSeek B200 decode measurement in the inspected sources, and added the complete pinned adapter with exact capacity/PCP citations. The augmented packet records that this was source inspection plus mechanical quote validation, not another model extraction. The corrected card was registered as a child of the original rejected card; an actual `hypothesis.run` revisit then used the **unchanged policy**. It finished **deferred,58/100**, with factual support now passing, and unresolved deployment/API/token-bound correctness plus the policy's mandatory-paper requirement remaining. No paper citation was added merely to satisfy a quota, and no policy was weakened to get acceptance.

Original rejected: `hypothesis:e4f2843d5a7873fb39c4533c1eeb4d18758ebadc01bff67d8fc4cfc9235693fd`. Corrected seed: `hypothesis:49e612f1ad8cffc2b83acf89f6a33f4d5062a606204262f327ad458722d41534`. Latest reviewed card: `hypothesis:cbaa74a8a3a2661e1ff93b400266631b5b89638f89512ba6cc4f6193551f3957`. See [repair decision](repair-review/decision.md). `experiments.json` now maps K1 to the latest reviewed card and retains the original assessment.
