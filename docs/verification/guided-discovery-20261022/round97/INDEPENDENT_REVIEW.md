# Independent round97 review — selective Sinkhorn layout

**Verdict: enough source-specific evidence for a deferred tracking card and bounded implementation design, with the cost premise corrected below. No performance qualification.** The inspected native helper has scalar Comb ownership in lanes8–23; the donor's two-row parity-class layout is absent. This is distinct from altering iteration count, replacing the backend, modifying activation format, or changing mHC overlap policy. Round70's body-only lead now has actual component/source evidence. Unknown ROI alone is not grounds to discard it.

## Correction: operation counts and store ownership

The target repeated stage has2 row XOR shuffles plus2 column XOR shuffles. The donor has four columns, each with one XOR1, hence4 shuffle operations per source stage as well. It also gathers eight values at entry, while the target has two initial row-max shuffles. These are source-operation counts, not compiled SASS counts. The phrases 'source-level shuffle reduction' and 'despite fewer shuffle operations' in the frozen report must not be read as established reductions in total warp shuffle instructions. A possible advantage is a different dependency/ILP arrangement. It is not an established speedup and comes with replicated per-lane arithmetic and live values.

Both lane parity classes replicate eight values across the full warp; only final owner lanes0/1 store the donor's16 matrix elements. A mapping bijection proves address coverage, not a free inverse communication path. Restoring original16-lane scalar ownership requires actual value transport/register selection; keeping two-owner scalar stores instead changes ownership/work. Either can be an explicit adapter design, but its cost and all-warp masks must be represented. Do not copy vector stores casually or claim only two threads execute.

## Arithmetic and caller contracts

Native target performs first row max/exp, row multiply by approximate reciprocal followed by epsilon addition, first column reciprocal of(sum+epsilon), then19 row/column stages with epsilon in each denominator. Retain the target's parameterized count with planned20, target1e-6 epsilon, fmaxf/__expf and rcp.approx.ftz primitives and their operation placement. Donor2e-6 default, expf/max_noftz spellings and fast-math flags are not permission to change these. The scalar pairing check proves reduction grouping modulo commutation for16 positions, not compiled floating equivalence, NaN/signed-zero behavior, contraction or generated resources. Its positive reassociation counterexample is valid and correctly does not demonstrate a mismatch of the proposed matched tree.

Keep split completion waits, __syncwarp masks/barriers, Pre/Post stores and their ownership conditions, plus return of the original lane mix_value. The plain normal worker consumes returned Pre coefficients for collapse; returning a redistributed Comb register would be wrong. Shifted stores new Pre; plain does not. The actual same helper serves both paths, so initial deployment may be shifted-only but code compatibility must cover both or explicitly retain the old plain branch.

Register pressure matters: shifted Mix workers deallocate to40 registers; normal workers allocate80. Eight local coefficients plus temporary sums can increase pressure/spills. No register allocation, compiler scheduling or actual cost is measured here. The source-distinct mechanism survives this uncertainty, but a prototype must preserve a control path and inspect emitted resources before claiming progress.

## Exposure

The V2 model's mHC stream remains only for FULL capture with positions.shape[0] in1..16. The dispatch checks a supplied stream before Mega eligibility; those captured overlap shapes use separate TileLang coefficient work and are outside this initial patch. Token rows are not request concurrency. Other Mega gates include nonnullPre/norm, no auxiliary capture, SM100-family support and valid geometry. H5120/hc4 satisfies static geometry but does not attest the live backend. First/broadcast and Engram paths are separate, and eager warmup does not establish captured exposure. TileLang Python fragments do not establish its physical lane layout. No overlap mode should be disabled to manufacture an apparent gain.

## Proposed next decision

Register SL97 as deferred if a formal identity is desired: exact operation is coefficient register/lane redistribution within run_mix_task, fixed20 and unchanged target semantics. State the possible benefit as shorter exposed dependency work or better ILP, with total-shuffle reduction unproven and extra arithmetic/store transport explicit. Cheapest remaining design evidence is a concrete output-ownership/inverse-transfer plan within resource limits; next native work needs later authorization. Compare unchanged native helper versus the guarded layout on the same admitted shapes/backend, then whole-workload objective. Do not transfer donor whole-call timing, multiply by every layer, or add this benefit to MF19/other changes.

All original author inputs remain unchanged. This review is source/mathematical scrutiny only, with no GPU, native build or additional performance test. A preliminary source-view output was truncated and followed by bounded reads of the exact arithmetic, helper and dispatch sections; no whole-generated-file read claim is made.
