# Correctness, capacity, and profiling

The harness drives any running OpenAI-compatible endpoint. Keep server image,
model revision, profile, experiment set, workload, SLOs, and hardware fixed
when comparing engines. Capacity runs are intentionally separate from
instrumented profiling runs.

## 1. Smoke before load

The default suite first checks `/v1/models`, exact arithmetic, reasoning,
tool calling, an 8K-class prompt, repeated prefixes, and a generated PNG image:

```bash
./.venv/bin/python testing/common/smoke.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model deepseek-v4.1-flash \
  --output /tmp/dsv41-smoke.json
```

The image check is required for vLLM/SGLang qualification. TensorRT-LLM image
support is unvalidated: first run its text-only correctness stage with
the same command plus `--skip-image`, then use the explicitly opted-in
multimodal procedure in `serving/b200/tensorrt/README.md`.

## 2. Generate deterministic workloads

Generation uses the pinned Hugging Face tokenizer and revision, fits prompts
to chat-template token counts, and writes request JSONL with session, prefix,
thinking, tool, image, and target/actual token metadata.

```bash
source lib/env.sh
./.venv/bin/python testing/common/generate_workload.py \
  --config testing/workloads/text-grid.yaml \
  --case mixed-8k-512 \
  --requests 128 \
  --seed 17 \
  --output /tmp/mixed-8k-512.jsonl
```

Available suites are:

- `default-mix.yaml`: fixed chat/agentic/long-document/code/multimodal mix.
- `text-grid.yaml`: isolated prefill, decode, mixed, and near-1M anchors.
- `prefix.yaml`: cold, hot, Zipf, and multi-turn prefix reuse.
- `multimodal.yaml`: sparse image-share/count/resolution anchors.
- `ragged-mix.yaml`: one deterministically shuffled case that places
  heterogeneous prefill, decode, reasoning, tool, prefix, near-1M, and image
  requests in the same closed-loop window.
- `offline-throughput.yaml`: fixed-output, thinking-off shapes for maximum
  closed-loop output TPS without latency SLO qualification.

`REQUESTS` controls dataset diversity, not the number of requests issued by a
duration-based capacity run; the load generator cycles the dataset.
Workloads can declare `minimum_requests`; the suite automatically raises the
generated record count to that minimum. Ragged and offline suites require at
least 256 records so the initial high-concurrency window is diverse.

## 3. Closed- and open-loop saturation

Closed loop keeps a fixed number of users busy and finds throughput saturation:

```bash
./.venv/bin/python testing/common/loadgen.py \
  --dataset /tmp/mixed-8k-512.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --model deepseek-v4.1-flash \
  --mode closed --concurrency 64 --duration 300 \
  --output-dir /tmp/dsv41-closed-c64
```

Open loop schedules Poisson arrivals independently of completions. A sustainable
rate must meet latency/error SLOs, keep queue-delay slope flat, and avoid
binding the client safety semaphore:

```bash
./.venv/bin/python testing/common/loadgen.py \
  --dataset /tmp/mixed-8k-512.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --model deepseek-v4.1-flash \
  --mode open --request-rate 12 --concurrency 4096 --duration 300 \
  --output-dir /tmp/dsv41-open-r12
```

The automated search performs both stages:

```bash
./.venv/bin/python testing/common/capacity_search.py \
  --dataset /tmp/mixed-8k-512.jsonl \
  --base-url http://127.0.0.1:8000/v1 \
  --model deepseek-v4.1-flash \
  --results /tmp/dsv41-capacity \
  --slo-ttft-p95-ms 2000 \
  --slo-tpot-p95-ms 50 \
  --slo-error-rate 0.001 \
  --think-time 10 \
  --screen-duration 300 \
  --boundary-duration 600 \
  --repetitions 5
```

Stage A walks closed-loop concurrency `1..256` until an SLO failure or two
successive throughput gains below 3%. Stage B screens 10–105% of the observed
peak, expands/brackets and bisects the open-loop boundary, then repeats the
best candidate. A passing open-loop run requires at least 99.5% completion,
the configured error/TTFT/TPOT limits, queue slope at most 1 ms/s, and a
non-binding safety semaphore.

## Offline throughput without latency SLOs

Offline mode answers a different question:

> What is the highest valid output-token throughput this running engine can
> sustain when interactive TTFT/TPOT objectives do not constrain batching?

It runs only a closed-loop concurrency ladder, optimizes `output_tps`, and
stops after two successive gains below 3%, invalid output completion, client
limitation, errors, or ladder exhaustion. It does not run the open-loop
capacity stage and does not calculate sustainable RPS or users.

Start the matching server, then run:

```bash
PROFILE=throughput make throughput-h200-vllm
PROFILE=throughput make throughput-h200-sglang
PROFILE=throughput make throughput-b200-vllm
PROFILE=throughput make throughput-b200-sglang
PROFILE=throughput STAGE=optimized make throughput-b200-tensorrt
```

Override the workload or duration when needed:

```bash
SEARCH_MODE=offline-throughput \
WORKLOAD=testing/workloads/offline-throughput.yaml \
SCREEN_DURATION=300 REQUESTS=512 \
PROFILE=throughput \
bash testing/b200/vllm/run.sh
```

The fixed-output workload sends both `ignore_eos=true` and
`min_tokens=max_tokens`. A run is invalid if:

- completion or error limits fail;
- the endpoint does not return authoritative server token usage;
- requested output lengths are shortened beyond the configured tolerance; or
- the client cannot sustain configured closed-loop concurrency.

Each case writes:

- `throughput/throughput_summary.json`: peak valid output TPS, corresponding
  concurrency, stop reason, and all closed-loop run references;
- `throughput/non_capacity_evidence.json`: TTFT/TPOT/E2E observations labeled
  diagnostic-only;
- `throughput/runs/*`: raw request records and regular loadgen summaries.

These are non-SLO offline measurements. Never merge them into
`capacity_summary.json`, label them sustainable users/RPS, or compare them
against latency-qualified capacity without preserving the evidence class.

## Heterogeneous ragged load

Run all supported request shapes simultaneously:

```bash
WORKLOAD=testing/workloads/ragged-mix.yaml \
REQUESTS=512 PROFILE=balanced \
make capacity-h200-vllm
```

The single `ragged-mix` case uses weighted variants totaling 100%:

- 10% prefill-only;
- 16% decode-heavy;
- 34% mixed text, including long-context tails;
- 20% reasoning and tool use;
- 10% hot/Zipf prefix reuse;
- 10% image requests.

The generator allocates exact weighted counts with largest remainders and then
uses a seeded shuffle. Closed-loop workers consume the shuffled JSONL in
request-ID order, so the first in-flight window is heterogeneous rather than
one blocked group per shape.

Use the native load generator for ragged qualification. The optional AIPerf
single-turn adapter does not preserve the ragged prefix variants' system-plus-
user message structure.

## Hardware/engine suite wrappers

Start the matching server first. Each wrapper runs smoke, generates every
selected workload case, performs the two-stage search, and collects telemetry:

```bash
PROFILE=balanced WORKLOAD=testing/workloads/default-mix.yaml \
  bash testing/h200/vllm/run.sh

PROFILE=balanced WORKLOAD=testing/workloads/default-mix.yaml \
  bash testing/h200/sglang/run.sh

PROFILE=balanced WORKLOAD=testing/workloads/default-mix.yaml \
  bash testing/b200/vllm/run.sh

PROFILE=balanced WORKLOAD=testing/workloads/default-mix.yaml \
  bash testing/b200/sglang/run.sh

# TensorRT: only after a separately saved smoke run with --skip-image.
SKIP_SMOKE=1 CASES=mixed-512-256 \
PROFILE=balanced WORKLOAD=testing/workloads/text-grid.yaml \
  bash testing/b200/tensorrt/run.sh
```

Equivalent Make targets are `test-h200-vllm`, `test-h200-sglang`,
`test-b200-vllm`, `test-b200-sglang`, and `test-b200-tensorrt`. The
`capacity-*` aliases currently run the same suite. Useful controls:

```bash
CASES=mixed-8k-512,mixed-32k-256 \
REQUESTS=256 SCREEN_DURATION=300 \
SLO_TTFT_P95_MS=2000 SLO_TPOT_P95_MS=50 SLO_ERROR_RATE=0.001 \
BASE_URL=http://server:8000/v1 \
PROFILE=balanced WORKLOAD=testing/workloads/text-grid.yaml \
bash testing/b200/vllm/run.sh
```

`SKIP_SMOKE=1` is only for a separately recorded smoke pass.

## AIPerf cross-check

Set `AIPERF_CROSSCHECK=1` on a wrapper to run AIPerf before the native capacity
search for every case. The integrated cross-check is closed-loop concurrency
64, with 30 seconds of warmup and `SCREEN_DURATION` of measurement:

```bash
AIPERF_CROSSCHECK=1 PROFILE=balanced \
  bash testing/b200/sglang/run.sh
```

Standalone closed/open examples:

```bash
DATASET=/tmp/mixed-8k-512.jsonl OUTPUT_DIR=/tmp/aiperf-closed \
BASE_URL=http://127.0.0.1:8000 MODEL_NAME=deepseek-v4.1-flash \
MODE=closed CONCURRENCY=64 WARMUP_DURATION=300 DURATION=600 \
bash testing/common/run_aiperf.sh

DATASET=/tmp/mixed-8k-512.jsonl OUTPUT_DIR=/tmp/aiperf-open \
BASE_URL=http://127.0.0.1:8000 MODEL_NAME=deepseek-v4.1-flash \
MODE=open REQUEST_RATE=12 CONCURRENCY=4096 \
WARMUP_DURATION=300 DURATION=600 \
bash testing/common/run_aiperf.sh
```

AIPerf is a cross-check, not a source to merge silently with native results:
token counting, timing boundaries, arrival scheduling, and failure handling can
differ. Preserve its record-level artifacts and explain discrepancies.

## Metrics and artifacts

Suite outputs live under:

```text
$RESULTS_ROOT/<hardware>/<engine>/<profile>/<workload>/<UTC timestamp>/
```

The run root contains:

- `manifest.json`: hardware/engine/profile/model, base URL, case list, GPU
  inventory, and SHA-256 hashes of workload, profile, and image config.
- `smoke.json`: complete smoke responses.
- `<case>/dataset.jsonl`: exact generated requests and metadata.
- `<case>/capacity/runs/<run>/requests.jsonl`: per-request timestamps,
  request/dataset IDs, mode, scheduled offset, queue delay, TTFT, TPOT,
  end-to-end latency, inter-token latencies, input/output tokens and accounting
  source, HTTP status, success/error, session, and workload metadata.
- Each run's `summary.json`: endpoint/model/dataset size, configured mode,
  concurrency/rate and requested/actual scheduling/run durations;
  scheduled/completed/failed counts; completion/error rates; completed/offered
  request rate; input/output token totals and throughput; mean/p50/p95/p99
  TTFT/TPOT/E2E/queue delay; queue slope/flatness and its limit; semaphore
  waits/concurrency-cap status; peak in-flight; and status/error counts.
- `<case>/capacity/capacity_summary.json`: peak closed-loop RPS, highest
  repeated passing open-loop RPS, 80%-of-boundary operational RPS, maximum SLO
  concurrency, mean E2E, think time, estimated users, SLOs, stop reason, and
  references to every trial.
- `<case>/aiperf/`: AIPerf record-level exports when enabled.
- `telemetry/telemetry.jsonl`, `telemetry.parquet`, and
  `telemetry-summary.json`.
- `clean_complete.json`, written last and only after every requested case
  finishes successfully.

Generate a cross-run report with `make report`; it writes
`capacity-comparison.csv`, `.json`, and `.md` with capacity plus GPU
utilization/HBM/power summaries.

## Clean-complete gate

A directory without `clean_complete.json` is partial and cannot be a profiling
baseline. `testing/profiling/require_clean.sh` also checks `manifest.json`,
`clean_run_complete: true`, and a non-empty completed-case list. Every Nsight
or PyTorch profiling wrapper enforces this gate and copies the clean manifest
beside its artifacts. Profiled metrics are marked
`capacity_publishable: false`.

## Telemetry

Telemetry runs at one-second intervals by default and samples:

- per-GPU SM/memory utilization, HBM, power, temperature, clocks, and PCIe
  throughput through NVML;
- host CPU, RAM, swap, network deltas, NUMA hit/miss/foreign, and major faults;
- engine Prometheus metrics and optional DCGM Prometheus metrics;
- summary mean/peak SM utilization, peak node HBM, mean node power, and energy.

Start the optional exporter and expose its URL before the suite:

```bash
bash testing/telemetry/dcgm_exporter.sh start
export DCGM_METRICS_URL=http://127.0.0.1:9400/metrics
```

The suite scrapes the public endpoint's `/metrics` by default. For multiple
backends, invoke `run_suite.py` directly with repeated
`--engine-metrics-url http://127.0.0.1:8100/metrics` arguments. Scrape errors
are recorded in telemetry rather than hidden.

## Profile only after capacity: Nsight Systems before NCU

First produce a clean, uninstrumented suite. Then use Nsight Systems to find
the critical kernels. Each command restarts the exact profile in an isolated
Nsight launch session, waits for readiness, brackets the focused load with
`nsys start/stop`, and shuts it down afterward:

```bash
BASELINE_DIR=/path/to/clean-run DATASET=/path/to/clean-run/default-mix/dataset.jsonl \
bash testing/h200/vllm/profile.sh nsys

BASELINE_DIR=/path/to/clean-run DATASET=/path/to/clean-run/default-mix/dataset.jsonl \
bash testing/h200/sglang/profile.sh nsys

BASELINE_DIR=/path/to/clean-run DATASET=/path/to/clean-run/default-mix/dataset.jsonl \
bash testing/b200/vllm/profile.sh nsys

BASELINE_DIR=/path/to/clean-run DATASET=/path/to/clean-run/default-mix/dataset.jsonl \
bash testing/b200/sglang/profile.sh nsys

BASELINE_DIR=/path/to/clean-run DATASET=/path/to/clean-run/default-mix/dataset.jsonl \
bash testing/b200/tensorrt/profile.sh nsys
```

Nsight Systems writes the `.nsys-rep`, CUDA/NVTX CSV statistics,
`load-command.txt`, baseline manifest, and `profiling.json`. Summarize its
kernel CSV with:

```bash
./.venv/bin/python testing/analysis/kernel_summary.py \
  /path/to/stats_cuda_gpu_kern_sum.csv \
  --output-dir /path/to/kernel-summary
```

Only after inspecting that timeline should NCU target a narrow kernel regex in
an isolated profiling container:

```bash
BASELINE_DIR=/path/to/clean-run DATASET=/path/to/dataset.jsonl \
PROFILING_CONTAINER=dsv41-isolated-profile \
KERNEL_REGEX='qualified_kernel_regex' LAUNCH_COUNT=3 \
bash testing/b200/vllm/profile.sh ncu \
  python /workspace/one_batch_microbenchmark.py
```

NCU replays kernels, so its timing is never serving capacity. Pause DCGM
profiling-counter watches first. PyTorch profiling is another diagnostic mode
(`.../profile.sh torch`) and must not run concurrently with Nsight because both
use CUPTI. NCU writes the baseline manifest, exact microbenchmark command,
`profile.ncu-rep`, and `profiling.json` under
`$PROFILER_CACHE_ROOT/ncu/<capture>`; PyTorch mode records start/stop
responses and `profiling.json`, while engine traces are written to the mounted
`/profiles/torch` cache.

## Capacity caveats

- Default 30-second screens and three 30-second boundary repetitions are
  development checks, not production qualification; use longer durations,
  more repetitions, and warm hardware.
- Capacity is valid only for the recorded workload, SLO, profile, experiment,
  model/image pins, router topology, and cache state. Restart and warm the
  server consistently between comparative arms.
- Test near-1M, prefix-heavy, reasoning/tool, and multimodal cases separately;
  a mixed average cannot prove their tail capacity.
- `estimated_users` is a Little's-law estimate from boundary RPS, observed mean
  E2E, and configured think time—not a measured user count.
- A binding open-loop concurrency cap invalidates the rate; raising it may
  instead expose load-generator CPU/network limits.
- Prefer a separate load-generator host prepared with `install/loadgen.sh`.
  Verify network bandwidth/latency and client CPU headroom so the server, not
  the driver, is the bottleneck.
- Never publish capacity from Nsight, NCU, PyTorch-profiler, TensorRT
  correctness-stage, failed/partial, or synthetic-acceptance runs.
