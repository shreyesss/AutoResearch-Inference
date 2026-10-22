# Round57 — indexer page layout: initial missing-work premise refuted

## Decision and yield

**Zero new hypotheses; two concrete component directions screened as already implemented.** No implementation recommendation or serving gain. This closes the source question raised during round54 review rather than searching for papers to support a disproven premise.

Planned baseline is Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, callgideon/vllm `c4557869393db4d75c483d92edd02a5125500883`, DeepGEMM `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, TP1/DP4/EP4 on B200. This is source compatibility, not an installed-image or live-dispatch attestation.

The initial question was whether nominal 68-byte MXFP4 /132-byte FP8 indexer rows cause avoidable payload/scale access fragmentation. **They are allocation/ABI shape widths, not the physical payload stride used by the native reader.** Both sides already use segregated page planes.

## Actual adaptive process

1. Read current discovery/critic skills. Read-only compact inventory covered143 canonical cards over two pages with an unchanged inventory hash; retained51 broad lexical matches and inspected relevant statements/mechanisms. A bounded top-level campaign report search retained three literal layout-term matches. Relevant AT03, MP17, LC and round37 sections were then read explicitly; report-text matching is not exhaustive semantic novelty detection.
2. Followed exact vLLM writer→cache-view→native-reader symbols. Reused three frozen round50 DeepGEMM headers and six pinned vLLM files. Inspected complete relevant functions, not a PR opening body.
3. Exact retained-source lookups for two missing DeepGEMM files returned no records. Executed two production `investigate` calls with pinned code-only sources, each budgeted one HTTP cache miss: dense kernel implementation then API descriptor construction. Both completed with full file text and no model calls. The second retrieval was waited to completion; a premature local extraction attempt before completion failed and was retried afterward. This was tooling timing, not a source/runtime fault.
4. Ran only an author-written integer translation of cited address expressions. No native/compiler execution. It checks a specific erroneous AoS interpretation and the aligned sparse-copy byte sets.
5. **Paper searches:0; paper hits:0.** The parent instruction made recent-paper retrieval conditional on an unresolved removable cost. Existing code resolves both proposed directions, so another search would not improve this decision. No claim of literature exhaustion.

Retained tool failures: initial `init --defer-snapshot` was rejected before mutation; retried without unsupported flag. Initial ops.py locator was wrong because ops is a package; corrected through file listing. Initial broad filename/console listings and prior-card output were truncated, so retained full JSON and bounded source reads governed conclusions. No failure was represented as a GPU result.

## Exact address chain

### Writer already separates scales

`attention.py:101–109` computes nominal width64+4 or128+4. That alone says nothing about actual token-address placement.

`common/ops/indexer_k_store.py:204–227` explicitly labels the page pointers “segregated: values first, then scales.” For non-ROCm layout, page base `P`, page token count `B`, payload width `D` (64 packed MXFP4 or128 FP8), token `t`:

```
value(t) = P + t*D
scale(t) = P + B*D + t*4
```

The writer retains RMSNorm and RoPE BF16 rounding boundaries and quantization before storing bytes. This investigation changes none of them. Only group-boundary tokens with valid slots publish; the live/page-valid population is not inferred from allocation size.

`SparseAttnIndexer.kv_cache_as_quant_view` constructs a nominal four-dimensional view with row width68 for the MXFP4 API. It does not copy or interleave scale bytes into each token's value payload.

### Dense API explicitly reconstructs the two planes

DeepGEMM `csrc/apis/attention.hpp:225–249` checks nominal dimensions/stride, then creates payload `from_blob` with token stride `kv_head_dim`, and scale `from_blob` at `base + block_kv*kv_head_dim` with token stride1 in32-bit scale words. Physical page stride is retained. For SM100 the API admits page counts32/64/128; these are source-supported possibilities, not a claim about loaded configuration.

Host `sm100_mqa_logits.hpp:313–330` builds separate payload and scale TMA descriptors. Therefore, treating the nominal tensor's68-byte stride as the device payload-reader stride would model a different layout.

For page64/token1/MXFP4, the correct offsets are payload64 and scales4100. A hypothetical token-interleaved interpretation produces68 and132. The diagnostic preserves this concrete counterexample.

### Sparse API uses the same planes

`PagedSparseKVAccessor::resolve_kv_block` in `sm100_sparse_mqa_logits.cuh:121–130` derives page and within-page token from the physical sparse block. It returns `page + token*D` and `page + PAGE_KV*D + token*4`. The actual paged host path disallows unaligned-KS mode, and the API checks page-stride256-byte alignment. Target candidate sparse scoring is opt-in and currently requires MXFP4; FP8 sparse-reader calculations below describe dependency capability, not an activated target path.

## Screened components

### L57-A — convert allegedly interleaved indexer cache to page-local payload/scale planes

**Already implemented; initial premise refuted.** Writer, dense API and sparse accessor agree. No new conversion, extra cache allocation or native patch is justified from this representation claim. This does not prove the representation is globally optimal or that every future alternative is useless.

### L57-B — batch scale loads and distribute payload-copy work

**Already implemented in the inspected readers.** Dense core `sm100_mqa_logits.cuh:183–222` groups scale pages four at a time using `tma_gather4`, handles the remaining pages separately, and assigns some payload pages to the scale producer when the derived load count warrants it. It also conditionally reuses a full KV ring for consecutive tasks sharing splits; this is already present, not a new generic reuse proposal.

Aligned paged sparse core computes one16-byte scale chunk per lane across a128-token copy-warp group, and copies payload as paired sparse blocks with16-byte lane chunks. Source already performs scale batching and contiguous payload copies; `cp_async` hints and SMEM swizzling remain part of the existing path.

There can still be tail padding, cache misses, replay, capacity limits, synchronization or instruction overhead. This audit has not identified a new exact intervention that removes them. P50 already covers metadata/PDL/cache-policy adaptations; do not rebrand those as a new layout finding.

## CPU address diagnostic and limits

`address_probe.py/json` executed standard Python only:

- 3,584 writer/sparse-reader pointer comparisons across explicit payload64/128, page32/64/128, sparse-block8/16 and token-offset scenarios.
- 24 complete128-token copy-group scenarios, with contiguous or scattered unique valid block IDs. It verifies exact requested byte sets and computes32-byte address-sector sets for each source-derived warp instruction.
- MXFP4 payload8,192bytes maps to256 requested32-byte sectors and scales512bytes to16; FP8 payload16,384bytes maps to512 sectors and scales512bytes to16. These are exact arithmetic counts under the declared aligned/full/unique-block model.

**Not executed:** Triton/CUDA compilation, generated lane mapping, TMA, native kernels, driver/cache transactions, performance counters, request traces, numerical outputs or service measurements. These equations are author transcriptions, not independent proof of source premises. Source writer/consumer analysis provides the layout evidence. The diagnostic checks arithmetic consistency and refutes a specific bad address model.

Do not convert these counts into HBM/L2 traffic or latency: cache hits, `cp_async` prefetch hints, TMA transaction formation, duplicate blocks, invalid/tail work and scheduling can change physical behavior. Non-power-of-two allocation width alone proves no inefficiency. The model does not certify all rows/tails, all backends or a changed representation.

## Prior comparison and evaluator relevance

- AT03 reuses repeated BF16 materialization across shared-source prefill layers. This screen concerns bytes inside the indexer cache; it cannot claim AT03's saved gathers.
- MP17/physical-map fusion addresses publication/reuse of selected physical slot metadata, not payload/scale plane layout.
- LC01–03 concern lossless coding/random access/capacity and already-quantized byte distributions. No entropy coding or changed precision is proposed here.
- Round37 selected-KV work distinguishes offload reuse and approximate prediction from current exact resident support. No transfer/offload regime is introduced by this screen.
- P50's native sparse metadata release/cache eviction question remains separate. Existing dense stage reuse is baseline behavior.

Agent75/Mooncake would measure a future real service change, but no new benchmark or GPU diagnostic is justified for these already-present components. Actual backend activation, source/consumer shapes, exposed indexer time and cache traffic remain unknown. There is no ROI estimate, no accepted implementation and no authorization for GPU work. Reopen only with a specific reader/writer transaction or repeated computation absent from this pinned code, not a nominal tensor-width argument.

## Durability

All review files, source copies/pins, exact code-investigation receipts, prior lookups, source export and command journal are retained under this isolated round. No canonical import, cloud publication or Git change occurred; deferred snapshot receipts explicitly say no new S3 backup. No global hypothesis status was modified.
