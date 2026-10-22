# Host scheduling discovery: conditional prompt-tail bookkeeping reduction

## Result

**One deferred, low-priority direction: avoid re-registering an unchanged prompt-tail prefix-cache alias. No implementation, endpoint result or numerical ROI.** This is a known upstream component from [vLLM PR 51333](https://github.com/vllm-project/vllm/pull/51333), not a novelty claim. The bounded source probe establishes repeated calls under specified cache geometries. The actual deployment's resolved cache groups are still required.

The strongest lead came from local PR triangulation after the online paper query failed. This round is not evidence that a recent paper supplied the final mechanism.

## Search and adaptation

Read the complete 138-entry compact prior inventory before searching. Prior N01 (`hypothesis:36d91144b8d619410f608f070e5f63ec4a29d4689b70852ace4754236ec60708`) removes scans of null SWA block-table prefixes on admission/free. This direction instead removes repeated prompt-boundary alias registration during output updates; it does not change eviction, prefix admission or replay policy.

One actual `researchctl paper-search` used arXiv, June 1 inclusive to October 23 exclusive, limit eight. It timed out; receipt has status failed and zero returned IDs, not a successful zero-hit literature result. Exit code was zero despite the failure status. `expand` recorded the host-authored plan; it did not invent queries. Two web tool calls then used three explicit host/control-plane queries. The first web receipt is represented by the query ledger and tool transcript, not a claimed full locally retained result; the second complete returned text is retained.

Recent relevant primary pages read:

* [ASPIRE, 2609.17943v1](https://arxiv.org/html/2609.17943v1), §4.1: mixed drafting/verifying forwards share the same target-model weights and MLP. Native DSpark has separate draft modules, so direct shared-forward reuse is unsupported. The per-request cost/acceptance policy overlaps existing adaptive-verification/C24 work. This is not a new host hypothesis.
* [DeltaServe, 2607.28848v1](https://arxiv.org/abs/2607.28848v1): spare-capacity LoRA training co-serving is outside the inference-only objective. Only abstract-level triage, not a full-paper rejection.
* Blink 2604.07609 was an already-rejected architectural replacement and outside the requested submission window. Edge/CPU-only model execution, PIM and agent tool-result caching hits do not establish this target's host decode path. Secondary blogs/search mirrors were discovery leads only, not technical evidence.

Three read-only canonical PR FTS queries returned 19 query edges. All returned bodies and dispositions are retained. Query `"CPU" "scheduler" "overhead"` found 51333; its primary PR object, exact head file, diff and comments were retrieved. Head `b00d7cc0829c3b1ca2fd638a3f9bb61b9fc9f837`; closed, unmerged. The retained comments contain only a bot message, so closure reason is unknown. Its broad originating experiment included a call-site guard omitted from the actual diff. The reported ~1% throughput at concurrency 500–1000 is not an estimate for our patch or workload.

## Existing host optimizations ruled out

At target `c4557869393db4d75c483d92edd02a5125500883`:

* `v1/worker/gpu/async_utils.py`: blocking D2H completion event already avoids busy-polling driver-lock contention.
* `v1/executor/multiproc_executor.py`: asynchronous output queue/thread already performs result completion when async scheduling is enabled.
* `v1/engine/core.py`: bounded batch queue already overlaps scheduling with asynchronous execution; heap freezing is already present.
* `v1/worker/gpu/dp_utils.py`: the draft can reuse the target's agreed `DPSyncState`. Removing a supposed repeated collective would repeat an earlier rejected hypothesis.

These are source capabilities, not confirmation of live flags or zero remaining host overhead.

## Exact missing operation

`FullAttentionManager.cache_blocks` calls the base cache update, then returns only if group `block_size == hash_block_size`. Otherwise `_cache_partial_tail_block` recomputes the prompt's final hash boundary, selects its owning block and calls `BlockPool.cache_partial_block`. The boundary does not change while output grows. The pool checks whether the key exists but still enters insertion bookkeeping. Current manager lacks the donor's `_registered_partial_tails` memo.

Async scheduler `_update_request_with_output` calls cache registration for RUNNING requests. The coordinator loops over caching-enabled managers. V4.1 compressed KV/indexer specs are `MLAAttentionSpec`, registered to `FullAttentionManager`; SWA specifies block size 32 before planning. The hash granularity defaults to the GCD of prefix-cacheable group sizes. Thus a resolved full-attention block of 256 with hash granularity 32 is a possible activating geometry, **not an attested runtime plan**. Planning may alter sizes or grouping, bounded replay can change cacheable groups, and exact launch configuration is missing.

EAGLE handling is per group. DSpark enables the global EAGLE-compatible path, but planning tags groups containing draft layer names; the coordinator propagates flags per group and only falls back to all groups when none were marked. Do not infer every target group has `use_eagle=True` from method=dspark.

For prompt length exactly 8192, block256/hash32 and a non-EAGLE target group, the registered boundary is 8160 on every eligible update. With the same geometry and EAGLE group, boundary8192 is block aligned and no partial registration occurs. With equal hash/block sizes, the caller skips the helper entirely. The saved agent-p75 workload targets 8192 input tokens, but rendered request token lengths and actual group flags are not measured here; Mooncake's length mix likewise requires saved effective inputs.

An additional potential simplification is skipping registration when interior hits are disabled: `partial_hash_hits_enabled` requires aligned Mamba state and V4.1 compressor state is circular rather than Mamba. **That does not yet prove all partial aliases are unused**: connector/event consumers and planning interactions need auditing. The conservative proposed arm is the unchanged-owner memo; blanket suppression is a separate unqualified refinement, not an accepted optimization.

## CPU evidence and limits

`partial_tail_probe.py` extracts the exact target helper using Python AST, with synthetic manager geometry and a recorder pool. Across 26 cases, four repeatedly called the same owner/boundary 1024 times; 22 were no-ops. Equal granularity, aligned boundary, insufficient computed prefix and missing block controls behaved as expected. This is a branch/call-count diagnostic, **not** the real allocator, alias-map correctness, full scheduler, timing or GPU test. No proposed memo implementation was tested.

## Next bounded gate and future evaluation

1. Recover resolved `KVCacheConfig`: group names/classes, block/hash sizes, prefix-cacheable flags, EAGLE flags, replay setting, connector/events. If no group activates the helper for real inputs, reject this deployment arm.
2. On CPU using real request/block-pool tests, compare baseline and memo through partial-to-full promotion, COW, hash replacement, preemption/free/reallocation, cache reset and aliases shared by multiple requests. An invalidated alias must be re-registered. Avoid assuming `(block_id, primary_hash)` is sufficient across all lifecycle changes merely because the donor uses it.
3. Count calls and actual elapsed CPU in retained scheduler replay, reporting per-output-update and per-completed-token denominators. No projected GPU benefit without exposed CPU time. If fraction f of the critical step is removable, ideal relative speedup is bounded by 1/(1-f)-1; f is unknown here.
4. Existing agent-p75 and Mooncake workloads are sufficient for eventual serving A/B if they activate the path. Retain request IDs, outputs, prefix hit behavior, retries, ITL/TTFT/E2E tails and goodput, plus scheduler/registration timing. Only add an explicitly labeled CPU lifecycle fixture; no new GPU workload is justified yet.

Implementation and service promotion remain deferred. No GPU queries, runtime patch or canonical mutation was performed.
