# Observed H200 baseline

**User-selected target:** 217.18.55.219, live two TP1/DP4/EP4 groups with DSpark k5. The initial “two TP4” description was corrected after inspecting the running containers; the user explicitly selected the observed DP4/EP4 layout. Checked-in H200 balanced TP4 recipes are not this baseline.

## Runtime evidence

Read-only SSH succeeded. [Inventory](evaluation/runtime-inventory.json) captured at 2026-10-20 12:18 UTC, with [startup evidence](evaluation/runtime-startup.json), [installed sources](evaluation/runtime-source/) and [package/model metadata](evaluation/runtime-source-extra.json). No container was modified or restarted.

| Item | Observed value |
|---|---|
| Hardware | Eight NVIDIA H200; 143771 MiB reported per GPU; driver580.126.20 |
| Interconnect/NUMA | NV18 GPU links; GPUs0–3 NUMA0, GPUs4–7 NUMA1 |
| Containers | `dsv41-h200-vllm-latency-2xdep4-sla-0` and `-1`; started12:07 UTC |
| Image digest | `sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c` |
| vLLM | `0.30.1rc1.dev493+gac9126e58` |
| Dependencies | Torch2.13.0+cu130; Triton3.7.1; FlashInfer0.7.0.post1; Humming0.1.16 |
| Model | `deepseek-ai/DeepSeek-V4.1-Flash`, revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027` |
| Per four-GPU group | TP1, DP4, expert parallelism enabled, API2 |
| Per-engine settings | max sequences64; batched tokens16384; graph cap512; max context1048576 |
| KV | FP8, block64, prefix cache SHA256; bounded SWA replay off |
| Speculation | DSpark5; probabilistic draft; block rejection; adaptive verification off |
| Engram | CPU offload and embedding across DP on |
| MoE | Startup explicitly selects **MARLIN** in both groups |
| Metrics/logging | Detailed request speculation, KV/graph/MFU metrics; request/output/delta logging enabled |

At the final readiness snapshot, **12:27:33 UTC**, both containers were running and still logging weight-loading progress. Connections to host ports8100/8101 were refused. This is not a serving-readiness attestation or a performance result. See [readiness evidence](evaluation/runtime-final-readiness.json). Do not infer a permanent startup failure from this snapshot.

The package metadata probe did not find a distribution named DeepGEMM/DeepSelect. These can be vendored; this does **not** prove absent kernel code. Resolve the actual extension/header path and build before a library experiment. Likewise, the startup `FLASH_ATTN` line is explicitly **ViT attention**, not proof of the text sparse-attention backend.

## Why the H200 ranking changes

| Candidate | Actual applicability |
|---|---|
| Humming backend, #52318 | Meaningful comparison: current logs select Marlin, Humming package present. V4.1 EP compatibility and numerical correctness still need qualification. |
| Humming indexed EP, #59488 | Conditional on selecting Humming and compatible prepare/finalize transport; current Marlin cannot benefit directly. |
| Small-head attention, #61615/#59418/#57673 | Model has64 heads; TP1 retains64. TP4 would have16. These changes are held outside the live-layout ranking. |
| Marlin alignment, #56697 | Expert width2304 is already divisible by128 at TP1/EP4. Pure TP4 width576 pads to640 today;64 alignment helps that different topology. |
| TP projection sharding, #58872 | No cross-TP redundancy to remove at TP1. |
| Engram/mHC fusion, #60938 | Its explicit gate is Blackwell-only; TP1 alone is insufficient. |
| DSpark graph reachability, #62040 | 64×6=384 already fits cap512. Must prove a missing rounded draft bucket; no automatic cap increase. |
| Draft budget, #59468 | MBT16384 is far above64×5. Requires observed budget-bound scheduling to matter. |
| Candidate-only indexer, #62463 | 2048×8=16384 candidate positions; useful work and compressed-context dimensions must be measured. Short8K synthetic traffic is not proof of long-context benefit. |

## Installed-source membership checks

These are scoped implementation observations, not an exhaustive clean-tree attestation:

- `indexer_topk.py` gates DeepSelect on the SM100 family. #59204 SM90 integration is absent in this inspected file.
- `candidate_blocks.py` still allocates full-width score work and calls full-width top-k; #61039 valid-block path is absent in this inspected file.
- `models/deepseek_v41/nvidia/ops/mhc.py` gates overlap on SM100. #60768 would introduce a new H200 path.
- `models/deepseek_v41/nvidia/flashmla.py` lacks #61615 native-prefill-head selection.
- `models/deepseek_v41/attention.py` lacks #58872 token-sharded fused projection.
- `fused_moe/oracle/mxfp4.py` still rounds expert intermediate dimensions to128, without #56697's SM90/BF16 alignment guard.

For remaining candidates, record `unknown` until the installed relevant functions are compared with the pinned patch. A merge date or vLLM version label is insufficient. Both containers' deployment identity is recorded; extracted code is a sampled installed-source snapshot, not proof that no hidden overlays exist anywhere.
