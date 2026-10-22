# Round 107 — exact-support attention tiling, without another duplicate card

**Outcome: zero new formal hypotheses.** Tessera's logical-mask/physical-tile separation is a useful implementation reference. Its direct port does not match the target's token-indexed sparse reader. The potentially useful cross-query reuse component belongs to the existing AT02/QUILT direction; generic per-shape plan selection belongs to the existing tactic-selection family. No native correctness or performance claim follows from this read.

No GPU/device/model/native imports, builds, serving changes, canonical mutation or cloud operation occurred. Planned baseline remains Flash1017/c455, TP1/DP4/EP4. Source eligibility is not live backend attestation.

## Search adapted to actual prior coverage

Started with the complete retained 153-card inventory and 38 attention/indexer/prefill matches, then bounded standalone report recall. This historical inventory is not a claim about the current canonical count. Read the decisive round15 QUILT/JSSA, round60 MpFA, round62 tactic-selection and round100 producer-scheduling conclusions; prior rounds92/96 concern a different index-K projection operation.

Two normal `expand` plans and two actual online searches used explicit **2026-09-01 inclusive to 2026-10-23 exclusive** dates in structured fields and CLI arguments. Query02 records the executed query01 ID in `based_on`.

- arXiv prefill/sparse-attention plus kernel/softmax/load balancing returned ten abstracts. The strongest execution candidates JSSA and MpFA were already read in rounds15/60. Their mechanisms were not counted again. Other abstracts mostly changed selected support, weights, hardware or remote tiers.
- OpenAlex attention/softmax/pipeline/synchronization returned eight rows. It supplied the selected Tessera component and several non-serving/backward/evaluation papers. Two explicit identities overlap the first query, leaving **18 references / 16 paper identities**. OpenAlex's recent publication filter is not an arXiv submission-date filter: the VOLTA hit has an arXiv2511 identity, retained as evaluation background rather than represented as a new September submission.

All abstracts and dispositions are retained. Tessera had previously appeared only as abstract-level background in rounds17/37. The canonical source identity was reused with `import-corpus`; one selected `investigate` then fetched its fulltext. The tool followed an **unversioned** arXiv HTML URL derived from OpenAlex DOI metadata. The observed body, retrieval time, content revision and file hash are retained; this is not an explicit arXiv-version pin or proof of future freshness.

## Selected primary source and component decomposition

[Decoupling Logical Masks from GPU Execution for Dynamic Block-Sparse Attention, Tessera, arXiv2609.25869](https://arxiv.org/html/2609.25869), selected sections2–6 and evaluation scope.

The paper preserves a logical set of query/key interactions while changing physical execution:

1. **Coarsening** combines logical blocks into a larger physical tile and masks inactive entries before softmax. It trades operand/index reuse for redundant masked arithmetic.
2. **Refinement** subdivides logical blocks. Query-side subdivision creates independent query tiles; K/V-side subdivision traverses the same online-softmax state.
3. **Task organization** groups runs of active blocks, adjusts traversal and pipeline depth, or partitions a reduction over CTAs with a separate partial-state merge.
4. **Offline regime selection** ranks eligible precompiled plans, avoiding per-invocation exhaustive search. It still builds GPU mask metadata and may use scalar mask statistics for host selection.

These are separable forward execution ideas, so the video-diffusion origin is not a blanket rejection. However, preserving the mathematical interaction set is not proof of the target's floating-point result: traversal, partition maxima, normalization, probability rounding and output quantization can differ.

The paper reports native catalogs for A100, RTX4090, H100 and RTX5090, not a B200 catalog. Its headline request speedups and large online-search penalty describe its own mask corpus and runtime. They are not target forecasts. The retrieved fulltext exposes third-party dependency links but no identified author repository sufficient to pin its implementation in this read. No unverified repository was fetched or treated as the donor implementation.

## Exact target source comparison

Two existing code identities/revisions were imported and their exact bodies retained:

- `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, `vllm/models/deepseek_v41/nvidia/flash_mla_mega_attn.py`.
- `vllm-project/FlashMLA@5dceadbd9eabc9acfc547ef18ec8f7b14b980682`, `csrc/cuda_kernels/sm100/prefill/sparse/fused_norm_rope_attn_rope_cast_fwd/core_attn/kernel.cuh`.

### Physical width is already distinct from selected support

`_forward_prefill_mega:367+` obtains per-query TopK indices, plans request chunks, gathers compressed and SWA KV into a BF16 workspace, and combines their indices with their per-row valid lengths. `combined_topk` rounds `top_k + window_size` to a multiple of128 for storage. It then calls the fused prefill reader on those indices and lengths. Storage width is not the logical attention support.

In the dependency, `_make_outer_loop_args:451+` maps a query token to a job and computes `max(ceil(topk_length/B_TOPK),1)` physical KV blocks. The indices-generator warp at1215+ loads each selected slot, handles partial tails, tests whether the slot is inside `s_kv`, and publishes validity masks. Thus the native kernel already groups arbitrary selected token slots into physical blocks, rather than issuing one separate attention kernel for every logical token. Tessera's simple proposition “decouple logical block size from tile width” does not expose a missing stage here.

The current job maps one query token's head group to a CTA/cluster; heads are a separate dimension from neighboring query tokens. A donor tile's query dimension cannot silently be reinterpreted as target head count. Cluster launch control obtains later jobs; this is not an unexamined fixed-wave scheduler.

### Cross-query coarsening requires a different reader

To reuse KV across multiple query tokens, form a typed union of their selected physical entries and carry a per-query membership mask. Without that mask, a union changes attention support. Without careful identity, compressed and SWA entries or different requests can alias numerically equal indices. Repeated meaningful occurrences cannot be deduplicated merely because their values match.

That residual is precisely the AT02/round15 QUILT family, not a new Tessera-specific hypothesis. Round15 already supplies a selective exact intersection/private-tail construction and a pinned FlashInfer union-mask donor, while disabling its approximate tail pruning. Re-reading a different paper does not create another intervention.

The native prefill stage already materializes BF16 KV once per request chunk. Reader grouping could reduce repeated **reader loads/on-chip traffic**, not automatically eliminate the prior gather/dequantization or its entire cost. AT03's across-layer gather reuse remains separate.

### Output and numerical contract remain part of transfer

The reader performs RoPE-related work, sink handling, inverse output RoPE and FP8/scales output into the WO-A consumer layout. A generic BF16 block-sparse output cannot replace that interface without restoring all operations and their rounding boundaries. Split-K adds partial-state stores and a merge; support equality alone does not certify finite-precision equality. The selected work must preserve row/request identity, causal lengths, padded rows, graph buffers and sink contribution exactly once.

A different B_TOPK/pipeline configuration might still be faster. This screen does not prove current tuning optimal. It establishes neither a missing target configuration nor a legal lower-cost one; introducing a generic runtime selector would repeat round62 without new evidence.

## PR triangulation

Readonly retained opening-text recall used the newly exposed operation vocabulary: exact Tessera/ID gave no PR; sparse-prefill plus tile/split terms returned a bounded latest12. Three exact records were imported, then a normal `pr-search` replay inspected that selected subset. This is partial local coverage, not upstream absence proof. Selected body sections were read; complete bodies/revisions are retained. No donor head/diff was hydrated, and no claim relies on a body proving compiled implementation.

- **SGLang45452:** split MiniMax score-only prefill over K. Its useful condition is that no softmax state spans the split, so scores need no merge. That condition does not hold for an attention-output reduction. It may inform an indexer-specific study, but current target/indexer work is a separate already-investigated family. MiniMax GB300 timings and synthetic EAGLE configuration do not describe Flash1017.
- **SGLang45274:** explore additional divisors for TileLang sparse decode split counts, reducing partial results. This targets a GLM2051/66-tile partial-plus-combine path. The inspected target uses FlashMLA fused Mega attention, not that selector. Its own body notes split-dependent FP8 probability rounding; reported task accuracy is not proof of exact output parity.
- **SGLang37275:** SM120 sparse-prefill geometry tuning with explicit shape/version gates and interleaved measurement. Useful evaluator discipline, but source/backend/head dimension differ. Its `BLOCK_M` tiles query heads, not neighboring query rows—another reason not to transfer names as geometry. No donor numerical or latency result is adopted.

## Decision, exposure and cheapest falsifier

The cheapest falsifier was source-level: determine whether token selection is already physically tiled and whether the proposed coarsening requires a new per-query membership interface. Both were resolved without a toy schedule or native benchmark.

For the remaining existing AT02 family, the decision-changing evidence is actual same-request neighboring-query selected-index overlap, typed union/private lengths, and the exposed BF16 reader time on the selected source path. Missing traces are not zero overlap. If overlap is weak, packing/masking can cost more than saved loads; if prefill is sparse in the service mix, a kernel gain may not improve long-output ITL. Causal short-context tails and mixed request chunks need their own accounting.

Any eventual comparison must include metadata construction, workspace, extra arithmetic, kernel launches, partial merges, gather/dequantization that remains, and the fused output handoff. Use unchanged agent-p75/Mooncake service loads for TTFT/ITL/throughput, with prefill-shape breakdown and exact output checks. No peak-bandwidth conversion, paper speedup or selected-token ratio supplies a valid service forecast.

No further broad search was justified after the concrete residual matched existing work. This does not reject all of Tessera; its exact-support mapping and eligibility discipline remain a design reference attached to existing families.

## Yield and reproducibility

Two online searches,18 references/16 identities,one newly selected fulltext,three selected PR bodies,zero donor diffs,two pinned target files,nine exact excerpts checked,three wrapper-method AST locations. **Zero runtime tests,new formal cards,qualified implementations or measured gains.** No artificial case sweep was run.

Source export:24 documents,25 immutable revisions,191 provenance edges; edges include imported history, not191 read sources. Ten normal commands are exported from actual `state/commands.sqlite` as normalized/redacted stored fields, not raw argv. Local state is retained with deferred snapshot; no publication or restoration is claimed. Wrong initial source/report path guesses and bounded body-read depth are preserved in failures rather than counted as provider errors.
