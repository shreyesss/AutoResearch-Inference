# Independent round56 source review

**Agree with zero-new, closed direct-port premise.** This review validates the narrow existing native tail support and the resulting cost-model correction. It does not qualify M01 or show measured target padding cost.

## Source result

The retained scheduler calculates each expert task's valid M from remaining rows bounded by BLOCK_M, then rounds the instruction extent to16. The SM100 MMA warp swaps A/B and updates UMMA N for every task. The newly pinned helper writes n_dim_=umma_n>>3, so the method name is backed by an actual instruction-descriptor field update. I verified the exact exported source body against the retained helper bytes and revision fingerprint.

The two CTA ranks select adjacent weight/output N blocks. The nonleader input begins at half the aligned live token extent, while a leader issues the cooperating two-CTA MMA. The inspected donor TUNING tail-split feature instead requires a two-CTA token cluster with an odd number of independent CTA token tiles; its paired-task reinterpretation changes weight loads and completion accounting. That missing-orphan-CTA premise cannot be transferred to this target merely because both use two CTAs. Donor benchmark and correctness assertions remain author claims, not independently executed results.

## Arithmetic versus remaining costs

An estimate that treats every expert tail as BLOCK_M tensor-core rows misses native dynamic extent. Rounding within16 remains. This source does not establish proportional cycle savings or that issue throughput scales with descriptor N. No synthetic alignment exercise is needed to strengthen the source finding.

The activation TMA shape remains LOAD_BLOCK_M=BLOCK_M/2 with fixed shared-memory transaction bytes. Weight tiles, scale movement, ring storage/counts and task/resource footprint are not eliminated by narrowing descriptor N. Some epilogue loads are already predicated by valid store blocks and release their stage early. A future cost model must separate instruction extent, fixed transfer/resource costs and task count; summing all of these as independent removable padding would double count. M01 may still benefit from tactics, occupancy or actual physical expert skew, but source-only row counts cannot forecast its ITL benefit.

## Stop and reopen

Stop a direct orphan-tail port and stop using ceil(n_e/BLOCK_M)*BLOCK_M as this path's executed tensor-instruction extent. Reopen only for a precisely identified residual operation and compatible existing per-step/rank physical receive histogram, selected legal tactic and baseline. Those records remain missing; do not replace them with arbitrary synthetic routing distributions. If a new schedule becomes justified, completion counters, ring reclamation, scale layout and actual numeric contract precede any timing.

This is selective source review, not a complete paper or donor implementation audit. All24 author artifact hashes were checked; no original was edited. No GPU, native build/model import, online query, timing experiment, canonical mutation or scientific state transition was performed.
