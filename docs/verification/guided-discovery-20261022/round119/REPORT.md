# Round 119 — source-default FP8 index pages refine SP109's allocation gate

**Decision:** same SP109 deferred investigation; zero new hypothesis or qualification. Round114's explicitly assumed MXFP4 case remains valid as a conditional scenario. This extension covers the pinned DeepSeek indexer's source-default FP8 route with sparse logits off. It changes baseline numbers and grouping, while preserving the tested failure/null conclusions.

## Source default and unchanged assumptions

At `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, `AttentionConfig.indexer_kv_dtype` defaults to `auto`. Its resolver substitutes the supplied default; `dsa_indexer_uses_fp4` supplies `fp8`. `_indexer_k_cache_head_dim(128, False)` returns `128 + 128//128*4 = 132` bytes, versus the opt-in MXFP4 width68. This uses a single FP32 scale per128 FP8 values, not eight UE8M0 scales or the main compressed-cache format.

The probe executes those **three actual scalar source helpers**, with every platform access explicitly denied. The auto→FP8 branch never calls a platform method or imports its conditional native dependencies. This is a source-default control, not an observation of resolved runtime flags. Sparse logits is explicitly false, also its source default: candidate-consumer sparse logits raises when the cache is not MXFP4. We do not test an invalid FP8/sparse-on allocation scenario.

Other assumptions remain round114's declared scenario: eligible SM100 Mega, compressed records288, target/draft SWA528 with selected target rows prospectively288, framework B128, SWA block32/window128, bounded replay on, TP1/PCP1/DCP1/PP1, hybrid manager and block-outer layout, three native draft layers, no HiSparse/offload/extra hidden-state-cache module. These assumptions do **not** make all unspecified settings source defaults or attest a live deployment.

## Exact metadata inventory and page formulas

All54 managed specs are retained:40 target SWA,3 draft SWA,4 compressed owners,4 index owners and3 compressor rings. Owners2/8/14 have compression ratio2; owner20 ratio1. Sharing/replay ownership is unchanged. Rings remain8×1024 FP32 scalars =32,768 bytes/page, derived from native draft5 plus bonus/open-group history and the existing minimum/power-of-two rounding.

The index spec takes `head_size=132`, uint8, one head, `head_size_v=0`, `tokens_per_state=ratio`, and512-byte page alignment in the declared V4.1 packed configuration. Thus:

| Index owners | States at B128 | Unpadded bytes | Padded page bytes |
|---|---:|---:|---:|
|2,8,14|64 each|8,448 each|8,704 each|
|20|128|16,896|16,896|

The prior MXFP4 pages were4,608/8,704 bytes respectively. The four index pages therefore add20,480 raw grouped page bytes; this is **not** the final common-stride difference. `MultipleOf(128)` at framework B128 contributes stride alignment1. The SWA row alignment, group maxima and LCM still determine the final common stride. Source property formulas and registration/owner evidence are retained from114, with source manifest hashes checked.

The probe retains six unchanged AST-extracted planner functions and eight unchanged metadata methods. Constructors, dtype-byte arithmetic, spec population and registry-family mapping remain scalar facades. It does not run full config finalization, native dataclass validation, loader, kernel backend or allocator.

## Results — four grouping scenarios and three manual controls

| Target SWA subset changed to288 | Source-generated outcome | Common bytes/block |
|---|---|---:|
|None|Complete54-spec partition,8 groups|136,224|
|Layers{0,1}|Empty split group → `StopIteration`|Not reported|
|Even layers0…38|Exact-partition failure: draft40/41/42 SWA omitted|Not reported|
|All target0…39|Empty split group → `StopIteration`|Not reported|

The FP8 baseline has six SWA groups of sizes8,7,7,7,7,7, one eight-member compressed/index group, and one three-ring group. The maximum group page sum is135,168; stride alignment rounds it to136,224. Round114's conditional MXFP4 baseline had10 groups and117,216 common bytes/block. This is a **19,008-byte change in the supplied metadata result**, not a resident-memory or throughput comparison. Group counts also differ, so comparing common stride alone cannot determine request capacity or total residency.

For each of the three prospective subsets, manually retaining the **new FP8 baseline's** exact group membership produces a complete partition and the same136,224 common bytes/block: zero saved stride bytes in these controls. We did not reuse MXFP4 group membership. These are manually constructed alternatives, not the current builder's output. Unchanged compressed/index group size and retained FP8 draft alignment explain the null result. Different valid grouping/allocation strategies remain possible; this does not prove that physical savings are impossible.

The same source grouping hazard transfers: mixed SWA widths remain one uniformity family, page-size list populations become unbalanced, and `zip`-based splitting can produce empty or incomplete groups. The exact-partition guard catches omitted layers. This is an integration hazard for the proposed mixed-width policy, **not** a claim that the uniform current deployment loses cache layers.

## Admission consequence and stopping point

Use the FP8-default result when no explicit MXFP4 override is established. SP109 still needs a complete valid physical partition and an actual allocation-cost receipt before a logical layer-payload budget can justify capacity selection. Logical attention-read traffic remains a separate potential benefit; unchanged compressed/index policies do not imply unchanged downstream values after SWA precision changes. Quality remains untested.

The requested source-default question is answered, so no B256, replay-off, sparse-on or additional metadata sweeps were added. Missing live resolved specs/layout/flags, group residency, memory budget and request limits still prevent a capacity or service forecast. This source-only refinement changes no candidate state, weights or runtime policy.

## Reproducibility

Run `python3 planner_probe.py` in this directory; it writes `fp8-planner-probe.json`. The recorded command executed once. `comparison.json` joins its four scenarios and three manual controls with the frozen114 result; no numerical/native/model execution occurred. Exact source copies, helper hashes and original114 manifest/script/result are retained. The attempted initial read of nonexistent `models/deepseek_v41/common/indexer.py` was corrected using the file inventory to `v1/attention/backends/mla/indexer.py`; `read-path-correction.json` preserves this harmless path failure.

No online query, provider request, native import, GPU probe, build, source patch, canonical/cloud write or new hypothesis identity.
