# Independent CR64 source and decision review

**Select the narrow experiment for future consideration; defer execution and performance qualification.** A shared physical cache owner and an actual payload-load policy provide a concrete mechanism. Unknown ROI does not invalidate this inexpensive policy question. No GPU, compilation, device/backend import, native execution or online search occurred in this review. Author artifacts remain immutable.

## Source closure and limits

The pinned Python selector explicitly selects Mega when requested and otherwise defaults to it only after capability, compiled-op and head/group checks (`model.py:235–255`; `flash_mla_mega_attn.py:91–103,150–172`). Decode calls the Mega op without the prefill threshold. This is strong source applicability for the planned TP1 SM100 configuration, **not an installed-backend attestation**. It does not establish H200 applicability. The retained GB300 timing comment is a different-format/backend comparison, not CR64 evidence.

Consumers return the source layer's actual `kv_cache` object (`attention.py:1222–1230`), then pass its unsqueezed view as the extra cache alongside the layer's own SWA cache (`flash_mla_mega_attn.py:305–365`). The source20 group spans20–39, but selected indices can change at20/24/28/32/36 and across queries. This supplies a reuse opportunity, not identical accessed lines, measured reuse distance or guaranteed residency. The actual source tensor's lifetime and effective cache format still need confirmation.

The native decode producer calls `issue_raw_gathers` for raw payloads. Its existing hint is FIRST at `core_attn/kernel.cuh:347–357`, and the SM100 wrapper forwards the 64-bit operand to `.L2::cache_hint` in inline PTX. Pinned CUTLASS defines distinct FIRST/NORMAL/LAST values. This is a concrete source change, not a logical cache admission/eviction policy. A hint cannot reserve or pin L2 capacity. No hardware behavior follows solely from the enum spelling.

The two-role adapter must preserve all-original, all-extra and mixed cases. At kernel1417–1422 the non-mixed helper receives `extra_map` when `num_orig_rows==0`; treating `MIXED_BLOCK=false` as SWA is incorrect. Mixed role boundaries are already expressed in gather4 groups; do not infer role from format equality, since both caches can have the same format. Retain byte-offset tensor-map construction, coordinates, gather counts, slot addresses, invalid-row handling and barrier expected transaction bytes. In two-CTA mode, CTA0's separate scale copies at1381–1396 remain unchanged. Unchanged scale instructions do not imply unchanged physical scale-line residency or measured scale traffic.

The code-generation addendum is valid. The existing compiler-crash comment concerns selected tensor-map pointers, not a proven failure of integer hint selection. Its pointer-offset workaround must remain. The h128 instruction-cache warning is explicitly scoped to that variant; the target's planned64 live heads do not prove an identical footprint cliff. Still inspect register/code-size changes and emitted operands for the exact compiled target. Avoid duplicating the full hot loop or unrolling the deliberately repeated eight-gather burst. No build was run.

## Diagnostic and comparison strength

The extracted Python method with object sentinels checks its ownership branch. The15 role cases are a hand-built policy routing illustration; they do not execute the C++ helper, a proposed native adapter, invalid-slot behavior or cache replacement. The two negative cases clarify design errors but are not independent native tests. I read these source/control contracts without rerunning a redundant symbolic suite.

The selected CPU-cache paper offers only a resource-contention question. The PR bodies are useful opposing evidence about mixed workloads and cold-L2 measurement, not audited donor code. Cache hints compete with weights/indexer keys/other requests; repeated source references or fewer misses cannot be added to a service ROI. AT03 materialization reuse, AT02 grouping and P50 indexer hints remain different interventions. WP38 weight policy can interact; hold it fixed in the first arm.

## Decision-rule correction and next gate

The original report's “FIRST or NORMAL wins” rejection line is not valid for the family {NORMAL,LAST} versus FIRST. The frozen decision addendum repairs it:

- NORMAL > FIRST under the frozen objective and guards supports the NORMAL arm, even if NORMAL > LAST.
- LAST > FIRST supports that arm; comparison with NORMAL determines selection, not whether FIRST was improved.
- B > C alone says nothing about B > A.
- If neither alternative establishes improvement, do not promote. Record a statistically unresolved or underpowered comparison as **inconclusive**, distinct from a confident null/rejection; the addendum's “null” is not proof of statistical equivalence.

The smallest future implementation gate is exact backend/build admission followed by a role-preserving operand-only adapter and code-generation inspection. Later differential checks and FIRST/NORMAL/LAST runs must preserve mixed/all-extra/invalid/two-CTA paths. Use a real consumer sequence with intervening model work; a cold-L2 isolated launch cannot test the cross-layer reuse premise. Measure complete-round and cross-rank exposure before standard agent-p75/Mooncake service promotion. No current execution authorization follows from this selection.

## Focused critic-skill review

The new multi-arm paragraph requires separate arm/baseline and family conditions, ties/uncertainty, guards and append-only corrections. It does not say B beating C proves B beats A. Its instruction to reject only C's advantage over B is conditional on that comparison's evidence; the following uncertainty clause prevents a noisy point estimate from becoming proof. This is a useful instruction repair grounded in an observed adjudication bug, with no runtime behavior change or demonstrated improvement in future research quality. The exact skill text/hash and root's frozen lesson packet are recorded in checks.json.
