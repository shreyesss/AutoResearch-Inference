# Round52: communication redundancy and early expert execution

## Result

**Two concrete components remain deferred; zero are qualified for implementation or a serving-gain forecast.** The useful result is a source-backed narrowing: repeated activation pulls exist in the pinned expert loop, but an unusually close donor already found that eliminating them did not improve layer time. A second, larger prefill scheduling component can remove a real all-rank admission dependency, but it requires a different readiness and buffer protocol and does not establish a benefit for the frozen long-output ITL objective.

This is a source-plan audit of `DeepSeek-V4.1-Flash-1017@1bae0e1088993b9b82de08f59de5be5a34e42170`, `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, planned TP1/DP4/EP4 groups. It does not attest a live image or active runtime. No GPU, model/native imports, serving change, benchmark, or canonical state mutation occurred.

## 1. How discovery adapted

1. Read all **143 compact prior cards across three pages**, with a stable inventory hash, and retained 47 communication/routing/reduction matches. Prior DA01 refers to M01's routing-histogram tactic selection, not the similarly named Data-as-Flag method. The current re-audit parks that diagnostic pending physical receive evidence; its old accepted investigation label is not service qualification. A bounded campaign REPORT.md search for dispatch dedup/rank cache/ready-source/streamFFN wording found no earlier matching report after excluding this round; this is lexical coverage, not exhaustive semantic recall.
2. Authored and executed `expand`, then an August1–October22 OpenAlex query for redundant MoE dispatch/combine. Ten hits included old Weave/MegaFlux, host-PCIe designs, placement methods, CascadeEP and Zepp. No duplicate fulltext download for the old Weave/MegaFlux papers.
3. The exact target source showed per-expert pulls of the same source token. A second explicit query therefore focused on token deduplication. It produced ten hits, including four repeated identities. **20 query hits, 16 distinct canonical paper identities**, with all dispositions in `paper-dispositions.json`.
4. Four selected fulltexts were retrieved through actual `investigate` calls: CoMoE, CascadeEP, Zepp, and UBEP. The first CoMoE lookup found prior abstract records only. UBEP was selected to examine a different synchronization component after the dedup counterevidence; its OpenAlex publication is August11 but arXiv identifier is July. These dates are preserved, not conflated.
5. Canonical PR FTS was read-only. Four selected PR records were imported into the isolated state, then actual `pr-search` replayed the bounded subset. This replay is not a new full-corpus scan or a completeness claim. It found the decisive donor history: FI4688 introduced dispatch dedup; FI5374 removes it.
6. Retained all13 returned FI5374 file entries and available patches; inspected the selected TUNING/token protocol diffs and base/head `TUNING.md` and `token_comm.py` via code-only `investigate`. PR5374 is **open/unmerged** at this observation: head `a192faac9154ae9ef87b4db121a0577f62e2b48e`, base `6870e3fff46b1e768ad423ea48d286e6f3e250fe`, fork `inocsin/flashinfer`. Nothing here claims that branch is installed.

The four paper texts are retained unversioned arXiv HTML responses with content hashes; they are not revision-pinned paper versions. Citation expansion failed for CascadeEP and Zepp; their fulltexts succeeded. Bibliographic links were not counted as papers read. No new query was needed once the source/exposure decision was clear.

## 2. D52-01: duplicate remote activation pulls — real code delta, poor evidence for payoff

### What repeats in the target

The planned configuration has hidden size5120,384 routed experts,top6. The MXFP4 format dispatches FP8 activations with group32 scales into `fp8_fp4_mega_moe`; weights/routing/results remain expert-specific. The wrapper prepares input and routing then enters the fused kernel. [Pinned wrapper](https://github.com/callgideon/vllm/blob/c4557869393db4d75c483d92edd02a5125500883/vllm/model_executor/layers/fused_moe/deep_gemm_mega_moe.py)

The native kernel iterates over each destination expert's assigned token rows. It reads `src_token_topk_idx`, derives `src_token_idx`, then TMA-loads the source token into that expert's local ring row and separately copies scales. Two experts on the same destination rank selecting one token therefore execute repeated logical input pulls. Routing coefficients and output rows must remain separate. [Pinned kernel, approximately lines533–620](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/impls/sm100_fp8_fp4_mega_moe.cuh)

For this format a row contains5120 activation bytes plus160 scale bytes, before routing metadata. This is a representation size, not observed network traffic. Top6/EP4 alone does not guarantee duplicate *remote* pulls: repeated destinations can all be the source rank. Actual destination distributions, cache behavior and overlap are unknown.

### Selective reuse

CoMoE motivates sharing identical inputs, but its host-backed multicast addresses GPUs without direct P2P. Moving this NVLink path through the host is not justified. Zepp similarly merges identical inputs across an inter-node fabric; its NIC redistribution is unnecessary for the intended single-node EP group. The transferable component is simply a byte-identical per-destination activation/scale copy reused by several expert assignments. [CoMoE](https://arxiv.org/abs/2610.09424), [Zepp](https://arxiv.org/abs/2610.11158)

The FI donor implements a more specific version: choose the smallest destination expert as carrier, tag duplicate route words, wait for a release-published carrier row, then copy its local payload and scales. It handles repeated expert IDs specially to avoid same-expert wait cycles. These are useful implementation details, not a production proof. [FI5374 selected base source](https://github.com/inocsin/flashinfer/blob/6870e3fff46b1e768ad423ea48d286e6f3e250fe/flashinfer/moe_ep/kernel_src/sm90/pull_style_cutedsl_megakernel/src/src/token_comm.py)

### Strongest counterevidence

The exact head TUNING notes report both sender-election dedup and receiver-only rank caching within±0.1% full-layer-forward time on four clock-locked H200s, two interleaved rounds,26 buckets: dispatch was hidden by GEMM work. Grouped combine instead lost12–27%. These are **donor-reported component/system measurements**, not independently executed or B200 measurements, and they do not prove every future implementation loses. They directly refute an assumption that fewer transferred bytes automatically produces a win. [FI5374 head TUNING](https://github.com/inocsin/flashinfer/blob/a192faac9154ae9ef87b4db121a0577f62e2b48e/flashinfer/moe_ep/kernel_src/sm90/pull_style_cutedsl_megakernel/TUNING.md)

The target additionally recycles expert rows through `pool_token_idx % kNumRingTokens`. Current reclamation waits for its compute consumers, not hypothetical dedup readers. A donor carrier pointer cannot safely outlive its ring generation without a new ownership protocol. A stable per-invocation cache avoids that alias but adds HBM, local copies, election/readiness bookkeeping and potentially pressure on other buffers. A bounded fallback design must preserve graph-static capacity and forward progress.

**Disposition:** defer, below established direct compute opportunities until an existing exact-baseline trace shows exposed repeated-pull cost. Do not port simply because the loop contains duplicate loads. No compatible exposure trace was identified here; the bounded historical `round10-exposure-audit` already distinguishes old model/runtime aggregates from current component exposure, and was not recast as a new exhaustive archive search.

**Cheapest next check:** use any already-retained exact routing/timeline data to count repeated remote keys and distinguish communication wait on the critical path from hidden transfer. If absent, keep ROI unknown; source-derived bytes cannot replace it. Before a future GPU test, prove byte/layout ownership across ring wrap, masks, zero-token ranks and repeated graph invocations.

**Future causal arms, not executed or authorized:** unchanged baseline; bookkeeping-only control; same bookkeeping plus input reuse. Preserve tactics, routing, quantization and output accumulation. Keep agent-75 and Mooncake service tests. Add internal copy/wait attribution because client metrics cannot explain whether saved transfers were hidden; do not invent a new workload by default.

## 3. A52-02: start prefill expert work from ready source lanes

CascadeEP's separable inference component is source-lane readiness plus threshold-based batching: let completed attention replicas supply expert work while another replica is still in attention. The final arrival flushes remaining work. The paper separately adds opportunistic weight fetching; that mechanism is excluded from this initial proposal. Its implementation uses generation-tagged source–destination lanes, release/acquire visibility, grouped expert packing, inverse route maps, separate scratch and a common final layer boundary. [CascadeEP, §3.2 and AppendixC](https://arxiv.org/abs/2609.33252)

This is not merely overlap already present inside MegaMoE. The pinned target writes source indices/counts, performs an NVLink barrier before pulling, then waits for every expert's count high word to reach `numSMs*numRanks`. Those complete counts determine cumulative expert pool offsets, total M-blocks and scheduling waves. A ready-source implementation must replace those full-count dependencies with bounded lane-specific or dynamic task addressing; deleting the barrier would be incorrect. Existing ring-full and ring-empty progression, source metadata and final zero-work completion also need an explicit protocol. [Pinned scheduler, `fetch_expert_recv_count`](https://github.com/vllm-project/DeepGEMM/blob/a7a927731b109fdfec770df7c2a5be5d7e2216b5/deep_gemm/include/deep_gemm/scheduler/mega_moe.cuh)

The paper evaluated an **EP8 B200 prefill node in PD disaggregation**, different models/revisions, SGLang/DeepEP and split grouped kernels. Its threshold is hardware/model-profiled. The reportedTTFT gains cannot be assigned to c455 EP4 or long-output ITL. A fused kernel can lose efficiency when early tiles are small, and changed row batching can change floating-point reduction behavior even with identical weights.

**Disposition:** deferred prefill architecture lane. Distinct from CMR01's equal-capacity decode microbatch membership, N03's SM allocation and DA01/M01's tactic choice. The missing admission boundary is real; useful target skew and implementation value are unmeasured. No performance simulator was substituted for those facts.

**Cheapest next check:** source-contract design for immutable per-lane counts/offsets, generation signals, ring termination, masked/empty ranks and final flush, then inspect already-existing compatible all-rank attention/dispatch timestamps. Lack of skew or efficient ready-lane sizes can stop the branch before implementation.

**Future evaluation:** first prefill-only; baseline versus early-lane without threshold versus early-lane with threshold, no weight migration. Existing Mooncake and agent-75 supply arrival/prefix variation and TTFT; mixed-serving decode ITL is a guard. Only if their retained workloads lack eligible readiness skew would a controlled arrival-skew diagnostic be warranted. Primary long-output ITL promotion remains unsupported.

## 4. UBEP and other negative screens

UBEP contributes a useful dependency decomposition and a direct hardware-contract caution. Its Token-Flag Fusion proof requires a flag and payload to be observed together in a512-byte atomic remote DataBlock on CM384. The inspected NVIDIA target has separate TMA payload completion and release/acquire flags, not that proved transaction contract. Sentinel polling also requires excluding the sentinel from all admissible future payloads; checking weights/initial examples is not such an invariant. This rejects the **direct protocol transplant**, not all possible per-token readiness or a future separately proved encoding. UBEP's hop-aware NPU scheduler has no established matching EP4 hop asymmetry here. [UBEP §3.4](https://arxiv.org/abs/2607.06202)

The target combine waits for selected peer ranks' L2-completion tags and accumulates shared output first, then routed top-k slots. Zepp's grouped output pre-reduction would change this ordering and add exposed work. It was not bundled into D52-01. Existing native fused overlap, prior Weave/MegaFlux/placement work, PCIe/no-P2P systems, cross-node NIC strategies, training backward synchronization and learned algebra replacements are all retained as scoped exclusions, not erased from the search denominator.

## 5. Evidence and yield accounting

-20 query hits /16 paper identities /4 fulltexts; all abstracts inspected for disposition.
-143 prior cards read compactly,47 selected communication-related matches; later DA01 re-audit meaning checked separately.
-4 selected PR opening records, one exact PR API/files observation with13 file patches,4 pinned donor code reads; target implementation/scheduler/layout and model config retained from existing pinned source.
-2 deferred concrete interventions,6 additional scoped negative/covered branches; **0 accepted implementation candidates,0 validated experiments,0 ROI percentages**.
-No native CPU/GPU experiment or timing fixture was run. Hash/quote/source-contract checks are evidence-integrity and static analysis, not execution of a modified decoder.

Artifacts: `candidates.json`, `screened-negative-branches.json`, `paper-dispositions.json`, exact source/revision quote anchors, raw query/reader receipts, command journal, source export and frozen manifest. Only isolated local state was changed; no S3/VM/Git synchronization is claimed.
