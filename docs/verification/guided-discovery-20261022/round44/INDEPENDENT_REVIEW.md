# Independent round44 review

Reviewer: guided_adversary. Source/receipt review only; no online queries, GPU, allocator execution or live topology inspection.

## Verdict

No blocker to the zero-new disposition. The bounded source audit rules out the proposed removal of per-request CUDA allocation/remapping in the inspected ordinary methods; it does not prove hardware translation is free. Conditional paper components are retained rather than rejected wholesale. No new card or selection transition is warranted from these sources alone.

## BOOST transfer audit

The retained v1 paper describes bandwidth-proportional **accesses per wave**, not merely a global fraction of allocated bytes. Its measured Grace-Hopper bandwidth and capacity results cannot be substituted for this planned B200 deployment's topology, host link or sparse read distribution. The paper itself discusses marginal PCIe benefit, small-MoE slowdowns and host reads breaking L2 reuse.

The source cache specs declare one KV head. This is shared KV storage, not the number of query heads: query-head parallelism does not create independently placeable KV heads. With H=1, BOOST's ordinary single-head-host assignment places the whole request's corresponding cache component in the host tier. Thus the unchanged policy loses the within-request head split on which the argument relies. The paper's shortage fallback can mix block types within a request; this does not restore a proven sparse-wave access ratio. A new request/block/selected-token policy is possible but unvalidated.

Target Mega attention consumes selected physical slots; a bandwidth fraction over all stored records need not match bytes accessed by any wave. Shared backing/group overlays and source-layer sharing further prevent treating head placement as an isolated tensor transpose. No actual hardware page size, physical contiguity, TLB pressure, or sufficient host bandwidth was established. Logical token blocks are not hardware pages.

## Existing allocator and Elastic KV

`worker/utils.py:564–627` has one ordinary device backing allocation and builds views; `block_pool.py:666–700` takes integer block objects from the free queue. This is an exact method-level observation. Optional allocator contexts, nested helpers, sleep and other runtime branches are outside that proof. The AST inventory is source structure, not a performance or allocator safety test.

Elastic KV's useful component is stable-address reserve reclamation. Its own cheaper small-prefill-chunk control is a strong competing explanation. TP1 does not automatically rule it out, but scarce target KV, activation reserve, and an actual chunk-size penalty are absent. The current source screen appropriately parks implementation until those measurements exist.

## PR60843: opening text versus implementation

The retrieved API head is `65a441b3b4764795d9975b46458ab929c470e459`; all11 changed-file patches are retained. In `csrc/cuda_view.cu`, allocation uses `cudaHostAllocMapped | cudaHostAllocWriteCombined`, obtains a device pointer, zeros it, synchronizes initialization and frees with `cudaFreeHost`. `gpu_worker.py` checks CUDA plus `is_integrated_gpu(local_rank)` and rejects sleep. `allocate_kv_cache` selects this allocation only under the new flag; NIXL registers it as DRAM.

These patches agree with the fresh body and contradict the older local body describing `cuMemCreate(HOST_NUMA)` and supported sleep. The author correctly preserves both revisions instead of treating the old opening record as code evidence. The integrated-GPU admission and RDMA-staging problem do not establish a portable B200 HBM-bandwidth optimization. Source inspection is not reproduction of the donor's reported performance or proof that every unchanged surrounding call site is correct.

## Useful next evidence and stop rule

Reopen BOOST only with a concrete compatible allocation/ownership plan, actual target sparse-wave access mapping and existing bandwidth/capacity evidence. Reopen elastic reserve only with evidence of both scarce KV and a meaningful small-chunk penalty. If these records do not exist, park; another synthetic page-ratio example would not improve qualification. Standard agent-p75/Mooncake serving metrics remain appropriate once an eligible implementation exists; mapping telemetry is needed for attribution, not a replacement benchmark.

No service latency, capacity win, hardware mapping, or runtime compatibility was inferred from AST assertions, donor headlines, or source byte counts.
