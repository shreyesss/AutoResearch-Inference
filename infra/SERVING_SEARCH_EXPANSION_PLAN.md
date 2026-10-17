# Serving search expansion: implementation plan for approval

**Status:** proposed design only, 18 October 2026. The active `qwen38-27b-ops4-v1` campaign, its B0, and its measured cells are unchanged. This plan targets the same pinned Qwen3.8-27B revision, vLLM 0.28.0 image, BF16/TP1, 40,960-token context and single RTX PRO 6000 Blackwell. A domain or launcher change creates a new campaign identity and matched B0; older results remain readable under their original protocol.

## What the agent can change today

The active `configs/search-domain.json` and trusted `runtime/config.py` allow exactly five serving controls. Omitted values resolve to B0. Values are enumerated, not continuous.

| Control | B0 | Admissible values now | What the existing workloads can establish |
| --- | ---: | --- | --- |
| `max_num_seqs` | 512 | 64, 128, 256, 512 | A cap matters only if demand reaches it. The manual 128 probe was flat on short chat; cap 32 previously caused queueing. Do not score an obviously binding low cap as an ordinary optimization. |
| `max_num_batched_tokens` | 8192 | 2048, 4096, 8192, 16384 | The 4096 OPS4 mixed contrast showed a repeatable directional TTFT tail change on the *same 36 requests*, concentrated at one document-shaped request; it is not an unseen-tail or capacity claim. |
| `gpu_memory_utilization` | 0.92 | 0.85, 0.90, 0.92, 0.95 | Boot/KV-capacity and preemption pressure; a larger fraction need not improve latency when memory is not binding. |
| `enable_prefix_caching` | true | false, true | Cold independent requests cannot establish session reuse benefit. A cache-hit counter and qualified reuse task are required. |
| `mtp_draft_tokens` | 0 | 0, 1, 2, 3, 5 | Manual short-chat repeats showed faster decode but higher TTFT at depths 1 and 3. Check acceptance, content and each workload shape before promotion. |

`enable_chunked_prefill` and `long_prefill_token_threshold` are recorded in the domain but `active:false`, so the agent cannot propose them. The launcher knows how to render both, but that is not activation. Model/GPU/image/context, dtype, workloads and arrival schedules stay fixed in this study. AIPerf adaptive search changes *offered traffic*, not these server controls.

## Proposed typed branches

Implement a typed, conditional domain and a trusted argument renderer; do not expose raw shell flags. Intervals give an optimizer room to interpolate while explicit mechanism branches let the agent test ideas. Each row below requires a pinned-image launch check, resolved-effective-settings receipt and a matched B0 comparison before it becomes searchable.

| Branch | Controls to add or activate | Binding rule and evidence gate |
| --- | --- | --- |
| **A. Prefill and admission, first** | Activate `long_prefill_token_threshold`; add `max_num_scheduled_tokens`, `scheduler_reserve_full_isl`, `watermark`. Expand batched-token values around 4096/8192 after a small feasibility probe. | Keep chunked prefill enabled. Long-prefill threshold matters only with long requests and overlapping work; capture long-request TTFT, short-request interference, queue, preemptions and per-iteration tokens. `max_num_scheduled_tokens` defaults to the batched-token budget and should be varied only when its smaller cap is actually used, especially with MTP. The reservation flag and watermark target KV admission/thrashing; require pressure evidence. |
| **B. Execution and startup, next** | `enforce_eager` as a contrast, then a bounded `compilation_config` / CUDA-graph capture-size branch. | Verify exact baseline CUDA graph mode and capture coverage. Report model load, compilation, capture, ready-to-serve, steady-state latency and VRAM separately. A faster steady-state candidate with prohibitive startup cost is visible, not hidden inside a single score. `enable_dbo` is a separate capability spike before search. |
| **C. KV capacity and format** | Explicit `kv_cache_memory_bytes` *or* `gpu_memory_utilization`; `kv_cache_dtype` for a later quality-qualified branch. | Explicit KV bytes override memory fraction in vLLM: model them as mutually exclusive branches. Record actual allocated KV blocks and preemption/eviction. FP8 KV needs model-specific answer-quality and numerical checks in addition to boot and throughput. |
| **D. Reuse and hybrid cache** | Prefix-cache controls, `mamba_cache_mode`, `mamba_block_size`, `prefix_match_unit`. | Activate only after a repeated-prefix/dependent-session dev and unseen test workload exists. `mamba_block_size` requires prefix caching and multiples of 8; other divisibility/runtime constraints must be checked by the pinned launcher. Measure cache-hit rate and resumed-session correctness. OPS4 independent cold traffic cannot validate this branch. |
| **E. Speculation refinement** | Existing MTP depth as an integer/conditional branch; optionally supported verification settings after a separate spike. | Preserve MTP-off B0; require actual accepted/draft tokens, complete output accounting, and a semantic check. MTP effects may differ across 256-token chat, long-thinking agent and document outputs. |

Do **not** turn off chunked prefill as a free Boolean in the present 40,960-context campaign. Pinned vLLM rejects `max_num_batched_tokens < max_model_len` when chunked prefill is off; all currently enumerated token budgets are smaller. A legal no-chunk branch would need a 40,960-or-larger token budget and separate memory/boot validation. Likewise, `priority` scheduling has no meaningful contrast until requests carry validated priorities; precision/weight quantization, CPU offload, multi-GPU topology, model changes and source/kernel edits need separate resource or correctness contracts. These are research branches, not assumed-safe knobs.

## What changes in the optimizer and agent

1. **Domain and launcher:** version typed integer/real intervals, categorical values, dependencies, exclusion rules and feasible branches. Keep B0 admissible. Resolve all defaults, hash the complete effective configuration plus model/runtime pins, reject invalid combinations before using the GPU, and preserve failed boot artifacts.
2. **Experiment selector:** use simple local perturbation and random proposals as measured baselines; add an outer BO/TPE sampler for numeric/categorical serving settings with explicit budget and feasibility observations. Compare it with the Codex proposer at equal GPU time and equal validation policy. Bayesian optimization can exploit smooth numeric effects; the agent should read evidence, choose mechanism-specific contrasts, request profiling and propose *reviewable* domain amendments. It should not silently bypass the frozen domain.
3. **AIPerf inner loop:** fixed, matched dev traffic compares server settings causally. Adaptive rate/concurrency probing is a separate capacity study on B0 and selected finalists once SLOs are declared. Record every sampled rate and repeat, not just AIPerf's selected point. A load optimizer does not replace the outer server-setting search.
4. **Agent evidence and skills:** update the single `agent/SKILL.md` and its reference to show active versus inactive axes, runtime semantics, workload-specific B0 distributions, measured MTP/4096 tradeoffs, raw artifact paths, uncertainty and startup costs. Require a predicted mechanism, expected per-task tradeoff and falsification condition. Give it read access to all dev diagnostics; keep test outcomes sealed during proposal selection. This is filesystem research with an explicit state/ledger, not compressed metric-only feedback.
5. **Result tracking:** include branch/parameter provenance, effective defaults, boot success, load/compile/capture time, GPU memory and cache capacity, full latency distributions, request completion, errors, queue/preemption, MTP acceptance and paired B0 deltas. Plot dev task fronts and load curves with repeated-point uncertainty; do not collapse unlike prompt shapes into one unexplained p99 or call an unconfirmed point a win.

## Order and costs

| Checkpoint | Concrete deliverable | Cost and stop condition |
| --- | --- | --- |
| 1. Contract and capability | New campaign/domain schema, renderer, exact CLI help/runtime verification for branch A; static rejection of illegal combinations | No benchmark until B0 resolves identically and every new flag is confirmed in the pinned image. |
| 2. First measured contrast | One prefill/admission axis that can bind on OPS4 mixed, plus matched B0 at the same fixed dev schedule; inspect per-shape requests and preemption/iteration metrics | Each fresh-server mixed cell was about 13 minutes in the measured repeat. A same-server protocol could save startup only after order/cache checks. Stop an axis whose mechanism does not bind. |
| 3. Execution contrast | Eager or bounded graph capture against B0, including startup and steady-state cost | Compilation/capture can increase launch time and memory. Reject failed boot/OOM or incorrect output before a long evaluation. |
| 4. Wider conditional search | Add supported A/B branches, outer BO/TPE comparison and agent evidence; gate weak candidates on short dev, repeat contenders, then four-task diagnostic and sealed test | GPU trials remain serial on one GPU. Do not infer a full-suite result from the fast gate. New cache/precision branches wait for their own workload/quality evidence. |

This is an expansion of *server optimization*, not an instruction to spend the first campaign on a huge Cartesian grid. The first inspection after approval should show the new domain contract, exact resolved B0, one new booted control and its matched measurements; only then enable broader autonomous proposals.

## Evidence and primary references

- Local active domain and launcher: [`configs/search-domain.json`](../configs/search-domain.json), [`src/inference_autoresearch/runtime/config.py`](../src/inference_autoresearch/runtime/config.py).
- Local measured signals: [`infra/MANUAL_SERVING_SEARCH.md`](MANUAL_SERVING_SEARCH.md), [`results/2026-10-18-research-reset/README.md`](../results/2026-10-18-research-reset/README.md).
- [vLLM 0.28.0 engine arguments](https://docs.vllm.ai/en/v0.28.0/configuration/engine_args/): scheduler, KV/Mamba and compilation controls and dependencies.
- [vLLM 0.28.0 scheduler validation](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/scheduler.py): no-chunk token-budget/context check.
- [AIPerf 0.13 adaptive-search reference](https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/sweeping/bayesian-optimization.md): benchmark-side search and repetition, separate from vLLM launch settings.
