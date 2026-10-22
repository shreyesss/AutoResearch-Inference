# Independent round49 review: static selected-row draft head

**Verdict: retain as a deferred alternative in the QH45 draft-head investigation family. No new card or implementation qualification.** Fewer base-head rows is a credible work-removal mechanism distinct from lower precision. It does not yet have target head exposure, a justified keep set, native block-verifier correctness or net progress/time evidence.

I verified the 23 frozen author artifacts and read the pinned native DSpark construction, sampling/scatter, configuration guard and rejection wrapper, plus selected HyCo/FR-Spec/FlexEE method passages. Additional pinned source reads below clarify two material adapter requirements. No probability fixture, native import, GPU test or canonical write was run. The five PR bodies remain historical opening evidence, not independently verified current patches.

## Existing support: useful but not a ready V4.1 flag

The native sequential path computes base logits once for the whole request×speculative-position tensor, reshapes it and applies Markov bias sequentially. Five positions do not imply five separately loaded base-head matrices. The Qwen-only top-k path also computes the full base logits before selecting candidates; it does not remove that base projection. The config explicitly rejects that flag for the native V4.1 architecture, whose public model hooks do not expose the gathered-bias adapter. The report correctly excludes a simple flag-based deployment.

The shared DSpark probabilistic scatter computes target columns as `arange(K) + d2t`. Its index is therefore an **offset map**, not raw target IDs. A selected sequence `[3,8]` requires offsets `[3,7]`. Duplicate, out-of-range or inconsistent ordering must fail before capture. The scratch starts at negative infinity and is separate from the persistent proposal cache; each sequential step overwrites selected columns and the sampler receives full-target-width logits. This is a useful conservative integration point. It preserves full-width work and needs its actual sampling/cache semantics validated; it is not a proof of native five-step distribution preservation.

## New source-derived adapter gate: logical width versus padded width

`vocab_parallel_embedding.py` defines `DEFAULT_VOCAB_PADDING_SIZE=64` and allocates `ParallelLMHead` rows using padded vocabulary size. `LogitsProcessor._get_logits` removes padding by slicing to **its own** `org_vocab_size`, not by consulting a selected-row map. Native V4.1 constructs its logits processor with the full target vocabulary.

Consequently a naive small selected-row `ParallelLMHead` can produce padded rows that survive the unchanged full-vocabulary processor. For a logical K=2 head with standard padding, the allocation is64 rows; slicing to129280 does not reduce64 to2. Passing that output to a two-element scatter index is incompatible. This is a conditional source deduction, **not an observed runtime error**; a direct unpadded derived linear could avoid that specific allocation but still needs explicit logical-width handling.

Require the selected base projection to return exactly K logits in frozen keep-set order, excluding all padding, before adding gathered bias and scattering. Bind the selected width, padding/alignment, loaded dtype/head_dtype, mapping and capture shape together. Preserve the original target head and its precision policy.

## New source-derived adapter gate: full Markov dimensions and processor

Native DSpark passes config `draft_vocab_size` into `DSparkMarkovHead`, whose `markov_w2` is a `ParallelLMHead(draft_vocab_size, rank)`. Its input embedding still covers target vocabulary. Native `compute_logits` and `markov_bias` also share the same full-vocabulary logits processor. Thus globally setting `draft_vocab_size=K` is not an isolated crop of the base head: it changes the Markov output module/load shape. Simply replacing the common logits processor with one sized K would truncate full Markov output to its **first K columns**, not the arbitrary selected target IDs.

The proposed first arm should keep full Markov weights, output width, processor and target-token input embeddings. Add separate selected-base-head logical-width handling; gather Markov columns in exactly the keep-set order after the original full Markov calculation. Do not silently fold a narrower Markov implementation or checkpoint transform into the same arm. Bonus/correction tokens outside the keep set must still be legal parent/input embeddings.

The loader currently aliases the target head when the model reports no own head; an adapter must explicitly create and retain its derived copy at the appropriate lifecycle boundary and refresh or invalidate it on target reload/replacement. The unchanged greedy mapping hook returns identity, so do not claim that activating the probabilistic scatter alone also implements a correct greedy reduced-vocabulary path. Scope unsupported modes out or implement their mapping explicitly.

## Fixed support, probability and scheduling

A frozen keep set makes one-time negative-infinity scratch initialization meaningful. Changing its set/order after allocation can leave stale finite columns; exclude dynamic changes or rebuild/reset the entire affected state and graph. Every sampled proposal must correspond to the cached actual logits under the same temperature/watermark conventions. Full-width cache retention removes one width migration, not every correctness obligation. Confidence inputs and any acceptance-estimator path are also exposed to the changed proposal distribution; unchanged policy code does not establish unchanged decisions or calibration.

For ordinary one-token exact rejection, `sum min(p,qS) <= p(S)` follows because qS is zero outside S. Residual recovery can restore full target support when implemented correctly. This bound is conditional target mass, not global dataset token coverage, and neither it nor held-out frequency coverage predicts five-step committed progress. The author explicitly preserves that distinction. All-zero/invalid proposal distributions and unsupported hard masking require declared behavior rather than an assumed normalized q.

## Paper transfer, cost and stopping rule

HyCo's static row restriction and FR-Spec's frequency-selected subset can be reused separately from mobile placement, training and relaxed acceptance. FlexEE's repeated exit-head reuse does not establish benefit for the current one-batched-base-head architecture. Dynamic full-head-then-select can serialize the current five-position work and retain the original weight read; it needs independent justification.

The target full head remains resident. A BF16 quarter-size derived copy costs about331MB per TP1 rank before alignment, scratch and transients; this is additional capacity, not a reduction in total original model storage. Full Markov projection, gather, full-width scatter/cache/sampling, verifier and other model work remain in the proposed first arm. Precision reduction and row reduction share a head-time denominator; they are alternative controls first, not additive forecasts.

Next useful evidence is retained exact-baseline head timing plus tokenizer-pinned output IDs from request-disjoint representative data. Held-out per-domain coverage and outside-set bursts can reject a poor keep set cheaply but cannot certify counterfactual acceptance or speed. If those artifacts are absent, park this alternative; no more invented probability cases are warranted. Keep standard Mooncake/agent75 for eventual service evaluation, with separate mapping/rare-token/domain diagnostics and native correctness checks when authorized.

## Locator correction

The author `source-manifest.json` points the c455 rejection-sampler file at `github.com/vllm-project/vllm`. The audited revision belongs to **callgideon/vllm**. The retained bytes match the exact pinned source; this is a locator correction only. `source-addendum.json` records the correct URL and hashes without changing the frozen author packet.
