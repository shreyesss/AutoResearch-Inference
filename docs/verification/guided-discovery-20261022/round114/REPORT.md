# Round 114 — SP109 physical cache grouping closure

**Decision:** retain SP109's deferred quality/implementation investigation, with an additional allocator gate. No new hypothesis, capacity claim, quality pass, or serving qualification. This is a source/stdlib refinement of frozen round109.

## What changed the decision

Changing selected SWA records from 528 to 288 bytes is insufficient to establish physical memory savings. Under the explicit metadata scenarios below, the pinned packed-group builder either fails construction or omits layers when asked to split the resulting unbalanced SWA bucket. Its exact-partition guard rejects omitted layers. A separate conservative control that preserves the original partition avoids that problem but saves **zero common-stride bytes** in the B128 cases. Different grouping or allocation layouts may still save memory; this is not an impossibility result.

This strengthens the next implementation prerequisite: design a complete, valid mixed-width partition and calculate its actual allocation cost before using a layer-wise payload budget to select SP109 subsets. Logical attention-read traffic and physical capacity are distinct rationales. Neither establishes latency benefit.

## Exact source and scope

Target `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`; model config revision `1bae0e1088993b9b82de08f59de5be5a34e42170`. The declared plan is Flash1017, TP1/DP4/EP4, B200, native DSpark5. The checkpoint/brief do **not** supply a serialized live resolved cache configuration.

The probe executes six unchanged AST-extracted planner function bodies and eight unchanged metadata method bodies from retained source, using scalar dataclass facades. It imports no target module, torch, model, native kernel or accelerator library. It is not the complete native planner or an allocator execution. Exact source hashes, function/method hashes and lines are in `source-manifest.json` and `planner-probe.json`.

The eight metadata methods include UniformType's actual `first_spec`, `page_size_bytes`, `is_uniform_type`, `from_specs`, and maximum-page-count method, plus the actual Full/SWA/circular grouping predicates. The FullAttentionSpec registry family is a declared scalar stub backed by `single_type_kv_cache_manager.py:2690–2692`. Constructors, dtype-byte arithmetic and block-stride arithmetic are scalar facades; native dataclass validation, configuration finalization, loader and registry execution remain outside this probe. Property formulas are bound to `kv_cache_interface.py:183–197,232–240,549–564,682–708`.

## Complete managed-spec inventory for these scenarios

| Owner | Count | Stored representation and page rule |
|---|---:|---|
| Target SWA layers 0–39 | 40 | block32, window128, 528 bytes/state; selected subset prospectively 288; page rounded to512 |
| Draft SWA layers 40–42 | 3 | block32/window128, remain528; not changed by target policy |
| Compressed owners 2,8,14 | 3 | ratio2, 288 bytes/state; framework block B stores B/2 states |
| Compressed owner20 | 1 | ratio1, 288 bytes/state; B states |
| Index K owners2,8,14,20 | 4 | same respective compression ratios, MXFP4 128/2+128/32=68 bytes/state |
| Compressor rings owners2,8,14 | 3 | one circular page/request, 8 FP32 rows of1024 scalars:32768 bytes/page |
| **Total** | **54** | This is a source-derived scenario inventory, not observed live groups. |

The ring derivation is explicit: `DeepseekCompressor` creates state only for ratio>1, with `state_dim=2*head_dim` and dtypeFP32 (`compressor.py:307–315`). Config head_dim512 gives1024 scalars/4096 bytes per row. `CompressorStateCache` reserves native5 drafts + bonus + previous open-group row, rounds7 to a power-of-two minimum8 (`206–237`). Its spec has one head and head_size_v0. Thus logical page shape[1,8,1024], bound tensor view[B,8,1024]. This represents current open-group overlap, not a growing full-context history. CircularBufferSpec is non-prefix-cacheable, one block/request, and has no generic slot mapping (`kv_cache_interface.py:919–955`).

Non-owning target layers share the four compressed caches. Later index-source layers24/28/32/36 reuse the latest source K cache; they do not add four more K caches. Native draft layers own only their SWA caches. Engram device history/hash storage and ordinary scratch are outside this managed KV spec inventory and remain part of unquantified total memory. Registration order follows target attention→index→SWA→compressor-ring (`attention.py:432–610`).

## Conditional scenarios and results

All cases assume eligible SM100 Mega, compressed288, index68, TP1/PCP1/DCP1/PP1, hybrid manager enabled, block-outer BLHNC/BLNHC, no HiSparse/offload/extra hidden-state-cache module. Subsets are transparent controls, **not quality-calibrated layer recommendations**.

| Framework B; flags | FP4 target SWA subset | Source function outcome |
|---|---|---|
|128; replay on, sparse-logits off|none|complete partition;117216 common-stride bytes/block|
|same|{0,1}|empty split group → StopIteration|
|same|even layers0…38|exact-partition failure;3 layers omitted|
|same|all target0…39|empty split group → StopIteration|
|256; replay on, sparse-logits off|none|complete scalar partition;6893568 common-stride bytes/block|
|same|{0,1}/even/all|partition failures;39/3/37 omitted respectively|
|128; replay off, sparse-logits off|none/{0,1}|baseline117216 / construction failure|
|128; replay on, sparse-logits on|none/{0,1}|baseline126720 / construction failure|

No allocation bytes are reported for invalid groups. These are **12 metadata scenarios**, not runtime tests. B256 is a sensitivity case, not an attested valid deployment configuration. Worker `select_common_block_size` accepts a supported kernel divisor of the manager size;128 divides256 (`worker/utils.py:518–560`). That does not prove every upstream config check, backend/layout combination or downstream allocation permits this scenario. In the inspected grouping entry, hybrid unification, uniform/HiSparse shortcuts and hidden-state separation precede packed grouping (`kv_cache_planning.py:1113–1164`). These supplied heterogeneous no-HiSparse cases bypass those shortcuts only under the stated assumptions. The complete finalization path was not executed, and unresolved flags can change the route.

The large B256 number comes from physical stride alignment/LCM, including the128-row index-page alignment when framework pages split into kernel pages. It is not a predicted runtime allocation, recommended block size or evidence of an existing deployed waste.

### Why the prospective mixed bucket fails

SWA uniformity compares block size, DCP flag, window and replay, **not record width**. The source builds page-size lists with unequal populations, then a state-bucket split can still run. `pattern_repeats = list(zip(*page_size_layers.values()))` truncates to the shortest list (`kv_cache_planning.py:1029`). Empty slices reach `first_spec`; nonempty incomplete splits fail `_check_exact_partition`. This is a specific future integration hazard exposed by mixed target widths and unchanged draft widths. It is not a report that today's uniform-SWA deployment drops layers.

### Conservative manual partition control

For B128/replay-on/sparse-logits-off, preserve the baseline layer-group membership verbatim and substitute widths for each of the three subsets. All three exact-partition checks pass, but bytes/block remain117216: unchanged widest full-cache grouping and retained draft FP8 row alignment dominate the common stride. These are **three manually constructed controls**, not source-generated alternative partitions or a runtime patch. They show one valid null result; alternative group splitting/stride layouts have not been ruled out.

## Remaining information required; stopping point

The brief lacks actual post-customization per-layer specs, resolved framework block size/layout, model-specific/default group builder, hybrid-manager setting, replay override, indexer-sparse-logits setting and any extra cache modules. A capacity statement additionally needs available KV allocation bytes, resolved group residency/request limits, max model length/max sequences, null-block reservation and any block-count override. Common stride alone does not determine resident blocks or useful concurrent contexts.

The cheapest next step is a read-only serialized configuration/spec/group receipt from the authorized future runtime, followed by a CPU complete-partition/physical-cost check for selected subsets. No GPU run is requested or performed here. If those fields remain unavailable, stop at this source formula and conditional integration finding. Quality calibration still requires the separately authorized future model work described in109; MultiAlloc gradient ranking cannot be executed under the present restriction.

## Provenance and limits

`superseded/v1-*` preserves the initial51-spec scalar model that omitted three compressor rings. It was an interim omission, not a final result. The final54-spec probe corrects it, executes actual metadata methods, and follows source registration order. No frozen109 file was changed. The command is `python3 planner_probe.py` from this directory; it writes `planner-probe.json`. Replay compares deterministic JSON, not native allocation.

No online searches, papers, PR fetches, new hypothesis identities, model/quality experiments, GPU work, canonical writes or cloud calls occurred. The result advances one existing deferred candidate's allocator admission and physical-cost gate; it does not increase measured improvement yield.
