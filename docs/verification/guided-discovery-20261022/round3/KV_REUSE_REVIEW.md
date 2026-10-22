# Compressed KV representation reuse and PageWeaver review

## R3-O1: repeated gathered compressed KV — promising source-specific diagnostic

**Disposition: promote the observation to a bounded source/CPU lifetime diagnostic if the author writes a card; no implementation or service qualification yet.** This has a more direct target path than porting a new attention kernel. It is distinct from earlier candidate-index scoring, TopK-to-slot fusion and CED sharing: CED already shares the stored source cache; the proposed delta shares the repeatedly reconstructed BF16 prefill representation.

### Independently verified dataflow

Pinned vLLM c455786:

- `attention.py:591–600`: only source layers construct the compressor; `:925–933` source cache insertion precedes sparse attention through the parallel preparation wrapper.
- `:1194–1229`: only sources own compressed cache; consumers resolve the same source object/cache. `flashmla.py:132–140` also resolves the source's metadata/block table, while SWA metadata is layer-specific.
- `flashmla.py:305–339` gathers/dequantizes the full compressed span on every prefill invocation, then fills a separate per-layer SWA tail.
- The likely SM100 default is Mega (`nvidia/model.py:198–255`, subject topology/build/config). Its `flash_mla_mega_attn.py:367–445` repeats the same full compressed gather plus SWA tail. Therefore the opportunity is not limited to the fallback FlashMLA branch. Live selected backend still unknown.
- `workspace.py:181–207` returns views into a reusable shared allocation; retaining these views does not preserve contents across intervening operations. `get_persistent_resource:133–157` already supplies independent keyed resources per ubatch/lane, with warmup/graph-lock and concurrent-stream rules.
- `sparse_swa.py:260–335` constructs chunk geometry from request lengths, compression ratio, window and workspace cap. Source-sharing alone does not establish identical buffer geometry; freeze this contract.

The pinned model config's `text_config` has source layers2,8,14,20, compression2 for layers2–19 and1 for20–39, window128, main head dimension512. Thus groups span6,6,6,20 compressed-attention layers. In an ordinary layer-major forward, a source's cache is written before its subsequent consumers and consumers do not own compressors. That establishes a plausible invariant, not a complete asynchronous/lifecycle proof. Target/draft forward_kv, preemption, decoder replay, microbatches and forward epochs must remain separate.

### Smallest useful reuse design

Start with source20, a single compatible prefill chunk, and the existing exact gather and attention kernels. Allocate a dedicated combined BF16 buffer. Gather its compressed prefix once; on each later consumer replace only the SWA tail and recompute that layer's combined indices/lengths. Keep query computation, TopK support, attention sink and output processing unchanged. This avoids a copy from a retained compressed buffer back into the old scratch layout. No layer reordering is required.

Use the persistent-resource API for **stable allocation identity**, prewarmed before graph locking. Store forward epoch, source generation, request/block mapping and chunk-validity as mutable validity metadata inside the resource. Do not make each new epoch a new persistent allocation key. Per-ubatch/lane isolation exists; concurrent stream use requires matching isolation or sequencing.

Fallback for multiple chunks initially: retaining only the final chunk from the source layer cannot satisfy the next consumer's first chunk. A general version must retain every needed chunk or use a deliberately changed traversal, which is a larger intervention. Likewise, fall back on incompatible chunk plans rather than reinterpreting a prior buffer under new strides.

### Memory and ROI accounting

At one8192-position request, ratio1, dimension512 and BF16, the compressed prefix is8MiB. For a complete8192-token initial prefill, the SWA gather tail is also8192 positions, so the reusable **combined** representation is16MiB before metadata/alignment. These are dimensional calculations, not observed allocation peaks. At shorter query chunks the tail changes. Shared scratch may remain allocated for other operators, so the dedicated resource can increase peak HBM even if it replaces this call's view.

A source20 group could avoid19 of20 repeated compressed gather calls **if** all consumers execute the same compatible prefill epoch/plan. That is a call-count upper bound, not19/20 of attention time or service latency. The required SWA gathers, attention, source writes and other model work remain. Complete net savings must subtract memory pressure, fallback handling and any staging copies.

### Next CPU-only checks

1. Build a pure state/lifetime replay for source write→first gather→consumer reads with chunk keys, source replacement, epochs, idle/mixed batches and graph reuse. Demonstrate scratch aliasing as a counterexample; test that the dedicated buffer's compressed prefix remains unchanged as each SWA tail is replaced.
2. Reconstruct actual chunk plans from saved scheduler metadata if available; determine source20 compatible single-chunk frequency. No GPU collection under current authorization.
3. Audit gather kernel writes, including padding, and attention input mutability. Confirm SWA offset cannot overlap the retained prefix under every supported plan.
4. Determine bounded prewarm allocation versus actual memory budget. Do not reserve max_model_len × all requests simply because the existing scratch was lazily sized.
5. If accepted later, use unchanged Mooncake/agent-p75 prefill episodes, paired complete forward/gather timings, peak memory, TTFT and ITL tail guards. Greedy/state equality and chunk-boundary differential tests are required. No current GPU result or gain percentage exists.

## AT02 PageWeaver — defer transfer, preserve useful execution idea

Primary paper: https://arxiv.org/html/2610.11201v1 . It regroups queries while keeping their selected supports and original output/causal IDs; load-affinity alone is not permission to add tokens. Its grouping-only whole-model benefit is small at longer contexts and regresses at8K; the Blackwell comparison removes the claimed general advantage. Whole-kernel and grouping deltas must be separated. No author repository has been positively pinned in this audit.

Target-specific obligations: main MLA head dimension512,64 query heads, tokenTop512 plus layer-local SWA and source-shared compressed KV. Identical integer IDs in SWA and compressed spaces are not identical storage; keys must include address space/source and physical block mapping. Keep per-token membership even if grouping is scored by pages. Preserve duplicate-support handling, sink normalization, per-layer causal positions and original output row ownership.

The useful partial transfer is bounded query grouping only when a target kernel can share loads without growing masked computation or breaking the fused Mega operations. A new Union8 kernel tuned for head dimension128 is not a drop-in. Saved selected-index traces could cheaply measure physical overlap and subgroup work, but low union size is not latency evidence. Compare with the strongest existing adjacent/native order and charge grouping/index indirection every invocation. Do not invent a new long-context benchmark to mask absent benefit on the current suite.

**Review of author cards:** AT01 DoSA CPU diagnostic and AT02 PageWeaver defer are consistent with the independent review. R3-O1 remains uncounted until its own bounded card and lifetime evidence exist. No GPU or canonical writes occurred.

## Follow-up gather write-bound inspection

`common/ops/cache_utils.py:529–587` (MXFP8) and `:590–648` (NVFP4) loop over actual gather length and write only row `offset+i`. Neither clears the compressed prefix when called for the SWA tail. Dispatcher `:764–819` chooses CuteDSL for supported FP8 records and Triton for NVFP4; `deepseek_v4/nvidia/ops/dequant_gather_k_cutedsl.py:265,268` likewise writes `out[req_id, offset+i, ...]`. This positively supports retaining a dedicated prefix under an identical chunk plan. Padding remains as in the original masked layout; do not add a whole-buffer zero operation. These are source-level write bounds, not an executed device-memory safety check.

## Author card update

Reviewed the subsequently written `round3-attention/candidates.json` AT03. Its status `advance_cpu_lifetime_and_memory_diagnostic_only` matches this review; it explicitly records no measured gather share,16MiB combined example, scratch aliasing, multi-chunk fallback and live-config uncertainty. The original unqualified observation is now represented by **one AT03 card**, not two directions. Static source/config checks are executed; the next lifetime fixture and capacity envelope are still pending. AT01 remains CPU numerical diagnostic and AT02 remains deferred.
