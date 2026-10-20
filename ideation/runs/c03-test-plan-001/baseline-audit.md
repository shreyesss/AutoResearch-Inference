# C03 baseline audit — corrected 0.5× campaign

The current-node Mooncake median baseline is usable for characterization: **4,001 of 4,004 requests succeeded**, replay p99 lag was **4.335 ms**, and replay was not degraded. Its `eligible: false` means it missed service SLOs; it does **not** mean the benchmark failed to run or that these data must be discarded. Keep the user-selected **0.5 trace speed** and exact `serving/h200/vllm/profiles/latency-2xdep4-sla.yaml` profile. This audit executed no benchmark and changed no runtime, environment, serving code, or evaluator code.

This supersedes earlier discussion of the 1× runs. The corrected shared result root contains exactly two runs below. Their own artifacts, rather than directory names, establish request counts and trace speed. Detailed provenance, raw error locations, commands, metrics, and SHA256 receipts are in [baseline-audit.json](baseline-audit.json).

## Which baseline belongs to this node

The final execution target is this node, `jl-vm-541077` / node 223. A read-only `nvidia-smi --query-gpu=uuid --format=csv,noheader` inspection matches **all eight GPU UUIDs** in the median run. The burst run records a different set of eight GPU UUIDs. Its exact remote hostname is not attested by these artifacts, which say only `localhost`/`127.0.0.1`.

Therefore use median as the historical current-node baseline. Burst is useful workload context, but cannot serve as this node's paired A control. Their overlapping wall-clock timestamps are not evidence of two benchmark clients competing on this node. Do not pool these runs to estimate repeatability: they differ in workload and GPU node, and each has one profiling repetition.

| Recorded result | Median, current node | Burst, other GPU node |
|---|---:|---:|
| Run ID | `20261020-145417` | `20261020-145708` |
| Profiling time, 20 Oct 2026 IST | 20:26:26–20:46:43 | 20:29:23–20:49:32 |
| Attempted / successful / errors | 4,004 / 4,001 / 3 | 4,220 / 4,220 / 0 |
| Completion / error rate | 99.9251% / 0.0749% | 100% / 0% |
| Replay p99 lag / degraded | 4.334592 ms / false | 3.364457 ms / false |
| Export complete / cancelled | true / false | true / false |
| Output tokens/s | 585.207 | 631.330 |
| Successful requests/s | 3.2854 | 3.4912 |
| TTFT p50 / p99 | 2,618.968 / 12,571.637 ms | 2,949.200 / 11,626.567 ms |
| Request latency p99 | 78,664.610 ms | 72,784.489 ms |
| AIPerf per-request ITL p50 / p99 | 61.748 / 1,006.916 ms | 72.420 / 1,077.434 ms |
| Long-output ITL p50 / p99 (≥50 tokens) | 35.885 / 222.322 ms | 43.968 / 274.591 ms |
| Long-output ≥30 tokens/s attainment | 47.8723% | 38.3378% |
| Repository scorer length-aware good fraction | 60.7143% | 54.6919% |
| Repository scorer length-aware goodput | 1.99470 requests/s | 1.90938 requests/s |
| Native AIPerf goodput | 0.90490 requests/s | 0.79502 requests/s |
| Cache-hit share | 30.9942% | 28.8906% |
| Token-weighted speculative acceptance length | 2.68787 | 2.63066 |
| Draft acceptance rate | 33.7574% | 32.6132% |
| Remote artifact delivery | complete | failed, return code 1 |

Numbers above are attributed to existing `score.json` and AIPerf exports, not independently generated performance results. Native AIPerf and the repository's length-aware goodput use different definitions; do not interchange them. Whole-trace ITL is strongly affected by short outputs; retain the length-aware cohort. Failed artifact upload is distinct from a failed benchmark: burst has local complete exports and zero request errors. Existing cost metrics assume $36/node-hour; this audit does not validate that price for H200.

## The three median errors

`artifacts/phase_manifest.json` and the per-request JSONL agree on exactly:

1. One HTTP 502 `Bad Gateway`, message `Server disconnected`.
2. One `ClientOSError(104, 'Connection reset by peer')`, with `ConnectionResetError` in its cause chain.
3. One HTTP 502 `Bad Gateway`, message `[Errno None] Can not write request body for http://127.0.0.1:8100/v1/chat/completions`.

These are connection/transport failures, not evidence of C03 correctness failure or model error. The artifacts do not identify their underlying cause. They remain in the denominator. The 0.0749% error rate is below the existing 0.1% gate; completion exceeds 99.5%. Burst has no recorded request errors. Neither corrected run has the mass connection timeouts seen in the superseded 1× artifacts.

Both runs fail existing service SLO gates: good-request fraction and long-output speed attainment are below 95%, and p99 TTFT exceeds 4 seconds. Median also exceeds the 75-second request-latency threshold. These are measurable baseline deficiencies C03 may or may not improve; requiring baseline service SLO success before allowing a controlled comparison would conflate performance with experiment validity.

## Exact workload and existing client

Both recorded commands invoke `/home/ubuntu/Deepseek_serve/.venv-aiperf/bin/aiperf profile`, AIPerf **0.13.0**, with streaming chat, server token counts, per-chunk usage, raw exports, one profiling repetition, random seed 42, fixed schedule, 256 maximum workers, 120-second warmup, and 300-second warmup grace. The public target is `http://127.0.0.1:8000`; server scrapes cover 8100, 8101 and 8000. Their actual input files are:

| Input | Actual rows | SHA256 |
|---|---:|---|
| `/home/jl_fs/datasets/aiperf/mooncake/scaled/0p5x/median.jsonl` | 4,004 | `91fb37aac45c4aafc4c8c04e42d92bb0654f68eebd4f02b09adeee5449c5e1e1` |
| `/home/jl_fs/datasets/aiperf/mooncake/scaled/0p5x/burst.jsonl` | 4,220 | `99ef8f89825c5df6eacef0a71457c3392130e85cb5e532dc9ea56eeba25ecf73` |

Both scaling manifests explicitly say `speedup: 0.5`, doubling the 600-second source window's arrival schedule to about 1,200 seconds while retaining requests. Measured durations including completion were 1,217.803 seconds for median and 1,208.756 seconds for burst. Do not substitute the unscaled files or infer the number of requests from a nominal duration. The workload hash in the run manifest hashes its YAML, not the trace body; both are recorded separately here.

Read-only local package metadata confirms `.venv-aiperf` is Python 3.12 / AIPerf 0.13.0. The existing `.venv` is Python 3.10 / AIPerf 0.11.0 and has no installed vLLM or Torch distribution. Serving uses the existing launcher/container setup; `.venv` must not be repurposed or upgraded. Preserve both environments and the active vLLM image. The benchmark's existing client is `.venv-aiperf`, not a newly created environment.

Raw request payloads request `ignore_eos: true` and trace-derived `max_completion_tokens`; they do not set temperature or request seed. Captured serving logs resolve `temperature=1.0`, `top_p=1.0`, `top_k=0`, `seed=None`, `watermarking=True`, `ignore_eos=True`. Client random seed 42 does not make model sampling deterministic. Preserve these service settings for A/B; an explicitly separate correctness fixture can fix request seeds.

## Identity and coverage limits relevant to C03

Both manifests record identical profile SHA256 `edb4c68cb4ee72415abe65c077683a8f88942bfcc8fff5833270ba05cdddcab8`, campaign SHA256 `4135f96553bce2935f2e4282ffff396d46e2d87b38d3646f5110adf8140ca54c`, model/tokenizer revision `2cba9e42aa026125f3ed06c6d98c1db82f7ca027`, and evaluator source hashes. The profile specifies two TP1/DP4/EP4 replicas, max sequences 64, batched tokens 16,384, graph maximum 512, DSpark k5, adaptive verification off, prefix caching on and bounded replay off. The run manifests leave `selected_image` blank; archived host attestations provide the pinned image, but are not contemporaneous per-run image receipts.

Median records git `11c249d28b2962f7384b4ab1fd7c1664704e7524`; burst records `cc479a4ba376ce4739126424f39881aa2c9311a3`. Current local HEAD is the latter. During this audit the original checkout has user/other edits in `ops_aiperf/runner.py`, `ops_aiperf/README.md`, and `tests/test_aiperf_campaign.py`; they were not modified by this agent. Current runner SHA256 `e9e84fa55e8007917c5eaca47429fb2447ab3999b5b58256b10c6b03008bc18a` differs from the recorded baseline runner `d17ddd297a2330bfdef682bad01136ea14d8e2516c8e9e5d36399d446198aa35`. Current campaign and analyzer hashes match the corrected baseline. Freeze and record the actual chosen runner before paired execution; do not silently overwrite these changes.

Both replicas have captured vLLM logs. Metrics expose engine labels 0–3 at both 8100 and 8101, so all eight engine identities are represented. Median has server usage and speculative metrics for all 4,001 successes; burst has server usage for all 4,220 successes and speculative metrics for 4,219. Retain this one-record speculative-coverage gap explicitly. Failed requests have no completed-token/speculative metrics. Last captured router in-flight and engine running/waiting gauges are zero, and all intended requests have terminal records. This supports completion/drain assessment, while not proving a predeclared multi-sample drain barrier was used.

The saved standard counters and serving logs do not contain the decisive C03 triplet—real request count, target padded count, draft padded count—joined by iteration and every rank. No `cudagraph`, `CUDA graph`, or `padding` match was found in the four run-scoped vLLM logs. Existing speculative token counters describe generated proposals and acceptance; they do not prove extra padded rows were executed. Thus these baseline results establish workload/service behavior, but **do not yet activate or falsify C03**. The first C03-specific check must observe the installed DSpark path's real/padded/dummy-rank behavior, with the same profile and 0.5× workload, before optimization code changes.

No new evaluator, benchmark, serving patch, environment installation, service restart, or GPU experiment was performed for this audit.
