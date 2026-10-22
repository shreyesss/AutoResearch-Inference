# Round110 — FV86 flag ownership and launch adapter

## Decision

**A bounded source-level adapter is feasible without a new kernel launch or a new tensor allocation in the inspected branch.** It uses an otherwise unused first-row cell of the existing residual buffer as a per-current-request Boolean. FV86 remains the same deferred hypothesis. This is a concrete implementation handoff, not implemented serving code, native numerical validation, exposure measurement or a promotion.

The most important unresolved gate is preserving the original terminal predicate after moving it into another kernel: the stored FP32 cumulative ratio, `exp`, indexed RNG, token position and inclusive `<=` must match the native path. Source identity alone does not certify compiled identity. No GPU, Triton, torch/model/native import, build, serving change, cloud request or canonical write occurred.

## Inputs and source pin

Read frozen rounds86,89,91 and94. Round86 supplies the terminal-pass idea and rejected interior-bound shortcut. Round89's ideal fixed-policy round estimator does not establish finite-precision AV flag semantics and is not used here. Round91 identifies the scheduled-versus-admitted counter gap; round94 provides bounds without pretending that exact terminal exposure is known.

Ten selected source files were matched byte-for-byte to the retained committed-object archive for `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; archive SHA `04261cf1228cf12fcf3f5256096ad31cdf8e273d5158234f0b1f8f4594e90a67`. The planned model remains Flash-1017 at `1bae0e…`, TP1 / DP4 / EP4, baseline d464. No live image attestation is inferred. No new paper or PR fetch was needed because the question was buffer ownership and existing control flow.

## Selected interface

For current request row r, let `[s,e)` be its effective sampler logits interval and m=e-s-1. Reserve `local_residual_mass[s,0]` for FP32 Boolean 0/1. Ownership is **verification-call batch row**, not persistent state slot. The latter continues to select seed, temperature and cached draft logits.

This cell is already unused by the original mass path. `_compute_local_residual_mass_kernel` returns for local position0. Its stores otherwise target interior rows, and `_compute_global_residual_mass` is read from rejection only for the next row, at least s+1. No resample kernel consumes this buffer. Therefore the first-row cell can carry metadata without overwriting a ratio or residual needed by the original path, under the existing packed-row invariant.

Move the existing conditional residual allocation before the cumulative-ratio launch. That launch resets the cell false for every actual request before greedy early return, tracks validity during the unchanged ratio loop, and writes true only for m>=2 with all admitted IDs valid and the unchanged terminal test passing. Add seed/position and residual-pointer parameters. The residual grid recovers s as `logit_idx-expanded_local_pos[logit_idx]`; the rejection grid already has s from `cu_num_logits`.

The six source launch stages remain stats, cumulative, residual, rejection, resample and insertion. A dedicated new flag buffer remains a legitimate fallback if the reserved-cell contract changes; avoiding a tiny allocation is not a correctness requirement. Here, the existing disjoint scratch cell supports the no-extra-allocation option. Allocation lifetime and kernel-resource changes are not claimed cost-free.

## Freshness, mapping and skipped-path audit

The writer launches once per actual request using `cu_num_logits.shape[0]-1`. It must reset the flag before greedy return, not merely set successful rows. Zero/one-draft requests stay false. Any placeholder, including grammar-invalid verification copies, forces fallback. There is no request-slot cache to invalidate across iterations: each call's actual rows get new writes before consumers.

AV reallocation writes final GPU cumulative boundaries before `expand_idx_mapping`. The expansion kernel writes local position `block` at `start+block`, establishing the consumer address equation. Reordering persistent slots does not affect ownership: current cumulative starts and current expansion agree, while idx_mapping still chooses each request's seed/temp/q state. Chunked verification rebases logits and cumulative starts together, leaving request-relative positions unchanged. AV is constrained to a single logit chunk by the existing sampler code, which explicitly avoids using stale CPU sums for AV chunk boundaries.

Model graph padding is distinct from sampler logits. The normal source path selects hidden rows using `input_batch.logits_indices` before computing logits; its sampler mappings cover selected logits, not arbitrary padded hidden rows. The initial scope therefore does not invent dummy flag writers for model-only padding. Arbitrarily padded or zero-length external sampler intervals, multi-bonus diffusion paths, custom samplers and unverified PCP partitioning are outside the proposed initial arm. TP1 is the planned target; a sharder source was inspected as context, not used to claim broad multi-TP support.

For true flags, rejection writes all m valid draft IDs, sets accepted length m, skips the old acceptance loop and reaches the original common tail. The common tail still stores the count and rejected logsumexp values. It does not compute rejected normalization when accepted length equals m. Recovery selects the unchanged bonus row, and insertion performs the original increment and bonus store. Omitted residual partials are never read. False flags preserve all original branches. Watermark recovery inputs and actual bonus sampling remain unchanged; this is not an independent watermark qualification.

The full interface, storage proof and path table are in `PATCH_CONTRACT.md`. No executable target patch has been written.

## Arithmetic and RNG boundary

Keep every existing ratio store. The producer terminal predicate must consume the same stored FP32 value at e-2, use step m-1, request seed from current idx_mapping, and position at e-2. Preserve `tl_rand32(...,includes_zero=False)` and **`u <= h`**. A true terminal pass determines the latest passing length independently of earlier tests only when all admitted drafts are valid. The producer cannot use the donor's strict comparison, interior `coin>=ratio` shortcut, a differently rounded expression, or a scheduler-length guess.

The seed helper and uniform call are indexed/stateless in source. Skipping earlier coin evaluations does not advance a persistent RNG state, but compiled scalar casts, arithmetic and RNG lowering still need native inspection. A failed terminal test adds a scalar producer calculation and the original rejection path repeats it; no free-work claim is made. NaN terminal comparisons stay false and use fallback. No new nonfinite sanitization is introduced.

## Verification actually performed

Executed stdlib source copying/hash comparison and a Python AST audit; none imports a target module. The audit checks six launch sites and their order, existing residual allocation placement, first-row guard before residual stores, the sole direct mass-reader function, the native inclusive comparator, mapping-writer structure, AV-before-expansion source order, absence of local-mass input from resampling and the seed/uniform helper bodies. Thirteen exact claims are checked against ten prepared source records.

These checks establish source structure and fail on changed assumptions. They do not execute the proposed adapter, simulate AV, establish memory visibility, validate native sampling distributions or measure performance. No new scalar workload sweep was added. A broad initial grep was truncated, then narrowed to the exact files; one guessed old model-state path was absent and was corrected to `deepseek_v41/nvidia/model_state.py`. Neither failed lookup was treated as evidence of absent behavior.

## What this changes and what remains

The ownership ambiguity is reduced to a concrete, local interface. A persistent-slot flag or a new mapping array is unnecessary in this pin. The source order also supplies a fresh writer for every eligible reader, including AV and reused request-state slots. This makes a future implementation smaller and reviewable; it does not resolve its native numerical gate or benefit.

The next decisive check requires separately authorized implementation: inspect compiled stored-ratio/exp/RNG equivalence, poison omitted mass storage, and compare valid sampled IDs, counts and relevant output stores for forced true/false/greedy/zero/one/placeholder/reordered/AV cases. Capture/replay and allocator lifetimes need their own native check. Do not add a host synchronization per request to count flags.

There is still no compatible target measurement of eligible terminal passes or exposed residual time. Existing counter bounds from94 remain applicable only with verified branch identity. Existing Mooncake/agent-p75 workloads remain the service comparator; no new benchmark is needed merely to test the interface. No ROI, latency improvement or additional omitted bytes beyond the original86 ceiling is claimed. Yield: one same-FV86 adapter refinement, zero new hypothesis identities, zero runtime qualifications.
