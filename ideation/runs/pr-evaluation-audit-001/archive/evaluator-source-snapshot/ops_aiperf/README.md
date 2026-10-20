# AIPerf workload suites

This subsystem adds reproducible AIPerf workloads without changing or starting
any vLLM serving profile. Point it at an already-running OpenAI-compatible
endpoint. Results are isolated below:

```text
$RESULTS_ROOT/b200/vllm/aiperf-campaign/
```

## Install

```bash
cd /data/Deepseek_serve
bash install/aiperf.sh
```

This creates `.venv-aiperf` with exactly AIPerf 0.13.0. The project serving
environment remains separate.

## Start a vLLM profile

Use two terminals. The first terminal owns the server process; the second runs
AIPerf.

Terminal 1:

```bash
cd /data/Deepseek_serve
source source.sh

PROFILE=latency-dep8-sla make serve-b200-vllm
```

Wait for readiness and verify the OpenAI endpoint:

```bash
curl -s http://127.0.0.1:8000/v1/models | jq
```

To serve the proposed two-TP4 DSpark-k5 candidate instead:

```bash
PROFILE=balanced \
EXPERIMENTS="lat-dspark-k5 lat-seqs-80 lat-graph-512 batched-32k" \
make serve-b200-vllm
```

Keep the server in the foreground so failures remain visible. Stop it with
`Ctrl-C` after the benchmark.

## Prepare Mooncake subsets

```bash
source source.sh
python3 ops_aiperf/prepare_mooncake.py --download
```

The pinned source is verified by SHA256. Three deterministic, non-overlapping
ten-minute traces are written under:

```text
$MODEL_STORAGE_ROOT/datasets/aiperf/mooncake/subsets/
```

- `median`: representative request rate and joint ISL/OSL shape.
- `burst`: maximum one-second/ten-second arrival pressure.
- `cache-heavy`: maximum repeated-block share outside the burst window.

Every subset has a manifest with source offsets, distributions, cache score,
request count, and source/subset hashes.

## Dry-run the suites

Synthetic workloads need one externally supplied load mode:

```bash
bash ops_aiperf/run_suite.sh \
  --suite synthetic \
  --workload all \
  --candidate r7-control \
  --profile-label latency-dep8-sla \
  --request-rate 20 \
  --dry-run --no-sync
```

Or use `--concurrency N`. `mixed-bursty` intentionally requires request-rate
mode because its Gamma arrival process is part of the workload.

Production workloads own their timing. Do not pass concurrency:

```bash
bash ops_aiperf/run_suite.sh \
  --suite production \
  --workload all \
  --candidate r7-control \
  --profile-label latency-dep8-sla \
  --data-root "$MODEL_STORAGE_ROOT/datasets/aiperf" \
  --dry-run --no-sync
```

AgentX is the only exception; its pinned configuration uses concurrency 16
session trees and a 900-second profile.

## Run against a live endpoint

Terminal 2:

```bash
cd /data/Deepseek_serve
source source.sh

bash ops_aiperf/run_suite.sh \
  --suite synthetic \
  --workload agent \
  --candidate r7-control \
  --profile-label latency-dep8-sla \
  --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
  --base-url http://127.0.0.1:8000 \
  --concurrency 384 \
  --duration 150 \
  --warmup-duration 120 \
  --phase discovery \
  --no-sync
```

This is the closest AIPerf equivalent to the previous fixed 8K/1K c384 agent
screen. The AIPerf synthetic workload does not reproduce the native Zipf
prefix-cache layout.

For open-loop Poisson traffic:

```bash
bash ops_aiperf/run_suite.sh \
  --suite synthetic \
  --workload agent \
  --candidate r7-open-r20 \
  --profile-label latency-dep8-sla \
  --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
  --base-url http://127.0.0.1:8000 \
  --request-rate 20 \
  --duration 300 \
  --phase discovery \
  --no-sync
```

For the bursty ragged mix:

```bash
bash ops_aiperf/run_suite.sh \
  --suite synthetic \
  --workload mixed-bursty \
  --candidate r7-bursty-r20 \
  --profile-label latency-dep8-sla \
  --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
  --request-rate 20 \
  --duration 300 \
  --phase discovery \
  --no-sync
```

Common AIPerf behavior:

- Streaming response metrics.
- Server-provided token counts.
- Per-chunk usage correction for DSpark bundled chunks.
- Per-request record export.
- SLO goodput.
- Pinned tokenizer/model revisions.
- Discovery/confirmation/final repetitions of 1/3/5.

Optional telemetry:

```text
--server-metrics-url http://127.0.0.1:8000/metrics
--gpu-telemetry-url pynvml
```

Use `--no-sync` only for local development. Otherwise the runner invokes the
existing verified S3 delivery path after success, failure, or SLO
ineligibility.

## Run production workloads

Mooncake owns its arrival timestamps, so do not pass `--concurrency` or
`--request-rate`. The runner supplies `--workers-max 256` so client worker
capacity does not impose AIPerf's default cap of 32:

```bash
bash ops_aiperf/run_suite.sh \
  --suite production \
  --workload mooncake-median \
  --candidate r7-control \
  --profile-label latency-dep8-sla \
  --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
  --base-url http://127.0.0.1:8000 \
  --phase discovery \
  --no-sync
```

When you decide to test additional Mooncake cohorts:

```text
--workload mooncake-burst
--workload mooncake-cache-heavy
```

To replay the same timestamps at twice the recorded arrival load, add:

```text
--trace-speedup 2
```

The runner writes a deterministic derived trace containing only scaled
timestamps; token lengths and cache hash IDs remain byte-for-byte equivalent
as JSON values. This avoids AIPerf's synthesis path, which revalidates and can
reject otherwise valid Mooncake prefix blocks. Do not substitute
`--request-rate` or `--replay-speedup`; those do not preserve this loader's
trace semantics.

The convenience runner accepts the same load through its environment:

```bash
MOONCAKE_TRACE_SPEEDUP=2 \
MOONCAKE_CANDIDATE=r7-1xdep8-2x \
bash ops_aiperf/run_mooncake.sh
```

Pass workload names after the script to run only selected subsets.

Run the pinned Exgentic workload:

```bash
bash ops_aiperf/run_suite.sh \
  --suite production \
  --workload exgentic \
  --candidate r7-control \
  --profile-label latency-dep8-sla \
  --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
  --phase discovery \
  --no-sync
```

Run AgentX on a finalist:

```bash
bash ops_aiperf/run_suite.sh \
  --suite production \
  --workload agentx \
  --candidate r7-finalist \
  --profile-label latency-dep8-sla \
  --profile-path serving/b200/vllm/profiles/latency-dep8-sla.yaml \
  --phase discovery \
  --no-sync
```

AgentX supplies its own concurrency 16 and 900-second duration.

Repetition phases:

```text
--phase discovery      # 1 run
--phase confirmation   # 3 runs
--phase final          # 5 runs
```

## Workloads

### Synthetic suite

- `chat`: fixed 512/256.
- `agent`: fixed 8K/1K with thinking controls.
- `code`: fixed 2K/1K with thinking controls.
- `document`: fixed 32K/512.
- `mixed`: fixed 45/20/15/20 chat/agent/document/code pairs.
- `mixed-bursty`: bounded ragged lengths and Gamma arrivals at smoothness 0.3.

These are search evidence, not production claims.

### Production suite

- `mooncake-median`
- `mooncake-burst`
- `mooncake-cache-heavy`
- `exgentic`
- `agentx`

Mooncake and Exgentic use fixed schedule rather than a configured server-load
concurrency. Mooncake has 256 client workers solely to preserve recorded
arrival timing. Exgentic is pinned to:

```text
benchmark=swebench
harness=openai_solo
source_model=gpt-5.2-2025-12-11
48 conversations
```

This preserves LLM request snapshots without requiring server-side tool
execution.

AgentX uses the date-pinned Weka corpus. AIPerf only replays LLM calls and
recorded delays; external tools are not executed by this deployment.

## Result layout

```text
$RESULTS_ROOT/b200/vllm/aiperf-campaign/
  <suite>/<workload>/<candidate>/<timestamp>/
    manifest.json
    command.json
    command.sh
    console.log
    status.json
    delivery_status.json
    score.json
    score.csv
    artifacts/
      profile_export_aiperf.json
      profile_export_aiperf.csv
      profile_export.jsonl
      inputs.json
      ...
```

The manifest hashes the campaign, workload, runner, analyzer, Mooncake
preparer, serving profile when supplied, model/image identity, command, and
relevant environment.

Mooncake score files report output-speed SLA twice:

- `whole_trace`: every completed request, including very short responses where
  token-interval speed is intrinsically unstable.
- `sufficiently_long_outputs`: responses with at least 50 output tokens.

Both include median speed, the p10 speed met by 90% of requests, 30 tok/s
attainment, and the highest Economy/Standard/Fast output-speed tier. Formal
Mooncake qualification applies the speed gate only to sufficiently long
outputs while retaining TTFT and request-latency gates for every request.
Fixed-schedule runs also require exported replay-degradation and replay-lag
metrics; missing metrics fail closed, and replay lag p99 must remain at or
below 500 ms.

Cache hit share falls back to the per-request server usage fields
`usage_prompt_cache_read_tokens / usage_prompt_tokens` when AIPerf does not
emit an aggregate cache-rate metric. Scores include token totals and reporting
coverage so a missing usage record remains visible.

`score.json` is the normalized evidence file for manual comparison. It
contains:

- Eligibility and hard-gate failures.
- Completion/error rates.
- Good-request fraction and SLO goodput.
- TTFT, ITL, and request-latency distributions.
- Replay schedule lag/degradation.
- Output throughput.
- Context-overflow and cache metrics when available.
- Cost per SLO-qualified request.

AIPerf ITL is token-normalized. It does not replace the native SSE maximum
chunk-gap analysis.

Candidate promotion and selection are intentionally manual. No AIPerf script
edits serving profiles or chooses the next deployment configuration.

## Expected runtime

Approximate profile time, excluding model startup and dataset setup:

- Fixed synthetic workload: 5 minutes per discovery point plus warmup.
- Full synthetic suite: about 35–45 minutes.
- Mooncake subset: 10 minutes plus drain; three subsets about 30–40 minutes.
- Exgentic 48-session replay: depends on recorded timestamps and model speed.
- AgentX: at least 15 minutes per run, plus reconstruction, warmup, and drain.

Use one discovery run during broad search. Reserve three or five repetitions
and AgentX for finalists.
