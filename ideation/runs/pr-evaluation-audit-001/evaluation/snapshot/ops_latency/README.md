# B200 latency campaign

This campaign is isolated from existing throughput profiles/results and writes
only below:

```text
$RESULTS_ROOT/b200/vllm/latency-campaign/
```

Shared load-generation defaults are unchanged. Per-class and p99 analysis
runs only after request generation exits.

## Measured recommendation

The best measured agent-f75 configuration is now encoded as a separate
latency-only profile:

```bash
PROFILE=latency-dep8-sla make serve-b200-vllm
```

It is DEP8/EP8 with DSpark k5 (adaptive verification off), seq64 per rank,
graph512, batch16K, prefix caching, four API servers, and no EPLB. In one
150-second, eight-process closed-loop run:

- `c=384`: 25.47 req/s, TTFT p50/p99 0.23/2.66 s, TPOT p50 14.10 ms.
- `c=512`: 26.09 req/s, TTFT p50/p99 0.32/2.88 s, TPOT p50 18.51 ms.

Use c384 as the measured operating point. c512 is the measured ceiling for
the separate p50 ≤ 0.5 s / p99 ≤ 4 s / ≥30 tok/s objective, but it does not
pass the campaign's balanced tier. Here `c` is client concurrency (outstanding
requests), not the server's `max_num_seqs`. This remains provisional until
repeated and validated with open-loop production ingress. The structured
source of truth and exact metrics are in `ops_latency/campaign.yaml`.

For multi-replica TP4 controls, the latency helpers also reproduce the router
used by the corrected server runs: sticky hashing bounded to 1.1× average
in-flight load, a 4,096-connection pool, and one retry for connector failures
before request dispatch. These are latency-only environment overrides;
`lib/router.py` keeps the old shared defaults when they are absent.

## Simple 2xDEP4 run at the R7 load points

This runs only two independent TP1/DP4/EP4 engines. It does not rerun DEP8 or
perform topology selection. The engines use GPUs 0-3 and 4-7, ports 8100/8101,
API2 per replica, and the fixed local router on port 8000.

```bash
# Show the exact settings without loading the model.
bash ops_latency/run_2xdep4.sh --plan

# Run c=256,384,512 and sync the result to S3.
bash ops_latency/run_2xdep4.sh

# Run without S3 delivery.
bash ops_latency/run_2xdep4.sh --no-sync
```

The workload and timing reproduce the R7 screen: `agent-f75` (8K input, 1K
output, target 75% cacheability), eight client shards, 120-second warmup, and
150 seconds per point. Concurrency remains node-wide; the router distributes
c=256/384/512 to approximately 128/192/256 outstanding requests per DEP4.
The result is stored under
`$RESULTS_ROOT/b200/vllm/latency-campaign/LAT-2XDEP4-R7-VALUES/`.

## Reproducing the measured endpoint types

```bash
# R7 DEP8 winner, fully encoded in one profile
PROFILE=latency-dep8-sla make serve-b200-vllm

# R4e 2xTP4 endpoint
PROFILE=balanced \
EXPERIMENTS="lat-dspark-k2 lat-seqs-256 lat-graph-512 batched-32k" \
make serve-b200-vllm

# R5 same-node TP4 prefill/decode endpoint
bash serving/b200/vllm/serve_pd.sh --profile pd-tp4-decode128

# Experimental single TP8 endpoint; add experiment flags as required
PROFILE=latency-tp8 make serve-b200-vllm
```

All expose the OpenAI-compatible API at `http://127.0.0.1:8000/v1`.

## Safe start

```bash
cd /data/Deepseek_serve
bash ops_latency/run_active.sh --plan
bash ops_latency/install_vllm_router.sh
bash ops_latency/run_import_evidence.sh
bash ops_latency/run_pd_smoke.sh
```

The PD smoke is mandatory before PD performance runs.

## Independent loaded configurations

Run one script, inspect the refreshed report, then choose the next:

```bash
bash ops_latency/run_tp4_balanced.sh
bash ops_latency/run_tp4_low_latency.sh
bash ops_latency/run_tp4_hybrid.sh
bash ops_latency/run_pd_baseline.sh
bash ops_latency/run_pd_prefill16k.sh
bash ops_latency/run_pd_decode64.sh
bash ops_latency/run_concurrency_sweep.sh \
  LAT-PD-D128 pd-tp4-decode128 ""
```

`run_all.sh` aliases `run_active.sh`. It refuses implicit full execution;
`--execute-all` is required. Independent scripts are preferred.

The original topology-selection scripts remain available for reproducibility.
The later closed-loop sweeps established DEP8 + DSpark k5 as the agent-f75
latency winner. The old broad LAT-01…LAT-12 flow is under
`ops_latency/deferred/legacy/`.

## Reusable concurrency sweeps

The server-side sweep tooling is now tracked:

```bash
LATENCY_LOADGEN_SHARDS=8 \
SWEEP_CASES=agent-f75 \
SWEEP_CONCURRENCIES="256 384 512" \
bash ops_latency/run_concurrency_sweep.sh \
  LAT-R7-REPEAT latency-dep8 \
  "lat-prefix-on lat-dspark-k5 lat-seqs-64 lat-graph-512 lat-batched-16k lat-api-4"
```

`run_sweep_queue.sh` runs a fixed queue; `run_dynamic_queue.sh` atomically
pops an editable queue. Both retain per-run reporting and S3 finalization from
the shared latency helpers.

To change only the supplied workload while retaining the endpoint and sweep
protocol, point the runner at another compatible workload YAML:

```bash
SWEEP_WORKLOAD=/path/to/workload.yaml \
SWEEP_CASES="my-chat my-agent" \
LATENCY_LOADGEN_SHARDS=8 \
bash ops_latency/run_concurrency_sweep.sh \
  LAT-CUSTOM latency-dep8-sla ""
```

## Active protocol

- Exact-output chat 512/256, code 2K/1K, single-turn agent 8K/1K, and a
  text-only 32K-capped 45/20/15/20 mix.
- Zipf(1.2) cacheability at 25%, 50%, and 75%; balanced TP4 and stock PD also
  run a 0% control.
- Per cell: 120-second one-token warmup, 180-second c=1 floor, 300-second
  near-knee open-loop run, then at most two conditional ±25% rate corrections.
- Balanced TP4 and stock PD calibrate three 120-second rates at 50% cache.
- One model/router load per configuration; no restart between cells.
- Warmup and every measured load point use separately seeded datasets. Each
  measured dataset is sized above its expected arrival count, and the runner
  fails if a trial would cycle back to an already used full prompt. This keeps
  cross-trial cache state limited to the intentionally shared Zipf prefixes.

Target cacheability and actual engine hit share are both reported. Cache-hit
mismatches are labeled and excluded from direct Pareto comparison rather than
retried automatically.

## Manual confirmation

First-pass cells run once. After reviewing the HTML report, add repetitions
2–3 only for selected points:

```bash
bash ops_latency/run_repeat_selected.sh \
  --run-root /path/to/LAT-TP4-BALANCED/<timestamp> \
  --point chat:50:8 \
  --point mix:75:6
```

The helper reloads one configuration, rewarmes selected cache tiers, and runs
only those rates. Three passing runs are required for the TTFT-p99 /
TPOT-p99 / SLO-goodput Pareto frontier.

Five-repeat SLA work, multimodal, sessions, natural outputs, bursts, soak,
remote ingress, and faults are deferred until topology selection.

## PD behavior

Stock PD uses native `vllm-router`, TP4 prefill on GPUs 0–3, TP4 decode on
GPUs 4–7, and NIXL with `kv_load_failure_policy=fail`.

If stock PD smoke fails, one prebuilt fallback attempt may be supplied:

```text
LATENCY_PD_FALLBACK_IMAGE
LATENCY_PD_FALLBACK_ROUTER_BIN
```

The campaign does not build or debug that fallback. If it also fails, PD is
marked unavailable and TP4 evidence remains valid.

## Reporting and S3

The singular experiment definition is `ops_latency/campaign.yaml`. Every
configuration documents its one intended change, expected signal, validity
gates, and interpretation.

The self-contained report is:

```text
ops_latency/report/latency-b200-campaign-export.html
```

Every runner is resumable, refreshes the report, and attempts the existing
verified S3 sync on success or failure. Use `--no-sync` only for local
development.
