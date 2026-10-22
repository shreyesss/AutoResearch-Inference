# Independent CMR microbatch partition audit

## Verdict

A distinct, bounded CPU/source diagnostic is defensible: **permute eligible whole decode-request bundles into capacity-constrained microbatches while preserving the existing DP-agreed padded split**. This is not an arbitrary context-weighted split point, an early DP handshake change, or proof that DBO is active. Retain deferred; no service improvement or implementation authorization. The paper's KARAT hardware, hundreds-of-thousands-token contexts and reported throughput do not transfer.

## Source-grounded gap

V2 `gpu/ubatch_utils.py:49–74` delegates to the existing midpoint split of DP-padded tokens. It does not use accumulated context lengths. `gpu/dp_utils.py:97–150` requires every rank to allow ubatching, checks thresholds on the minimum rank and agrees padded execution shape. `_make_forward_contexts:399–426` explicitly assumes every rank has the same token count for each microbatch. A locally chosen unequal split breaks that assumption. The proposed restricted permutation leaves collective count/order and padded slice sizes unchanged.

Activation remains unknown: `parallel.py:258–273` defaults DBO off, ubatch_size0; `use_ubatching:645` allows DBO or ubatch_size>1. `maybe_build_ubatch_runner:544–564` also requires DP>1. Decode/prefill thresholds and actual batch composition determine use. Source supports the path; there is no live activation evidence.

The hardware paper CMR repartitions by aggregate context per KARAT device because its attention runtime scales with full context. Target core sparse attention reads bounded Top512 plus SWA128, so that explanation alone fails. However, `attention.py:1417–1440` explicitly leaves pre-candidate and candidate-producer indexers dense; `sparse_attn_indexer.py:880–917` uses per-row effective seq_lens for paged indexer logits. Later candidate-sparse paths are optional. Thus context-dependent target work is possible, but raw context length is an uncalibrated proxy: compression ratios, candidate cap, query count, source sharing, tile padding and selected runtime flags matter. It must not be modeled as full-context attention in every layer.

## Required eligibility and integration gates

1. Attest actual V2, exactly two active microbatches and supported backend/DP configuration. The frozen serving baseline remains live-unattested. If ubatching is off, this is inactive; enabling it is a separately controlled intervention.
2. Restrict initial scope to actual uniform decode bundles with equal Q and no active adaptive compaction, mixed prefill, CP/PP/multimodal/LoRA complications until separately proven. `sort_batch_req_ids:2458–2471` preserves verification/decode → short extend → prefill ordering relied upon downstream.
3. Require the agreed split to be an actual request boundary. Uniform FULL descriptor validation (`cudagraph_utils.py:235–254`) checks total/num_reqs but does not force even padded request count. Q6 with five padded requests has total30 and midpoint15, splitting a request. Existing runner supports straddling, but the proposed whole-bundle binning does not automatically preserve it.
4. Active adaptive verification is a concrete blocker to a naive CPU-only bundle map: `model_runner.py:1418–1451` compacts and reallocates draft budgets on GPU, changing query starts. Same total tokens does not imply unchanged per-request boundaries. A valid future extension needs its own mapping proof; do not synchronize the GPU merely to make a cheap CPU heuristic work.
5. Place a permitted request permutation before gathering all derived batch state, or rebuild every dependent mapping coherently. `gather_batch_req_state:1284–1364` derives request IDs, indices, scheduled tokens, draft counts and prefill status together; `prepare_inputs` derives query/logit spans and adaptive state; `prepare_attn` gathers block tables and slot mappings from request indices. Permuting hidden rows alone is incorrect. Sampling runs once on merged full batch; `_slice_input_batch` explicitly carries full-batch logits/draft fields unchanged.
6. Keep graph shape/address ownership, per-ubatch workspace lanes, padding flags and complete model output reassembly intact. Preserving counts is necessary, not a full capture proof. Do not move physical KV data; change request order and consistent metadata only.
7. Preserve existing yield/collective order. `ubatching.py` uses a fixed thread/event handoff; each layer still dispatches/composes in the same microbatch order. Rank-local request membership may differ normally, but adaptive microbatch ordering must not follow local completion-time decisions. Changed expert row order can also affect numeric behavior; require later differential checks.

## ROI falsifiers

A lower maximum context sum is not a latency result. Serial total work is unchanged; no exposed overlap means no gain. Rank-wise balance may simply move waits to another collective or the other microbatch. Producer indexer fraction, padded dense GEMMs, expert skew, graph shapes, sort/staging overhead and critical-path phase timing all govern benefit. No target imbalance or available headroom has been measured. Use existing Mooncake/agent75 only after proving eligible exposure, and preserve fixed service objectives and tails. No new benchmark is justified solely by this paper.

`partition_falsifiers.py/json` executed four integer counterexamples: odd graph midpoint, CPU vs compacted boundaries, context-only greedy1/3 request split violating equal DP shape, and a balanced proxy with unchanged serial total. These are source-derived adversarial models, not actual graph/collective/adaptive-policy tests.

## Relationship to prior work

The examined prior set has no exact context-weighted request-membership partition card. RUNTIME-R2-02 moves the first DP agreement earlier; this proposal preserves it. Earlier AT02 changes attention query grouping for load reuse; this proposal changes DBO batch membership for pipeline balance. Neither provides target performance evidence. A new deferred identity may be appropriate if the candidate states this restricted intervention and gates, rather than claiming turnkey CMR or generic scheduling novelty.
