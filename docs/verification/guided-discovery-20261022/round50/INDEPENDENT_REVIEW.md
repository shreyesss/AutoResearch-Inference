# Independent round50 source review

## Verdict

Retain both selectively reusable components as **deferred and exposure-first**, with zero implementation or service qualification. P50-01 has a concrete source delta: enable the native consumer's programmatic launch and release the native sparse metadata grid early while keeping its existing dependency wait. P50-02 is a separate fixed cache-hint experiment, not evidence of a portable context-threshold policy. Neither is a demonstrated improvement for the current deployment.

The most decision-changing check is the actual pinned caller: `indexer_sparse_logits` defaults false and its source description explicitly warns of a short-context disadvantage. That statement is upstream source guidance, not a new benchmark. Enabling the sparse path to obtain a possible small PDL saving changes the baseline and is not justified by this packet. A retained exact-baseline launch/config record showing this route is active is the next useful evidence; more synthetic host-policy examples would not establish it.

## Independently inspected dependency chain

I read the native a7a metadata tail: every CTA participates in final completion accounting; the last CTA acquires producer writes, builds the schedule, writes the header and resets workspace counters. I read the native logits setup: TMA descriptor prefetch/barrier initialization/TMEM allocation/scale-padding initialization precede `cudaGridDependencySynchronize()`, and global metadata-header use follows it. The donor elected warp0 release precedes its completion atomic. Those support overlapping only the consumer's independent setup with the producer tail; they do not authorize reading unfinished metadata.

I also read the exact DeepJIT default/override/launch-attribute path and native sparse launch initializers. The inspected default is false, runtime merges call overrides, and the native initializers do not request PDL. Merely finding a wait instruction therefore did not establish an enabled launch mechanism. This is a source-path finding, not attestation of the live binary or a check of every external override.

Required adapter gates remain:

- Every launched metadata CTA, including no-work CTAs, must reach its release point; do not condition release only on useful rows. Preserve host handling of genuinely empty launches rather than inventing a zero-grid behavior.
- Preserve native finish-counter acquire/release, final writer, header/reset stores and all consumer waits. Early release is scheduling permission, not data publication.
- Verify launch attributes and dependency edges for the actual captured graph pair. Static instructions and generic graph support do not prove the deployed graph edge is correct.
- Consumer setup uses resources, including TMEM. Overlap is opportunistic; neither producer nor consumer may require co-residency to make progress. Donor fixed geometry does not prove native scheduling or speed.

These are unresolved implementation gates, not detected bugs in the current baseline.

## Scope, reuse and cache policy

The Python sparse wrapper builds expansion/scheduling only when `kernel_metadata is None`; otherwise it reuses them. Therefore the metadata-tail opportunity belongs to the first applicable consumer of that metadata instance. Multiplying donor savings by every indexer layer is invalid. Reused scheduling is not proof that different indexer layers share key contents, so it does not separately establish the profitability of the KV-data hint.

The cache-hint component must preserve addresses, valid predicates, data/scale copies and graph geometry. Native data loads and donor optional eviction priority can be compared without transplanting generated kernels. An eviction-priority hint does not remove any logical key reads or guarantee lower physical traffic. Repeated queries/steps may reuse keys, and evict-first can lose useful locality. A fixed on/off comparison is a cleaner eventual first arm than adopting the donor's constructor-time mean-context thresholds.

I inspected the donor Python policy and saved extracted-method probe. Its mean is a bound-vector scalar, potentially weighted by flattened verification rows; it is not a selected-byte or reuse-distance measurement. Changing bound context vectors after construction makes the old scalar a stale performance policy, not an arithmetic-correctness failure. The seven inert-stub cases and mutation control are appropriately limited to host logic. I did **not** rerun them, import torch/the donor module, instantiate a plan, or execute CUDA.

The dense-path follow-up is a useful stopping decision: the retained dense source already has early release, while its metadata construction/copy occurs outside the inline pair assumed by this donor. A missing launch override alone is insufficient to transfer the sparse-pair benefit. A different Q-producer pair would require its own dependency/exposure evidence.

## Evaluation and priority

Keep PDL and cache hints separate initially, then test interaction only if each is useful. Measure first-consumer and reused-schedule calls separately and include subsequent cache consumers, not only a cold isolated pair. Exact valid logits/selected identities, padding, dynamic contexts and captured replay remain correctness gates. Source-level absence and donor claimed single-digit chain improvements provide no target ITL Amdahl fraction.

These are distinct from NQ33 CTA-count scheduling, MF19 activation-quantization stores and WP38 routed-weight packet/cache work. That distinction does not increase priority: route exposure, producer-tail/setup time and useful key reuse remain unmeasured. No new hypothesis identity or status transition was performed by this review.

## Evidence and limitations

All 75 frozen author-file hashes and the author manifest pin were checked. Selected target copies were compared with the existing c455 tree. I inspected selected native kernels, DeepJIT defaults/runtime/attribute binding, donor release/policy and target caller/config; I did not audit every generated donor instruction, reproduce sanitizer claims, or independently fetch repositories.

One initial bounded multi-file grep guessed filename prefixes incorrectly and emitted missing-file errors plus truncated output. `rg --files` resolved the actual retained paths, then bounded reads were used. This review does not treat the truncated search as exhaustive evidence. No network, GPU, model/native imports or serving changes occurred. Separate authorized source-only retention work may run concurrently; it is not a scientific test of these mechanisms.
