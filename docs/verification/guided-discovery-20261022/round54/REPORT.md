# Round54 — BF16 cold-chain tuning: retain an evaluator control, zero new hypothesis

## Decision

Retain FlashInfer PR6360 as a **conditional tuning/evaluation component**, not a qualified Flash1017 improvement or a new deferred hypothesis. No deployment setting was changed. The missing evidence is the selected unquantized-linear backend, its actual eligible shapes and exposed time, and the installed FlashInfer revision. The completed trace-applicability inventory provides none of these. A useful mechanism is present in the donor, but default pinned CUDA `linear_backend=auto` does not invoke it.

This is a source/control-flow screen. Five exact extracted dispatch cases passed with inert metadata stubs; no tensor, GPU, native package, model, CUDA availability or serving execution occurred. No canonical state or Git changes.

## Discovery and source identity

Root's already executed local PR search in round53 surfaced [FI6360](https://github.com/flashinfer-ai/flashinfer/pull/6360). This round imported that one opening record into an isolated store using the production selected-source tool, then fetched current PR metadata/files and two exact-head files through the existing Sources cache. Four HTTP requests; no paper search or broad provider queries were needed after this source lead. `parent-local-pr-search.json`, `import-pr.json`, API receipts and cached isolated state preserve the discovery path.

The examined donor is open/unmerged `zcnrex/flashinfer@96f9b9947c19ce6ceb864c4a4fa9ee532ad3f8a8`, base `a9dae2503f37e8df4eafaad910d3d4ab6604e890`. All seven returned file patches were retained, plus full `autotuner.py` and `gemm_base.py`. PR body is observed mutable author prose, separately hashed; exact source controls interpretation. Target source is `callgideon/vllm@c4557869393db4d75c483d92edd02a5125500883`, not upstream vllm-project at an assumed matching commit.

Prior recall inspected all143 canonical typed hypothesis nodes' statement/mechanism/proposed-change fields read-only, then21 lexical matches. Initial selected local_id/title fields were absent; comparisons use the actual statements/IDs, not missing titles. Closest prior is `hypothesis:7deeaba77bd1290ce3850134faa175d3b7b38a877efb126357a4feab8364baf0`: MegaMoE tile selection from actual expert histograms. This donor instead changes how fixed BF16 GEMM tactics are measured. Neither family proves the other's exposure. PJ01/OP36/EG01 address MXFP8 work or representation handoffs; this donor explicitly leaves its arena-less MXFP8 tuning config unchanged. Humming/Hopper quantization and router FP32 cards do not establish this route. No existing status was changed.

## What the donor changes

1. **Rank tactics using an eight-launch graph chain.** `_BF16_GEMM_SM100_TUNING_CONFIG` adds `cold_chain_launches=8` and arena input index1 (weight B). `cold_l2_profile` captures the ordered lane inputs, flushes L2 before each sampled graph replay, and reports median chain duration divided by its launch count. It does not flush between all eight launches. The arena uses distinct staged weights/stride-preserving views; oversized weight payloads can use the original inputs. This measures an explicit cold-weight graph workload, not the target's observed cache behavior.
2. **Bound tuning overhead.** A warm replay estimates chain time, limiting samples to about10ms per tactic, bounded below by one and above by the existing sample count. This is a tuning-time decision, not a serving token budget.
3. **Keep the profiling policy with the choice.** Policy labels include `cold-chain:8`; incompatible old policy entries are ignored in tuning mode. Success removes stale runner winners before replacement. Legacy user-loaded files also compare policies while tuning, so applicability is not restricted to managed v2. Distributed cache-hit coordination and rank-safe tuning remain relevant.
4. **Preserve layout and filter unsupported runners.** Non-overlapping transposed/gapped arena tensors preserve strides. cuBLASLt/CUTLASS explicitly require contiguous A and B.T. These guards concern their runners, not proof that every target operation is legal.

Author numbers are B300/GB300 SM103. Current revision uses B300 SXM6 AC and a graph rotating at least2GiB of weights. It reports chain8 within1.6% of its fastest candidate across its tested cells and increased warm tuning cost. These are author measurements with a selected tuning workload, not B200 measurements, target ITL, or an independent reproduction. The body's last reviewer note says `cold-chain:32`; exact code and current main results say8. Its tests use numerical tolerances, not target output equality. The donor is a timing/ranking repair, not a claim that a new tactic automatically preserves every reduction bit pattern.

## Exact target reachability and exclusions

| Boundary | Pinned evidence | Consequence |
|---|---|---|
| CUDA default | `dispatch_unquantized_gemm('auto')` looks up only explicit FlashInfer mapping, misses, and returns `default_unquantized_gemm` (`F.linear`) | vLLM auto is **not** FlashInfer backend auto. Donor's multi-backend auto wins do not transfer through this setting. |
| Explicit choice | Only `flashinfer_cutedsl` is mapped; availability failure falls back. Wrapper passes FI backend `cute-dsl` and configured PDL | Activation would be a separate intervention from changing its tactic timing. It would not add FI auto competition. |
| Per-call admission | SM100-family, BF16 same-device contiguous A/weight, K%128,32-byte pointers, legal optional bias | Source shape eligibility does not attest loaded weights/configuration or a successful donor kernel. Batch-invariant mode bypasses this path. |
| Indexer weights projection | `weights_proj` is `ReplicatedLinear(hidden_size,index_n_heads,quant_config=None)`, called from `_run_parallel_input_projections` | A concrete unquantized candidate, but already placed on an auxiliary stream when eligible; isolated savings may be hidden behind the heavier default-stream projection. |
| Indexer K projection | Owning indexer uses `wk(main_head_dim,index_head_dim,quant_config=None)` and `_produce_k` calls it | A reachable module only when that indexer owns/writes K; do not multiply by every attention layer indiscriminately. |
| Compressor projection | Parallel compressor kv_score directly calls `torch.mm(...,out_dtype=torch.float32)` | Does not traverse this UnquantizedLinearMethod dispatch. Do not count it as BF16 donor exposure. |
| Draft/context projections | DSpark main/context modules pass their quantization config | Three shared-input MXFP8 projections are not made eligible by their BF16 input or this donor's name. PJ01 remains separate. |
| FI cute-dsl donor shapes | `_CUTE_DSL_BF16_MAX_M=32`; its cute-dsl family uses a cuBLASLt fallback above32 | The donor's larger-M multi-backend auto table is not a promise of that competition on our explicit cute-dsl wrapper. |

Target source already has warmup bucket matching: hybrid token buckets include DSpark query capacity, `round_up=True` matches serving; deferred MoE counts receive bounded additional passes. This is not a newly missing fix. Warmup defaults to legacy per-rank files for initialized world_size>1; managed v2 is gated pending a different FI coordination fix. The source passes a tuning process group when needed and profiles collectively. Donor provenance/policy behavior must be exercised through this actual path, not validated only with a single-rank managed-v2 unit test. No actual initialized target world/configuration was probed.

`requirements/` and `docker/` are absent from the retained partial pinned tree. Thus the installed FlashInfer dependency and whether a later image already contains this repair are **unattested**. The target's default source behavior is established; a live target absence claim is not.

## Controls worth keeping for a future authorized benchmark

Reopen only after an existing manifest or future authorized trace proves that a legal unquantized BF16 route is both used and materially exposed. Record exact image/FI revision, loaded backend/dtype, module names, actual and bucketed M/N/K, strides, PDL, batch-invariant setting, tactic and cache policy, and rank-cache load/hit decisions.

Separate three arms:

- A: existing selected target backend and settings.
- B: explicit eligible FI cute-dsl route with old isolated timing, otherwise same dependency/kernel candidates and same buckets.
- C: same explicit route/candidates with donor chain8 policy. B→C isolates ranking; A→B measures backend activation. Do not call A→C a pure timing-policy result.

Before interpreting service results, enumerate legal tactics on B200 for the exact shapes and compare matched warm/hot-weight and realistic cold-weight graph conditions. Preserve compile/warmup cost separately. Verify old policy re-ranking, warm reload, all-rank cache-hit/miss consistency and fallback behavior. A different reduction tactic needs numerical/output-contract testing; frozen weights alone do not establish exact token equality or distribution equality. For stochastic target sampling, do not silently downgrade an exact-output requirement to a loose GEMM tolerance.

Standard agent75 and Mooncake can measure any eventual TTFT/ITL/E2E/goodput effect; no new serving workload is justified yet. They cannot explain a tactic mismatch alone, so add module/tactic/cache-policy instrumentation and a bounded component measurement only if authorized. Primary long-output ITL headroom is unknown: exposed eligible fraction f times measured per-component reduction r is at most f*r under no added overhead, not a forecast. Auxiliary overlap, cold-versus-resident weight conditions, compilation cost and explicit backend changes may erase or reverse a microbenchmark gain.

## Yield and limitations

One source-led component examined; zero new hypotheses and zero accepted implementations. Useful output: backend activation versus tactic-ranking control, concrete reachable modules, explicit bypasses, cache-policy/reload and numerical guards. Park until backend/exposure evidence is available; do not spend another broad literature query to compensate for missing deployment data.

The five-case dispatch diagnostic executes the original function body with annotations stripped and inert platform/availability/callee stubs. It establishes default, explicit unsupported, explicit supported and unmapped selections, not hardware compatibility. Initial diagnostic failed because a sentinel passed to functools.partial was not callable; corrected to inert callables and reran. An initial dependency-directory search failed because those directories are not retained. Both are tooling failures, not target runtime failures. Early prior-match console output was truncated; complete JSON remains retained. No original failure was represented as a GPU result.
