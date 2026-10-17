# v3c serving search space

**Status:** versioned proposal. `configs/campaign-sla-serving-v3c.json` is a new campaign; the running v3b campaign and its evidence are unchanged. The model, vLLM image, GPU, 40,960-token context, workload bodies, arrival schedule, and approved research SLA remain pinned.

| Server control | B0 | v3c values | Interpretation |
| --- | ---: | --- | --- |
| `max_num_batched_tokens` | 8192 | 2048, 4096, 8192, 16384 | Prefill/decode scheduling on the mixed workload. |
| `long_prefill_token_threshold` | 0 | 0, 2048, 8192 | Diagnostic with chunked prefill enabled; check actual long-prefill contention. |
| `enforce_eager` | false | false, true | Compare startup/graph cost and steady-state service separately. |
| `max_num_seqs` | 512 | 64, 128, 256, 512 | Restored diagnostic axis. Read observed active sequences and queueing: a small cap may create overload rather than improve service. |
| `gpu_memory_utilization` | 0.92 | 0.85, 0.90, 0.92, 0.95 | Restored diagnostic axis. Check successful boot, actual KV allocation, occupancy, and preemption before claiming a capacity benefit. |

The runtime already accepts these five controls. Omitted values resolve to B0. AIPerf request rate is an evaluator input, not a serving parameter. This grid is a proposal domain, not a claim that all combinations are feasible or valuable. The short 36-request screen establishes only gross validity and regression evidence; class-specific research SLA evidence requires larger samples and independent confirmation.

Prefix caching remains on and MTP remains off. Independent cold requests have no demonstrated prefix reuse; enable a cache branch only with token-exact repeated prefixes and observed hits. Earlier MTP 1/3 manual trials found a decode gain and a TTFT cost, but accepted-token telemetry and semantic-quality checks are still needed before MTP can enter the SLA winner search. Disabling chunked prefill is also held out because the present token budgets are below the pinned 40,960-token context and require a separate feasible branch.

The campaign specifies `gpt-6-sol`, medium reasoning, eight proposal attempts and a two-finalist budget. **The current v3 controller has not yet implemented a cheaper two-finalist promotion path**: it requires finalists to equal proposals and can run the expensive development/profile stages for every viable proposal. Do not launch v3c until that controller gate is updated and tested. The two-finalist decision must use adequate evidence; a single 36-request p90 ranking is too noisy.

Source: `configs/search-domain.json` (historical larger domain), `configs/search-domain-v2.json` (v3b domain), `src/inference_autoresearch/runtime/config.py` (trusted argument renderer), `infra/V3_AXIS_ADMISSION_DECISION.md` (axis evidence limits), and `infra/MANUAL_SERVING_SEARCH.md` (MTP observations).
