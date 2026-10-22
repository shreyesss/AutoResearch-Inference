# Independent review — round115 FP8 sparse-MQA adapter

## Verdict

No blocker to retaining the **parked target-specific host-ABI refinement**. A concrete FP8 adapter is missing in the inspected c455 sparse path even though the dependency has the required FP8 kernel variant. This is not a new sparse-attention mechanism, a high-ROI finding, or an implementation qualification. Keep the existing direct-paged family relationship and the manual-opt-in scope.

Verified: all75 author hashes,39 exact revision fingerprints,17 quoted anchors,10 target files equal to the pinned vLLM archive,6 donor files equal to their retained revisions and6 dependency/helper copies equal to retained prior files. One extra archive copy (`target-common.py`) closes the scale-pack helper definition. I read the focused target/donor/API paths and author control code; I did not execute the host proxy, native tests or models. Saved workload counts were independently recomputed from retained length pairs and original-file hashes checked. No network, GPU, canonical mutation or claim of donor test execution.

## Exact ABI gap

The target source selects FP8 for indexer `auto` (`indexer.py:55–62`), while sparse logits default false and two guards require FP4. That is source configuration, not a live setting attestation. The current sparse wrapper assumes a `(values, scales)` tuple, uses the packed-int8 FP4 tag and requests FP4 gather/cache views. Removing only guards is insufficient. The three-row host control is a useful narrow illustration of that mismatch, not a current-runtime bug: constructors normally prevent the invalid call.

The target writer supplies the missing compatibility premise:

- `indexer_k_store.py:196–213` segregates page values from the scale plane; the FP8 branch uses128 value bytes and4 scale bytes per token.
- Lines248–266 write the same per-token power-of-two scale as four repeated UE8M0 bytes when `MX_SCALE` is true. `deep_gemm.py:597–606` selects that branch for SM100.
- The actual archive helper `common.py:157–161` extracts the exponent byte and multiplies by `0x01010101`. This is packed MX scale data, not four bytes to reinterpret as a float32 scale.
- The a7a `PagedSparseKVAccessor:101–141` addresses the same segregated value/uint32-scale planes. Its host API accepts FP8 e4m3,128 logical head dimension, packed int32 Q/K scales and BF16 weights; the launcher selects the FP8 storage/swizzle/MMA variant.

The donor preserves FP8 Q dtype and calls `mqa_logits_mx_inputs`, supplies the actual cache format and changes prefill workspace sizing. The current dense path already calls that helper (`sparse_attn_indexer.py:877–891`): unit Q scales and BF16-converted weights are not a newly invented algebraic shortcut. Preserve the FP8 producer's FP32 weights until this existing conversion. Source compatibility is not compiled numerical equivalence.

Keep donor default `None`/automatic enablement separate. It changes policy and workload exposure beyond the adapter. The initial comparison should retain current defaults and explicitly select the same eligible FP8 route. FP4 is a regression control only when configured, not an equal-precision substitute baseline.

## Exposure is the first priority gate

The retained model has2048 candidate blocks of8 positions:16384 compressed positions. Consumer indexers24/28/32/36 have ratio1. At finite valid scores with all valid blocks retained, a planned8192-input plus1024-output request remains below that budget, so this arm removes **no live logical score positions** in that shape. It does not reduce the scored domain to512:512 is final attention selection, not candidate scoring capacity.

This is not a proof of equal physical work or zero speedup. The current dense decode passes `max_model_len` and subsequently masks logits; sparse output sizing, padding stores, top-k, scheduling and native kernel tactics differ. Any short-context gain needs an explanation and measurement of those costs rather than credit for logical pruning. No allocation-width-to-HBM/ITL conversion is justified.

The saved requested-input counts above16384 are417/4004,437/4220 and364/4053. Input-plus-requested-output counts are439,448 and380. These establish a bounded standard-workload opportunity to inspect, not actual completed tokens, runtime rows, time-weighted exposure or gain. Prefix cache, prefill replay, effective limits and query admission remain unknown. Four potential consumer indexers must not be multiplied by every main-attention consumer or treated as four measured costs.

M03 `hypothesis:78e5ab2fbe61364536be6b0a2646f7b55cbaad49f2ec1bebeaca81b3519e02cf` already owns the all-blocks-fit producer-ranking bypass. This adapter does not remove that producer. The direct-paged family `hypothesis:ebbeb3770815c1a4f41305f14c23ad88eb1d0b7ee21f60ff4115237924d0865f` has a different baseline; retain the relationship without importing H200 performance or rewriting it. No fresh paper novelty or formal-card promotion follows.

## Native contracts still open

The a7a API is specific: sorted unique live block prefixes, request-consecutive rows, identical block-table rows for paired queries, correct dtype-dependent metadata, page/block alignment and SM100. Existing expansion sorts and repeats only padding, with an `end` boundary. Preserve this original valid-prefix/partial-block/empty-row contract; do not infer general duplicate-candidate support from a Triton comment. Metadata reuse must correspond to the same candidates, dtype, row geometry and lifetime.

The sparse workspace is per stream and requires first allocation/zeroing before capture (`attention.hpp:319–338`). Existing unit-Q-scale buffers keep older allocations alive for previously captured graphs. Those source safeguards are useful, but neither proves the new path's stream/graph/AV/replay correctness. The host proxy uses inert tensor/kernel stand-ins and skips constructors, prefill, zero-row metadata, actual scales and capture. It cannot close these gates.

Donor `_assert_same_selection` explicitly permits different token indices at equal logit values. Its selected-value multiset checks and torch-reference tolerance tests do not establish exact selected IDs or downstream attention outputs. In particular, the donor comment that errors are below selection-changing gaps is not a proof for target scores. For the stated same-selection arm, unresolved ties and changed numerics require an explicit admission/fallback contract and native comparison. They do not, on their own, establish a task-quality regression or a universal requirement that every future experiment be bitwise identical. Any intentional relaxed contract would need separate justification; it is not silently supplied by donor accuracy numbers.

## Next step and stop rule

Inspect compatible retained evidence for effective FP8 format, sparse flag/backend, metadata eligibility and compressed-domain lengths. If the route is inactive or only below-capacity logical domains are exposed, do not rank the pruning mechanism as high leverage. A separately justified physical-padding/kernel comparison remains possible. No more scalar or metadata-only cases are needed to pretend to resolve compiled equality or benefit.

Later authorized native/service arms should keep candidate policy/cache precision/workload fixed, account for metadata/top-k/capture overhead and compare selected identities and downstream results under the declared contract. Donor TP4 B300 timings are external observations, not target forecasts. Inadequate evidence remains inconclusive; no current status/ROI change is warranted.
