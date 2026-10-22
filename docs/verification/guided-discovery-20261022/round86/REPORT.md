# Round86 — terminal-prefix gating of block residual work

## Decision

**Retain FV86 as a deferred, source-backed experiment proposal; no typed identity or implementation created.** The selective intervention is narrower than the donor's general lazy verifier: when a complete valid native DSpark block passes its unchanged terminal-prefix test, skip its interior vocabulary residual scans and use a matching acceptance fast path. Failed or ineligible blocks keep the existing parallel scans. No target/proposal distribution, draft budget, confidence policy or AV setting is changed.

This is not an accepted performance improvement. No GPU/native imports, model tensors, compiler, serving runtime, canonical or cloud writes ran. Baseline remains planned Flash1017/callgideon-vLLM c4557869393db4d75c483d92edd02a5125500883, target temperature1/top_p1, DSpark5 and baseline `d4640b183a115b67c1e0365e34d22349c5a72fa9df780ec71c41b16f7a543279`.

## Why this follow-up

Root's round85 local PR search surfaced [SGLang42297](https://github.com/sgl-project/sglang/pull/42297). The current detail, ten changed-file patches, reviews, exact head implementation and tests were retained. Head is `3e5cd56c297838abfdd7d760e77c58948a39ee9c`, from `maocheng23/sglang`; the PR is merged. The PR attributes its algorithm to *Block Verification Accelerates Speculative Decoding* (2403.10444). No fresh paper fulltext was needed or counted: the current native implementation already uses block verification, and the unresolved question is selective execution of its existing predicates.

Complete149-card prior inventory from round84 was reused, with round39 and42 reports read directly. Round42 rejected an interior `p==1` residual-elision shortcut after a finite-precision counterexample. Round39 considered producer logit statistics, and C025/round85 concern draft proposal sampling. FV86 is the same broad residual-cost family as42, but a different predicate and control change. It does not revive that rejected numerical assumption or rebrand C025.

A readonly literal paper lookup found six references, including the existing target source and donor PR. No broad provider query was added; new synonyms would not resolve this source dependency. The donor was imported from round85's isolated corpus, then hydrated through three logical GitHub reads and a two-file `investigate`. The exact target source was imported using existing canonical identities into an isolated state. Initialization completed before any dependent mutation. No canonical writes occurred.

## Donor decomposition and limits

The donor computes prefix ratios forward, tests prefixes longest-first, and stops after the first passing test. It avoids a vocabulary reduction when the coin is at least the ratio, using the real-arithmetic bound `h<=r`. It reuses a chosen residual mass for its final CDF normalizer. Its tests explicitly use **strict `<`**, including equality-boundary rejection, whereas the target's native block branch uses **`<=`**.

These are three separate components:

1. **Longest-first selection:** permits earlier decisions to be omitted once a later passing prefix is known.
2. **General bound guard:** skips an unresolved interior reduction using `coin>=r`; not yet equivalent to the target's floating implementation.
3. **Residual normalizer reuse:** useful in the donor's CDF sampler, but target recovery uses unnormalized residual logits with Gumbel/argmax. There is no identical normalization scan to remove blindly.

The donor's historical full-model comparison predates this sampler optimization and has variable per-seed throughput. Its GB300 sampler microbench uses FP32 probability buffers, constructed q, vocabulary131072 and different reduction tiles/warps. Its reported tests include native source parity and joint-distribution checks, but those were not rerun here and do not validate target c455. A sequential vocabulary loop over unresolved prefixes is also a different parallelism choice from the target's independent row/vocabulary-block grid. No donor percentage is transferred.

## Exact native dependency

The target first computes normalization statistics and cumulative log ratios. With full probabilistic draft logits it launches `_compute_local_residual_mass_kernel` over `(num_logits,vocab_num_blocks)`, with8192 vocabulary columns per program. Guards already omit first/bonus rows, placeholder ends and greedy requests. At five drafts, at most four interior rows remain.

`_rejection_kernel` then walks admitted tokens in order. It generates indexed uniforms with `spec_step_seed(seed,i)` and the token position. Interior tests consume the next row's residual mass and calculate `h=mass/(mass+1-r)` with the existing fallback. The last admitted valid token has no following draft and uses **`h=r` directly**. Each passing test updates the latest accepted length. Therefore, if this terminal test passes, every earlier acceptance outcome is irrelevant to final accepted length. The original kernel still writes draft token IDs along the way; an optimized branch must reproduce these stores.

The proposed first arm requires all admitted draft IDs valid. Any placeholder falls back rather than guessing a shorter terminal location. Actual admitted length comes from `cu_num_logits`; AV lengths2–5 may qualify without changing AV. Zero/one-draft and greedy requests have no selected benefit and remain on their original path. One-hot drafting and synthetic acceptance do not use this intervention.

After a complete pass, recovery already chooses the native bonus row and uses target logits. Existing bonus sampling, watermark handling if active, resampled-token insertion and count updates remain unchanged. We do not substitute a new random generator or sampler.

## Minimal proposed implementation boundary

A fresh per-current-request flag can be produced after cumulative ratios. Prefer doing so inside the existing cumulative-ratio launch if emitted arithmetic and ownership are validated; a separate prepass is an explicit evaluator control with added launch cost, not a free optimization.

The flag must be initialized false before greedy/zero/padded early returns; its row/state-slot mapping must agree with `expanded_idx_mapping` in the residual grid and the current request mapping in rejection. Reused slots and changed request order cannot inherit a previous flag. The same helper, step, position, stored FP32 ratio, `exp`, and **`<=` boundary** must reproduce the original terminal decision. Moving from a stored/reloaded scalar to a register expression is not automatically a compiled bit-equivalence proof.

For flagged requests, residual programs return before vocabulary reads. The rejection fast path writes all accepted draft IDs and accepted count, then reaches the unchanged bonus/recovery path. It must not read omitted/uninitialized residual storage. Unflagged requests use the existing parallel residual and rejection flow; no sequential unresolved-prefix scan is introduced. Existing target/proposal logits and confidence/AV policy are untouched.

This creates one small flag/control contract. It does not require a new cache, scheduler, model weights, verifier probability law, or serving workload. Graph capture and concurrent request ownership still require future native validation.

## Completed CPU/source falsifiers

`control_probe.py/json` contains ten source-inspired control cases, not extracted Triton execution. They cover final pass, native equality boundary, final failure with earlier acceptance, no acceptance, shortened AV block, one/zero drafts, placeholder followed by an apparent later pass, NaN terminal fallback and irrelevant earlier NaN when the terminal test passes. The reference-style latest-pass result and accepted token stores match the proposed terminal fast path in these cases. Negative controls show why a strict donor comparison, any-earlier-pass flag, ignored placeholders, or batch-row/state-slot confusion is unsafe. Fresh flag initialization is checked as a host bookkeeping condition only.

A separate binary32 operation-order control reinforces42's warning. For `r=mass=round32(0.3)`, `round32(round32(mass+1)-r)` is0.9999999403953552 and computed `h` is0.30000004172325134, larger than `r=0.30000001192092896`. A scalar coin at h passes native `<=` but would be skipped by `coin>=r`. This is a counterexample to unqualified source-algebra transfer, not an observed model trajectory or compiled Triton bug. Compiler reassociation or actual RNG reachability can matter. The narrow terminal arm never uses this interior bound.

No target probability/distributional validation was executed. The exact source quotes and head-pinned donor tests establish what must be preserved, not that a runtime port already preserves it.

## Benefit bound, null branch and evaluator

For vocabulary129280 and five drafts, assuming both input logit arrays are BF16, the maximum omitted residual-stage input reads per flagged request are **4×129280×(2+2)=2,068,480 logical bytes**. Exponentials/reductions may also be omitted. This is not HBM/PCIe traffic, elapsed time or client ITL: cache residency, repeated normalization metadata, contention and launch cost matter. Normalization, cumulative-ratio work, the residual-grid launch itself, proposal computation, bonus/recovery and token stores remain. At lengthm the analogous upper bound uses m−1 rows.

The key measurement is the joint distribution of **actual admitted valid draft length and accepted length**, or a directly equivalent terminal-pass counter. Average accepted length and separate per-depth cumulative counters do not establish that frequency under variable AV. There is no compatible saved trace here to supply it.

Support branch: many eligible complete passes, residual programs are exposed, and the flag/branch cost is smaller than the avoided work. Null branch: complete passes rare/blocks short, existing scans overlap or are cheap, added flag/branch work costs more, or exact native parity fails. No positive outcome is presumed.

When separately authorized, the smallest native gate compares sampled IDs/counts and all valid output stores for the same logits, seeds, positions and mappings across ragged lengths, AV, placeholders, ties, slot reuse and nonfinite fallback. Poison skipped residual storage to detect an accidental consumer. Inspect compiled terminal arithmetic and RNG helper parity. Then compare baseline, explicit-prepass control and fused-flag implementation under the same AV policy and unchanged5-step ceiling. Use existing Mooncake/agent-p75 matched serving evaluations; a residual-stage timeline and joint acceptance counter are mechanism diagnostics, not a new load harness. No GPU work is authorized now.

## Yield and remaining scope

One reused PR was fully hydrated, two exact donor files read, two pinned target files read, one deferred intervention proposed, zero implementation/service promotions and zero new typed identities. No new paper query/fulltext. All three donor components have dispositions; the useful subset is terminal-pass gating, the general numerical bound is gated, and CDF-normalizer reuse has no identical target consumer. The source/CPU diagnostic is completed; runtime implementation and benefit remain deferred.
