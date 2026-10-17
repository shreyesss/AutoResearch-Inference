# OPS4 baseline and agent handoff

**Status:** calibration and independent frozen replay in progress. This file will be updated from the real four-task B0 ledger before autonomous search is enabled. Do not infer baseline metrics from source generation or earlier manual serving runs.

## Frozen study

- Campaign: `configs/campaign-ops4.json` (`qwen38-27b-ops4-v1`).
- Four tasks: short chat, agent, long document, smooth mixed. Exact IDs and immutable payload/schedule hashes are in `configs/workloads/ops4-registry.json` and `configs/workloads/ops-frozen/`.
- B0 serving: Qwen/Qwen3.8-27B, BF16, tensor parallel 1, 40,960 context, `max_num_seqs=512`, `max_num_batched_tokens=8192`, GPU memory fraction `0.92`, prefix caching and chunked prefill on, MTP draft tokens `0`.
- Protocol: fresh pinned vLLM server per timed task, three disjoint warm requests, fixed open-loop schedule, raw AIPerf records, server logs and metrics, GPU telemetry, full accounting and drain checks.

## Calibration evidence (source traffic; not the final fresh-server B0)

| Task | Current source cell | Configured rate | Observed finding |
| --- | --- | ---: | --- |
| Chat | `.artifacts/ops-b0/curve-chat-low/` | 2.56 RPS | 307/307 completed; realized 2.376 RPS; no queue growth. |
| Agent | `.artifacts/ops-b0/curve-agent-low/` | 0.15 RPS | 27/27 completed; realized 0.126 RPS; no queue growth. |
| Document | `.artifacts/ops-b0/curve-document-cold-0p05/` | 0.05 RPS | 18/18, realized 0.0480 RPS, zero prefix-cache hits, Qmax 3 briefly then cleared; drain 27.49 s / dispatch 354.07 s = 7.8%. TTFT p50/p90/p99 5.87/32.84/37.27 s, TPOT 63.9/99.0/114.2 ms/token. The 0.20 RPS overloaded cell is excluded. |
| Mixed | `.artifacts/ops-b0/curve-mixed-cold-0p1/` | 0.10 RPS | 36/36, realized 0.0966 RPS, zero prior-cache hits, Qmax 2, drain 23.63 s / dispatch 362.19 s = 6.5%; selected under the predeclared bounded-transient-queue rule. TTFT p50/p90/p99 1.35/17.15/30.76 s, TPOT 43.0/58.4/64.9 ms/token. The hot 0.10 retry is excluded. |

## Final matched fresh-server B0

Pending four validated cells. The ledger, per-request AIPerf exports, server/GPU logs, qualification verdict and `suite-front.json` will be linked here after the measurements complete.
