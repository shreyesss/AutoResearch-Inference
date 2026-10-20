# C03 implementation review — logical DSpark draft request counts

Status: plan only. Inspected serving software read-only on **this node, `jl-vm-541077` (223)** while its containers were running earlier in this planning session. No optimization, package installation, CUDA import, GPU job, container restart, or live-source edit was performed. This review owns optimization implementation and launch isolation. A separate evaluator designer owns the contract; a further independent evaluator builder implements its fixtures/probe/scorer without implementing C03.

**Latest state recheck, 20 October 2026 at 21:11 IST:** no router or serving-launcher process, no listener on port8000, and no running/stopped Docker containers were present. The service stopped after the earlier inspection; this review made no stop/start calls. The identity below describes the directly observed previous runtime, not a currently running service. Reattest after its next startup. The previous router executable is not established by the launcher executable, and a live `/proc` check is now unavailable.

Use the existing `latency-2xdep4-sla` profile and the user's fixed Mooncake multiplier **0.5**. Do not change either as part of C03. Work in `/home/ubuntu/Deepseek_serve-c03`, branch `experiment/c03-logical-draft`; preserve the original checkout and its current environments.

## 1. The actual current runtime

`/home/ubuntu/Deepseek_serve/.venv/bin/python` is the Python 3.10 launcher environment. `importlib.metadata.distribution("vllm")` there returns `PackageNotFoundError`: vLLM is not installed in that host environment. The observed launcher process used this interpreter to execute `lib/serve_recipe.py`, which launches Docker. Preserve this interpreter and the separate existing AIPerf environment; do not install vLLM into either. This does not attest the interpreter of a separately started router.

Both serving containers at the earlier live inspection were:

- Names: `dsv41-h200-vllm-latency-2xdep4-sla-0` and `dsv41-h200-vllm-latency-2xdep4-sla-1`.
- Image and image ID: `vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c`.
- vLLM: `0.30.1rc1.dev493+gac9126e58`, source pin `ac9126e58aa7bbab1856ba6593ba4d5003fea516`.
- Actual interpreter: container `/usr/bin/python3` (Python 3.12); package root `/usr/local/lib/python3.12/dist-packages/vllm`.
- Installed wheel provenance: `file:///vllm-workspace/dist/vllm-0.30.1rc1.dev493+gac9126e58-cp38-abi3-linux_x86_64.whl`.
- Model revision: `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`.
- Two TP1/DP4/EP4 engines; GPU groups `0,1,2,3` and `4,5,6,7`; backend ports 8100/8101; DP RPC ports 29510/29610; API server count 2 per replica; existing router on 8000.
- Seq64, maximum batched tokens 16,384, graph cap512, DSpark k5, probabilistic draft sampling, block rejection, adaptive verification **false**, prefix cache enabled, bounded replay disabled, FP8 KV with block64, existing Engram offload settings and full observability.

Evidence: the running launch process arguments, `docker inspect` restricted to image/ID/start time, and metadata/file reads inside both containers. Profile source is `serving/h200/vllm/profiles/latency-2xdep4-sla.yaml:3`; the host interpreter is selected by `serving/h200/vllm/serve.sh:9`.

The six inspected installed files have identical SHA-256 hashes in both replicas:

| Path relative to the installed `vllm/` root | SHA-256 |
| --- | --- |
| `v1/worker/gpu/dp_utils.py` | `b81a663c7e736f93c7be6ff7b6facebeb93ee4a52c280163b2ba9146fe33c341` |
| `v1/worker/gpu/spec_decode/speculator.py` | `3eba83a88928a1df1a9b3de152255d024df0ed566eef4b8480e6d546a3cfbf31` |
| `v1/worker/gpu/spec_decode/dflash/speculator.py` | `e7950d0bbdb3f982890689268eafc1a9d46d97335487e3c5c624945e3312afc6` |
| `v1/worker/gpu/spec_decode/dspark/speculator.py` | `97bcfaa655c6d4a5ecdfb17ab87b80547e8216b9d15a91c341798ebbb558f146` |
| `v1/worker/gpu/spec_decode/autoregressive/speculator.py` | `c40e801436bc78a77624e1d2c688db823a21b73ffc65f75d18ad78ffeef18118` |
| `v1/worker/gpu/model_runner.py` | `5fdae42c96977ddbdc2bf1363a5f16b0760a2288a68991ece31c9537932fd1a8` |

These identify the inspected source; compare again immediately before implementation/execution because a later restart or deployment could change it.

## 2. Exact installed path and missing behavior

All line numbers in this section refer to the installed source above, not a newer upstream checkout.

1. `spec_decode/__init__.py:37` selects `DSparkSpeculator` for DSpark. `spec_decode/dspark/speculator.py:40` inherits `DFlashSpeculator`, and DSpark does not override `propose`.
2. `dp_utils.py:67` builds the existing six-row CPU synchronization tensor. Row 5 records each rank's request count (`:73`); the existing all-reduce already supplies the DP-wide logical maximum. No new collective or tensor row is needed.
3. `dp_utils.py:142` initially computes that maximum, but `:143` overwrites it with the FULL microbatch descriptor capacity. The normal FULL path similarly stores `synced_desc.num_reqs` in `DPSyncState.num_reqs` at `:204`. Eager currently stores the logical maximum at `:170`.
4. `spec_decode/dflash/speculator.py:415` starts with the input-batch request count, prepares inputs, and at `:496` calls `_build_uniform_batch_dp_sync`.
5. `spec_decode/speculator.py:519` computes `target_dp_sync.num_reqs * num_query_per_req`, so target capacity becomes the draft query-token budget. `dp_utils.py:301` may then pad again to a draft graph bucket.
6. An online dummy target batch is created using target descriptor capacity in `model_runner.py:1813`. That padded `InputBatch.num_reqs` reaches DFlash `propose`; it must be narrowed consistently with the new logical DP bound. Merely changing the helper's multiplication would leave incompatible dummy metadata and assertions.
7. Shared helper caller `spec_decode/autoregressive/speculator.py:347` must remain correct even though this experiment runs DSpark. This installed version predates upstream's `target_dependent_ar/` directory name.

This establishes source eligibility: C03 behavior is missing in the running version. It does **not** establish that the chosen traffic produces useful eligible events or a speedup. The evaluator owns that next check.

## 3. Adapt the final PR semantics, not its intermediate commits

The archived four-commit patch is [changes.patch](/home/ubuntu/AutoResearch-Inference-c03/ideation/runs/h200-fresh-research-001/primary/vllm-project--vllm--58984/changes.patch). Its final commit is `77e45ab1cb273470b77e9158fd3d41b6239e8e63`, subject “simplify DP request count tracking.” It supersedes the earlier `num_reqs_unpadded` field and explicit `max_num_reqs` helper argument.

The final contract is:

- `DPSyncState.num_reqs` = the DP-wide maximum logical request count, identical on all ranks.
- `BatchExecutionDescriptor.num_reqs` = the graph's padded request capacity, when applicable.
- `num_tokens_across_dp` continues describing the agreed execution token shape; it may be padded.
- An online dummy drafter can reduce its local effective request count to `min(input_batch.num_reqs, dp_sync.num_reqs)`.
- Startup capture keeps the full descriptor capacity. An idle rank still participates in the required collective execution; it cannot independently skip drafting.

Only after the independently designed exposure diagnostic establishes useful eligible execution, the minimal adapted optimization should touch **three existing Python files**:

| File | Planned change |
| --- | --- |
| `v1/worker/gpu/dp_utils.py` | Change the `num_reqs` field comment and the FULL/microbatch return values to the logical maximum already available from row 5. Preserve target descriptor and token-padding behavior. Eager remains logical; all-zero early return remains unchanged. |
| `v1/worker/gpu/spec_decode/dflash/speculator.py` | Clamp only online dummy `num_reqs` when a DP sync exists, before query sizing and metadata construction. Add the final patch's optional effective-count argument to `prepare_dflash_inputs`; use that count for its launch grid and scheduled-length slice. Preserve positive-count/bounds assertions, all padding sentinels, slot mappings, and full capture allocations. |
| `v1/worker/gpu/spec_decode/autoregressive/speculator.py` | Adapt the final upstream compatibility clamp **after** the target-shaped prefill pass and before decode preparation (`:334`). Keep prefill shape and metadata unchanged; preserve the single-step early return. |

The existing base helper's final arithmetic already matches the final upstream version; it should not require a semantic change. The DSpark sampler, model, CUDA/C++ extensions, graph bucket definitions, checkpoint, scheduling settings, and acceptance algorithm require no C03 changes. Do not add the intermediate unpadded field or import unrelated #61806/#61807 changes wholesale.

Perform a final call-site search over the exact installed package before editing, because the `DPSyncState.num_reqs` contract is shared. The archived patch was previously found not to apply cleanly to this image. Translate its final behavior to the installed files; retain a small reviewable diff against byte-for-byte originals rather than attempting a blind cherry-pick.

## 4. Startup capture invariants and a concrete mechanism example

Read-only parsing of current `CG Capture:` startup-log descriptors found the same sets on **all eight ranks**:

- Target FULL: uniform query width6, 41 descriptors, maximum 384 tokens /64 requests.
- DSpark FULL: uniform query width5, 37 descriptors, maximum 320 tokens /64 requests.
- Configured general graph cap remains512. It is not the number of requests in either graph family.

Target request capacities:

```text
1,2,3,4,6,7,8,10,11,12,14,15,16,18,19,20,22,23,24,26,27,28,30,31,32,34,35,36,38,39,40,42,43,46,48,51,54,56,59,62,64
```

Draft request capacities:

```text
1,2,4,5,7,8,10,12,13,15,16,18,20,21,23,24,26,28,29,31,32,34,36,37,39,40,42,44,45,47,48,50,52,55,58,61,64
```

This confirms the current checkpoint's actual DSpark width5 rather than assuming the generic DFlash width6. Source: `dspark/speculator.py:49` distinguishes anchor sampling; the observed captures resolve the selected layout.

For a qualifying uniform target step with DP logical maximum **5**, target rounds to capacity6. Current drafting starts from six requests and rounds to the draft capacity7: **35 draft query rows**. C03 should start from five requests and select capacity5: **25 query rows**. This is source-derived arithmetic, not a measured event or performance estimate. At logical maximum9, target capacity10 and draft capacity10 yield 50 rows in both arms, so changing the logical count alone does not imply execution work was saved. Balanced rank occupancy alone is not a no-change case; graph boundaries matter.

Keep `dflash/speculator.py:161` capture and `dflash/cudagraph.py:93` descriptor-based capture intact. Capture's `prepare_graph_context(num_reqs)` uses descriptor capacity. Do not shrink the persistent max buffers or captured descriptor set in response to online counts. The proposal adds no capture-size tuning to C03.

## 5. Minimal source isolation using the current binary dependencies

Use **read-only per-file bind mounts into fresh experiment containers using the identical existing image digest**. Store byte-for-byte originals and treatment copies under the serving worktree, for example `c03/source/base/vllm/...` and `c03/source/treatment/vllm/...`, with a manifest of base and treatment hashes. Do this only during the implementation stage; no such copies or mounts were made for this review.

The first implementation step may prepare **launcher-only isolation and backend handover support before the exposure gate**, because the evaluator builder's diagnostic observation patch needs an isolated baseline container to run. Review this launch support independently and use it with the evaluator-owned observation patch while preserving baseline C03 semantics. The three-file C03 semantic adaptation above still waits for useful exposure. This avoids requiring an optimization port merely to determine whether the mechanism is active.

The mount replaces the Python source path for that experiment container only. It does not edit an installed package, rebuild the image, change dependency resolution, shadow the whole package with `PYTHONPATH`, or modify the current running containers. All compiled libraries and model dependencies continue to come from the exact current image. Use mounted baseline copies for the evaluator's equivalent launch/instrumentation control when requested.

Existing `lib/serve_recipe.py:138` has **no arbitrary source-mount option**. `common_docker` currently adds only the model-cache, engine-cache, and profiler-cache mounts (`:181`), then appends environment/entrypoint/image arguments (`:188`). Plan one small opt-in extension in the serving worktree: accept an explicit C03 source manifest, validate its allowlisted relative Python paths and expected baseline hashes, and append `--mount type=bind,src=...,dst=...,readonly` for those files before the image argument. With no manifest, the existing command remains unchanged. Apply the same manifest to both replicas and verify the in-container files before any request.

The worktree has no `.venv`. Run its backend launcher with the existing original checkout's **absolute interpreter path**. Preserve the router independently: `lib/serve_recipe.py:568` hardcodes `ROOT/.venv/bin/python`, but this is not proof that the last baseline router used that interpreter. Do **not** replace it with `sys.executable`, change router code, or start a worktree router as part of C03. The minimal launcher extension must permit backend-only handover, suppressing its router start/stop path; keep an existing attested router process running across A/B. No new environment or environment symlink is needed. Source the original checkout's existing `lib/env.sh` for its storage configuration rather than copying a possibly stale `.env` into the worktree; do not print its secrets.

If the router is absent, as in the latest read-only recheck, first try to recover and attest its prior Python executable/version, source hash and arguments. The corrected campaign manifests record the AIPerf client command, not a router PID/executable; merely reusing the Python3.10 launcher is insufficient evidence. If exact prior provenance cannot be recovered, explicitly disclose that gap, freeze and attest the restored router for a fresh baseline A, and preserve that exact process/runtime identically for B. In that case the older campaign results remain historical context, not a causally matched control. Router restoration is a separate, matched baseline operation shared by A and B, never a silent treatment-only dependency change.

Illustrative future command shape, **not executed and not yet supported until the small launcher extension is implemented**:

```bash
source /home/ubuntu/Deepseek_serve/lib/env.sh
/home/ubuntu/Deepseek_serve/.venv/bin/python \
  /home/ubuntu/Deepseek_serve-c03/lib/serve_recipe.py \
  --hardware h200 --engine vllm --profile latency-2xdep4-sla \
  --backends-only \
  --c03-source-manifest /home/ubuntu/Deepseek_serve-c03/c03/treatment-manifest.json \
  --dry-run
```

The expected added Docker argument for one file has this form:

```text
--mount type=bind,src=/home/ubuntu/Deepseek_serve-c03/c03/source/treatment/vllm/v1/worker/gpu/dp_utils.py,dst=/usr/local/lib/python3.12/dist-packages/vllm/v1/worker/gpu/dp_utils.py,readonly
```

Before launch, rule out reuse of bytecode from the original source: in disposable experiment containers only, use a fresh Python bytecode-cache location identically for both arms, or remove only the three corresponding cached bytecode files before starting the normal entrypoint. `PYTHONDONTWRITEBYTECODE=1` alone is insufficient because it does not prevent reading an existing `.pyc`. Verify loaded source identity in both replicas. The evaluator owns any no-op control and instrumentation-overhead checks.

Do not run baseline and treatment simultaneously on these eight GPUs. The orchestrator schedules backend stop/start handovers only after implementation and evaluator review. Preserve the exact profile and the independently attested router process/runtime. Unique artifact directories are sufficient; no additional service framework is needed.

## 6. Readiness, handoff and rollback

Implementation handoff consists of the three-file adapted diff, byte-identical baseline copies, source hash manifest, the small opt-in backend launcher diff, and rendered baseline/treatment commands. The evaluator designer owns the frozen diagnostic requirements and verdict contract. A distinct evaluator builder owns diagnostic hooks as a separate observation patch, applied identically to diagnostic baseline/treatment, together with fixtures and scorer implementation. The optimization developer adapts only C03 and the launch isolation; it must not revise the observation patch, evaluator or pass/fail thresholds. The orchestrator combines the separately reviewed patches and resolves any file overlap without changing their meaning.

Startup must retain image/interpreter/dependency identity, both GPU groups, model revision, profile arguments, sampler configuration and complete graph descriptor sets above. Compare both replicas' mount/source identities. Any graph capture failure, different descriptor set, mismatched rank shape, or import/buffer error blocks the treatment handoff until resolved; it is not a reason to silently change graph size, dependency versions, speculation, or the evaluator workload.

Rollback is a backend launch operation: stop only the experiment containers after the orchestrator authorizes the handover; rerun the saved baseline backend launch with the same original image and **no treatment source mounts**, leaving the attested router process untouched, then verify both backends and router. Since neither original checkout, original `.venv`, image filesystem, nor installed running-container files is edited, there is no package uninstall or reverse patch to perform. Keep all baseline results under `/home/ubuntu/Deepseek_serve/results/h200/vllm/aiperf-campaign` untouched.

Still unverified: exact last-baseline router interpreter and launch command; restoration of serving after its external stop; actual eligible-event frequency on the fixed current traffic; reduction in executed draft rows; distributed/sampler/KV correctness; treatment capture identity; loader/bytecode isolation; serving benefit; and a working implemented mount hook. These belong to the subsequent implementation and independent evaluation stages. This review claims source applicability of the inspected runtime and a concrete isolated implementation path only.

Reference family: [C03](/home/ubuntu/AutoResearch-Inference-c03/ideation/runs/h200-cross-audit-comparison-001/families/C03.md), including its linked E02/H02/H04 cards. The current PR is used through its archived patch; no new upstream version is substituted into the plan.
