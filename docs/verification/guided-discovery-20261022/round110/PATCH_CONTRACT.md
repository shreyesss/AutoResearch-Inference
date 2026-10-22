# FV86 flag adapter: proposed source contract, not executable patch

This is a design against callgideon/vLLM c455786. No serving code was edited. Initial scope is the inspected Flash-1017 one-bonus-token rejection sampler, full draft logits, block verification, and its existing valid packed logits slices. No general support for arbitrary diffusion/PCP/multi-bonus or malformed metadata is claimed.

## Ownership choice

Use a **current-verification-call, batch-row-owned flag**, physically stored in an unused residual-buffer cell:

- Request row `r` owns logits interval `[s,e) = [cu_num_logits[r], cu_num_logits[r+1])`.
- Its admitted draft count is `m=e-s-1`.
- Reserve `local_residual_mass[s,0]` as an exactly representable FP32 Boolean `0.0` or `1.0`.
- This is not a persistent request-state slot. Persistent indices continue to select temperature, seeds and cached draft logits only.

Why the cell is available in this pin: the residual writer returns for `expanded_local_pos==0`; its only direct mass-reader helper is called from rejection at `logit_idx+1`, never at `s`. Other residual columns of the first row remain unused. Do not modify cumulative ratio values, encode bits in their sign, or share storage with a live mass cell.

The source footprint proof is structural: current residual stores belong only to interior rows `s<j<e-1` with valid next draft and nongreedy mode, over vocabulary blocks. Flag writes belong only to `(s,0)`. Distinct nonempty request intervals have distinct starts. Under the existing packed mapping invariant, the write sets are disjoint. This proves address ownership at source level, not compiled visibility/race behavior.

A dedicated explicit flag tensor is a simpler fallback if this scratch contract becomes invalid in another revision. Avoiding a tiny allocation is not a correctness prerequisite. The inspected revision permits scratch reuse, so an extra allocation is not inherently required.

## Host boundary

In `rejection_sample`, move the existing conditional allocation of `local_residual_mass[num_logits,vocab_num_blocks]` to before `_compute_cumulative_log_p_kernel`. Keep allocation conditional on block verification plus full draft logits. Do not allocate it for one-hot or ordinary rejection solely for this flag.

Pass its pointer/stride, seed and position pointers to the cumulative launch, plus a compile-time feature guard. Add only the flag read and branch in residual/rejection. The existing launch sequence stays:

`stats -> cumulative ratios + flag -> residual partials -> rejection -> resample -> insert`.

All original ratio stores remain. No new memset, host readback, prefix map, kernel, synchronization launch or persistent buffer is needed at source level. Moving the allocation changes its lifetime slightly; allocator/capture/resource behavior remains an implementation gate, not a measured zero cost.

## Writer: cumulative-ratio kernel

For every actual request program in the opted-in full-q block branch:

1. Load its current `s,e`; initialize `local_residual_mass[s,0]=0.0` **before the existing greedy return**. This includes zero/one-draft and placeholder requests. The target layout gives every actual request at least its bonus row; do not apply this to unsupported zero-length intervals.
2. Leave the existing cumulative loop and stores intact. Track whether every admitted `draft_sampled[s+i+1]` is valid. Do not break the cumulative loop early on a placeholder or substitute a prefix inferred from scheduler counts.
3. Only when `m>=2`, nongreedy, and all admitted IDs are valid, use terminal index `t=e-2` and step `m-1`.
4. Obtain the **same stored FP32** `cumulative_log_p[t]` used by the original reader, then apply the same `tl.exp`. Do not use an algebraically equivalent unstored cumulative expression as a proof of parity. A forced reload or a verified exact FP32 SSA representation is an implementation choice that must be inspected after compilation; source alone cannot guarantee store forwarding/reassociation behavior.
5. Generate the terminal coin by the same helpers: `spec_step_seed(seed[idx_mapping[r]],m-1)`, then `tl_rand32(step_seed,pos[t],includes_zero=False)`. These helpers are indexed/stateless in the inspected source; omitting earlier calls does not advance a mutable RNG stream. Preserve casts, `_TL_RAND_MIN` behavior, offset and step.
6. Write `1.0` only for the original **`u <= exp(stored_ratio)`** test. NaN comparisons remain false, and failed tests retain zero. No donor `<` or interior bound is substituted.

A false terminal result duplicates a small scalar computation that the ordinary rejection path will repeat. It does not save that work. The cumulative producer may compile differently after adding state/helpers; native parity is not established by this design.

## Residual consumer

Keep the existing first-row/bonus/placeholder/greedy guards. Before any vocabulary reads, compute `s = logit_idx - expanded_local_pos[logit_idx]` and read `local_residual_mass[s,0]`. If true, return without a partial-mass store. Do not load a flag using persistent `expanded_idx_mapping` as a batch-row index.

The mapping writer stores local position `block` at `s+block`; therefore this subtraction recovers the current request start. AV runs before expansion, and expansion uses the resulting GPU `cu_num_logits`. Request-chunk slicing rebases `cu_num_logits` and logits together, while preserving request-local positions. No stale CPU cumulative sums enter the flag address.

The flag read can be placed after existing cheap guards so first/bonus/greedy rows avoid an unnecessary metadata load. All eligible interior readers still have a fresh writer in the preceding cumulative launch. Skipped partial-mass memory may remain stale or poisoned; correctness depends on the next consumer branch, not clearing it.

## Rejection consumer and common tail

Under block/full-q/feature guards, read the same `local_residual_mass[s,0]`. If true:

- Set `accepted_length=m`.
- Write exactly the same accepted draft token IDs to `sampled[r,0:m]`, reading the existing verification draft argument.
- Skip the entire old acceptance loop, so no omitted residual partial is read.
- Keep `target_lse=draft_lse=0.0` initialization and reach the original common tail. Do not early-return past rejected-step and logsumexp stores.

If false, execute the original loop unchanged, including placeholder termination, greedy argmax behavior and all interior floating-point tests. The original common tail writes `num_sampled/accepted_length` and both rejected logsumexp arrays. On a full pass, its `accepted_length < m` normalization branch is false, exactly as before.

Resample sees `start+accepted_length=e-1`, uses the bonus target logits, and does not consume local residual mass. Existing watermark/seed/context processing stays in that kernel. Insertion increments the count and stores the bonus exactly as before. Preserve valid output slots; unrelated unused sampled padding is not newly specified.

## Freshness and exclusions matrix

| Path | Flag ownership/writer | Reader consequence |
|---|---|---|
| Eligible full pass | Current `s,0` reset then true after unchanged ratio stores | Interior scans skipped; rejection fast path writes all drafts; original bonus path |
| Terminal fail | Current cell remains false | Existing residual and rejection paths |
| Greedy request | Reset false before greedy producer return | Original greedy stats/argmax; no skipped residual reads |
| Zero or one admitted draft | Reset false; no terminal optimization | Original path; no beneficial interior row |
| Any admitted placeholder / grammar invalidation | Reset false; validity uses `verify_draft_sampled` already passed to native helper | Original termination and recovery; no assumed shorter block |
| AV variable admission | Writer and expansion use final GPU cumulative boundaries | No CPU scheduled-count substitution |
| Reordered persistent slots / next invocation | New batch starts define cells; all actual writers reset | No request-slot flag survives into a different row |
| Request-chunk invocation | Local logits and cumulative boundaries are rebased together | Fresh private scratch for the invocation; local positions stay relative |
| Model graph padding | Sampler gathers selected logits rows, not padded model hidden rows | No flag for nonexistent sampler row; arbitrary externally padded sampler metadata is unsupported |
| One-hot / synthetic / non-block | Feature disabled; synthetic+block remains existing assertion | No flag pointer read; existing behavior |
| NaN terminal ratio | Native comparison false | Ordinary fallback; do not sanitize it into a pass |
| Watermarked bonus | Flag changes acceptance control only | Existing bonus/context/watermark processing preserved; native gate still required |
| Unsupported PCP/multi-bonus/custom sampler | Initial scope disabled | No generalized ownership claim |

## Remaining decisive gates

Source/AST establishes a bounded interface and disjoint scratch cells. It cannot establish compiled terminal arithmetic/RNG identity, sanitizer race freedom, capture allocator equivalence, execution cost or target full-pass frequency. Future authorized implementation must inspect the stored-ratio boundary and helper lowering, poison omitted residual cells, and compare valid IDs/counts/logsumexp outputs under the same flags and mappings. Negative controls must force every fallback branch and permute persistent state indices. No extra scalar case sweep substitutes for those native checks.
