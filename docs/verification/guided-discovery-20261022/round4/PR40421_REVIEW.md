# SGLang #40421: independent donor audit

Audited 2026-10-22 by read-only GitHub API and pinned source inspection. No GPU or serving work executed.

## Decision

**Upgrade AT03's implementation evidence, retain deferred implementation/target validation. This is the same hypothesis, not a new discovery count.** A concrete external implementation already reuses compressed-KV dequantization across V4.1 consumer layers. Borrow its lifetime contracts and adversarial tests. Do not advertise a ready B200 port or transplant its performance claims into our pinned vLLM.

## Pinned state and dependencies

PR https://github.com/sgl-project/sglang/pull/40421 was open, unmerged, non-draft; last updated 2026-10-21T06:54:12Z. Head `be9259983a47ecbe8d0dea073f24f4c12087d573`, base `93088901fb413e5a81eeb81b675fc21b4adc5b1f`, 4 changed files and 6 commits. No submitted reviews or inline review comments were returned. Comments primarily contain CI commands/results.

Body says based on #40179, whose current head is `e44e29a3ac72e413b5b5d79c499783a0f5a78f14`, open/unmerged, 28 files. That body in turn depends on #40548, head `f86e0619d645d0f340bc780f79404759778f1ffe`, open/unmerged, 27 files. Their current base is `fc404bbbb30a880e91ad2cea2434bc5567849e76`. This is declared lineage; current #40421 diff has only four files against main, so it does not prove all dependency patches are mandatory for a selective vLLM adaptation.

## What code actually does

`deepseek_v4_backend.py:4261–4299` enables reuse only for compression ratios 1/2 under CP, separates workspace per ratio, uses `(compressed source layer, workspace data_ptr)` identity, always refreshes on producer execution, and always regenerates the SWA portion. Per-forward metadata stores the identity. `copy_` at 1079 and breakable replay metadata refresh at 1123 reset the cache. The producer refresh handles same-address source mutations at group entry; it does not authorize arbitrary mutations between consumers.

This corroborates our narrower source20-entry refresh and layers21–39 reuse contract. Our vLLM plan still needs its own fixed-allocation graph/lane lifecycle, fresh combined indices/lens, contiguous dynamic view, and external reader/write-order validation. SGLang's eager/serial workspace helper is not itself proof of vLLM CUDA-graph resource correctness.

## Critical dispatch mismatch

Current `deepseek_v4_backend.py:2734–2762` permits CP into `_use_sparse_prefill` only for **SM90**, V4.1, non-Mega attention, interleave metadata with `local_index is None`, and a non-q8kv8 prefill backend. The sole call to `_forward_prefill_sparse` at 4079–4102 is guarded by that predicate. Reuse inside the callee requires CP. Therefore the inspected current path does not establish B200/SM100 CP activation. This must be reconciled with the body’s B200 benchmark, by identifying the benchmark revision or a different reachable path. A direct unit call bypasses this dispatch.

Helper definition verified at the same pin: `runtime_context.py1811,1844–1852` maps `is_sm90` to `common.is_sm90_supported`; `common.py332–336` supplies capability majors `[9]`, and `_check_cuda_device_version`273–285 tests membership, not a minimum capability. SM100 therefore does not satisfy it under normal platform facts. Scoped test overrides exist, but no evidence of a benchmark override was found. Successful E2E tests could execute the fallback without exercising this reuse branch.

This mismatch is not evidence that the mechanism cannot help B200. It prevents treating this head as a validated B200 drop-in.

## Correctness test scope

`test_dsv41_shared_prefill_kv.py` runs CUDA tensor allocation/copy and real backend control logic, but **mocks dequantization with index_select/copy and mocks FlashMLA to return the KV buffer**. It checks exact materialized-buffer equality against forced baseline, source changes, ratios, repeated producer writes, consecutive forwards, size growth/shrink, and reallocation. Good lifetime regression scaffolding; not real dequant-kernel, attention-output, graph replay, CP metadata, or complete model correctness validation. We did not execute it.

An Oct20 CI bot response reported this test file could not be found. Earlier focused E2E jobs succeeded, but their names refer to older PR commit `e58302f22855580e03d0c4bbbc2cd4e927e98144`; workflow head is separately `07eb671b6af092a4f9344365508ebdc56de74aef`. Those results cannot certify current `be925...`. The earlier Oct12 dedicated unit job also predates current head.

## Current-head CI: avoid false attribution

All 174 checks inspected: 100 success, 56 skipped, 17 failure, 1 unfinished at retrieval. Current main run `39534098049` failed. Its CPU shard11 job `119006844347` failed `TestLayerRunnerDispatch.test_gfx1250_internal_router_requires_full_expert_weights`: expected ValueError was not raised (`test_standard_dispatcher.py:460`). The B200 JIT job `119006844082` failed **health gate**, with annotation explicitly naming CPU shard11/wait-for-base-a; it did not establish a B200 kernel regression. Other JIT failures likewise stopped at health gate. Extra run failure includes process/label gating. AMD run failures were visible but not exhaustively root-caused here.

Thus neither “all CI green” nor “KV reuse breaks B200” is supported. CPU failure lies outside the four modified files; causation is unproven without a matched base run. Raw API snapshots, annotations and CPU log are retained.

## Donor benchmark evidence and transfer boundary

PR author reports 16 smoke outputs equal to baseline and a six-step trace with compressed dequantization calls reduced 228 to 24 (89.5% fewer). The reported serving regime is 8 B200, PD prefill TP4/EP4/CP, BCG/MegaMoE/DSpark, 512 requests, 64K input (~60K uncached), 500 output, median of three runs. These are **author claims**, not our reproduced results. Call count reduction is not end-to-end latency reduction. Embedded image values were not transcribed in this audit.

Our planned two DEP4 groups, source pin, 8K agent workload and frozen long-output ITL objective differ. This is primarily prefill TTFT/work reduction; decode ITL benefit requires demonstrated prefill/decode interference. No 8K gain forecast or service qualification follows.

## Next decisive work

1. Resolve benchmark revision/dispatch mismatch and inspect relevant dependency code only where needed.
2. Adapt only source20-entry fill/static consumer reuse into a separate vLLM change with fixed flat backing and per-lane resources; retain original gather fallback.
3. Port adversarial lifetime cases, add real target metadata/dispatch tests, consumer indices/lens tests and source-mutation exclusion checks.
4. Future GPU authorization: exact materialized KV and attention/output equality, repeated capture/replay and mixed workloads, then measured TTFT/interference with paired controls. No GPU work now.

## Tool usefulness

PR search found an exact donor that paper-only search missed. Pinned full-source dispatch inspection weakened the turnkey claim. Current-head CI jobs/annotations distinguished health-gate failures from real kernel failures. Test source inspection prevented mocked buffer equality from being represented as model correctness. These checks materially changed the decision; novelty alone was never a gate.
