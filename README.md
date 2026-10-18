# Inference serving research

Find better serving configurations through real measurements, operating curves, and held-out checks. This repository contains the experiment code, frozen configuration, results, graphs, and evidence needed to inspect the findings.

## Start here

| Need | Location |
|---|---|
| Current work: source research and hypothesis review | [Research plan and fresh-session prompts](research/README.md) |
| Results beside their baselines | [Development / held-out comparison](results/2026-10-18-direct-optuna/comparison.html) |
| What improved and what did not | [Completed study analysis](results/2026-10-18-direct-optuna/ANALYSIS.md) |
| Final operating curves / Pareto | [Held-out curves](results/2026-10-18-direct-optuna/heldout-operating-curves.svg) · [Held-out frontier](results/2026-10-18-direct-optuna/heldout-pareto.svg) |
| Exact experiment protocol | [Direct Optuna runbook](infra/DIRECT_OPTUNA_RUN.md) |
| Code and commands | [Implementation map](infra/direct_optuna/README.md) |
| Every study, including earlier work | [Research index](docs/RESEARCH.md) · [Results index](results/README.md) |
| Evidence / logs / reproducibility | [Tracking guide](docs/TRACKING.md) · [Evidence archive](results/2026-10-18-direct-optuna/evidence/README.md) |
| Meaning of replication and promotion | [Replication criteria](docs/REPLICATION.md) |
| Imported DeepSeek / B200 reference | [B200 analysis](docs/B200_REFERENCE.md) |

## Completed experiment: direct Optuna, 18–19 October 2026

**Optimizer:** Optuna 4.5.0 multivariate TPE, using InseeFrLab's auto-tuning-vllm controller. **Evaluator:** GuideLLM 0.7.1. No LLM proposals or AIPerf load search were used in this campaign.

**Serving:** Qwen/Qwen3.8-27B, BF16, TP=1, maximum context 40,960, vLLM 0.28.0, one NVIDIA RTX PRO 6000 Blackwell Server Edition GPU (96 GB class). Image, model and source hashes are in the [study manifest](results/2026-10-18-direct-optuna/study-manifest.json) and [model manifest](results/2026-10-18-direct-optuna/model-manifest.json).

### Input workload

One synthetic mix with engineered shared prefixes. Input lengths include the chat template; exact observed counts are validated. Output lengths are forced, temperature is zero, and thinking is disabled.

| Class | Share | Input tokens | Output tokens | Requests per 120-request point |
|---|---:|---:|---:|---:|
| Chat | 45% | ~512 | 256 | 54 |
| Agent-like | 20% | ~4,096 | 512 | 24 |
| Code-like | 20% | ~2,048 | 512 | 24 |
| Document | 15% | ~8,192 | 256 | 18 |

Search measured **16 and 32 concurrent clients**, 120 requests at each point, with one server launch per configuration. Closed-loop traffic replaces completed requests; it is not a fixed offered requests/s or burst workload. Inputs and cache preparation were matched across configurations. The search scored throughput, p90 TTFT and p90 decode TPOT at 32 clients.

### Search surface

| Parameter | Options | B0 |
|---|---|---:|
| `max_num_batched_tokens` | 2048, 4096, 8192, 16384 | 8192 |
| `max_num_seqs` | 16, 32, 64, 128, 256, 512 | 512 |
| `gpu_memory_utilization` | .85, .90, .92, .95 | .92 |
| `long_prefill_token_threshold` | 0, 1024, 2048, 4096 | 0 |
| `async_scheduling` | true, false | true |
| `enforce_eager` | false, true | false |
| `max_cudagraph_capture_size` | 32, 64, 128, 256, 512; graph mode only | 512 |
| `enable_prefix_caching` | true, false | true |

[Executable domain](configs/direct-optuna-study.json). Chunked prefill stays enabled; MTP stays off. There are 9,216 nominal conditional combinations, not 9,216 completed experiments.

### Final result

Search completed **25 trials / 24 unique configurations / 6,000 valid requests**. Held-out confirmation completed **5 evaluations / 1,800 valid requests**: B0 → search trial 9 → search trial 10 → search trial 24 → B0 repeat, at 16/32/64 clients. Calibration used another 168 requests. Zero failed search or confirmation trials.

At the common 32-client held-out point:

| Configuration | Output tok/s ↑ | p90 TTFT s ↓ | p90 TPOT ms/token ↓ |
|---|---:|---:|---:|
| B0 before | 384.4 | 6.70 | 66.00 |
| Trial 9 | 383.9 | 6.76 | 68.53 |
| **Trial 10** | **387.5** | **4.44** | **68.18** |
| Trial 24 | 273.4 | 27.29 | 52.76 |
| B0 after | 386.7 | 6.26 | 67.33 |

- **Useful lead:** trial 10 changes batch tokens 8192→4096, sequence cap 512→64 and GPU memory fraction .92→.95. Held-out p90 TTFT was 29–34% lower than the two baselines, with throughput within 1% and TPOT 1.3–3.3% worse.
- **Rejected claim:** trial 9's development +10% throughput did not reproduce.
- **Tradeoff to avoid for these targets:** trial 24 improves decode latency by admitting fewer sequences, with much worse first-token waiting and throughput.
- **Evidence limit:** one held-out run per candidate, two baseline runs. This supports a latency tradeoff, not a statistically established universal winner or confirmed SLA capacity.

The approved class p90 TTFT research targets are 1.5s chat / 2.5s agent / .75s code / 12s document, with p90 TPOT ≤70ms/token and zero observed failures. They were reported as diagnostics, **not hard optimizer constraints**. No development configuration met all class targets at either search load. See per-class test outcomes in the comparison page.

## Repository structure

| Directory | Purpose |
|---|---|
| `research/`, `.agents/skills/` | Current vLLM/DeepEP source-research plan, evidence map and researcher/critic skills |
| `infra/direct_optuna/` | Current completed-study optimizer adapter, evaluator, reporting, archival and monitoring |
| `configs/direct-optuna-study.json` | Its frozen search domain and B0 |
| `results/` | Versioned research outputs; each study has its own protocol and evidence scope |
| `b200-bench-analysis/` | Imported DeepSeek/B200 reference data and report; separate hardware and workload |
| `docs/` | Research navigation, replication rules, evidence policy and historical snapshots |
| `src/inference_autoresearch/`, `agent/`, `deploy/` | Earlier Codex/AIPerf harness and container implementation, retained for reuse |
| `infra/`, other `configs/`, `tests/` | Earlier campaign tooling, protocols and tests; [index](infra/README.md) |
| `.artifacts/` | Ignored local execution state; the completed direct study also has a committed evidence archive |

The rsynced `inference-autoresearch-handoff/` is a reference input. The separate `Deepseek_serve/` checkout was refreshed by user request; [source pins](research/SOURCES.md) distinguish it from the imported B200 measurement snapshot. Earlier root design documents are indexed as historical in [docs/RESEARCH.md](docs/RESEARCH.md).

## Inspect without running a GPU

```bash
python3 infra/direct_optuna/archive.py --verify
python3 infra/direct_optuna/compare.py
# With matplotlib installed (the local .venv already has it):
.venv/bin/python infra/direct_optuna/final_plots.py
```

The completed run used a pinned base Docker image with a mounted benchmark environment and upstream checkout. Its Dockerfile recipe has not been build-tested; the current launcher is tied to this host's GPU and NVMe paths. See the runbook before starting another campaign. Completed study IDs and evidence must not be overwritten.

**Next checkpoint:** review source-backed vLLM/DeepEP hypotheses and their cheapest falsification experiments using the B200 evidence and refreshed `Deepseek_serve`. [Run broad research with integrated critique and revision](research/README.md). The TPE study is complete; additional parameter trials and B0/trial-10 repeats are deferred. No new GPU campaign is launched by this research setup.
