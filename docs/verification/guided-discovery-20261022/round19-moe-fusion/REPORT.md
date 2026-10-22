# Round 19 — narrow mHC → MegaMoE producer fusion

**Outcome:** one deferred target-scoped port candidate, **MF19-01**. Zero GPU runs, runtime patches or qualified serving improvements. Three actual online queries returned 18 records / 17 explicit paper identities; two fulltexts were read. The selected papers did not justify replacing the target MoE. They led to a narrower source gap and an existing upstream donor, vLLM PR #57977.

## 1. Exact scope and why this is not generic communication fusion

Target is the planned Flash-1017 revision `1bae0e1088993b9b82de08f59de5be5a34e42170`, vLLM `c4557869393db4d75c483d92edd02a5125500883`, two TP1/DP4/EP4 groups on B200. Live image and workload dispatch remain unverified. Default DeepGEMM dependency is `a7a927731b109fdfec770df7c2a5be5d7e2216b5`, not an attested installed binary.

The current native path already uses fused expert execution and shared-expert work. The proposed delta is before that kernel:

```
current eligible MegaMHC → rounded BF16 x → unchanged router
                                      └→ prepare_megamoe: read x, group32 quantize,
                                         store symmetric FP8/scales, pack routing
                                         → existing MegaMoE

first proposed arm:
eligible MegaMHC → rounded BF16 x → unchanged router
               └→ symmetric FP8 + routed/shared scales directly
                    prepare_megamoe packs routing only → existing MegaMoE
```

BF16 remains required by the unchanged router and unfused shared expert, where present. This removes a BF16 activation read and relocates quantization into its producer. It does **not** remove the BF16 output write, quantization arithmetic, FP8 output bytes, expert communication, or necessarily a kernel launch. Keeping routing unchanged leaves the routing-only prepare launch. Direct router output into symmetric buffers is a separate optional donor component, not counted in the first arm.

The source gap is concrete: pinned `ops/mega_mhc.py` passes only `y_bf16`; pinned `deep_gemm_mega_moe.py` always calls `prepare_megamoe_inputs(hidden_states, ...)`. The pinned dependency already exposes `y_fp8`, routed and shared scale destinations. Existing code support in a dependency is not existing integration in this target.

## 2. What the papers actually contribute

### MonoMoE — component selection, and counterevidence

[MonoMoE, 2609.04244](https://arxiv.org/abs/2609.04244) puts small decode-token tiles on tensor-core N and fuses routing/quantization/GEMMs/reduction. Its H200 FP8 block128 models use E256/top8; the target has FP4 expert weights, MXFP8 group32 activations, E384/top6 and native MegaMoE. A direct whole-kernel substitution is unqualified.

Crucially, its EP variant using symmetric peer memory was correct but approximately at parity: short NVLink transfers and rank waiting remained, while shared expert work was already overlapped. Reported TP8 DeepSeek TPOT changes span a regression through a modest gain; isolated operator results are not serving predictions. The reusable idea is inspect producer/consumer representation boundaries, leading here to the actual `prepare_megamoe` call and PR #57977. We did not import MonoMoE performance claims.

### MegaFlux — inference-only piece exists, but not yet a practical target card

[MegaFlux, 2610.00671](https://arxiv.org/abs/2610.00671) has a forward-only on-device replica planner that preserves router choices and pipelines W1/W2 replica-weight readiness. Its training section can be excluded. The forward format MXFP4/MXFP8 is closer to the target than MonoMoE.

However, evaluated forward workloads are EP8 B200, 1K–64K tokens/rank, H7168, top8 and a spare replica budget. Balanced-forward geometric mean is 0.985x; adaptive gating is future work. End-to-end V4-Pro measurements concern large-chunk prefill/first token, not target long-output ITL. No author implementation pin was positively identified; the cited TensorRT-LLM SHA is a baseline dependency. Current target skew, spare HBM and expert-transfer cost are unknown. Keep this as a deferred research lead, not another service-ready hypothesis. No blanket rejection of its forward component.

All other returned records and reasons are retained in `paper-screening.json`. Weave/resource allocation is prior N03; trained-router/offloaded-cache work and consumer PCIe systems lack the current target premise. No recall-completeness claim.

## 3. Exact donor and selective reuse

[PR #57977](https://github.com/vllm-project/vllm/pull/57977), open/unmerged at the read, head `18aac3985191e3850baeb16311ac7431521349d9`, updated October 20. API object, all file patches and six full files are retained. The body describes a bundle including attention input/output GEMM backend changes, FFN activation staging and routing-output staging. Only the FFN activation component is proposed first.

Latest head uses `MegaMhcFp8Out`, `MegaMoEInputs`, `input_buffers()` and `hidden_states_staged`, not older body API names. It retains BF16 output. The mHC wrapper returns a non-null FP8 descriptor only if the MegaMHC path actually wrote it; overlap/TileLang fallback returns null. The consumer skips activation staging only for MXFP8. EPLB remapping remains before routing packing; newly mapped physical IDs are copied even if logical IDs previously occupied the symmetric buffer.

Author-reported four-B200 TP4/EP4/SP bundle measurements include C1 GPU busy 7.64→6.85 ms (about −10%) but TPOT 6.58→6.50 ms (about −1.2%); C4/C16 TPOT changes are similarly small. These are **donor claims**, not our reproduction, not an isolated FFN result and not proof at the current head/our exact target revision. They argue against translating component busy-time savings into equal ITL savings.

## 4. Critical dispatch counterexample: the low-row decode path can get zero benefit

Pinned `model.py:506–513` keeps an mHC overlap stream only during FULL capture with 1–16 local rows. `ops/mhc.py` returns from that stream path before reaching MegaMHC. `supports_mhc_overlap` does not require TP4; supported B200 shapes with no ubatching can enable it in TP1 too. Thus a future FULL graph replay follows the captured overlap path. An eager warmup showing MegaMHC is not evidence that small FULL graphs execute it.

| Conditional mode | Rows | Native route, assuming platform/dependency support | First arm |
|---|---:|---|---|
| FULL capture/replay, overlap enabled | 1–16 | overlap implementation | **No benefit; unchanged fallback** |
| FULL capture/replay | >16 | MegaMHC if other guards pass | eligible to investigate |
| eager or piecewise | positive eligible rows | MegaMHC if other guards pass | eligible to investigate |
| ubatching | any | overlap disabled by support predicate | excluded until symmetric-buffer ownership proven |
| absent pre-mix/norm, aux capture, unsupported runtime | any | fallback | unchanged |
| zero rows | 0 | source guard is not a complete runtime contract | excluded from proposal |

`dispatch_contract.py/json` executes the exact AST guard expressions with explicit CPU stubs: 30 conditional combinations, not a workload histogram or GPU dispatch test. It demonstrates why selecting the idea solely from H5120/B200 support would overstate applicability. Do not disable the existing overlap policy to manufacture exposure. Actual scheduled/padded rows can differ from requests and speculative depth.

## 5. Numerical and buffer contract

1. **Rounded BF16 boundary:** dependency epilogue `normalize_bf16_pair` rounds to BF16 before both BF16 store and FP8 conversion. The first arm must preserve this boundary; FP32→FP8 directly is not the same proposal.
2. **Exact scale domain:** group32 absolute maximum, floor/UE8M0 exponent rule, clamp, byte packing and E4M3 cast must match current staging, including signed zero, subnormal and nonfinite policies. Source scale helpers have been independently compared by parent; see `../review/round19/scale_contract.py/json`. Integer/formula agreement is not compiled kernel equivalence.
3. **Shared scale layout:** the actual MegaMoE `BLOCK_M` determines padded shared-scale row permutation. The producer must receive the whole correctly sized backing storage and the exact same block choice as the consumer. This couples to M01 tile experiments; do not combine them in the first contrast.
4. **Ownership:** current symmetric buffer cache is keyed by process group/device/dimensions/formats, not layer or ubatch ID. Serial execution can reuse it after the previous reader completes. No proof here permits concurrent streams/ubatches to write it early. First arm is no-ubatching, original stream ordering only. Graph resources must be prewarmed on all ranks; no allocation/barrier is introduced inside replay.
5. **First launch:** donor obtains input buffers before `forward()`'s initial synchronization. That synchronization follows any preceding producer work and is not by itself a demonstrated race. All-rank symmetric allocation order, warmup and first-launch behavior still require a real integration test later.
6. **Router/quantization fallback:** keep original router semantics, bias/sqrtsoftplus/top6, padding and EPLB physical-ID remapping. Keep BF16 input for consumers that require it. A shape- or backend-ineligible producer must never set a staged flag based only on allocated destinations.

## 6. ROI before GPU: what can and cannot be bounded

For H5120, one eligible boundary avoids one logical BF16 read of `2*5120*T = 10,240*T` bytes, if the original prepare kernel would read those values once. This is an algorithmic traffic count, not physical DRAM traffic or time. The read may hit cache; fused mHC adds registers/instructions and may slow. No absolute microsecond estimate is justified.

Let `E` be exposed activation-staging time on eligible target boundaries, and `A` added producer cost. The optimistic end-to-end saving is bounded by `E`, with actual change approximately `E-A` only if other overlap/scheduling is unchanged. The no-overlap first arm retains routing packing and its launch, so a claim that every prepare launch disappears is false. Small FULL graphs can have `E=0` for this intervention. Current profiling/shape evidence is absent, so prediction is **unknown**, not a positive percentage inferred from donor GPU-busy time.

Priority: promising code-reuse candidate for already-MegaMHC shapes; **deferred, low priority for claimed long-output ITL improvement until exposure is established**. This is distinct from M01 tactic choice, RD01 weight placement, EG01 host-table staging, N03 SM partition, WO-A and PDL. It is an upstream port opportunity, not a novelty claim.

## 7. Exact future experiment, not executed

**CPU/source next:** finish selected diff/API review and prove resource/key ordering for the intended no-ubatch configuration. Read retained baseline traces or configuration if available to determine FULL graph buckets and actual eligible rows. Do not infer row distribution from concurrency or DSpark k5.

**When GPUs are separately authorized:**

1. Pin image/runtime/dependency hashes and exact model; confirm the native selected path. Initialize buffers outside graph capture on all ranks.
2. Differential component test at 1/16/17/32/64/128 rows and ragged/padded rows: baseline BF16 output, fused BF16 output, FP8 bytes, routed scale bytes, shared padded scale pages, topK IDs/weights, EPLB mapping and expert outputs. Use adversarial group-boundary/exponent values; signed zero/nonfinite behavior must be defined. Small FULL overlap cases must remain unchanged. Validate repeated calls and shape changes, not only fresh allocations.
3. A/B activation-only arm versus baseline at identical routing, block_m, backend and graph mode. Measure complete mHC+router+prepare+MegaMoE span, not quantizer alone. Keep attention/WO-A changes and direct routing buffers off. Test direct routing buffers only as a separately attributed arm if warranted.
4. Run the existing Mooncake and agent-75 workload definitions unchanged, paired order/repeats. Primary is the already frozen long-output ITL objective; preserve TTFT, tail ITL/E2E, failures and throughput guards. Record eligible row/time exposure as an explanatory metric. If these real workloads never exercise the eligible branch, do not invent a serving win from a synthetic large-row microbenchmark.
5. Reject promotion on numerical mismatch, fallback regression, negligible/unstable serving change, or insufficient uncertainty. Preserve a useful neutral component result in memory; do not rewrite it as validation.

No additional service evaluator is required by this hypothesis yet. A narrow operator differential harness is needed for correctness; it supplements, not replaces, the existing service workloads.

## 8. Tool outcome

The useful sequence was online papers → fulltext limits → local PR search for the actual producer/consumer call → exact donor/head and pinned baseline → dispatch falsifier. Query expansion was changed after real results. Fulltext prevented a generic EP fusion claim; native source prevented a small-decode claim; PR mining supplied a reusable implementation rather than a new kernel project. Retained receipts include dates, exact queries, provider revisions/cache statuses and zero GPU/model calls. No single-shot rubric accepted this as a measured improvement.
