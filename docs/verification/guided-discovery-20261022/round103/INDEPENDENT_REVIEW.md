# Independent round103 native adapter review

## Verdict

**No blocking source contradiction found for the narrow explicitly seeded parity design.** This advances the same deferred SN98 by resolving a concrete interface and identifying a real seed-lifetime gap. “Source-feasible” means a coherent proposed patch boundary; it does not mean code exists, compiles, runs, preserves target numerics/cache state or improves service performance. Normal unseeded serving remains outside the admitted persistent-tape design until ownership is repaired or an alternative conditional-law argument is supplied.

Verified33 author hashes,20 target copies against exact c455,17 excerpt/line locations and3 retained benchmark copies. The only initial check failure was my multiline-line matcher failing to trim source indentation; exact excerpt/file hashes had already passed. Both checker versions and the failure explanation are retained. No target imports, numerical simulation, GPU, network or canonical mutation occurred.

## Effective seed lifetime is source-grounded

SamplingStates.add_request (`sample/states.py:41–58`) copies the public request seed to a local variable and draws a new int64 if it is None. It does not write that generated value back into SamplingParams. Runner.finish_requests (`model_runner.py:1164–1176`) unions preempted IDs into worker removals. Runner.add_requests (`1193–1236`) removes old state and calls sampler.add_request again. Therefore the same logical unseeded request can receive a new effective worker seed after re-add; the GPU slot array alone is not a durable request seed owner.

An explicit unchanged seed re-creates the same coordinate stream under the proposed primitive. This supports ArmA as a bounded parity design, not default-workload qualification. ArmB must own the effective seed across the actual preemption/re-prefill lifecycle while clearing it on genuine termination/incarnation replacement. Preserving public explicit-seed behavior does not require adding a new arbitrary incarnation salt. Conversely, mutating public `SamplingParams.seed` to preserve an originally implicit value can change `seeds_set`/`any_explicit_seed` backend eligibility; an effective-seed field/owner should distinguish this from changing the user-visible seed flag. In the initial full-support Gumbel arm the fused top-k/top-p sampler is already excluded, but broader modes need that distinction.

The saved workload YAMLs omit a request seed and the retained runner forwards only supplied fields. This is evidence of configured defaults, not proof of any executed payload or runtime override. It is correct to distinguish load-generator random_seed from model SamplingParams.seed. Fresh randomness on re-add is not, by itself, a demonstrated bug in native ratio sampling; it violates the stronger persistent-tape invariant this new mode proposes.

## Device row mapping and shifted comparison

`input_batch.py:410–465` selects trailing logit rows from query_end using each request's device cu_num_logits. `rejection_sampler.py:78–143` gathers the corresponding input token and absolute position and marks future prefill placeholders invalid. The native verification comparison at `rejection_sampler_utils.py:574` reads the candidate at logit_idx+1. Thus target row s+j predicts candidate s+j+1; s is the anchor, and e−1 is the bonus row. The proposed packer has the correct shift and emits the mismatch target draw as well as any matching prefix.

AV compact_batch explicitly leaves CPU cumulative counts as an upper bound for a nonzero compacted budget. reallocate_drafts constructs device cumulative logits from admitted capacities plus bonus count. The adapter must use those returned device offsets, not the old host arrays, and must preserve per-request rather than aggregate batch counts. The table correctly handles n=1 with one target draw and no comparison.

DFlash `_prepare_inputs` stores unclamped sample_pos=query_pos+1 for DSpark, while attention query positions may be clamped. `_sample_logits` then uses sample_pos−1. The target gather reads actual predecessor positions. This supports the stated key alignment for valid rows; replacing it with local row/step numbers, clamped positions, request slot or a new prompt-relative scheme would be a different contract. Preserve existing padding masks and real-request bounds. No finite address fixture was needed to establish these source relationships, and none would certify native AV/graph freshness.

## Counts and cache/output consumers

For m matched drafts and d admitted drafts, the proposed packer returns m+1 sampled outputs including correction/bonus. The existing helper (`input_batch.py:509–534`) then produces d−m rejected inputs, with both counts zeroed for unfinished prefill. `_post_update_kernel` (`558–615`) appends exactly num_sampled outputs and advances computed state by query_len−num_rejected. The correction token is emitted but not yet target-KV-computed. These meanings align with first-mismatch sampling.

DFlash context preparation (`dflash/speculator.py:674–724`) uses valid_ctx_end=ctx_end−num_rejected and initializes rejected suffix positions/slots without writing valid KV there. Keeping the count interface is consequently a useful source compatibility result. It is not proof of every CED/indexer/Engram/SWA state transition in executed code. Native differential cache checks remain necessary later.

The sample/pack must finish before the existing AsyncOutput copy boundary; preserve its early copy before postprocess/drafting. Scheduler stop trimming remains per-token, and later unconsumed speculative outputs must not become delivered-progress measurements. Existing EOS/stop policy is retained, rather than disabled to simplify parity. An ordinary no-draft request and a zero-admission row must agree with the same target tape; a mixed batch cannot inherit another request's count or mode.

## Admission, fallback and cache allocation

The explicit new proposal branch is essential. The existing object `draft_logits is None` branch means argmax; passing no cache argument to the Gumbel primitive is a separate change that suppresses cache-column seed mixing. `is_drafting=False` selects the target stream. Keep conditional Markov construction and confidence observation. Leaving the allocation present initially is a coherent scope reduction; it claims no capacity win and does not authorize later native rejection over unwritten/stale q values.

The initial whole-engine mode plus early unsupported-request admission is coherent. A batch-level switch to native because a later request is unsupported would break the already-admitted shared-tape contract. After tape-dependent invalidity, retain the same target draw at the correct prefix; never replace it with fresh independent native correction without a separate proof. The report correctly includes this distinction from review98.

`needs_logits_processing=False` alone is insufficient because grammar processing is outside that stage; the explicit grammar/custom/stateful exclusions are necessary. Runtime thinking budgets are distinct from template reasoning settings. Target support, temperature, precision, logprobs/sampling-mask/watermark/replay policy and distributed mode need actual admission checks. Neither a source flag nor the planned baseline attests live configuration. TP1 avoids one sharded-sampling extension, while DP4/EP4 ordering still remains unchanged in the proposed initial mode.

## Physical work and next decision

The127-column-block partial-array arithmetic is correct for vocabulary129280/BLOCK_SIZE1024: FP32 maxima plus int64 indices total1,524 logical bytes per target row; FP64 totals2,032. These are temporary storage sizes, not measured traffic or time. Full target draws on every admitted row and a packer add work; removing native ratio/residual stages may lose progress. Dense target logits, draft Markov passes, confidence/AV and cache operations remain. No speedup follows from these counts.

The source-design task has now provided a useful stopping point: an explicitly seeded, full-support, no-extra-processing parity arm with exact maps/counts and a separate unseeded ownership repair. Do not repeatedly prove the same scalar law. Subsequent native implementation/differential testing requires separate authorization; the user's GPU prohibition remains in force. Preserve SN98's deferred status and unknown ROI, and evaluate the ordinary unseeded workload only after its effective-seed ownership contract is actually implemented and checked.
