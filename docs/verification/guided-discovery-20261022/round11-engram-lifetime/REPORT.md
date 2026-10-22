# EG01 round11: packed-input write coverage and prefetch handoff

**Disposition: refine the same EG01; implementation and service qualification remain deferred.** No GPU, torch/model import, new provider call, serving change, or canonical-memory mutation. This is source arithmetic and Python orchestration evidence, not GPU correctness.

## Actual result

The closed PR58766 unsharded producer explicitly writes every active FP8 value and every scale byte in the returned padded scale view. Its padding loop is sufficient in a byte simulation using its exact scale-offset expression. The current fork adds sorted lookup and inline-vs-background prefetch selection that the donor lacks. A direct textual transplant can break scale placement or forget to produce scales on the inline branch.

Two CPU scripts executed:

- `python3 write_coverage.py`: 49,152 donor/target scale-coordinate comparisons; 28 positive sequence cases (two modes × two layer-owned buffers × seven calls); three deliberately broken adaptations detected.
- `python3 event_order.py`: four cases executing the exact AST-extracted `_start_prefetch` and `_finish_prefetch` methods with logging stubs. No actual CUDA events/streams run.

Full inputs, source hashes and outputs are in the adjacent JSON/script files. Input sequence is **130→1→129→0→7→128→1**, target width24×256=6144, groups192, independent illustrative buffers for layers1 and14. Initial values/scales contain dirty0xD7/0xE3. IDs include valid reordered rows, DEAD_ID=-1 and out-of-vocabulary rows. Table bytes are deterministic synthetic data, not checkpoint values.

## Source-derived coverage

PR58766 head `5030d5dd66884830e5b20149218ca27e9864901b`, common Engram lookup:

1. Actual rows=`tokens×local_heads`; swizzled `num_out_rows=round_up(tokens,128)×local_heads`.
2. FP8 stores are masked by `rows<num_rows`; invalid IDs load zero and still write their output slots.
3. Scale stores are masked by `rows<num_out_rows`. Padded rows have `owned=false`, so zero is stored at every F8_128x4 offset.
4. `_mxfp8_input` returns exactly active value rows and `round_up(tokens,128)×width/32` scale bytes, backed by persistent max-token storage.

The target's helper uses `ceil(groups/4)` while the donor uses an algebraically equivalent expression when groups is divisible by4. At this target groups192, all49,152 checked offsets agree and uniquely cover the padded buffer. This is not a proof for unsupported arbitrary widths.

At token count1,6144 active value bytes and24576 exposed scale bytes are refreshed. Old capacity outside both returned views may remain dirty but is not part of the logical input. **External FlashInfer physical reads/masking were not executed or fully proven here.** An empty lookup returns immediately and the returned views have length0, so the model has no stale-readable logical bytes; actual zero-token GEMM behavior is a separate runtime contract.

## Concrete falsifiers that changed the adapter design

| Deliberately broken adaptation | Detected after130→1 | Repair requirement |
|---|---|---|
| Write only live-row scales, omit padded zero stores | Only192/24576 scales refreshed; first mismatch offset4 | Clear/write all scales in the active padded view each invocation |
| Preserve sorted destination for values but use iteration row for scale offset | All bytes refreshed, but first scale mismatch offset1024 | Derive scale token/head from **destination row**, not sorted iteration index |
| Skip invalid IDs rather than zero-write them |256 value bytes and8 scales remain stale; mismatch starts0 | Invalid/dead rows must explicitly write zero values/scales |

These are failures of intentionally broken proposed ports, **not newly discovered bugs in existing vLLM**. The positive sorted adaptation is a transcribed byte model, not serving code.

Pinned c455 lookup sorts local IDs and carries `sorted_dst` to restore original token/head row. Donor PR58766 has no sort path. The narrow adaptation must maintain this destination mapping, then separately zero padded scale rows. Extending the sorted-input iteration to padded rows must not read absent sorted IDs/destinations or scatter padding through a dummy destination. A separate padding section or explicit masked padded domain is clearer than pretending padded rows belong to the permutation. Retain current sort selection; disabling it changes host TLB behavior and confounds the conversion experiment.

## Prefetch event audit

Pinned c455 `common/engram.py1610–1659` chooses inline execution using the **maximum token count across DP ranks**. A localT1 call withDPmax256 can select inline. Otherwise the prefetch stream waits the current stream, temporary hash storage is recorded on it, and lookup executes there. The event is recorded on whichever stream actually executed lookup. `_ready_rows` waits this layer's event only.

Donor NVIDIA Engram always uses the background path and passes `out_scales=self.staged_scales` into lookup before recording its event. The current fork's BF16 implementation does not pass a scale pointer, by design. A port must add the pointer to **both current inline and background calls**, preserve the selected stream and event record after all value/scale stores, and keep each layer's buffers separate. Do not replace current threshold selection with the older always-background wrapper or wait the whole shared stream.

The AST logging cases verify source order `lookup→event.record→wait_event`, and show the DPmax-triggered inline branch. They do not establish CUDA completion, event reuse under overlapping forwards, captured graph resource ownership, sleep/wake behavior or independent microbatch lanes. Persistent buffers and the current stream handoff provide a plausible sequential-forward adapter boundary, not a concurrency proof.

## Bounded next design

Preserve current per-layer staging and prefetch schedule. For eligible table-dp1/TP1 plus exact supported WKV consumer:

1. Allocate stable per-layer FP8 values and padded F8_128x4 scale storage.
2. Adapt current sorted/unsorted lookup so active values and scales share original row identity; zero padded scales independently.
3. Pass both outputs through existing inline/background orchestration, followed by the existing per-layer event.
4. Return active FP8 and padded-scale views as the existing QuantizedActivation ABI; retain BF16 fallback elsewhere.

No runtime adapter was written. Remaining gates are actual checkpoint numeric domain and pinned FlashInfer requantization equivalence, exact live consumer/config, external kernel input-read contract, graph/lane/sleep resource lifecycle, and exposed-cost/serving evidence. The source coverage findings resolve a specific design question; they do not turn EG01 into a validated optimization.
