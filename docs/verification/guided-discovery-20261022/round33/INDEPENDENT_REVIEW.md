# Independent NQ33-01 review

## Verdict

**Retain as deferred, low-priority source-level investigation.** The proposed write partition has a coherent all-byte contract and targets work present in c455. No numerical, compiled-kernel, PDL, graph or service qualification follows. Priority is below PJ01's clearer dead-column removal until retained shape/backend exposure exists. This is an investigation ranking, not a measured latency comparison.

I verified all31 frozen author file hashes against manifest `1a5815edf51b3de0d8828bc407d97a6e47b8eacc4bd5731af81a87c9613adb6b`, read original producer and consumer dispatch, and ran only a standard-library integer/source extraction. No serving imports, GPU, compilation, network or canonical writes.

## What the source supports

`query_quant.py` genuinely launches `(ceil(n/128)*128, 2)`. At n1–16/Q1280/KV512: two live CTA families, padded Q CTAs which write zero scales, and padded KV CTAs with no normalization work. PDL wait/release executes before the branch, including otherwise empty CTAs. Q normalization is rounded through input dtype before scale computation/FP8 conversion. KV uses its existing normalization and output cast. These live formulas, reduction geometry, strides and rounding boundaries must be preserved.

Allocation and consumers remain unchanged: Q payload has actual tensor shape, KV has its original shape, scales retain the entire F8_128x4 allocation. Padding zeroing is an existing semantic requirement, not expendable work. Original `torch.empty` allocations make stale contents possible whenever a required scale byte is omitted. The proposal correctly moves zeroing rather than deleting it.

The two-dimensional grid could in principle become a single grid with two live-row families plus masked padding tiles. The source-offset inverse used by the author correctly recovers row index. For Q1280 there are ten512-byte physical tiles and40 scales per live row. At n1,5080/5120 bytes require zero; at n16,4480 require zero. Live and padding writes are disjoint, and the allocation remains fully covered.

The independent check extracted the **actual pinned** `mxfp8_scale_offset` expression, removing only its Triton decorator/annotation and providing integer cdiv. It compared the author's offset/inverse at n1/5/8/16/128/129 and verified one owner per scale byte. This strengthens the source-address correspondence. It still proves no memory transaction, warp-lane or synchronization behavior. The author's128 cases use symbolic live bytes; they do not exercise `_norm_row`, FP8, UE8M0 conversion or floating-point edge behavior. Neither this review nor those cases show a latency win.

## Required scope correction

`attention.py:_can_fuse_query_quant` starts with `[self.wq_b]` and appends `indexer.wq_b` **only when that layer has an indexer**. The constructor creates the indexer only for `is_index_source` layers. Thus main→indexer consumption and two-loaded-class checks describe index-source layers; other layers can have just the main consumer. Do not multiply by a fixed number of indexer calls or require a nonexistent second consumer. Per-layer eligibility and call counts are needed. The worker supplied an append-only REVIEW_ADDENDUM.md correcting this without changing frozen originals.

Native config supports the default MXFP8 route, but source preference is not loaded backend attestation. Overrides, skipped layers, dependency availability and disabled kernels can bypass it. The fused helper checks exact kernel classes because the quant key alone does not identify scale layout; an adapter must retain this narrow condition.

## PDL and graph constraints remain open

The original producer executes `gdc_wait()` then `gdc_launch_dependents()` before all stores. Retaining these calls is necessary but is **not by itself a proof** of a replacement grid's visibility. Fewer/changed CTAs can alter early dependent scheduling. Every new live and padding CTA must participate in the intended dependency contract, and consumers must wait correctly before reading all needed Q/scale/KV bytes.

The pinned `vllm/utils/flashinfer.py:mm_mxfp8` wrapper delegates to external FlashInfer without an explicit PDL argument in this call. This audit did not inspect or execute the exact installed external kernel's waits. Do not claim source-level end-to-end PDL proof from matching producer intrinsics or from a single-stream Python call. Conversely this absence is not evidence that the existing runtime races; it is an unclosed external-contract gate. PDL-on/off and eager/graph producer-plus-real-consumer tests are necessary when device work is authorized.

Use `qr.shape[0]`, not service concurrency, useful-token count or accepted length. The graph-captured tensor may have padded rows counted as live by the current kernel. A graph captured at32/128 cannot silently replay the n<=16 grid because only five requests are active. Grid, allocations and specialization must remain static for the captured shape; large-shape fallback and n0's no-launch behavior remain intact.

## Why CTA reduction is not an ROI estimate

The illustration retains one launch:256→12 CTAs at n1,256→42 at n16. Ten padding CTAs remain fixed overhead; this is not a zero-cost memset. They write the same total padding bytes, with a new inverse-address/mask computation and possibly unchanged block resource allocation. The existing empty KV CTAs may retire cheaply; heavy live normalizers can dominate the critical path. Compiler decisions from adding an alternate body can change register usage or occupancy of all CTAs. At128 rows the illustration increases256→266 CTAs, supporting explicit small-shape restriction.

A useful future attribution control, only if needed after the first device comparison, is omitting only empty KV workers while retaining all original Q row writers (128+n CTA model). That distinguishes removing no-work dispatch from regrouping scale stores. It is not a new hypothesis, required parameter sweep or evidence it is faster; it is a narrower repair if the tiled scheme regresses. Do not implement or benchmark it during this CPU-only investigation.

The relevant possible savings are the exposed scheduling/producer interval before its consumers; neither5120 bytes nor244 fewer CTAs is a duration. Compression and attention preparation may overlap the main path. Any component gain must survive real consumer ordering and the frozen ITL/tail workload. Unknown ROI is not a mechanism rejection, but it bars high-priority implementation claims.

## Stop and reopen

The next cheapest useful input is an **existing** exact-baseline capture/loader record with per-layer loaded class and actual QR tensor-shape distribution. The direct-decode audit's52 local metadata files do not supply it. Do not repeat synthetic address sweeps or expand papers to substitute for exposure. If no eligible small captured shapes occur, reject the scoped adaptation for that baseline. If exposure exists, preserve deferred status until authorized device correctness and producer-plus-consumer timings demonstrate value. Test all allocated scale bytes with dirty initialization and repeated shape changes; larger, zero and boundary shapes must take their specified fallback. No new service workload is justified: retain Mooncake/agent-75 and add only the missing component correctness/attribution tests.
