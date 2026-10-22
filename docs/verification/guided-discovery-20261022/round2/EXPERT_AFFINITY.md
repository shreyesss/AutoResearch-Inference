# Round 2 — expert-affinity routing and a topology falsifier

This separate checkpoint does not change round1's four-card yield. One new intervention was considered deeply: M05, **deferred**, with no implementation or performance qualification. No GPU work.

## Adaptive query

After M01 reached a source-supported but trace-limited state, the next actual OpenAlex search changed emphasis from communication kernels to `MoE serving dispatch routing overhead`, June1–October22. Eight results returned without provider errors (`../paper-search-04.json`). DA-MoE was a duplicate; Gimbal related to prior pressure routing. ELDR supplied a different mechanism worth inspecting. The remaining abstract screens and reasons are in `tool-use.json`.

## M05: expert locality across independent deployment groups

[ELDR](https://arxiv.org/html/2607.00466v1) derives expert footprints at prefill and routes at the prefill/decode handoff. Its strongest transferable idea is grouping requests with similar expert demand while retaining a load guard. The source uses MI300X and other models; its EP experiment also changes per-decoder expert placement. It does not isolate a simple frontend-routing win on our configuration. Some language cases have worse tail latency despite median gains. Its selection signal appears *after* prefill, which matters for feasibility.

The target plan has two independent DEP4 model groups. Within either group, four DP request streams feed the same expert-parallel execution. Moving the same requests among those four ranks does not itself shrink the collective's expert set in the same round. It may change communication source locality or scheduling, but that is a different mechanism. To pursue the paper's working-set mechanism, request assignment must change **which independent model group** sees which requests, or change temporal batching.

### Executed CPU structural discriminator

`ep_union_discriminator.py` checks all24 permutations of four synthetic requests within one EP group. The expert union stays `{0,1,2,3}`. Across two independent groups, a mixed grouping has total8 distinct expert memberships while affinity grouping has4. This is set arithmetic, not latency, actual target traffic, a 2x speedup, or a proof that affinity helps EP rank balance. The same-round assumption is explicit.

### Actual source check

Pinned `vllm/v1/engine/core_client.py:1738–1801`, `DPLBAsyncMPClient.get_core_engine_for_request`, scores local unfinished requests against waiting/running counts, adds a KV-pressure queue penalty, and rotates ties. There is no expert-footprint term in the inspected function. This is internal DP routing; it does **not** prove how the external two-group router is configured. The MegaMoE shared-buffer source encodes source rank/token/top-k metadata and gathers expert work across its EP peers, supporting the single-group distinction.

### Why it is deferred rather than dressed up as an easy win

1. The current aggregated setup has no established post-prefill group reassignment path. Adding KV migration or PD disaggregation solely to obtain the signal is a large extra intervention.
2. A prior-turn session signature might inform future routing without PD, but predicting current expert demand from history is a new premise needing retained traces. It is not the paper's validated current-request signature.
3. Only two independent groups allow less partition freedom than the source's multi-decoder pools. Expert skew, stale signatures, queue imbalance and lost prefix affinity can dominate weight reuse.
4. Bounded local artifact searches found proposal/source references, not actual per-request physical routing traces. This is not proof no trace exists remotely.

Selective reuse remains legitimate: keep the footprint representation and cache-coherent accounting, omit a wholesale PD architecture change, and consider historical signatures only after verifying predictive value. This is related to prior rank affinity/Gimbal; it earns no new accepted count until a distinct target-compatible signal and routing point are demonstrated.

## Future evaluation only if the premise is established

Use the current external group router as the control, including its cache/load policy. Reuse Mooncake session/prefix/burst traffic and agent-p75 if they preserve real semantic payloads. Synthetic random-token workloads cannot validate domain-conditioned expert overlap. Only if the existing payloads lack that exposure, add a held-out semantic mix with matched lengths and arrivals, documenting this precise coverage gap.

Measure the frozen service objective and tails, TTFT, prefix hit rate, queues, expert union and physical-rank imbalance. Preserve model expert choices and outputs. Retain placement-only and load-only ablations to distinguish grouping from expert remapping. No calibration or GPU trace collection was performed.
