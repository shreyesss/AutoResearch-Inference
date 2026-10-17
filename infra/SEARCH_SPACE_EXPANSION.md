# Serving search-space expansion for the next campaign

Status: evidence-backed design, not an active change to `qwen38-27b-ops4-v1`. The active campaign's hashes, B0, and measured candidate stay comparable. A wider domain must receive a new campaign/domain version and new matched B0 before autonomous evaluation.

## Why the current five axes are insufficient

The current [domain](../configs/search-domain.json) exposes only `max_num_seqs`, `max_num_batched_tokens`, `gpu_memory_utilization`, prefix caching, and MTP depth, each on a small grid. It omits scheduling, KV allocation and precision, Mamba cache, and compilation choices that exist in the **pinned vLLM 0.28.0** interface. Treating the existing grid as the whole serving search would miss meaningful mechanisms. Conversely, adding a large Cartesian product without boot checks, mechanism relevance, and quality rules would consume the GPU on invalid or uninformative configurations.

## Candidate families in pinned vLLM 0.28.0

| Family | Specific controls documented in the pinned runtime | Condition before activation |
| --- | --- | --- |
| Scheduler and prefill | `max_num_batched_tokens`, `max_num_scheduled_tokens`, `max_num_seqs`, `long_prefill_token_threshold`, `scheduler_reserve_full_isl`, `watermark` | Verify exact CLI/config resolution; long-prefill effects require long requests and measured contention. `enable_chunked_prefill=false` conflicts with a budget smaller than the 40,960 model context in pinned scheduler validation, so it is a conditional branch with a larger feasible budget, not an independent Boolean. |
| KV capacity and representation | `gpu_memory_utilization`, `kv_cache_memory_bytes`, `kv_cache_dtype` | Never vary memory fraction and explicit KV bytes as though both bind: explicit KV bytes overrides the memory fraction. FP8 KV requires a numerical quality check and capacity/precision evidence. |
| Reuse and hybrid Mamba state | `enable_prefix_caching`, `mamba-cache-mode`, `mamba-block-size`, `prefix-match-unit`, `use-replayssm` | Current OPS4 independent cold streams cannot validate reuse benefits. Add a qualified session/reuse dev/test task first. Check model/kernel support and any numerical differences. |
| Speculative decoding | Native MTP `num_speculative_tokens`, acceptance metrics | Verify boot, acceptance, output semantics, and cost on each output class. Explore depth conditionally, including no-MTP B0. |
| Execution/graphs | `enforce_eager`, `compilation_config` capture sizes/mode, `enable-dbo` | Compare compile/startup cost separately from steady-state serving. Check graph coverage, memory, and pinned-model support. DBO is a feasibility experiment before it is a search axis. |

These are **candidate research axes**, not a claim that all combinations boot or help this model. Precision/quantization, alternate kernels, source edits, multi-GPU topology, and model changes need separate answer-quality and hardware contracts; they should not silently enter this particular server-settings campaign.

## Search policy

1. Expand the *typed* domain beyond a few preset values: integer/real intervals, Boolean/categorical choices, conditional dependencies, and explicit mutually exclusive branches. The trusted launcher must map typed values to argument arrays, record resolved runtime settings, and reject unsupported combinations before GPU traffic. Version domain and baseline identity.
2. Preserve a mechanism-focused proposer that can read evidence and request a contrast. Add an outer optimizer baseline for the same domain and GPU budget (e.g. mixed-variable Bayesian optimization/SMBO). Compare both against simple random and local perturbation baselines; use the agent where it can justify new mechanisms or domain amendments, not as a substitute for statistical selection.
3. Use AIPerf adaptive search for **client load** only. Its `--search-space` fields address AIPerf benchmark configuration, not vLLM launch arguments. A load-capacity probe belongs on selected configurations after a numeric SLA is declared; it does not make every outer-loop candidate cheap.
4. Pair all server configurations on the same fixed dev schedule for causal comparisons. Run an adaptive load boundary separately on B0/finalists and confirm its selected rate on a fresh fixed test schedule. Keep task-conditional results and uncertainty rather than collapsing unlike prompts into an unexplained p99.

## Immediate implementation checkpoint

Build a *new* campaign's launcher/domain in small branches: first activate and smoke one scheduler control (`long_prefill_token_threshold` with chunked prefill on) and one execution control (`enforce_eager` or a bounded compilation config). Record boot and resolved settings, then measure a matched B0 and candidate on the fast dev task. Expand KV/Mamba/precision branches only after a workload and quality gate can observe their intended effect. Do not relabel the current single-window OPS4 results as evidence for untested axes.

## Primary pinned-runtime references

- [vLLM 0.28.0 engine arguments](https://docs.vllm.ai/en/v0.28.0/configuration/engine_args/): scheduler, KV, Mamba, compilation and executor controls.
- [vLLM 0.28.0 scheduler configuration source](https://github.com/vllm-project/vllm/blob/v0.28.0/vllm/config/scheduler.py): token-budget/context and chunked-prefill validation.
- [AIPerf 0.13 adaptive-search reference](https://github.com/ai-dynamo/aiperf/blob/v0.13.0/docs/sweeping/bayesian-optimization.md): benchmark-side search dimensions, SLA filtering and trial repetition.
