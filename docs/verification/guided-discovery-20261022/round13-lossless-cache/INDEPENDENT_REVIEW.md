# Round13 independent lossless-cache audit

**Verdict: no qualified resident-KV compression hypothesis from these sources yet.** Reject direct deployment/benefit claims, retain scoped source observations and component-reuse possibilities. This does not prove all lossless compression impossible. No target KV byte histogram, capacity pressure, eviction/preemption or exposed bandwidth measurement was supplied. No GPU/model import, new online query, serving patch or canonical mutation by reviewer.

## Pin the representation before choosing a codec

At vLLM c455786, `attention.py130–140` selects the V4.1 packed MXFP8 record only on SM100 family: **512 E4M3 payload bytes+16 UE8M0 scale bytes=528B/stored state**, including quantized RoPE. The H200 record is584B with BF16 RoPE; results are not interchangeable. `nvfp4_ds_mla` additionally permits a288B compressed record (256 packed E2M1+32E4M3 scales) while retaining528B SWA. Resolve actual cache format before estimating anything.

Indexer caches are separate:128-dim FP8 plus a4B FP32 scale gives132B, or64B packed MXFP4 plus4UE8M0 gives68B. A codec for528B attention records is not automatically an indexer codec. Model KV source layers own shared compressed caches; consumers reuse them. Do not multiply capacity savings by every consumer layer. `MLAAttentionSpec` stores one latent vector, not separate K and V copies.

## Existing sparse-read contract prevents a drop-in variable record

`common/ops/cache_utils.py859+` computes `slot_ids = block_numbers * block_size + block_offsets`; FlashMLA `_forward_decode` passes global indices and a paged tensor with fixed record width/stride. Prefill gather dispatch identifies record format from `k_cache.shape[-1]` and decodes528/584/288 layouts explicitly. The insertion C++ op checks this width and writes at fixed token offsets.

A variable-length entropy record cannot preserve this ABI merely by storing fewer bytes. Choices are: restore native records into a scratch buffer before existing kernels, or add a compressed-record offset/directory and reader/inserter kernels. The first adds codec work, scratch and potentially full-page decoding for sparse requests; the second changes cache allocation, prefix-block handling, append/update, graph capture and random access. Their benefit needs actual byte savings and workload exposure, not a paper compression ratio.

Current `state_content_bytes` and page-size arithmetic still reserve native-sized pages. Compressing bytes inside the same allocated pages alone does not free serving KV capacity. Conversely, encoding new storage and simultaneously retaining native pages/decoded scratch can raise peak memory. This is conditional source accounting, not a measured allocation regression.

## SplitZip: exact bits can survive while the useful compression claim fails

Retained paper2605.01708v3 AppendixC measures E4M3 Top8 ratio0.933 (size expands≈7.18%), versus E5M2 Top16 ratio1.136 on its Qwen3-32B workload. E5M2 success does not support our E4M3 representation. E4M3 reported escape rate7.83% overwhelms its one-bit-per-value dense saving. These are external observations, not target measurements.

Pinned released source42c743118a29db3270ae6a921a4a4eecb20cad04 `codec_gpu.py`:

- `encode` treats contiguous input as16-bit words without an FP8-specific branch; `decode` returns a BF16 view.
- Splitting/combining those bits may round-trip arbitrary16-bit patterns, so raw paired FP8 bytes must not be declared inevitably corrupt. However the selected BF16 exponent field then spans unrelated FP8 bit fields; BF16 calibration/statistics do not transfer. Correct bytes and worthwhile compression are separate gates.
- Explicit escape storage charges4B chunk ID+2B local position+1B symbol per escape, seven bytes. `compressed_bytes` excludes construction counts/starts; the returned object still retains those scratch tensors. Transmitted payload accounting is not peak resident allocation.
- `int(offsets[-1].item())` obtains dynamic escape count before variable-sized allocations. This eager host readback is not an existing graph-compatible compressed-cache insertion mechanism.
- Decode allocates the entire output and performs a dense decode followed by sparse escape repairs. It is not an indexed per-token decoder for our chosen attention positions.

The worker's all-word symbolic roundtrip is useful to avoid a false exactness veto, but cannot certify GPU codec outputs, target entropy, allocation savings or sparse latency.

## Concrete bounds, not ROI predictions

`capacity_bounds.py/json` executed12 arithmetic sensitivity points. Under an ideal E4M3 Top8 adaptation, dropping one exponent bit saves at most64B of the512B payload: **12.12% of528B before escapes, codebooks, directories and unchanged scales**. With3B per escape, the zero-header break-even escape rate is4.17%; with the released BF16 implementation's7B escape accounting it is1.79%. The latter is a hypothetical FP8 adaptation calculation, not an implemented FP8 codec. Reported7.83% exceeds both.

Compressing only the16 scale bytes has an impossible zero-byte upper bound of **3.03% of528B** before any metadata. That small structured stream is a possible selective investigation if a real trace shows concentrated values and cheap decoding; it is not sufficient evidence for an experiment card. The optional288B NVFP4 format has a different scale fraction and coding problem; do not reuse E4M3 assumptions.

## Selective reuse without pretending the papers solve our problem

- **D-Quant2609.19880:** its bounded per-token containers address random-access locality, but its drift changes symbol assignments when a stream exceeds budget. It is not lossless relative to existing resident KV bytes. An exact alternative could retain container locality plus a raw fallback/overflow table, but would need separate capacity/latency evidence. Reserving native worst-case space for every slot forfeits resident capacity savings. Treat lossy quantization as a separately scoped experiment with quality requirements, not this lossless candidate.
- **AlignPred2610.17970:** alignment/predictive transforms and chunked restoration may inform external cold-prefix storage. Its DeepSeek case captures pre-FP8 C4 values, uses an error budget and restores native FP8; this is not exact compression of current resident V4.1 records. The paper reports DeepSeek restoration ranging from3% faster to15% slower in its setup. No active persistent restore bottleneck is attested here.
- **SplitZip:** exact raw-symbol escape repair and codebook separation may be reusable for cold transfer or a future format-aware codec. First measure actual stored bytes and include all directories/escapes/live scratch. Its released whole-buffer API and donor transport regime do not make it a resident sparse-attention optimization.

## Smallest evidence that could reopen this lane

Use an already saved cache-byte sample, if available, with source revision/cache format/token order recorded. Compute entropy, exact reconstruction and complete payload/directory sizes per native page, including incompressible pages. Audit random selected-token restoration rather than only sequential full-buffer decoding. Compare against existing hardware-cache/quantized format and the original fixed-page allocator. No new GPU collection is authorized. If the sample does not exist, record missing evidence; do not synthesize target distributions or assume pressure.

Current evidence supports a documented negative search outcome, with component reuse notes. It should not inflate accepted-hypothesis yield or overwrite prior cache/prefetch candidates.
