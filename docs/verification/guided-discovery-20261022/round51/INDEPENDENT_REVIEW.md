# Independent round51 review: exact Engram projected-result reuse

## Verdict and a material prior-recall correction

**Keep the same EG02 family deferred; no new card, qualification or runtime patch.** The conditional pre-gate split is legitimate, but the intervention is not new to this campaign. `engram-projected-cache-preflight/REPORT.md` and its `online-followup/ADDENDUM.md` already propose the complete ordered24-head WKV result cache, 51,200-byte value, numerical/tactic and miss-compaction gates, prefix-cache exposure confound, and the same missing executed-token/hash trace. Their exact report bytes and hashes are retained with this review.

Round51 adds a newly selected cross-domain paper and a clearer dependency/amortization analogy. It does not establish a new missing component, improve the measured hit-rate evidence, or resolve a correctness/ROI gate. The author's zero-new-card count is correct. Its one conditional component adaptation should be understood as **new-source support for an existing intervention**, not fresh hypothesis yield. Searching only typed hypothesis cards missed this exact prior report. Future prior recall should include retained screening/report artifacts as well as card titles/bodies; this review does not implement or claim a retrieval-tool improvement.

## What the code does establish

The actual two `Engram.forward` WKV calls consume either prepared quantized embedding input or flattened looked-up rows. The current hidden state enters the later post-WKV gate, not these WKV arguments. The constructor makes a bias-free6144→25600 projection for this config. Repeated exact ordered table-row inputs under identical weights therefore define the same real-arithmetic pre-gate result. Keeping the changing gate is the appropriate selective component; caching the final Engram output is not.

The model already intentionally maps n-grams into table-row hashes. Different raw token sequences that produce the same complete ordered table IDs are not a new cache-hash error: they already fetch the same baseline input. A shortened fingerprint used by the proposed cache still needs full-key comparison. Constituent row popularity does not establish complete-tuple recurrence.

The key/eligibility contract must cover:

- Layer, table and shard identity, all ordered row IDs, and immutable table/WKV weight and quantization representation epochs. Current staged data must actually correspond to the claimed tuple.
- A supported numerical backend/layout/padding/M/row-position/capture contract. A cache entry produced under another tactic cannot be called byte-equivalent solely from equal input.
- No dynamic adapter modification, or explicit adapter identity and compatibility. The frozen base-model proposal should simply exclude unsupported LoRA/wrapper paths rather than assume a global reload epoch covers per-request changes.
- DEAD/padded/masked positions and their original lookup semantics. Hidden-state-dependent masks remain in the gate; they are not permission to populate entries from stale staging bytes.

This is a dependency audit, not proof that the deployed configuration meets those conditions.

## Batching, storage and distributed execution

Miss compaction changes GEMM M and possibly the reduction/tactic. If numeric compatibility requires retaining the full original GEMM, substituting cached outputs afterward saves no projection work. A restricted same-shape policy or fully compatible native miss path may be possible; neither was validated. An all-hit batch can have different economics from a mixed batch, so a scalar eligible hit fraction is only a rough explanatory variable.

A cache value must own immutable storage rather than retain an alias of a recyclable GEMM/workspace output. Entry publication must happen only after completion, and eviction/reuse must not race the post-gate reader. Concurrent requests, graph replay and separate lanes/streams need explicit lifetime handling. Static storage can support graphs, but a Python dictionary of tensor pointers would not establish correct captured behavior.

For the narrow projection-only arm, preserve existing table lookup/prefetch/readiness events, rank agreement and any active exchange. Skipping lookup/exchange on hits is a second integration problem; ranks cannot independently omit collective participation. `EngramBatch.create` itself excludes `dp_size==1`; the shared-host table branch forces that local table DP size to1. Thus generic DP4 deployment language does not prove the packed EngramBatch path is active, and savings from every alternative cannot be summed.

A hit still supplies a50KiB output to the gate. If the adapter scatters cached results into a contiguous batch output, it adds cache reads and scatter writes; it does not simply erase output traffic. Direct pointer/indexed consumption has its own gate-kernel/layout cost. The current source exposes no measured tradeoff.

## Capacity, paper evidence and priority

Independent stdlib arithmetic agrees with the author:24 ordered IDs;6144 BF16 input elements/12,288bytes;25,600 BF16 output elements/51,200bytes;1024 entries in each of two layers cost100MiB in output payload alone. Illustrative int32/int64 full keys cost192KiB/384KiB respectively. Metadata, graph buffers and compacted-miss workspace remain extra. Repeating such a private cache on eight ranks would reserve800MiB of output payload node-wide; that arithmetic is not a measured allocation or proof of reduced KV capacity.

I read the selected neural-operator fulltext's branch/trunk equation, fixed-coordinate partial evaluation, within-device310-case controls, compiler-freezing comparison, and preparation/lifetime passages. It supports dependency-preserving reuse and strong-baseline/lifetime accounting. Its fixed geometry is reusable by construction, unlike changing Engram tuples. Its byte checks and energy/latency percentages cannot certify our quantized projection or recurrence. Standard freezing already removing the same invariant work is important contrary/control evidence, not an LLM serving result.

A01 can hide some WKV time; EG01 changes input representation; EG02 raw-row caching operates at a different key/value granularity; PJ01 shares input quantization within a call. These comparisons are useful, but the exact projected-result predecessor is the closest prior. Their benefits are not additive.

The next decision-changing artifact remains an already-existing, representative **executed** tuple/epoch/numerical-context trace after prefix-cache behavior, with phase and request/round chronology, plus exact-baseline exposed WKV evidence. A source-derived simulator can reject poor locality only after such data exists. The inspected packet supplies neither. No additional synthetic Zipf or algebra fixture is justified to prolong this parked branch. Source/CPU capacity confirmation is complete; implementation priority remains low until the missing evidence appears.

## Verification scope

Verified all20 frozen author-file hashes, compared six source copies against the existing c455 tree, independently recomputed capacity from the pinned config, and AST-checked the two actual WKV call expressions without importing the model or torch. The AST/capacity script and output are retained. I did not run native numerical, graph, race, cache-policy, allocation or latency tests. Selected fulltext passages were read, not every figure/section. No author files, canonical state, hypothesis status or service were changed.

A combined initial read was output-truncated; subsequent bounded source/fulltext reads supply the specific claims above. No exhaustive source/trace search is claimed.
