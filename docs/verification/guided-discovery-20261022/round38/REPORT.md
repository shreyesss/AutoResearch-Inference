# Round38 — persistent execution search to FP4 weight packets

**One independently reviewed, distinct deferred packet-layout proposal; no implementation or service qualification.** Only online retrieval, read-only source inspection and standard-library bookkeeping were performed by root. No GPU/device query, native kernel import, model load, compilation or serving modification.

## Search changed direction rather than filling a quota

The first dated OpenAlex query, `persistent GPU kernel LLM decoding`, returned ten mostly unrelated kernel-agent, pruning and orchestration abstracts. The next explicit expansion used `persistent megakernel` and returned eight abstracts. An arXiv alternative was planned but not executed. The date interval was August1 through October22 inclusive. These bounded results are neither exhaustive nor a novelty test.

MonoMoE and MegaFlux initially had zero exact-title matches in compact hypothesis recall. **Both papers had already been read in round19.** Root verified their freshly downloaded fulltext bodies are byte-identical to the earlier retained bodies. They are revisits, not new source discoveries or independent corroboration. Two avoidable HTTP cache misses exposed a real weakness: isolated research workspaces have separate caches, and compact card recall does not search every linked investigation/artifact. A selected-source reuse tool improvement is being implemented separately; no caching improvement is claimed yet.

The papers remained useful for a specific new question: which weight-stream/layout changes remain absent beyond the target's existing persistent MoE kernel? Four bounded whole-corpus local FTS searches led to DeepGEMM PR394. No title or exact-source recall match was found for its packet mechanism; a separate reviewer compared it with RD01 and M01. Absence from these searches is not proof of scientific novelty.

## What the two papers establish, and what they do not

### MonoMoE, arXiv2609.04244

Selected sections describe weight-major execution, tokens on the tensor-core N dimension, resident execution and fused routing/quantization/GEMM/reduction. Its measurements use Hopper FP8 models, E256/top8 and mostly B1–8. Its EP discussion reports parity when fused dispatch/combine leave cross-rank waiting exposed. Whole-kernel performance does not predict our FP4/MXFP8 EP4 path.

The pinned target already says **“always swap A/B”**: `UMMA_N = BLOCK_M`, with a minimum multiple16 and two-CTA MMA. Therefore adopting SwapAB alone is not a missing optimization. Removing per-expert materialization would require a different distributed scheduling/ownership design, not merely switching matrix operands. This round does not reopen the old backend-selection or M01 tile-choice card under another name.

### MegaFlux, arXiv2610.00671

Its forward replica placement/weight-readiness pipeline can be selected without backward or gradient reduction. This is legitimate partial reuse. However its evaluated forward workloads begin at1K tokens/rank; end-to-end results concern large-chunk V4-Pro prefill, EP8 and spare replica slots. Planning/weight-transfer costs and static skew are not established for our small decode steps. The paper itself leaves runtime gating to future work. Keep the earlier optional placement lead; this reread adds no separate hypothesis.

Both fulltexts were retrieved from unversioned arXiv HTML and retained by content hash. Retrieval is not a claim that every paragraph was reviewed; this round read selected mechanism, evaluation and limitation sections. Prior reports and newly retained bytes remain separate evidence.

## WP38-01: preserve values; change expert-weight packet locality

Source: [DeepGEMM PR394](https://github.com/deepseek-ai/DeepGEMM/pull/394), open/unmerged at retrieval; exact head `d1e73685349137b5019ec7b75fe640509e89fbd4`. Retained API object, all nine file patches and six full files. Target dependency is `vllm-project/DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`, with vLLM `c4557869393db4d75c483d92edd02a5125500883` and Flash1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`. These are planned/source identities, not a newly attested running image.

### Mechanism

Current routed FP4 weights and their packed scale words occupy separate layouts. Cooperating CTAs consume adjacent output tiles, but their bodies/scales need not lie together in memory. The donor places each128×256 logical FP4 weight tile and its associated scale words into a17,408-byte packet:16,384 weight bytes plus1,024 scale bytes. Packet order is expert → output-tile pair → K tile → peer. Paired CTAs' packets are adjacent; 3D TMA descriptors load them. K128 consumes the two halves of a K256 packet.

The intervention reorganizes existing bytes. It does not reduce weight element count, replicate experts, change routing, remove weight loads or establish fewer measured HBM transactions. Potential benefit is better access locality and reduced exposed weight-stream cost. Extra descriptor/layout handling or changed cache residency could cancel it.

The donor's small-token arm also selects one epilogue warpgroup and EVICT_FIRST for routed packet loads. Those are separate mechanisms. The body reports a9.51% component improvement at one token/rank on four GB200s, H7168/I3072/E384/top6 and **no shared experts**; this is an author claim for the combined arm, not a local result or an isolated layout estimate. The body also says a clean-branch four-GPU rerun remains pending. It cannot supply our ITL ROI.

### Exact target geometry

The retained target config is H5120, intermediate2304, E384/top6, planned EP4 and FP4 routed weights with FP8 shared expert. Its two routed matrices are:

| Matrix | Logical N×K | Paired N groups | K256 tiles | Packets per expert |
|---|---:|---:|---:|---:|
| Gate/up |4608×5120|18|20|720|
| Down |5120×2304|20|9|360|

Both satisfy complete128-wide CTA pairs and K256 divisibility. This is a necessary static check, not compiled-kernel verification. Packet payload plus scales totals18,800,640bytes per routed expert across the two matrices, equal to the corresponding unpadded FP4/group32 byte accounting. Loader temporary allocations and any adapter duplication are separate.

The small-token branch tests `num_tokens * EP * top_k / E <= 8.5`; at the stated E384/EP4/top6 this means physical `y` rows<=136. Rows may include graph padding and speculative verification positions. They are not request concurrency, output tokens accepted, or the context length. No actual row histogram was recovered.

### Adapter requirements before this is an executable experiment

1. **Preserve target loader semantics.** The target fills already interleaved weights and UTCCP-transposed scales directly. Calling the donor's complete `transform_weights_for_mega_moe` on those finalized buffers would repeat transformations. Select only the packing step at an explicit post-load boundary, or implement one verified equivalent loader path.
2. **Own storage explicitly.** Donor weight and scale views alias one packet arena. Export the expert-contiguous arena once for migration/lifetime purposes, with stable reconstructed consumer views. Do not export overlapping weight/scale storage independently as if it were disjoint.
3. **Repair EPLB integration.** Current `get_expert_weights` requires first dimension=num_local_experts and contiguous expert views (or the existing scale transpose). Flattened packet counts fail that contract. A per-expert arena view and uniform layer schema are required; preserve scalar auxiliary parameters and expert ordering. A shape check is not proof that rebalancing, sleep/wake or reload works.
4. **Port narrowly to the actual dependency.** Keep the target's existing locality scheduler, shared-expert support, buffer/get_block_m API and default activation semantics. Replacing the entire dependency with the donor branch would change unrelated behavior. Audit descriptor ABI, capture lifetime and loader ordering.
5. **Shared experts need a control.** Shared FP8 weights keep ordinary TMA/cache policy, but choosing one epilogue warpgroup affects the kernel specialization including shared/combine work. The donor's no-shared result does not cover this case.
6. **No assumed composition with RD01.** RD01 concerns physical GPU memory-domain placement. Packet order is a different logical layout. Combining them requires compatible per-expert slices/domain ownership; their gains cannot be added.

## Evaluation that answers the actual claim

Freeze the target checkpoint/source/dependency, topology, quantization, shared path, router outputs and graph/eager shapes. Initial objective remains long-output ITL with separate tail, TTFT, correctness and error guards. No new serving workload is justified yet: use existing agent-75 and Mooncake for matched service comparisons.

The necessary additional diagnostic is **weight/scale mapping and lifecycle correctness**. Existing HTTP benchmarks cannot expose a mispacked scale, expert permutation, duplicate migration buffer or stale captured pointer reliably. First compare original and packet representations with the actual loader and kernel, including K128/K256, local expert identity changes, shared expert, padding, fallback and EPLB/reload paths that the experiment supports. Preserve per-rank outputs and expert statistics. The donor tests are source evidence only; none ran here.

For a later authorized performance study:

- **A:** original row-major weights, existing warpgroup/cache policy.
- **B:** packets, original warpgroup/cache policy. This isolates packing.
- **C:** packets + one epilogue warpgroup, original routed-cache policy.
- **D:** packets + one epilogue warpgroup + routed EVICT_FIRST, matching the donor small-row bundle.

A→D answers whether the proposed bundle helps; B/C separate causes if attribution changes the next decision. These switches must be explicit—the donor defaults automatically bundle them for small rows. Include the target's shared-expert path and actual physical graph rows. Alternate paired runs and preserve per-rank critical path, complete MoE elapsed time, completed decode progress, end-to-end ITL and guards. Do not substitute cumulative GPU busy time for latency or infer service gain from a single operator percentage.

**CPU-stage decision:** source geometry clears one compatibility check; the loader/EPLB ABI prevents a drop-in activation. Keep WP38-01 deferred pending the bounded adapter and exact exposure/quality checks. Unknown ROI is not filled using the donor9.51%. There is no measured gain, implementation-ready promotion or GPU authorization.

## Task-derived rubric and independent challenge

| Criterion | Judgment | Evidence or limiting fact |
|---|---|---|
| Missing target mechanism | Supported at source | Pinned kernel has separate row-major weight/scale loads; retained donor adds packet descriptors and layout. Existing SwapAB alone is not new. |
| Static compatibility | Necessary checks pass | FP4/MXFP8, EP4/E384/top6 and both matrix divisibility checks; shared path and loader ABI remain integration work. |
| Correctness-preserving intent | Plausible, unverified | Weight/scale permutation preserves bytes in principle; actual loader, TMA, EPLB and captured lifetime must agree. No numerical claim from geometry. |
| Useful service improvement | Unknown, worth bounded investigation | Repeated routed weight-stream path and donor small-row signal; no exact-target exposure, actual graph rows or shared-path timing. |
| Discriminating evaluation | Designed, not executed | A→D service comparison with B/C attribution, mapping/lifetime check added because HTTP tests cannot diagnose those failures. |
| Existing ideas / task constraints | Distinct scoped delta | RD01 physical domains, M01 tile choice and MF19 activations are separate; no novelty requirement, no GPU action. |

Independent review is `review/round38-agent/REVIEW.md`, manifest `ef8e8b8a7a279816df29e41edda396b6d9b736812c6c319e18ba495b50bace41`. Its standard-library coordinate/geometry checks cover target matrices, K128 halves, the136/137 threshold, expert ownership boundaries and non-idempotent UTCCP transformation. They are a reviewer-authored index model, not execution of PyTorch packing, CUDA/TMA, EPLB or numerical kernel correctness. The review agrees with deferral and explicitly rejects a turnkey port or transplanted speedup.

Within the **new** candidates, investigate WP38's ownership adapter before OP36's numerical-policy/backend change or NQ33's padding-only scheduling. This is an engineering investigation priority: the opportunity is a concrete absent layout, preserves trained values, and affects a repeated MoE path. It is not a prediction that WP38 beats PJ01/MF19 in serving gain. Keep the existing PJ01 source/exposure investigation active and do not add their estimated component savings together.

## Tool failures and honest coverage

- A canonical CLI recall waited behind the existing writer/publication lock; root terminated only that waiting recall and copied the hypothesis database read-only into an isolated state. Backfill was not interrupted.
- The first multiword compact recall is literal, returned zero; root then used separate terms and retained all pages. One console print was truncated; retained complete JSON was paginated and selected records reviewed. No completeness claim rests on the truncated display.
- An invalid `query-expand` command was corrected to `expand`; guessed documentation/source paths and one wildcard were corrected locally. These were operational failures, not empty scientific searches.
- The two paper rereads repeated existing bytes because isolated caches differ. The selected-source reuse fix is tracked separately. No provider billing or host-agent model cost is inferred from logical request counts.
- Four bounded local FTS queries are retained (17 MonoMoE hits, zero MegaFlux hits, capped30 weight-major hits, seven persistent-megakernel hits). Bounded zero/capped results do not establish absence/completeness. PR394's actual head and all patches were inspected; other retained PR results remain discovery leads.
