# Independent round39 source review

**Verdict: agree with zero new hypothesis identities. Preserve the target-statistics producer component as parked source evidence. No implementation, target numerical or service qualification.** Direct FlashSampling substitution is incompatible with the required verifier interface. The recent FlashInfer component is reusable in principle, but the actual exposed work removed and compatible small-row producer are missing.

## What was checked

Read the frozen author report, screened component, pinned FlashSampling core and standalone baseline, FlashInfer5752 generated producer/backend, and c455 target LM head, logits processor, sampler and rejection consumer. Verified every author manifest hash. Compared the exact C025-family card and round25 dispositions. No provider calls, GPU/backend imports, model, compilation or new runtime benchmark. Source-formula examples below are counterexamples to broad equivalence, not target activations.

An initial file-location objection was corrected: the fused FlashSampling kernel is defined later in its retained core.py, not in a missing separate file. The separately retained tl_matmul.py casts to BF16, but that is the ordinary matmul baseline and cannot establish the fused sampling kernel's rounding. One initial attempt to parse prior-inventory.json found the retained empty failed receipt; the two successful paginated inventories and exact prior card were used instead.

## 1. Direct sampling changes both an arithmetic boundary and the consumer contract

FlashSampling core.py546–602 uses FP32 dot accumulation, applies temperature, and adds Gumbel noise before any BF16 cast. Its optional logits output is FP32. In contrast, the conditional BF16-head reference materializes rounded logits before later statistics/sampling. A mathematically exact sampler for its own FP32 logits need not sample the same distribution as the BF16 reference.

A concrete exact-input example makes the difference possible even with BF16 operands: hidden vector `[1, 2^-5]` and two weight rows `[1, 2^-5]`, `[1, 0]` produce FP32 results `[1+2^-10, 1]`; BF16 rounds both to1. A fixed noise difference2^-11 changes the winning token between the raw and rounded logits. This is a finite arithmetic argument, not a GEMM execution or occurrence estimate.

**Important scope:** pinned `LogitsProcessor._apply_head` explicitly honors a configurable `head_dtype`, including an FP32-output torch.mm route. The retained model config's BF16 dtype does not attest the live head override. Thus the BF16 counterexample rejects blanket compatibility under the proposed BF16 reference; it does not assert every c455 deployment produces BF16 logits. The author's actual-dtype admission gate is necessary.

The second incompatibility is independent of rounding. Native DSpark block verification uses target and draft distributions, cumulative ratios and full-distribution residual mass, followed by recovery/bonus sampling. Returning one categorical target sample cannot supply those quantities. The author's two-category ordinary-rejection residual example correctly disproves a generic substitution claim; it is explicitly not a simulation of the actual block verifier. Keeping/recomputing sufficient target information could define a larger implementation, but the donor does not establish that implementation here.

## 2. FlashInfer5752 contains the selectively reusable component

At pinned67155685 the generated producer converts each accumulator to BF16 and back to FP32 before max/sumexp calculations, stores BF16 logits, and writes per256-column `(max,sumexp)` partials. This is actual implemented source evidence for producer statistics while retaining logits. It avoids the specific raw-FP32 bypass of the FlashSampling path.

It remains training-shape-specialized: H6144, V154880,605 tiles,128-row tiles and two-CTA scheduling. Target H5120/V129280 means505 width256 tiles, whereas the native verifier uses16 width8192 blocks. Neither divisibility nor changing constants proves a competitive tiny-row kernel.

Global reduction still exists. Native local target statistics and draft statistics share one kernel; replacing only target statistics leaves draft work and its launch. An adapter must either consolidate producer partials into the existing8192-column partitions, or change all downstream reduction contracts consistently. A supplied global LSE is not a drop-in replacement for local buffers also used by cumulative-ratio, residual and fallback paths. Greedy rows additionally require argmax; the proposed temp1-only eligibility should not silently cover them.

The donor's sequential `expf` recurrence and native Triton reduction have different floating evaluation orders. BF16-identical logits are necessary but do not prove identical LSE, near-threshold rejection, RNG consumption or output distribution. The donor initializes `pmax=-3e38`; native `_compute_max_and_sumexp` explicitly handles all-negative-infinity blocks. For an all-inf masked tile the donor partial max can remain a finite sentinel with zero sum, rather than native negative infinity/zero. That is a concrete buffer-contract difference; it is not evidence that an eligible unmasked finite LM head produces such a tile. Empty, nonfinite and masking behavior therefore remain real admission/differential gates.

## 3. Producer statistics must describe the logits the verifier actually sees

c455 rejection_sampler._verify calls `apply_sampling_params` before `rejection_sample`. The latter consumes processed logits. The upstream runner may also mutate grammar-constrained logits. When processing is enabled, penalties, bias, forced markers, temperature and truncation can invalidate raw head partials. Saved temperature1/top_p1 alone does not prove all those paths absent.

Round25 already established the no-processing early return, which avoids a full FP32 copy. Reproposing that copy removal would be a duplicate. Here a smaller potentially absent interface remains: expose compatible producer statistics for eligible rows. A useful implementation must explicitly fall back for unsupported processing, preserve ragged request/bonus mappings, and handle the minimum target/draft vocabulary width. Full target logits remain required by target token lookup, residual/recovery and optional output interfaces.

## 4. Work accounting supports low priority, not rejection of the component

At V129280, one BF16 target scan is258,560 logical bytes per eligible nonbonus row. The target-stat branch may disappear; the complete current target+draft kernel does not automatically disappear. Original target output storage, draft reads, residual/recovery reads, producer partial writes and global reductions remain. Caches, launch scheduling and GEMM register/epilogue cost decide net performance. The ratio to one full head-weight read is arithmetic context, not a memory bottleneck diagnosis or latency ceiling.

The three controls in the author report are appropriate if revisited: current producer/verifier; adapted producer retaining logits with old stats path; same adapted producer plus partial reuse and draft-only stats. This separates producer regression from fusion benefit. A faster isolated statistic stage does not compensate an unmeasured slower head by assertion. Existing Mooncake and agent-p75 are adequate future service workloads; numerical boundary and RNG/acceptance checks are additional correctness tests, not a new service evaluator.

## 5. Prior comparison and stop condition

Exact C025-family card `hypothesis:cea206f05572cfec802b0bb21db6ea579763d4035d917ebeaf565e1f9d2dd75c` targets sequential draft Markov sampling/storage around five bias GEMMs on an H200 baseline. This source lead changes target projection→normalization, so it is not the same implementation. That distinction does not license transplanting C025 component timings or creating a qualified idea. Round25 greedy substitution/copy-removal screens still stand.

Keep zero new cards at this stage. Reopen on an already-generated exact baseline record showing head dtype/backend, post-head mutation eligibility and meaningful exposed target-stat cost, or a compatible small-row producer with exact consumer contract. Do not commission more synthetic fixtures simply to increase the evidence count. No claim that the component is impossible, no inherited donor speedup, and no promised long-output ITL improvement.
