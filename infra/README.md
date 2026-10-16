# First real measurement

The pinned AIPerf input, replay, reporting and MTP capability check is documented in [CAPABILITY_SPIKE.md](CAPABILITY_SPIKE.md). Its small generator config and TraceLab sample selector are in this directory; raw evidence stays in `.artifacts/capability-spike/`.

This is a small, manual infrastructure check before the full `iar` campaign CLI exists. It measures a diagnostic synthetic chat workload on the target GPU. It does not establish a representative workload or a confirmed p99/SLA result.

Pinned inputs:

- Model: `Qwen/Qwen3.8-27B` at revision `1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0` (BF16 checkpoint)
- Server: `vllm/vllm-openai:v0.28.0`; `first-baseline.sh up` saves the pulled image digest
- Benchmark client: AIPerf `0.13.0` in `../.venv`
- Fixed task: one GPU, BF16, 40,960 maximum context, non-thinking chat requests. vLLM's default `max_num_seqs=1024` failed startup because the hybrid Mamba cache had only 646 blocks; this diagnostic uses a 512-sequence cap and preserves the failure log.

From this directory:

```bash
../infra/first-baseline.sh up
docker logs -f iar-b0
../infra/first-baseline.sh smoke
ARTIFACT_SUBDIR=validation REQUEST_COUNT=3 RPS=0.5 SEED=41 ../infra/first-baseline.sh benchmark
ARTIFACT_SUBDIR=disjoint-warmup REQUEST_COUNT=2 RPS=0.1 SEED=43 ../infra/first-baseline.sh benchmark
INPUT_TOKENS=552 RPS=0.1 CONCURRENCY=2 REQUEST_COUNT=12 SEED=42 ../infra/first-baseline.sh benchmark
../.venv/bin/python ../infra/summarize.py ../.artifacts/first-baseline/aiperf
../infra/first-baseline.sh down
```

The validation cell found that AIPerf's nominal 512 input tokens became 472 server tokens because non-thinking formatting differs from AIPerf's default chat template. A target of 552 is expected to yield 512, and the timed export must confirm it. AIPerf reused built-in warmup prompts in the timed phase, so warmup is run separately with a different seed and no built-in warmup is used for the timed cell. The first diagnostic benchmark sends 12 requests at 0.1 request/s and requests exactly 256 output tokens using vLLM's `ignore_eos` and `min_tokens` controls. It exports raw HTTP and per-request records under `../.artifacts/first-baseline/aiperf/`. Actual server-reported counts must confirm both lengths. The 12-request p99 is only a path check. A load sweep, repeated windows and a declared SLA threshold are needed before a performance claim.

Check the server response, actual token counts, all request outcomes, offered versus achieved dispatch, TTFT and inter-token latency p50/p99, completed output tokens/s, and GPU/server logs. Inspect AIPerf's definition of inter-token latency before mapping it to the handoff's request-level TPOT. Keep this diagnostic separate from representative and search-qualified campaign results.
