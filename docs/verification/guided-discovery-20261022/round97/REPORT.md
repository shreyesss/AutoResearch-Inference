# Round 97: selective two-lane Sinkhorn layout transfer

## Decision

Retain **SL97-01**, a source-supported, deferred component of the round70 mHC execution investigation: redistribute the four-by-four Sinkhorn matrix into two rows per lane parity class inside the existing DeepGEMM `run_mix_task`. Keep the current backend, twenty iterations, target arithmetic primitives, epsilon, split reduction, outputs, scheduler and synchronization. The pinned target has not already made this layout change. A different donor backend is not a reason to discard this separable component.

This is one investigated intervention and zero new formal hypothesis cards. It is ready for a bounded future implementation design, not qualified for deployment or demonstrated to improve ITL. No native code was edited, compiled, imported or executed. No GPU, model, serving, canonical-state or cloud operations were performed.

## Evidence and adaptive reading

Before retrieval, read round70's report, its independent review, the retained #6202 body and selected EqiForge `2609.12330v1` sections 4/7.3 and Figure 9. Round70 had body-screened this exact lead but had not established its absence from the native backend. That was the unresolved question; another keyword query would not answer it.

Selected-import reused the canonical #6202 record and versioned EqiForge fulltext into isolated state. Two API requests hydrated the exact PR detail and all 37 changed-file records. Five pinned raw-source requests then read the relevant old/new kernel, dispatcher, reciprocal helper and shifted variant. All seven requests succeeded; cache hit/miss receipts are retained. No new paper query or fulltext download was needed. EqiForge's real-arithmetic rewriting framework is background, not proof of native bit equivalence or of a target performance gain.

PR #6202 head is `yyihuang/flashinfer@8384ebb9db9e1a8ec440d5f10893723340a17e41`, base `8a215c822cf8ed34b87fc3ac2cec3c23a18556f1`, merged as `d853ff30e10ae1787067ec5d61c3154f7e517d14`. The donor dispatcher maps H5120, split40, plain/non-shared-scale to `f710...`; shifted/non-shared-scale maps to `41df...`. Both full files were inspected around the relevant coefficient path. The PR body says split40/27 variants changed while split20/16 stayed unchanged; only the selected split40 plain and shifted implementations received this full-file inspection. Do not generalize that read depth to every generated variant.

The donor uses `--use_fast_math`; its Python default `sinkhorn_eps=2e-6` differs from target `hc_eps=1e-6`. Its `expf` and `max_noftz` source spellings differ from target `__expf` and `fmaxf`-based reduction. Its whole-call B200/GB300 timings are donor observations, not performance evidence for the selective target patch. Generated-file changes also contain other refactoring, so this audit does not attribute all reported gains to the lane change.

## What is actually missing in the target

Pinned `vllm-project/DeepGEMM@a7a927731b109fdfec770df7c2a5be5d7e2216b5`, `epilogue/sm100_mega_mhc.cuh:16–103`, maps Pre to lanes0–3, Post4–7, and Comb8–23. Each Comb lane holds one scalar. Row reduction uses XOR2 then XOR1; column reduction uses XOR4 then XOR24. This sequence runs once for initial normalization and another nineteen times for the configured twenty iterations. There is no eight-element local row array in this function.

The donor gathers the sixteen Comb scalars into eight local registers per lane, duplicated across parity classes: even lanes hold rows0–1, odd lanes rows2–3. Row sums become register-local `(c0+c2)+(c1+c3)`. Each column combines its two local rows, exchanges the pair sum with XOR1, then normalizes both local elements. This is four column exchanges in source per normalization stage, not a claim that the entire iteration compiles to one shuffle instruction. All lanes execute the shuffles; only lanes0/1 store the sixteen Comb outputs. Two storage lanes do not mean a two-thread warp launch or an eightfold reduction of GPU work.

The target and donor both have `rcp.approx.ftz.f32` helpers. The transferable idea is the layout, while retaining target `__expf`, max semantics, target epsilon and target reciprocal sequence. Keep every initial/additional epsilon placement, including first row normalization's epsilon addition after division. Keep the target's parameterized iteration count with planned value20; do not substitute a reduced-iteration or division-free approximation from #6790.

## Reachability and first useful consumers

The c455 model selects overlap only when an mHC stream exists, execution is FULL-graph capture and token-row count is in1–16. This is `positions.shape[0]`, not request count. Verification width, adaptive verification and captured padding can change token-row count, so a serving concurrency alone does not select the branch. The shifted dispatcher handles a non-null stream before testing Mega eligibility. This branch uses separate TileLang coefficient work and is outside the initial SL97-01 patch.

Without that stream path, shifted Mega additionally requires Pre coefficients and a norm weight, no auxiliary capture, row count <=2^20, device-family100, H divisible by1024, hc_mult4 and callable native Mega support. H5120/hc4 satisfy the static geometry; runtime availability and selected paths remain unverified. First-layer/broadcast and Engram injection paths also have distinct dispatch. Do not multiply a measured mix cost by every layer or assume eager warmup proves captured-route exposure.

In shifted Mega, WG4 runs four token Mix workers, one warp each, after the split completion wait. The `run_mix_task` outputs Pre/Post/Comb arrays used by later target sublayer operations. Its completion can matter even where current norm work is separately scheduled. Plain Mega reuses the same helper in normal workers; it returns the original per-lane Pre `mix_value`, which is then broadcast for collapse. That return contract must not be replaced by the redistributed Comb values. Preserve the split wait, all-warp participation and final sync, and the conditional shifted Pre stores. Initially keeping scalar target output stores through an explicit inverse lane mapping avoids coupling the lane-layout experiment to donor vector-store ownership changes.

Target shifted Mix workers deallocate to40 registers, while normal workers allocate80. The extra local values may spill or increase instruction pressure; source-level shuffle reduction is not a latency prediction. The donor's separate role allocation cannot be copied wholesale.

For TileLang, c455 declares a4x4 fragment in the mix warp (`thread<32` on NVIDIA) and uses reduce/exp/division expressions. No explicit physical fragment layout was established from these Python source declarations. It is incorrect to infer either that TileLang already has the donor layout or that its compiled layout is the same sixteen-lane baseline. The donor layout is therefore retained as a possible later TileLang question, not included in the claimed missing DeepGEMM component. `split_mode=input` does not compute Sinkhorn and offers no such work to remove.

## Bounded CPU discriminator

`python3 lane_contract.py` executed with only stdlib. For all sixteen matrix positions it constructs the current XOR reduction trees and proposed local-row/pair trees; they match after commutative operand canonicalization, and the two storage-lane/eight-register mapping is a bijection. This establishes source-derived data grouping and destination coverage only. It does not execute target FP32 Sinkhorn, `exp`, reciprocal, compiler contraction, masks or synchronization. NaN, signed zero and exceptional values are explicitly outside this symbolic equality.

A positive binary32 counterexample shows why arbitrary reassociation is not allowed: `[1,1,2^-23,2^-24]` gives2.0 with XOR2/1 pairings and2.000000238418579 with adjacent pairings. This is a legal arithmetic witness, not an observed model state or a mismatch of the proposed matched grouping. The remaining numerical gate is target-vs-modified coefficient/output equivalence with actual compiler semantics and exceptional-value handling; this CPU result does not waive it.

## Prior overlap and dispositions

- Round70's #6202 body lead is now narrowed to an actual missing component; not a new paper discovery.
- R3 legacy/H200 configuration and R4 coefficient-stream overlap change deployment or scheduling. SL97 changes work inside the selected native coefficient kernel and does not disable overlap to manufacture exposure.
- MF19/round29 address FP8 activation handoff and small-row producer arithmetic. SL97 changes no activation format, GEMM, router input or scale packing.
- Round58 first-entry specialization has a different input invariant. SL97 works on the general4x4 coefficient matrix.
- Whole CAKE replacement and donor task/split policy are not proposed. #6790's H4096 division-free design is not needed for this source closure and was not newly hydrated.
- TileLang physical layout transfer remains unresolved, not rejected merely because it is another compiler.

## Smallest next step and evaluator

Future work, only after separate execution authorization: implement a guarded alternative inside `run_mix_task`, keeping the existing native path as control and all twenty iterations. First compare generated code/resource use and exact coefficient outputs on same target-native inputs; maintain Pre/Post/Comb stores, masks and zero-token/tail behavior. Reject a naive alternative that changes pairings, primitives or epsilon. Check both shifted and plain callers even if only shifted is intended to dispatch.

Then measure the same captured shape/backend path, not donor CAKE versus target. Inspect source-selected row distributions and the exposed coefficient-to-next-consumer interval before claiming materiality. Use unchanged Mooncake and agent-p75 workloads for ITL/throughput/TTFT and the existing output/numerical gates. A small scoped native coefficient differential is additionally needed because those serving metrics cannot certify the changed lane arithmetic. No new workload family or arbitrary tolerance is justified. Null outcomes include no actual Mega exposure, spills/code expansion, unchanged end-to-end latency, or regression despite fewer shuffle operations.

No ROI percentage is estimated. Current evidence improves implementation specificity and closes a prior read-depth gap; it does not outrank PJ01/CF59 on proven service benefit.
