# Round 44 — GPU page mapping and KV allocation: zero-new screen

## Decision

**No new hypothesis promoted or created.** Recent papers supplied useful conditional components, but none yet establishes a missing, worthwhile operation on planned Flash-1017 / `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, B200 TP1/DP4/EP4. This is a bounded source screen, not evidence that GPU translation is free or that the literature has no applicable idea.

One dated arXiv query returned nine papers. Two were read at mechanism/evaluation-section depth; the other seven received explicit abstract dispositions. Three local PR opening records were imported; one fresh PR head and all changed-file patches were inspected. Zero GPU calls, serving changes, model executions, numerical-output tests, or canonical mutations occurred.

## 1. What is already implemented

The ordinary runner path calls `allocate_kv_cache` during initialization (`attn_utils.py:398–430`). That allocator obtains **one backing device tensor** with `torch.zeros`, then builds layer views over it (`worker/utils.py:564–633`). The code explicitly supports overlapping groups and block/layer strides. It does not allocate a new CUDA tensor per request in this function.

The request-side block pool hands out integer block objects from `free_block_queue.popleft_n` (`block_pool.py:666–700`). Therefore an idea framed as eliminating repeated CUDA allocation or virtual-memory remapping on every normal token/request would target work that is absent from these audited methods. Nested helpers, optional allocation contexts, HiSparse, and live overrides remain separate paths; this is not a global proof about all memory calls.

The target compressed attention and indexer cache specs both declare `num_kv_heads=1` (`attention.py:1195–1220,1263–1295`). Mega attention consumes sparse physical slot IDs over packed records (`flash_mla_mega_attn.py:305–340`). Its logical token blocks, group strides, record alignment and GPU hardware translation pages are different things. No hardware page size, TLB miss rate, physical contiguous placement, or allocator setting was measured here.

`source_audit.py/json` reproduces these narrow source facts with Python AST only. It imports no serving/backend modules. Its assertions are source-inventory checks, not allocator correctness or performance tests.

## 2. BOOST — selective idea retained, direct proposal parked

Primary source: [BOOST, arXiv:2609.13592v1](https://arxiv.org/html/2609.13592v1). Retained text SHA `b31a4488dd353540d2042f0935c1148a03fd0bc7a2bdbeb128f37116567c4b40`.

### Actual mechanism

BOOST obtains additional memory bandwidth from host memory alongside HBM. It places weight pages according to each CTA's access footprint and assigns KV blocks to maintain a bandwidth-proportional mix of head chunks across GPU waves. Its contribution is **tier placement and matching accessed work to that placement**, not removing hardware page-table lookup or replacing the ordinary free-list allocator.

For KV, it combines single-head-host blocks and all-local blocks; each request usually retains one block type. The paper states: **“All blocks of a request share one type”** (§4.3). It reorders the head dimension to support tier placement while preserving supported attention strides.

### Why current target cannot inherit the result

- The donor evaluates coherent Grace-Hopper host/HBM access. Its own §6.2 says PCIe has marginal benefit; no measured ratio/topology for our exact B200 node was acquired.
- Our packed MLA cache has **one KV head**. Under the donor's ordinary assignment, a single-head-host request is therefore all-host for that cache component. This removes the finer within-request head split; the donor itself avoids whole-request placement because context lengths can create tail imbalance. This is a source-derived incompatibility with the *unchanged policy*, not proof that a redesigned sparse-token policy cannot work.
- Sparse indexer-selected records and SWA accesses do not follow the donor's demonstrated dense head-chunk wave mapping. Preserving a global host fraction does not establish the fraction of bytes touched by each sparse wave.
- The paper reports small-MoE-batch slowdowns and sensitivity to host loads bypassing L2. Our small-row target path has no demonstrated surplus CTAs that hide host latency.
- Exact c455 allocator overlays groups in one backing tensor. A tier split must account for the complete shared address/stride layout, source-layer KV sharing, graph lifetime and coherent ownership. A donor head-only view transformation is insufficient.

**Retained component:** access-pattern-aware placement can be useful if an actually tiered target is introduced. **Reopen only** with a concrete compatible backing-memory plan, exact sparse CTA access mapping and existing evidence of bandwidth/capacity pressure. Do not manufacture host-access ratios or forecast the paper's gains. No special benchmark is justified today; a future eligible placement change would require standard agent-p75/Mooncake serving comparisons plus mapping/access telemetry to attribute results.

## 3. Elastic KV — mechanism works in donor, premise did not

Primary source: [Elastic KV Cache, arXiv:2608.23658v1](https://arxiv.org/html/2608.23658v1). Retained text SHA `cb3d5175db20435a196e8ceaed20a36d7788e6892d7bef4789ed1891b649959c`.

The donor maps an always-resident base allocation and an elastic allocation into one stable virtual range per layer. It lends prefill-activation reserve to decode KV capacity, drains the elastic blocks and unmaps them before prefill, then recommits with hysteresis. This is distinct from compacting fragmentation inside the KV pool.

The paper reports its own negative result: reducing `max_num_batched_tokens` provided more KV capacity at nearly the same TTFT than the elastic controller. Its live toggle costs were 3.8 ms to decommit and 23.8 ms to recommit. Those are donor A100/Qwen observations, **not B200 estimates**. Its TP dilution argument does not automatically exclude our TP1 deployment, but TP1 alone does not establish a valuable reserve or chunk-size penalty.

For our exact target, startup activation reserve, effective chunk sizes, preemption rates and sensitivity to smaller chunks were not established. The target's shared multi-group backing also differs from the donor's per-layer description. Retain the allocator technique and the negative-control lesson; defer implementation until existing baseline records show both scarce KV and an actual small-chunk penalty. A configuration-only chunk-size control must precede any complex VMM arm. No synthetic speedup or new hypothesis card is warranted.

## 4. PR triangulation caught an obsolete implementation description

[PR #60843](https://github.com/vllm-project/vllm/pull/60843), current observed head `65a441b3b4764795d9975b46458ab929c470e459`, is **open/unmerged at retrieval**. Its integrated-GPU host-pinned KV route solves RDMA registration/staging for GB10/Thor. The exact changed-file patch gates `is_integrated_gpu()` and rejects sleep mode; B200 is not its admitted target.

The local opening record (fetched October 20) described a `cuMemCreate(HOST_NUMA)` allocator and supported sleep. The newly retrieved opening body explains the revision to `cudaHostAlloc(Mapped | WriteCombined)` and rejection of sleep because the virtual address cannot be retained after free. The actual changed-file diff agrees with the **new** body. Both revisions are retained in the isolated corpus. This is a concrete example where keyword search finds a relevant-sounding PR but the current source and platform gate change the decision.

PR #55449 was read at body depth: its packed-MLA block alignment claim is scoped to hybrid GLM/Mamba and cannot be carried onto this target by keyword. PR #61025 was read at body depth: it profiles batch-sharded TP sampler all-to-all before KV sizing; planned TP1 has no demonstrated premise. No fresh diffs were fetched for these body-level exclusions.

## 5. Discovery behavior, omissions and yield

- Full compact prior inventory: **141 identities**, hash `e4b1696042533edc10fc7d6a1121a19041799ef72c8dd7364513be8b191c90c7`, two pages. N01 (SWA walking), MP17 (software slot mapping), LC03 (exact cache compression), RD01 (GPU weight-memory domains), AT03 (gather reuse) and host Engram caching are adjacent but do not establish a hardware-TLB benefit.
- Query dates: August 1 inclusive through October 23 exclusive. Query used LLM anchors plus virtual memory/address translation/TLB/page size. It returned **9 identities**, one provider call; no hidden relaxation or model calls.
- Canonical fulltext lookup found BOOST's already retained abstract and earlier query receipt. The new work fetched its versioned fulltext, not the abstract again. Elastic KV had no prior exact-ID match. Both fulltexts used the existing cached `Sources` API.
- Four local FTS queries were broad and produced many off-path excerpts. All returned unique IDs are dispositioned in `local-result-dispositions.json`; those not followed are **uninvestigated screens**, not technical rejections. Three exact records were copied through production `import-corpus`, preserving original revisions.
- Two GitHub API requests fetched fresh PR detail/files. The source-receipt hashes pin their observed bytes and head. No donor performance was reproduced.
- Initial `init --defer-snapshot` failed because current CLI disallows deferral for initialization. Retried ordinary local `init`, then copied hypothesis memory read-only. Empty pre-seed recalls are preserved and explicitly not used. `recall-setup.json` documents this.
- No second paper query was run: the source boundary and selected paper mechanisms resolved this screen more usefully than broader synonyms.

**Yield:** 9 paper identities screened; 2 deeper paper readings; one current PR diff examined; **0 new hypothesis identities**, 0 service-qualified wins. The useful outcome is excluding fictitious allocation/TLB work, preserving conditional reusable ideas, and detecting a stale PR design before proposing an incompatible port.
