# RUNTIME-R2-03 revision: selectively prune unfinished-prefill draft work

The original direct-port rejection in REPORT.md/candidates.json is preserved. **Its blanket assertion that all aggregated DSpark proposals have a verifier consumer was too broad.** Reviewer-guided source inspection identified a meaningful partial transfer from Herschel §9.3. This revision supersedes that statement; it does not establish performance or safe removal of an entire forward.

## Evidence that some proposed IDs are unused

Pinned c4557869393db4d75c483d92edd02a5125500883:

- `v1/core/sched/scheduler.py:2651–2655` ignores draft IDs for `request.is_prefill_chunk`.
- `v1/core/sched/async_scheduler.py:34–35` skips speculative placeholders for such requests.
- `v1/worker/gpu/input_batch.py:441–444` returns before draft-token insertion while `seq_len <= prefill_len`.
- `v1/worker/gpu/sample/sampler.py:190–198` gives unfinished prefill no sampled token.
- `gpu/spec_decode/dflash/speculator.py:681–686` nevertheless chooses the next prompt token as anchor when `num_sampled==0`. The proposer prepares and executes query forward for all request rows (:599–622).
- `gpu/spec_decode/dspark/speculator.py:249–268` executes backbone then sequential Markov sampling. The proposal is therefore narrower than turning DSpark off: skip unused query-generation work for unfinished prefill while retaining real prompt-context preparation.

## Why ignored IDs are not enough

1. **Required context KV is inside the full CUDA graph.** `_prepare_graph_forward:192–205` combines target hidden states, publishes context anchor and stores context KV. `_prepare_graph_replay:208–237` only eagerly handles rows beyond graph capacity. Simply skipping the graph drops the prefix rows it owns. A context-only path must cover the complete target span exactly once, preserve rejected/PAD/null-block and sliding-window semantics, and retain graph staging buffers.
2. **Query KV writes exist.** Query slot mappings are real when resident, and the query backbone writes its own attention KV. Need proof that next true context precompute overwrites every future slot before any subsequent read, including tiny chunks, chunk finalization, shared caches, page reuse and eviction. Noncausal DSpark windows include the whole query block, so prefix/slot bounds matter.
3. **Confidence has a hidden consumer.** `adaptive_verification.py:256–280` copies all rows into a double buffer; budgets read stale values at :309. A pure CPU state-machine illustration (`cpu-confidence-lifecycle.py/json`) shows first-decode budgeting can read the penultimate unfinished-prefill confidence after final-prefill record. It is not a live execution test, but refutes the claim that all head output is necessarily dead. Preserving frozen adaptive verification behavior may prevent skipping this head/backbone. Alternatively redesigning the confidence transition is a separate policy change, requiring explicit comparison, not silent substitution.
4. **RNG must be audited by actual implementation.** DSpark calls Gumbel with seed and `sample_pos-1`; `sample/gumbel.py` derives keyed randomness from seed/position/token offsets and speculative column. No simple global-generator advancement is evident in this inspected path. That supports a possible stateless skip, but watermarker/alternate sampling and any RNG state side effects need separate proof. Exact greedy equality and stochastic distributional correctness are separate contracts.
5. **EP and other side effects:** every rank must enter the same collective sequence. First scope is all active requests on all ranks strictly unfinished prefill, with explicit idle-rank handling; do not gate on only local `num_sampled==0`. Preserve EPLB bookkeeping, confidence state, logits cache, callback/watermark state, KV-save finalization and cancellation/preemption behavior. Never skip final prompt chunks, EOS-bearing output, or normal decode.

## Repaired hypothesis and stage

**Conditional hypothesis:** when an entire DEP group executes strictly unfinished prefill, a context-only DSpark path can avoid genuinely unused query backbone/Markov work without changing required cache, scheduler, adaptive-confidence or sampling state. This may lower cold TTFT and the blocking time imposed on other requests. It may have little relevance to long-output ITL if eligible steps are rare.

**Status: advance CPU dependency diagnostic; defer implementation and service qualification.** The confidence consumer is a concrete obstruction to full skip under the present adaptive configuration. A smaller removable component may survive; no claim that a complete query forward is currently removable.

Fastest no-GPU screen:

1. Pin exact effective runtime and confidence mode. Reconstruct predicates from CPU progress and scheduler outputs; do not read `num_sampled` back from GPU.
2. Produce live-out graph for query KV, IDs, logits, confidence, RNG and EPLB. A state consumer invalidates removal unless reproduced exactly by retained work.
3. Validate context-only slot coverage symbolically across chunk partitions (including chunks shorter than draft5, exact final boundary, window and page boundaries, dummy/idle rank and preemption).
4. Replay existing CPU scheduler logs if available to measure all-rank eligible-step frequency. Without logs the workload fraction is unknown, not 100%.
5. Estimate upper bound from existing synchronized timing only: eligible critical-path query work divided by full workload time, minus retained-context/coordination cost. No timing data currently supports a percentage.

Future tests, only after GPU authorization: exact target-only/DSpark correctness on chunked vs unchunked prompts; baseline vs context-only state parity before first actual draft; seeded stochastic output/distribution check with same confidence schedule; repeated paired agent-p75 and Mooncake with cold/warm breakdown, TTFT and p95/p99 ITL guards, per-step eligible/skip counts, complete draft stage time and end-to-end goodput. Existing benchmarks suffice if their actual chunk schedule exposes all-rank unfinished-prefill steps; add a narrow chunk-boundary differential test for correctness, not a new headline serving workload. Stop if skipped outputs affect later budget/cache/RNG or if no exposed savings remain.

This repair demonstrates the intended synthesis behavior: retain the source paper's useful partial mechanism, then audit the actual side effects instead of rejecting the whole idea because its original deployment used P/D.

## Head decomposition after root challenge

`_sample_sequential` computes each next parent from the preceding sampled draft. Confidence receives `sample_hidden` plus the stack of parent Markov embeddings. Preserving five learned confidence values needs the first four sampled tokens; deleting all dense vocabulary projection or sampling does not preserve this state. In the trained-confidence-head mode, the acceptance estimator is disabled (`load_draft_model:106–113`). A potential residual is omit only terminal fifth-step logits/Markov-bias/Gumbel while retaining its parent embedding and all confidence evaluation. The final sample is not itself a parent in this five-step head. This still requires proving logits/proposal buffers have no consumer on nonfinal prefill, handling top-k/watermark paths, and a separate partial graph; it is not currently implemented or promoted. With acceptance-estimator fallback, confidence can depend on logits and this simplification may fail.

C025 already found only modest component-level savings for the complete five-step sampling call. That is counterevidence against spending substantial effort on one terminal step at a subset of prefill steps; its microseconds cannot be used as a target-specific gain estimate. This narrow residual is lower priority unless source/runtime timing proves material exposure.
