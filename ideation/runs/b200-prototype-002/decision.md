# Hypothesis shortlist

Untested proposals. Publication novelty is not established.

Citation checks: PASS

## H01: Ancestry-preserving prefix-cache admission with ghost hashes

**adaptation · confidence Moderate in the cache invariant and plausible failure mode; low in workload benefit. · Low-to-moderate for a CPU lifecycle prototype; low for serving integration until pinned hybrid-group and asynchronous-commit semantics are resolved.**

Under local KV pressure, retain complete reusable prefix blocks and decline optional cache writes for an unproven private suffix. Record each declined block's exact hash and parent hash in a bounded metadata-only ghost table. If the block is recomputed on a later request, promote it only after its parent is resident and all required cache groups can commit it. Once one block is declined, decline its descendants for that trajectory until a later request rebuilds the contiguous admission frontier. Active generation KV remains allocated normally.

**Nearest prior art:** The open #51981 PR supplies request-level no-store; RR-Evict proposes tail-first reclamation for agent histories; open #54625 and #58837 reorder waiting-request admission; PEEK proposes queue-informed protection. A write-admission policy at the contiguous block frontier is a narrower adaptation. None of these sources proves a gain on the target deployment.

**Proposed addition:** Add bounded ghost metadata and a per-trajectory admission frontier at completed-block commit. Promote only after a repeat exact hash is observed through recomputation. Treat the cache-group bundle as the admission unit: publish a prefix hit only after every required group has committed the same complete token span. For asynchronous commits, use a completion fence and generation identifier before publishing; cancellation or speculative rollback invalidates pending writes and ghost observations from uncommitted tokens. If the pinned cache manager cannot provide this lifecycle, disable the policy for that configuration.

**Code surface:** V1 block-pool commit and eviction hooks, hybrid KV-cache group coordinator, asynchronous cache-commit completion, and per-run cache accounting. Exact pinned-file locations remain unknown.

**Strongest objection:** Declining a suffix may discard precisely the block needed on the next agent turn; ghost metadata cannot supply its KV and promotion requires recomputation. The extra policy may lose to simple request no-store or tail-first eviction, and no supplied B200 block trace establishes avoidable eviction.

**Cheapest test:** Ghost-hash probation with ancestry-preserving promotion; keep checkpoint, precision, sampler, cache preparation, and active backend fixed within each topology.

**Control:** Stock admission, #51981-style request no-store, and RR-Evict-style tail eviction at equal effective KV capacity and identical request order.

**Reject if:** The lifecycle test violates contiguous group commits, CPU replay does not reduce recomputation against the strongest static control, or matched serving loses after scheduler cost.

**Revision:** Explored request-level no-store, RR-Evict tail eviction, queue admission ordering, and block probation. No-store fails to distinguish reusable and one-use segments within a request; a capacity-matched CPU replay is its cheapest falsifier. Tail eviction cannot prevent pollution before reclamation; the same replay compares its recomputed tokens. Queue ordering needs eligible waiting peers and may delay cold requests; a scheduler replay checks both conditions. Retained probation with explicit ancestry, recomputation-based promotion, group commit, and async rollback rules.

Evidence:

- `github:vllm-project/vllm:51981` (context): Request-level no-store is an existing comparator.
- `arxiv:2609.32278` (context): The abstract motivates retaining contiguous agent prefixes under pressure; it does not validate this admission rule.
- `github:vllm-project/vllm:48401` (supports): Promotion must wait for a complete recomputed block.
- `github:vllm-project/vllm:51820` (challenges): Asynchronous and speculative paths require a commit fence before hash metadata becomes usable.
- `github:vllm-project/vllm:58837` (challenges): Cold-request TTFT and scheduler overhead remain necessary checks for cache-aware alternatives.

## H02: Payback-gated expert-placement commits

**adaptation · confidence Moderate in the migration-versus-skew tradeoff; low in target benefit. · Low. A host policy replay is straightforward, but safe migration integration requires backend and memory qualification.**

Keep a computed EPLB placement plan pending until recent rank skew is likely to repay migration and the serving state can tolerate the commit. Change the timing of weight movement and map publication, without changing the placement algorithm, token routing, or expert precision.

**Nearest prior art:** Open #62009 adds asynchronous EPLB work, MegaMoE mapping fusion, and a migration backend; open #61839 adds a rebalance cap; open #59168 describes online placement and replica routing. These are direct controls. #62009's GB200 multi-node, decode-only result does not establish single-node B200 transfer.

**Proposed addition:** Add a pending-plan state and payback gate to the EPLB controller. The first implementation uses a quiescent all-rank serving boundary for in-place migration: drain in-flight forwards and graph replays, agree on plan version and source map, migrate weights, verify each rank's destination rows, then publish the new map version before serving resumes. Before any weight mutation, timeout safely discards or defers the plan and leaves the old map active. After mutation starts, a failed collective must fail closed and recover from a known placement or restart; it cannot claim to roll back merely by restoring the old map. Shadow slots are an optional alternative only if measured free HBM supports them.

**Code surface:** EPLB plan state, migration scheduler and communicator, per-rank weight/map version tracking, and the active MoE backend's map publication path. The pinned active backend and #62009 base/head are unresolved.

**Strongest objection:** Single-node migration may be cheap enough that gating only prolongs imbalance, while quiescent in-place migration may stall serving and shadow migration may exceed HBM. #62009 already removes host work from the decode critical path. Durable rank skew, migration payback, and support in either B200 layout are unmeasured.

**Cheapest test:** Same placement algorithm and migration backend with only the pending-plan commit gate added.

**Control:** EPLB off, best fixed placement, qualified existing async cadence, and a rebalance cap at equal redundant-expert memory.

**Reject if:** The component test finds no durable skew, insufficient HBM or migration payback, or matched serving loses to the best fixed/async/capped control.

**Revision:** Explored enabling existing EPLB, a fixed rebalance cap, per-token replica routing, and a payback-gated commit. EPLB activation is existing work; a component test of skew versus migration cost can falsify its value here. A cap is simpler but cannot react to changing load; a host cadence replay is its cheapest comparison. Replica routing overlaps #59168 and needs redundant capacity; a memory and routing component check can rule it out. Retained commit timing with a quiescent, versioned in-place protocol and safe defer/discard before mutation.

Evidence:

- `github:vllm-project/vllm:62009` (challenges): Existing work already addresses a major source of EPLB overhead.
- `github:vllm-project/vllm:62009` (challenges): The reported cross-node migration advantage is not a single-node B200 prediction.
- `github:vllm-project/vllm:61839` (supports): Commit frequency and timing can affect service latency.
- `github:vllm-project/vllm:61839` (context): A simple rebalance cap is a strong low-complexity comparator.
- `github:vllm-project/vllm:50647` (challenges): Improved rank balance can still lose total throughput after migration.
- `github:vllm-project/vllm:59168` (context): Placement refresh and replica routing are existing alternative mechanisms.

## Comparators

- Historical baseline: vLLM ac9126e58aa7bbab1856ba6593ba4d5003fea516 and DeepSeek Serve 2e6fa287d90adf7318ad314de27aa2f595aac821. Refreshed configuration and later main-branch availability are separate from inclusion in these pins.
- DEP8 and two DEP4 are separate eight-B200 topology controls. Match checkpoint, request bodies and arrival order, cache preparation, concurrency, precision, KV format, MTP/DSpark state, active MoE backend, sampler, and quality scorer within each comparison.
- Open #62541 targets main base aa3564ceefbd605f1d28238fa0fbbb964201c6b8 at head 64d4d308b50432449b25fdd4f73576f98b5ae5a5 and changes guide text only; its validated recipe is not thereby in the historical baseline.
- Open #62073 is stacked on woosuk/beam-fused-allreduce base 4fb4e7530ef9b2b558c842853edb6c7bb087d7ea at woosuk/beam-moe head 86a5bbe75a7971275952477bb1ce03e715bcc339. A supplied comment reports conflicts. Its merge_commit_sha field is not proof of merge, and its Beam paths are not V4.1 serving evidence.
- Open #62009 has no supplied base/head SHAs; its inclusion in either pinned deployment is unknown. The later #62073 flashinfer_moe_ep.py body cannot establish the pinned B200 backend.
- For H01: stock cache admission, #51981 request no-store, RR-Evict tail eviction, and #54625/#58837 waiting-queue policies. For H02: EPLB off, best fixed placement, qualified async cadence, #61839 rebalance cap, and #59168 routing if applicable.
- No speculation and fixed DSpark depth remain quality and performance controls. The #62417 chat/tool report is for the 1017 checkpoint on SM120, not a demonstrated B200 failure.

## Rejected Leads

- SSD or FASER as a direct B200 port: supplied evidence does not establish the required scheduler, KV, hardware-placement, or active-backend transfer; #36037 includes a maintainer objection.
- Fixed-to-adaptive DSpark depth alone repeats the prior B200 decision and existing dynamic-k/adaptive-verification work; an unchanged activation is a comparator.
- CuTeDSL MegaMoE selection and #62073 decode-workspace behavior are existing backend work on an open stacked Beam PR, not a new V4.1 mechanism.
- FP4 KV or mixed expert precision from title matches lacks pinned B200 sparse-MLA and quality support; #50416's prefill regression is on SM120.
- Distributed cache-affinity routing repeats the prior B200 proposal and overlaps documented engine-aware consistent hashing; no target evidence separates avoidable misses from load imbalance.

## Gaps

- Two defensible cards survived the requested maximum of five; shortfall: three.
- No supplied B200 request, block, rank, or kernel trace establishes cache thrashing, durable expert skew, migration payback, or the winning topology. These are experiment questions, not prerequisites to proposing the mechanisms.
- The pinned ac9126e58aa7 flashinfer_moe_ep.py body is absent. The later #62073 file and diff cannot identify the pinned active backend, EPLB path, or cache lifecycle.
- Exact repeated-prefix overlap, per-run cache hits, eviction reasons, preemptions, hybrid-group behavior, per-rank HBM headroom, and migration cost are unknown.
- The actual checkpoint, precision and KV encoding, MTP/DSpark configuration, active backend, and chat/tool quality must be resolved before matched comparisons. No numeric speedup is predicted.
