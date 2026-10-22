# Independent round43 source review

Reviewer: guided_adversary. Scope: retained paper passages, pinned target source, author scalar/representation fixture and dispositions. No GPU, backend imports, target weights or intermediate tensors, live deployment inspection, network requests, or canonical mutations.

## Verdict

The scoped outcomes are justified: reject the advertised direct Celty replacement and the literal MMA-only branch; leave an exact existing-zero codec and a repaired coordinated skip protocol open. These are three screened interventions, zero implementation-qualified hypotheses, and zero demonstrated service improvements. Missing target sparsity evidence is an exposure gap, not a proof that zero-work elimination is impossible.

## What carries the decision

1. **Selective paper reuse is valid.** Celty's software column-skip idea is separable from its proposed hardware and induced sparsity. Its measured FP16/single-user regime and unreleased implementation do not establish a replacement for resident, routed MXFP4/shared MXFP8 MegaMoE. ByteCross's matched-baseline/crossover evaluation is useful; magnitude thresholding is not exact-zero discovery. UnionSparse's union bitmap can preserve existing values without adopting pruning, INT4 activations, row reordering, or the published edge-GPU kernel.
2. **MMA-only skipping does not remove the traffic motivating it.** `target-mega-moe.cuh:728–755` loads activation/scales for every K iteration; the separate weight producer at 786 onward loads weight/scales and contributes expected barrier transactions. The MMA loop at 887–933 waits, copies scales, executes MMA and releases each stage. A conditional MMA alone leaves those reads intact. A useful traffic-saving variant must coordinate producers and consumers, including paired CTAs, transaction counts, task completion, and all-zero tasks.
3. **Initialization is repairable.** At line923 the accumulator flag uses literal K/UMMA positions. Skipping the first position while preserving that flag can accumulate stale TMEM. The fixture's 99+6 example illustrates that contract; it did not execute CUDA. First-active initialization or explicit zero initialization can repair it, subject to the actual synchronization protocol. This is not a veto on the general mechanism.
4. **Individual zero percentage is the wrong admission statistic.** The source's power-of-two per32 activation scaling preserves a nonzero maximum for an ordinary non-floor group. Four groups with one nonzero each have 96.875% zero elements but no skippable K128 tile. An actual shared MMA skip needs the required K range zero across the relevant active rows and paired-CTA consumption. Tiny floor-regime values, zeros from upstream arithmetic, or exceptional routing remain possible; none were measured here. Existing padding/inactive-route zeros must not be counted as new model sparsity benefit.
5. **The weight codec has an informative cheap falsifier.** For Q=4 and four-bit payloads, one bitmap bit plus all four payloads for each live group costs `1 + 16*(1-z)` bits per group versus 16 dense bits. Thus `z > 1/16` is necessary before offsets, alignment, scales, reconstruction and any retained original allocation. The independent-element assumption `z=p^4` is illustrative, not a checkpoint distribution. Paper groups align four areas, not necessarily four adjacent physical nibbles. The actual packed mapping and scale layout must be used for a real census.

## Exactness and test limits

- The author probe transcribes FP32 bit expressions and a mathematical positive E4M3 codebook. It does not validate compiled conversion, FTZ, target SwiGLU values, negative values, NaNs, or deployed sparsity frequency. Its selected cases are contract examples, not random coverage or confidence bounds.
- Skipping zero products additionally needs a finite-input contract: IEEE zero multiplied by an infinity/NaN is not interchangeable with no operation. Signed-zero elision is not automatically bit-preserving. A representation claiming original packed bytes must retain the necessary zero-sign information or explicitly restrict eligibility.
- Reconstructing original codes/scales can avoid arithmetic changes; replacing reduction order or sparse execution still needs separate target correctness checks. Retaining the dense original while adding compression cannot claim its capacity savings.
- No source fixture proves useful latency savings. Producer coordination, metadata decode, reconstruction to TMA-compatible shared memory, expert ownership/EPLB and mixed shared/routed formats remain integration costs.

## Next cheapest checks and stop rules

**Exact packed-weight codec:** only if exact pinned packed bytes are already available on CPU, inventory the actual four-area groups and encode complete bytes including metadata, scale and alignment costs. Compare reconstructed bytes with originals. Stop if net storage is not smaller; do not build a runtime decoder first. If bytes are unavailable, park rather than substitute another model's zero histogram.

**Activation skip:** require an already-retained, exact-baseline post-quantization trace with physical row/expert/K-tile identity. Count wholly eligible producer-consumer tiles, excluding padding. If no such trace exists, park pending explicitly authorized instrumentation. Another synthetic zero distribution would not advance the decision.

**No service promotion:** long-output ITL remains unmeasured. Neither paper speedups, byte counts, nor a repaired protocol create a target latency estimate.

## Review process

Read the author probe rather than rerunning its self-contained arithmetic as independent implementation validation. Read target producer/MMA/quantizer source and selected primary-paper passages. Broad text searches returned truncated output; conclusions above use the subsequent bounded source/passages and retained full text. A wrong upstream namespace in the initial target-source manifest was flagged before the author's final freeze; final checks record its disposition.
