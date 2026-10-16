# First real diagnostic baseline

Run window: 16 October 2026, 22:01:53–22:04:03 UTC. This is a functioning infrastructure check and one low-load diagnostic point, not a representative workload, an SLA pass, or a confirmed tail estimate.

## Pinned setup

| Item | Observed value |
|---|---|
| GPU | NVIDIA RTX PRO 6000 Blackwell Server Edition; 97,887 MiB; driver 595.91.07 |
| Model | `Qwen/Qwen3.8-27B` BF16, revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` |
| vLLM | `vllm/vllm-openai:v0.28.0`, digest `sha256:61fc8a896b0a4fbbbdc063bc4b0dbc25ce98e02b5050c24aeb7830ac02039b14` |
| AIPerf | 0.13.0; raw records, HTTP trace and server metrics exported |
| Server | TP1, BF16, context 40,960, `max_num_seqs=512`, qwen3 reasoning parser; no MTP |
| Resolved defaults seen in log | chunked prefill with `max_num_batched_tokens=8192`; prefix caching enabled; 32.61 GiB KV cache |

The first unmodified boot failed before serving: vLLM's default `max_num_seqs=1024` exceeded the 646 available Mamba cache blocks. The error and original argv are retained as `server-failed-stock.log` and `server-failed-stock-argv.json` in `.artifacts/first-baseline/`. A 512-sequence feasibility cap booted without disabling CUDA graphs. The model's first cold weight load took about 302 seconds; a cached rerun took under one minute. Startup cost is separate from request metrics.

## Traffic realization

A three-request AIPerf validation showed that a nominal 512 input-token target produced 472 server tokens when the request disabled thinking. Setting the AIPerf target to 552 produced 512 server tokens in a separate-seed warmup. AIPerf's built-in warmup repeated prompt payloads in the timed phase, so the timed cell used separate warmup content and no built-in warmup.

The timed cell offered 12 distinct requests at 0.1 requests/s. All 12 returned HTTP 200 with no errors or cancellations. Server usage reported 512–513 prompt tokens (mean 512.17), exactly 256 completion tokens, and zero reasoning tokens per request. The 12 request bodies had distinct hashes. Actual dispatch spacing was 9.999–10.002 seconds; scheduled-credit to dispatch lag was 0.51 ms p50 and 0.80 ms p99. Server metrics reported at most one running request, zero waiting requests, and zero preemptions.

## Measured point

| Metric | p50 | p99 |
|---|---:|---:|
| TTFT | 88.01 ms | 105.62 ms |
| Request-level TPOT (AIPerf inter-token latency) | 37.39 ms/token | 37.43 ms/token |
| Request latency | 9,621.40 ms | 9,647.08 ms |

AIPerf reported 23.70 completed output tokens/s over the full 129.62-second phase, including the initial scheduled interval and drain. From the first actual dispatch to the last terminal response, the same 3,072 tokens yield 25.68 tokens/s over 119.62 seconds. These denominators are stated separately because the run began sending its first request after a 10-second scheduled interval.

Per-chunk server usage was requested and each response streamed 256 chunks; the reported inter-token latency is a request-level decode average, not a pooled token-gap percentile. The AIPerf GPU telemetry worker missed heartbeats and stopped, so GPU telemetry is incomplete. vLLM server metrics and raw request records were exported.

## Evidence and limits

- Summary: `.artifacts/first-baseline/aiperf/profile_export_aiperf.json`
- Per-request metrics: `.artifacts/first-baseline/aiperf/profile_export.jsonl`
- Raw requests/responses: `.artifacts/first-baseline/aiperf/profile_export_raw.jsonl`
- Server metrics: `.artifacts/first-baseline/aiperf/server_metrics_export.json`
- Server log and startup failure: `.artifacts/first-baseline/server.log`, `server-failed-stock.log`; exact successful invocation: `server-success-argv.json`
- Reproducible commands: `infra/first-baseline.sh` and `infra/README.md`

Twelve requests are far too few for a reliable p99 or an SLA conclusion. The workload is synthetic and low-load; no production representativeness, capacity ceiling, tuning gain, or scientific search qualification follows from this point. The next inspection should choose SLA thresholds and approve a bounded load ladder with repeated windows before any serving-parameter search.
