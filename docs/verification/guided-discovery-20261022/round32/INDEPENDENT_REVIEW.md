# Independent CRAFT/CAP applicability review

**Verdict:** no newly qualified target intervention. The papers contain reusable planning ideas, but the current replay and communication proxies cannot qualify a Flash1017/c455 MegaMoE EP4 improvement. This is a source/CPU preflight verdict, not a failed GPU experiment or a rejection of all replica allocation/placement work.

## CRAFT integer replay counterexample

At donor968ecd, `run_bal_trials` takes each per-iteration logical count, applies `idist_slice // logcnt_slice.unsqueeze(0)`, expands the quotient to every valid replica, and scatters it to GPU totals. The inspected remainder never enters the scatter. Therefore the accounted total for count n and r replicas is r*floor(n/r), losing n mod r. This is a defect in that replay proxy's conservation, independent of whether the tensor values were stored as ints or exact integer-valued floats.

The scalar AST probe faithfully isolates this exact expression; it does not run the donor tensor placement solver. Its one invocation/two copies example is a legitimate arithmetic falsifier: all replay loads become zero, and the mean/max expression with equal epsilon returns1.0. Any realized integer assignment of that invocation onto one EP4 rank has balance about0.2500075. Do not label this a measured target imbalance or infer how often it occurs in our workload. The probe's260 cases and123 nonconserving cases are a constructed boundary set, not workload frequencies.

A remainder-conserving round-robin control repairs total counts but is not proof of native replica selection. Even replacing floor division with fractional n/r conserves expected mass without reproducing expected maximum/step latency: for one token/two replicas the fractional placement `[.5,.5,0,0]` yields a different balance than any realized one-token assignment. Qualification needs the actual per-step physical mapping/selection policy or a properly validated stochastic model, including padding, admission and rank/source provenance. Existing M01's missing physical receive histograms remain a blocker to a target-specific ranking.

Selective reuse remains possible: marginal replica benefit and a bounded per-layer memory budget are planning ideas. Recompute them with conservation and actual runtime semantics; compare against already available EPLB and placement-only controls. The exact V4.1 model metadata updater accepts one global physical/local expert count and applies it to every MoE layer (`nvidia/model.py1554–1574`), while Mega kernels require expert-count divisibility by rank. A donor per-layer allocation is not already a supported flag. It needs an explicit allocation/kernel/lifecycle plan and memory budget. No current memory pressure or enabled-EPLB configuration was observed in this review.

## CAP distinct-destination proxy does not describe this MegaMoE path

CAP §II-C explicitly assumes device-centric zero-redundancy transfer: send a token once per destination device, reuse it among colocated experts, locally sum expert outputs, then return one aggregate. This assumption is essential to its communication cost model.

Pinned DeepGEMM a7a kernel instead records token-topk assignments per physical expert (lines352–392). Its dispatch iterates each local expert's token range (440–539), recovers the source token and topk slot, and pulls activation/scales into expert-specific pool slots (550–600). Each L2 expert epilogue writes a separate BF16 result into `combine_token_buffer.get_rank_buffer(dst_topk_idx)` (1347–1366). The source rank subsequently reads/reduces the topk slots (1439–1477). Colocating two selected experts therefore does not itself remove one logical activation pull or merge their two return stores into one aggregate in this implementation.

This is **not** a measured NVLink-byte count. Repeated source addresses may hit cache or be served locally; source/destination ranks, memory topology, coalescing and hardware behavior affect transactions. Likewise, moving experts may change rank readiness and imbalance without changing the number of logical per-expert operations. The source disproves direct identification of CAP's distinct-destination count with native communicated bytes; it does not prove placement has zero possible benefit.

Selective reuse: co-activation traces can be a placement input if evaluated using this backend's actual expert/rank compute, traffic and readiness behavior. A donor device-deduplicated dispatch or local combine would be a separate kernel intervention with synchronization, precision/reduction-order and overlap costs; it is not supplied by changing placement alone. Retain lossless placement separately from CAP pruning, which changes selected computation/quality. Do not import paper headline speedups or its communication cost function unchanged.

## Minimum useful next evidence and stop rule

1. Existing provenance-pinned per-step routing/physical receive data with layer, source rank, selected topk and final replica maps; logical aggregate expert counts alone cannot establish CAP co-activation or physical traffic.
2. Exact planned runtime's enabled EPLB/replica memory/shape constraints. Distinguish two independent EP4 groups from an8-rank group or the donor CLI's default8-GPUs-per-node setup.
3. If these already exist, bounded CPU replay checks conservation, actual assignment and strong existing-EPLB controls before any allocation recommendation. If absent, park the target ranking; do not substitute arbitrary synthetic balance improvements for a service forecast.

The current source audit and integer falsifier warrant preserving a deferred planning lead or rejected direct-proxy transfer, not a new accepted service hypothesis. No GPU, model execution, online query, canonical mutation or runtime patch was performed.

## Frozen packet readback

Reviewed final REPORT.md after freeze and verified all30 declared artifact hashes/sizes. Independently recomputed every scalar count/remainder identity from the260 saved rows; this checks the small arithmetic receipt, not donor tensor execution. The report accurately retains zero new identities/qualification, scoped transfer objections and failed-search/export limitations. No correction required.
