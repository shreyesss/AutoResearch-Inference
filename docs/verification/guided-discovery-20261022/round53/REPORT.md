# Round53 — recent compiler/runtime mechanisms and the rollback premise

**Source screen; no new formal hypothesis or implementation promotion.** 22 October 2026. Zero GPU, native engine, model or serving executions. This round adapts the search after checking earlier persistent-decode, cache and host-runtime work; it does not introduce a new fixed research workflow.

## Actual retrieval

One production `expand` followed by one `paper-search` queried arXiv for LLM inference plus compiler/compilation/autotuning/specialization, October1 inclusive–October23 exclusive, limit12. Six abstracts returned, all inspected. `investigate` fetched one version-pinned fulltext with one logical HTTP cache miss and no provider error. No paid-model call. Method and relevant evaluation/implementation passages were read, not every paper figure. `COMMAND_CORRECTIONS.md` preserves an agent flag typo rejected before retrieval and a failed attempt to use Git in a retained source archive.

| Paper | Component-level screen |
|---|---|
| SubTernary2610.28671v1 | Read deeper: separate unified graph arena and zero-copy rollback from ternary weights. Target comparison below. |
| GPU Goldmines2610.17321 | WebGPU tuning/database contribution; backend and execution regime differ. Reusable tuning methodology is possible, but generic shape/tactic selection already has DA01; no new target delta from this abstract. |
| Code2Worlds-2 2610.17651 | Scene/physics compilation, not inference-runtime compilation. Off-topic retrieval. |
| AlignQuant2610.07457 | Tile-aligned mixed precision changes weight/activation representation and calibration. Not an exact unchanged-precision compiler rewrite. No blanket claim that all quantization is forbidden; a separate accuracy/precision experiment would be needed. |
| MX-Like Tensor Core2610.26083 | NPU datapath/co-design, not a B200/H200 software-only intervention. |
| Stratified Sparse Attention2610.28441 | Sampling residual support changes the sparse-attention estimator. Existing exact target support cannot be replaced merely because quality on other models improves. Keep as a different accuracy tradeoff direction, not this exact-execution branch. |

## SubTernary: retain components, test the target premise

[The primary fulltext](https://arxiv.org/html/2610.28671v1) describes CPU draft/target graphs sharing an arena and thread pool, plus a static speculative scratch region whose valid extent is advanced or reset. Its low-bit kernel is a separate component; rejecting ternary weights alone would miss the runtime ideas. However, its rollback discussion assumes costs from copies/allocation in its compared CPU setup. Its results do not establish those costs in our GPU runtime. No released author implementation was identified by this dossier's bounded repository-link extraction; that is not proof that none exists.

### Exact target source evidence

Pinned `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`. The retained archive hash was recomputed and five selected files compared byte-for-byte against archive members, rather than trusting directory names. Live image equivalence remains unverified.

- `vllm/v1/core/sched/scheduler.py`, around2203–2213: derive accepted/rejected counts and subtract rejected count from `num_computed_tokens` and async placeholders, with stale-output/preemption guard. This branch does not copy the historical KV tensor.
- `gpu_model_runner.py`, around1507–1533: deferred speculative correction adjusts request and batch token counts. This is another count/state update, not evidence of a full historical KV copy.
- `kv_cache_manager.py`, around541 onward: request lookahead slots are included in required capacity; skipped-block freeing uses processed-token bounds to preserve in-flight/rollback semantics. This is not a per-rejection operating-system page-table rollback.
- `block_pool.py:get_new_blocks`, around666–707: allocate logical blocks by popping free block objects, updating references/cache metadata and callbacks. Do not equate the term “block allocation” with a CUDA allocation or TLB shootdown. This does not prove that every related path is free of costs; it falsifies that simplistic transfer premise.
- Native DSpark `_generate_draft` calls the parallel backbone once then sequential Markov sampling under the draft graph. The paper's standalone autoregressive drafter/thread-pool context-switch model is not this exact execution structure.

**Decision:** no demonstrated missing full-history-copy rollback optimization on the inspected target paths. Do not propose a new contiguous transactional cache or predict the donor's speedup. Retain the selective principle—reuse persistent execution resources and update validity metadata—but current source already does substantial relevant work. Whole V4.1 CED/SWA/Engram cache correctness was not revalidated here. A new allocator/staging inefficiency would require its own source location and cost evidence; it does not follow from this paper.

No synthetic counter test was run merely to validate subtraction or a queue. Native source is sufficient to reject the claimed direct missing operation; it is not sufficient to claim measured zero rollback overhead.

## PR triangulation changed the next question

Three read-only local corpus searches, all-term conjunction and limit12 each:

- `speculative rollback`: scheduler correctness and grammar-history copying hits; grammar state is a different object from KV. The supplied agent-75 workload does not establish constrained-decoding grammar exposure.
- `transactional KV`: lifecycle/plan/cache APIs. FI#6448 describes duplicate FA2/FA3 MLA plan validation and zero-query rows. Its reported H200 GLM path is not automatically our V4.1 backend. It is a follow-up lead, not a qualified current-path optimization.
- `graph arena`: FI#6360 describes ranking BF16 tactics with a cold launch chain, and distinguishes its B300/GB300 evidence from B200. This resolves a different uncertainty: whether isolated tuning chooses the wrong kernel under realistic launch/cache behavior. The source audit is assigned separately as round54, including exact dispatch, prior-report overlap and activation conditions. It is not counted as a second result here.

Opening bodies were read for vLLM#41356, FI#6448 and FI#6360; no fresh PR diff or CI was inspected in this round. The saved query results contain36 records, including a paper hit; they are not36 independently reviewed PRs. Retrieval spans existing corpus dates rather than imposing the online paper window. These bounded results do not certify corpus-wide absence or full issue/review coverage.

## Rubric and yield

The frozen objective remains useful long-output ITL improvement with correctness/TTFT/tail guards, on the planned Flash1017 TP1/DP4/EP4 deployment. No numerical benefit is predicted. Novelty is not a gate; evidence of an actual missing operation is.

**One online query → six screened abstracts → one selectively read fulltext → one direct-transfer premise rejected by pinned source → two PR leads for separate compatibility review. Zero new formal cards, zero implementation selections, zero service results.** Unknown source routes are deferred rather than assigned a fabricated ROI.

The query had one clear semantic false positive and several methods requiring different runtime or numerical assumptions. Useful improvement was the adaptive shift from paper terminology to concrete operation searches; it found the tuning-evaluation lead. No evidence supports changing the search ranker merely to favor compiler keywords. Preserve failed command diagnostics, exact source hashes and the distinction between source screen and native verification.
