# Separate review: Engram WKV look-ahead

2026-10-22. Reviewer: evaluation-gating subagent. This is a separately performed review within the same research session, with feedback exchanged during drafting; it is not blinded independent reproduction. No GPU work or node mutation occurred.

## Verdict

**Retain one narrow conditional hypothesis; advance source/CPU diagnosis, defer implementation and service qualification.** The intervention is to prepare selected Engram WKV projections earlier, using a legal overlap window. It is not to “enable Engram prefetch,” already present in the inspected source. No numerical target speedup is established.

## Evidence checked

I read the retained vLLM Engram/model source, SGLang PR #44028 body and diff, vLLM PR #59923 body, PR #56512 body, and searched prior hypothesis cards and historical Engram audit notes. All five local source files matched their recorded SHA256 hashes in `source-manifest.json`. Their declared commit is `c4557869393db4d75c483d92edd02a5125500883`, the node research fork; this review did not independently attest the deployed image to that commit.

- `source-audit/vllm__models__deepseek_v41__common__engram.py:1689` calls `self.wkv(self._batch.wkv_input(...))`; the fallback also calls WKV inside `forward`. The later gate consumes `hidden_states`. This supports the data-dependency premise that projection can be prepared earlier than the residual-dependent gate.
- `source-audit/vllm__models__deepseek_v41__nvidia__model.py:1027` already prepares batch embeddings before decoder layers. [vLLM #59923](https://github.com/vllm-project/vllm/pull/59923) already reduces lookup/exchange cost and produces MXFP8 WKV input. Re-proposing those operations would duplicate existing work in this source.
- [SGLang #44028](https://github.com/sgl-project/sglang/pull/44028) supplies a concrete staged implementation, not merely a paper suggestion. Its retained state is open. Its combined lookup/collective/projection result is not an isolated WKV ablation and does not provide our vLLM B200 gain.
- [vLLM #56512](https://github.com/vllm-project/vllm/pull/56512) reports near-neutral decode results for earlier lookup prefetch. #59923 reports under-1%-of-TPOT Engram overhead in its cache-resident fixed-output decode setup. These are strong reasons to avoid an optimistic forecast. The latter microbenchmark ends at WKV input, so it does not by itself quantify the separate WKV projection opportunity.

## Strongest support and strongest objection

**Support:** the proposed delta has an identifiable source location and an implementation analogue. It preserves the distinction between independent preparation and the residual-dependent operation. That is a meaningful improvement over a generic “overlap more work” suggestion.

**Objection:** independence permits reordering; it does not prove useful overlap. WKV may have too little exposed cost, compete with attention for compute/bandwidth, use a shared mutable GEMM workspace, or finish only after an earlier mandatory MegaMoE fence. Existing packed lookup/transport reduces the opportunity relative to the SGLang PR's baseline. The installed deployment may also contain different source.

## Conditions the draft must retain

1. **Backend workspace safety:** #44028 restricts projections to particular safe implementations. vLLM must establish its own WKV backend/workspace behavior; copying SGLang's flag is insufficient.
2. **Actual launch-stream fence:** #44028 joins before the persistent MegaMoE kernel on the stream that actually launches it. A join on the caller stream can leave work outstanding on another stream and threaten full-grid barrier progress. Any moved collective needs matching rank order, including idle ranks.
3. **Bounded look-ahead:** stage the eligible next Engram near its preceding attention window. Enqueueing every future projection can make the first MoE fence wait for them all and erase the benefit. A first-layer Engram has no preceding attention window.
4. **Replay/buffer correctness:** preserve per-layer readiness, allocator lifetimes, graph replay addresses and batch-specific prepared results. Do not reuse a prior request's projections. Global mode and padding eligibility must agree across DP ranks.
5. **Scope:** start with legal decode/target-verify shapes; mixed prefill and alternate transports need their own eligibility proof. Keep DSpark policy fixed when eventually comparing serving runs.

## ROI and cheapest next decision

For a single eligible stage, an optimistic removable-time bound is limited by both exposed WKV duration and the legal preceding overlap window. Added synchronization, packing, graph costs and interference must be subtracted. Real change can be negative. Do not clamp a regression to zero or replace unknown WKV duration with the PR's combined-path gain.

Across a workload, eligibility frequency, rank imbalance, actual useful committed tokens, queueing and interactions matter. Five speculative positions are not five committed tokens. No average component calculation establishes TTFT tails or goodput. Preserve null target gain until inputs support an explicit conditional calculation.

**Next CPU decision:** pin the relevant source/installed-image mapping; enumerate WKV backend and workspace ownership, exact producer/consumer/fence boundaries and eligible modes from source. A bounded dependency-order fixture can expose missing fences or stale-buffer reuse, but cannot prove CUDA-graph/distributed correctness or speed. If source identity is unavailable, mark applicability unresolved; do not fabricate a negative result.

**Later, only when GPU evaluation is authorized:** paired unprofiled agent-75 and Mooncake can assess serving effect. A separate targeted projection/event trace is justified because those service workloads do not observe WKV overlap or event ordering. Its cost must be separated from scored runs. If existing workload requests contain no eligible steps, report lack of exposure and use a specifically labeled diagnostic workload rather than relabeling it a standard-benchmark win.

## Duplicate risk and research disposition

The searched canonical hypothesis-card data and historical audit directories contain Engram storage, lookup prefetch and transport work. I found no direct WKV-only look-ahead card in those searched records; this is a bounded duplicate check, not a novelty claim. Retain the connection to prior Engram work explicitly.

Bounded replay and prefill-pressure scheduling already appear in earlier hypotheses. New workload exposure evidence should update those hypotheses with its new premise, not inflate the count of new ideas. Rank this WKV candidate by the information obtainable from the source check, not by an invented expected percentage gain.

This review supports **hypothesis-only / bounded CPU follow-up**. It does not authorize implementation on occupied GPUs, benchmark execution, deployment changes or promotion.
