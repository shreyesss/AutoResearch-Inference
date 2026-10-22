# Round 3: exact sparse-attention work elimination

**AT03 revision2 is authoritative below.** Initial memoization/epoch design and83-check fixture are superseded, preserved in `revision1/`; they supplied oracle validity inputs and did not prove a deployable lifecycle.

Research checkpoint, 22 October 2026. **No GPU experiment, model load, serving change, or measured target improvement.** Three actual online OpenAlex paper-search calls produced 26 raw hits. We followed mechanisms beyond model-name matching, inspected primary full text and author implementation, and compared against pinned target code. No candidate qualifies for implementation/promotion yet.

## Target and source limits

Target source: `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; planned Flash-1017, TP1/DP4/EP4, MXFP4 indexer, token TopK512. Actual container flags/binary and serving shape distribution have not been verified in this CPU-only research round. Target source is under `../..` only by absolute shared path: `/Users/shreyas/.local/share/autoresearch-reviews/pinned-vllm-c455786/`.

`attention.py` distinguishes candidate producer, dense consumer, and optional `indexer_sparse_logits` consumer. The optional sparse consumer computes only inside previously selected candidate blocks; it still evaluates all index heads there. Candidate capacity 2048 blocks × 8 compressed positions is a capacity bound, not the actual count for a request. Use visible **compressed candidate positions**, not raw prompt length, for cost estimates. For a visible set of at most 512 positions, all positions survive TopK512 and score-screening offers no selection work benefit.

## AT01 — certified head screening inside the existing consumer index domain

**Status: advance bounded CPU numerical/dispatch diagnostic; defer kernel implementation and service claim.**

### Evidence and the actual new mechanism

[DoSA, 2610.13990v1](https://arxiv.org/html/2610.13990v1) proposes upper bounds on each key's full signed multihead index score. Keep selected head dot products; bound omitted positive contributions and lower-bound omitted negative contributions. Obtain a threshold from at least K distinct visible keys evaluated with the full original score. A key with a conservatively computed upper bound **strictly below** that seed Kth threshold cannot win. Compute the original all-head score for survivors, then the original exact TopK/tie policy. Folded heads belong only to screening; weights and final scores remain unchanged.

This skips some **head arithmetic before full scores exist**. It is distinct from selecting TopK after scoring, physical index mapping fusion, length-aware bounds, and cross-layer route reuse. Negative head weights are explicitly supported; they are not a reason to reject the paper.

Author code is real: landing `llm-sys/flash-indexer@d744698bb452433b16a7c7cb4a8d7094e06cdecb` contains README/PDF and links actual `llm-sys/dosa-sglang@582a8a151d5b14bd3b9d79e932a6390638d11e5a`. We downloaded 22 selected implementation/test files and recorded hashes. Directed FP64 planner and full-visible-domain recovery are implemented, independently inspected by reviewer. The HTML header is 26 September while its arXiv identifier is October; retain both metadata rather than invent a publication chronology.

### Why direct port does not qualify

Actual author guards require SM100, FP8 query/head_dim128, 32/64 heads, TopK2048 and specific FP8 paged layout. Certified prefill path begins at **131,072 keys**, seed 12,288, recent 1,536; target TopK512/MXFP4 must be re-derived. Author decode uses full-head scoring plus witness/selection machinery; it is not proof of head-screening decode gain. Author benchmarks use GLM5.2/DeepSeekV3.2, 128K–1M contexts; the reported V3.2 128K service case is 0.979x. We cannot claim a benefit for our short primary benchmark or frozen long-output ITL objective from these results.

### Selective integration and correctness obligations

First scope: prefill **consumer-only** inside exactly the existing visible candidate domain. Dense pre-candidate non-producer index layers could be a separate exposure check, not silently included. Producer publishes both token Top512 and candidate-block Top2048; token winner preservation alone does not preserve its block output, so producer is excluded initially.

Target `vllm/model_executor/layers/sparse_attn_indexer.py` MXFP4 prefill calls DeepGEMM then converts SM100 BF16 logits to FP32. Upcasting does not undo BF16 rounding. `vllm/model_executor/kernels/attention/dsa/sparse_mqa_logits.py` takes BF16 consumer weights. A mathematically sound real-number certificate may therefore fail against rounded target scores. Derive a conservative envelope for MXFP4 per-block decoded scales, dot accumulation, head-weight multiplication/reduction, and reference BF16 rounding. NaN/Inf and invalid scales must force keep/recovery. Strict inequality and target ID ties are mandatory. Seed keys must be visible/distinct and rescored for this exact query; previous-query numerical thresholds cannot be reused. Overflow must recover the **whole visible domain**, including previously pruned keys.

RouteRelay's [route reuse paper](https://arxiv.org/html/2609.07306v1) is not exact: “The only approximation is whether the chosen index set matches”. Its prior routes can selectively supply *seed IDs* after current-query full rescoring; never accept its unchecked route reuse as an exact target optimization. This is a component of AT01, not a second hypothesis.

### CPU falsification and next gate

Executed `cpu_contracts.py`: 1,000 randomized exact-integer signed-head cases, no TopK disagreement. The check omits negative head contributions using their aggregate lower bound. It computes all dots on CPU to validate algebra, so its synthetic rejected-key count is **not a performance result or estimated target pruning rate**. A separate block-scale counterexample shows treating independently scaled MXFP4 blocks as one scalar can underestimate score. Reviewer `../review/round3/contract_falsifiers.json` supplies BF16 reference/tie and producer dual-output counterexamples.

Next bounded diagnostic: implement a conservative target arithmetic envelope against saved/constructed decoded MXFP4 vectors and the exact reference reduction contract; prove NaN/tie/recovery behavior, then assess candidate-domain counts from already saved metadata. Without measured/saved activation distributions, do not predict survivor rate. Useful lower bound on cost: full-score >=512 seed keys plus planner/screening and survivor refinement.

**8K is not zero exposure.** The pinned model config has ratio1 for layers20–39, candidate producer20, and index consumers24/28/32/36. At an 8192-token prompt, those consumers can expose up to8192 compressed positions, below the16384 capacity but well above512. The exact visible count remains query/causality/candidate dependent. Index head count32: a full8192-key row uses262144 head dot products. A hypothetical seed512 plus8 retained screening heads on the remaining7680 keys costs16384+61440+245760*p head dots, where p is the fraction of non-seed keys requiring full32-head refinement. Ignoring planner/reduction/memory overhead, it wins arithmetic only if p<0.75. These are source-derived operation counts, not predicted pruning or speed. Real screening may add bound-vector dot products; substitute its actual effective head cost. A measured/constructed conservative numeric bound and saved-activation survivor distribution decide usefulness; the author's131K implementation guard is a directport limit, not proof of no 8K opportunity.
 If no regime remains where that can beat current work, reject before GPU work.

### Future evaluation (not executed)

Correctness: target reference scores and TopK IDs including boundary ties, NaN/Inf, causal masking, compressed candidate selection, DSpark multiple rows. Replay producer excluded. Target-only greedy output hashes after any accepted numerical implementation.

Cost: planner, screening, survivor count, refinement, recovery frequency, indexer latency; separate prefill from decode and each source/consumer branch. Mooncake provides mixed prefill exposure; agent-75 must be bucketed by actual compressed lengths. Both can test TTFT/service regressions if the branch executes. A future long-context supplemental workload is justified only if existing trace has no eligible context counts. No new benchmark is needed merely because paper used a different benchmark. ITL is a guard here, not an unsupported primary gain claim.

## AT02 — regroup queries by selected KV-page affinity while preserving token masks

**Status: defer target feasibility; reject direct paper configuration and performance transfer.**

[PageWeaver, 2610.11201v1](https://arxiv.org/html/2610.11201v1) groups nearby queries whose selected page sets overlap to reuse KV loads in a two-CTA Union8 attention kernel. Original query IDs carry causal positions, selected support, and output addresses. This changes execution order, not intended selected attention support. It is distinct from mapping logical TopK IDs to physical slots.

The paper's main setup is H200 MiniMax-M3 GQA head_dim128, 16 local query heads/KV head, Top16 ×128-token pages. Our target sparse attention uses head_dim512 and token-level Top512 plus SWA and CED shared sources. Converting selected tokens into entire selected pages would widen attention support and is invalid. Query regrouping can use page identity for load affinity only while maintaining the original per-token masks and typed compressed/SWA address spaces. Pinned config specifies64 query heads at TP1, with head_dim512; query grouping, backend dispatch, and register/shared-memory feasibility still need audit before a port. This differs materially from the paper's16-local-head regime.

Counterevidence is unusually direct: incremental grouping gains reported only 0.47–0.73% at 32K/64K, regressions at 8K; no tested online grouping beats the faster native/original-order choice across the paper's eight B300 captures. Whole-kernel gains include FP8 arithmetic changes and are not grouping-only results. No author implementation repository has yet been positively identified from the paper; full text is evidence of method/results, not a verified executable tool.

Executed `cpu_contracts.py` token-to-page widening counterexample: tokens {0,3} at page size2 become {0,1,2,3}; preserve token masks. Next CPU/source gate: determine actual target head/CTA fill and selected token-page overlap from saved index traces; without traces, no predicted reuse or gain. Future evaluator only after eligibility: identical-support differential kernel tests, then unchanged Mooncake/agent-75 A/B with TTFT/ITL tails and grouping overhead. A bespoke workload is not justified yet.

## AT03 (refined R3-O1) — same-forward compressed-KV materialization reuse

Pinned `nvidia/flashmla.py:305–339` gathers/dequantizes a full compressed region into BF16 workspace at each prefill layer and separately gathers SWA. `attention.py:_compressed_kv_cache` returns the source layer's shared cache for consumers. `flash_mla_mega_attn.py` also gathers in prefill. This suggests checking whether a dedicated immutable gathered compressed representation could be reused across consumer layers within one forward epoch.

**Updated after independent source review: advance bounded CPU lifetime/memory diagnostic; no implementation or service qualification.** Existing workspace is scratch/aliased and per-chunk; simply retaining its tensor is incorrect. Allocation keys must be stable configuration keys per ubatch/lane/stream. Validity stored inside that resource must include source identity/write generation, forward epoch, request/block-table mapping, compression ratio, sequence lengths, quantization, chunk offsets and device; never allocate one persistent resource per epoch; keep SWA per-layer; prove source writes complete and immutable until final consumer. Separate allocation may increase HBM pressure or require copying, erasing any saving. Whole-layer reordering is not implied. Pinned config sources2/8/14 each serve6 layers at ratio2; source20 serves20 layers20–39 at ratio1. At8192 positions, one BF16 cr1 representation has8192*512*2=8MiB per request before padding/SWA. Keeping it through those20 consumers could remove19 repeated compressed gathers if no copies/invalidation are needed; this is a work-count premise, not a latency prediction. Check the full live-request capacity and source-write ordering before proceeding. This is a more target-specific next question than another generic long-context TopK search.

## Search decisions and all dispositions

Actual query receipts are `paper-search-01/02/03.json`; all calls succeeded. Initial exact-indexer query led to DoSA; second expanded beyond TopK into reuse and rejected approximate RouteRelay support; third sought shared KV/memory-layout mechanisms and found PageWeaver plus the source-materialization question. Queries were adaptive to remaining gaps, not model-name-only.

| Paper/lead | Disposition |
|---|---|
| DoSA | AT01 selective prefill certificate retained for CPU diagnostic; direct port rejected |
| LiteTopK 2607.11976 | Pinned author repo cd277d6773fd01635aed4596ca0eb4047f16032c; DSV4 FP4 path gated >=65536, older TP4/EP4/MTP2 artifact; existing TopK prior overlap. No new generic-TopK card |
| HPC-Ops | Duplicate M02; retain previous rejection, no new yield |
| MSA 2606.13392 | Architecture/trained block support; generic layout reuse possible, no concrete delta beyond PageWeaver |
| CoSA 2607.25291 | Proxy skipping changes selected support; exact-preservation not established |
| RIS-Kernel | Stochastic pruning and different CPU regime; no exact target bridge |
| Self-Indexing 2609.13205 | Approximate sign-based retrieval; exact support contract absent |
| SPADE | Video diffusion target; no concrete frozen autoregressive component extracted |
| SparseEngine | Broad sparse-serving system; no isolated target intervention after source comparison |
| Celty 2608.01536 | Pruned weights/hardware regime incompatible with frozen current target |
| FastJEV 2610.11379 | Recurrent/history reuse premise not target-established |
| GLIDE 2607.24788 | Attention architecture change, no frozen target equivalent identified |
| Mathematics of Arrays 2606.07713 | General intermediate elimination; no source-specific missing transformation |
| LaCache 2607.16339 | Diffusion temporal invariant premise absent from native DSpark |
| FARIMC | Distillation/hardware change; no selective exact current-runtime component established |
| RouteRelay 2609.07306 | Direct approximate route reuse rejected; current-rescored seed IDs can support AT01 |
| WISE 2609.27373 | Recurrent-depth reuse premise absent; no justified layer equality |
| HySparse2 2609.26368 | Architecture-level KV sharing; target already has CED sharing; investigate implementation reuse separately |
| PageWeaver | AT02 integration feasibility deferred; paper's short/Blackwell results oppose direct promotion |
| SparLeak | Security subject, outside requested performance mechanism |
| HiSparse | Duplicate M04 with wrong offload/capacity regime unless new premise emerges |
| AVSG 2609.37538 | Offload/reuse regime not configured for target main KV |

Deduplication: 26 raw hits / 22 distinct paper labels, 3 intervention cards (AT03 added after source review), **0 qualified implementation candidates, 0 measured gains**. Search/source artifacts remain useful despite rejection; stronger grounding reduced false promotion rather than forcing a quota.


### AT03 source review refinement and experiment contract

Review confirmed both FlashMLA and Mega prefill consumers obtain the same source KV tensor and source metadata. Existing `WorkspaceManager.get_persistent_resource` provides stable resources isolated per (ubatch,lane), with graph warmup/lock rules and explicit stream-overlap constraints. A minimal proposal is a persistent **combined** KV buffer: fill its compressed prefix once after the source insert; regenerate the SWA tail at every consumer; retain each layer's own Q, sink, selected token IDs, and output. This avoids copying cached compressed data back into generic scratch. Start with source20 and a single prefill chunk; unsupported/multichunk cases retain the current path. Whole-layer reordering and decode-cache replacement are excluded.

The 20-layer topology supports an upper bound of19 avoided repeated compressed gathers per eligible forward/chunk only after verifying each layer dispatches the same compatible prefill backend and layout. Source-write completion, shared source20 metadata, same chunk_N/M and request mapping, and absence of writes by consumers are the required predicates. Read source-specific insert ordering; do not assume a Python object cache itself proves GPU synchronization.

Memory correction: 8MiB is only the compressed8192-position prefix. A full8192-token initial prefill can also need an8192-position gathered SWA tail under the current buffer layout, making the combined BF16 buffer **16MiB/request**, before index scratch/padding. Persistent capacity is additional to other live allocations and may be multiplied by ubatch/lane/stream instances. Chunked prefill may have a smaller tail; use actual chunk metadata. Multi-chunk execution is layer-major: one cached chunk overwritten by the next is not available to a later layer. Either retain all necessary chunks within a declared budget or fall back; do not reorder the model.

CPU gate: reconstruct source-to-consumer mapping and chunk plans from pinned config/saved request metadata; simulate generation-tagged resource lifetime, per-layer SWA overwrite and request reuse; falsify unsafe cross-epoch, aliased scratch and multi-chunk reuse. Compute required peak persistent capacity before any allocation. Static dispatch inspection and this metadata proof do not establish material gather latency.

Future evaluation: first bitwise equality of gathered compressed slices and per-layer attention inputs/outputs on original vsreuse, including partial prefill, prefix hits, mixed decode/prefill, multiple requests, source writes and ubatches. Then unchanged Mooncake and agent-75 TTFT/E2E/ITL tails, goodput, prefill gather count/time, peak HBM, KV capacity/preemptions and graph replay stability. These two existing workloads already exercise prefill; use them first. No custom workload is necessary unless saved coverage lacks the required source20/single-chunk dispatch or concurrency cases. Frozen long-output ITL is a guard: this proposal targets repeated prefill preparation, so no decode gain is promised.


### AT03 executed CPU and source follow-up

`kv_lifetime_falsifiers.py/json` executed **83 symbolic CPU reference comparisons**, covering20 consumer layers, two interleaved lanes, two epochs, source-generation changes, request/block-mapping changes, and multi-chunk fallback. Two stable resource allocations suffice in that simulation; epoch changes invalidate contents rather than create unbounded allocations. The first80 comparisons perform four compressed fills (one per lane/epoch) while SWA changes at every layer. Two more fills occur on source/mapping invalidation; multi-chunk takes the unchanged reference path. Scratch-alias retention and one-buffer multi-chunk retention counterexamples fail as expected. These are literal Python lists encoding intended memory lifetime, **not execution or validation of the GPU implementation**. GPU ordering, graph replay resets, exact reader mutation behavior and real dispatch remain unverified.

Independent reviewer source audit `../review/round3/KV_REUSE_AND_PAGEWEAVER.md` confirms source tensor/metadata sharing and repeated gathering in both backends. Gather implementations write only `offset+i` for `i<gather_len`: the SWA tail write at offset=chunk_N does not clear a valid compressed prefix. Leave unused padding subject to the original mask contract; zeroing the entire persistent buffer would destroy reuse. Persistent manager lifecycle already exists but requires allocation during warmup and no concurrent use of the same lane/stream resource.

Root's executed `workload_cost_envelopes.py/json` uses exact model config and saved Mooncake input lengths: all requests exceed512 input tokens; reported compressed-source20 median around6.1MiB/request and p95 around22–27MiB across saved sets. Full8K initial combined16MiB example included. These are metadata capacity/work envelopes, **not actual prefill chunk sizes, cache-hit rates, visible candidates, scheduling, or latency predictions**. These files join the retention packet. Existing workloads have potential relevant exposure, so neither AT01 nor AT03 is rejected merely for being shorter than the paper regime.


## AT03 revision2 — unconditional source-entry fill, no epoch oracle

The initial fixture was too generous: it supplied source generation and metadata validity as oracle inputs, while pinned `ForwardContext` does not expose the required epoch. String comparisons also did not test realistic validity detection. **Do not use the initial83 checks as evidence that a deployable cache-invalidation protocol exists.** Original card/report/fixture are preserved under `revision1/`.

The narrower proposal removes across-call memoization entirely. On every source20 **prefill attention invocation**, unconditionally execute the current compressed gather into a dedicated combined buffer. Consumers21–39 may reuse that prefix within the same verified group, overwriting their own SWA tails and indices. Same source address with changed content is safe because each group invocation refreshes the representation. Under CUDA capture, the source gather must be in the captured ordered execution and execute on every replay; a Python `already_filled` flag must not suppress it. Allocation identity is stable per configuration/lane/stream; there is no epoch/version key or dynamic hidden cache-validity oracle.

### Actual entry coverage

Pinned `nvidia/model.py:843–869` constructs decoder replay at `cut=max(kv_source_layer_ids)=20`. Normal model forward runs early layers then the replay wrapper; `_run_replay_layers:1224` always executes `range(decoder_replay_start,end_layer)=20..39`. With replay disabled, the ordinary layer loop includes20 before21–39. The wrapper may write source20 KV for the full batch and then run the trimmed replay batch under its own context. The gather belongs to source20 attention **inside this chosen execution context**, not the outer full-batch write-only call. `decoder_replay_cudagraph.py:54` wraps the whole replay callback. No inspected path enters consumer21 alone.

Reviewer executed the extracted actual wrapper control flow in `../review/round3/decoder_replay_control_audit.py/json`: five paths (plain, eager replay, piecewise replay graph, small piecewise, capture without live batch) enter the whole layer callback; nested context restoration checked. Torch/CUDA/layer bodies were mocked, so this proves limited wrapper control flow, not captured gather correctness. Source20 has special SWA metadata in model_state; identical context objects do not prove identical chunk geometry. That remains an explicit eligibility check.

### Revised CPU discriminator and remaining gate

`source_entry_lifetime.py/json` contains no epoch or source-version inputs. It changes contents at the **same source address** between four calls, runs two lanes through all20 layers, and compares every combined buffer to a fresh reference:160 comparisons,8 unconditional source fills,152 consumer reuses. Missing-source-entry, reordered-group, multi-chunk and unequal-geometry schedules take the original gather path before using stale buffers:79 more comparisons across four rejected schedules. This models static eligibility and fallback; it does not claim a new runtime detector inside CUDA graphs.

An additional mid-group source mutation deliberately produces a mismatch: this design cannot detect that without new machinery. It must be excluded by proving source-write exclusivity and ordered execution. Consumers have no compressor and read source20's shared cache in the inspected source, but complete asynchronous and replay write ordering remains a gate. GPU source-entry gather dominance, same chunk geometry, read-only attention access, stream ownership, warmup capacity and real memory budget must all pass before implementation qualification. No GPU code was run.

**Current disposition:** candidate retained, implementation deferred, CPU/source review ready. The next work is bounded static dominance/geometry review and memory-envelope interpretation, not another invented epoch mechanism. Saved online query command receipts are in `discovery-command-journal.json`; the query plan reconstructed after execution is explicitly retrospective.
