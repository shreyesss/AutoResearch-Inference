# AutoResearch Inference

**Current experiment (18 October 2026): Optuna + GuideLLM using InseeFrLab's auto-tuning-vllm.** The [direct study](infra/DIRECT_OPTUNA_RUN.md) uses multivariate TPE to vary eight serving controls together. A frozen synthetic chat/agent/code/document mix exercises real token lengths and prefix reuse. B0 and candidates receive the same two concurrency points, 120 requests each, with one server launch per configuration. The budget is B0 plus 24 candidates, followed by held-out curves for frozen finalists and a B0 repeat. There are no LLM proposals in this experiment. See the [executable configuration](configs/direct-optuna-study.json), [live status](.artifacts/optuna-direct-v1/status.json), and [measurements and curves](results/2026-10-18-direct-optuna/README.md). Results are observed tradeoffs; open-loop SLA capacity is not established by this protocol.

**Historical v3c checkpoint (17 October 2026):** The development-input and matched-B0 chain was running; no candidate proposal had started at this checkpoint. That study used one synthetic mixed workload with four request classes, user-approved research p90 targets, a custom class-aware rate planner that runs AIPerf at each point, and a seven-control serving domain. The 36-request candidate screen selects a diagnostic rate from the valid B0 profile and compares B0 and candidates at the same rate, request bodies and Poisson seed. The two 240-request finalist windows were development data; sealed test inputs were planned but not captured. See the [launch audit](infra/V3C_LAUNCH_AUDIT.md), [exact search domain](infra/V3C_SEARCH_SPACE.md), and [run design](infra/V3C_RUN.md).

**Historical v2 plan:** [Evaluation v2 design for review](EVALUATION_V2_PLAN.md), with detailed [adaptive evaluator](infra/ADAPTIVE_EVAL_PLAN.md), [serving search expansion](infra/SERVING_SEARCH_EXPANSION_PLAN.md), and [agent research](infra/AGENT_RESEARCH_PLAN.md) plans. The sections below describe earlier campaigns and remain as evidence, not the current v3c runbook.

An executable, evidence-tracked harness for **Qwen/Qwen3.8-27B serving settings on one GPU**. AIPerf replays frozen requests against pinned vLLM. One Codex CLI proposer suggests bounded parameter changes; the evaluator alone starts containers, measures cells and maintains compatibility-scoped Pareto results.

**Earlier short-chat state:** the short-chat B0 and manual parameter comparisons are documented in [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md). The earlier evaluator completed a real two-load B0 with full request accounting under `fresh-server-cell-v1`; results are below. Its registry also carries an engineered mixed probe and a recorded TraceLab control. Results from mock, manual shared-server and fresh-server protocols remain separate.

| Frozen short-chat load | Completed | Output tokens/s | TTFT p99 | TPOT p99 | Server queue |
|---|---:|---:|---:|---:|---:|
| 2.56 requests/s | 154/154 | 556.2 | 209.0 ms | 56.03 ms/token | 0 |
| 3.2 requests/s | 192/192 | 688.9 | 224.0 ms | 63.82 ms/token | 0 |

Both cells used the resolved B0 `max_num_seqs=512`, `max_num_batched_tokens=8192`, `gpu_memory_utilization=0.92`, prefix caching on and MTP off. These are single 60-second dispatch observations, not confirmed p99 or capacity estimates. Raw artifacts and the generated report are under `.artifacts/vertical-slice-v3/` (ignored by Git).

The Dockerized first-pass `mtp_draft_tokens=1` pilot completed the same 154/154 and 192/192 requests with zero queue. At 2.56 requests/s it measured 591.4 output tokens/s, 220.3 ms TTFT p99 and 35.26 ms TPOT p99; at 3.2 requests/s it measured 738.5, 232.63 ms and 39.29 ms respectively. Acceptance was 81.0% and 82.1%. Relative to matched B0, decode improved while TTFT worsened. The sensitivity plan still requires a second matched repeat and its inactive-axis control before calling this effect reproducible. The tracked [result snapshot](results/2026-10-17-short-chat/README.md) includes four points and graphs.

## Layout

| Path | Role |
|---|---|
| `configs/campaign.json`, `configs/search-domain.json`, `configs/pilot-plan.json` | Frozen model/runtime/B0, conditional serving domain, predeclared sensitivity contrasts and budgets |
| `configs/workloads/` | Versioned workload cards/manifests with asset hashes and readiness |
| `src/inference_autoresearch/workloads/`, `benchmark/` | Workload verification and native AIPerf replay/export adapter |
| `src/inference_autoresearch/runtime/`, `evaluation/` | Pinned Docker lifecycle, GPU lease, telemetry, cell validity/accounting |
| `src/inference_autoresearch/search/`, `storage/` | Codex proposer, qualification gate, append-only ledger, inspection index, Pareto exports |
| `agent/SKILL.md` | Single operational instruction file for the proposer; each attempt gets staged research files and writable notes |
| `deploy/` | Controller and isolated proposer container recipe; pinned vLLM runs as a sibling service |
| `infra/` | Prior real measurements and reproducible manual probes |
| `EXPERIMENT_DESIGN.md` | Experiment policy and inspection checkpoints |

The supplied `Deepseek_serve/` and rsynced `inference-autoresearch-handoff/` are left in their original locations. No implementation writes to them.

## Install and inspect

Python 3.11+, Docker with NVIDIA GPU support, the pinned vLLM image, AIPerf 0.13.0 and the local model are needed for real evaluation. The `iar` controller and proposer can be built as containers using [deploy/README.md](deploy/README.md). For local development:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]' aiperf==0.13.0
.venv/bin/python scripts/prepare-model.py --check-only
.venv/bin/iar doctor --backend real
.venv/bin/iar prepare --backend real
```

If the model is absent, run `.venv/bin/python scripts/prepare-model.py` to download the exact pinned revision. It is an explicit bootstrap step and may require Hugging Face access and substantial disk space. `doctor` inspects hardware/image/model and loads the exact AIPerf tokenizer offline; it does not run the model. `prepare` verifies the registered immutable input assets and reports missing mixed/session qualification.

## Safe execution sequence

```bash
.venv/bin/iar baseline --backend mock
.venv/bin/iar pilot --backend mock
.venv/bin/iar search --backend mock --max-proposals 2
.venv/bin/iar report --backend mock
.venv/bin/iar qualify --backend mock
```

Mock output is labeled and stored under `.artifacts/autoresearch-codebase/`. It exercises the controller and plot path without scientific performance claims. A bounded real diagnostic can be run with `iar baseline --backend real`; each cell starts a fresh pinned server and runs the same frozen short-chat stream. `iar pilot --backend real` runs the predeclared MTP1 contrast across both cards; `iar evaluate --backend real --candidate configs/pilot-cap64.json --stage pilot` runs the inactive-axis control. The pilot plan requires both scenario IDs and matched repeats. `--scenario REGISTRY_ID` can narrow a baseline investigator run. `iar qualify --backend real` writes a sensitivity/qualification report with exact missing gates; it does not launch GPU work. Real `search` refuses to run until a matching real qualification report opens the gate. Failed evaluations return a nonzero exit code while retaining JSON artifacts.

Every evaluation should leave resolved settings/argv, model and image pins, AIPerf native exports, normalized per-request records, Docker logs/state, server `/metrics`, GPU samples, cell verdicts and ledger events. `report` exports a Markdown report, JSON/CSV, feedback/proposal records and SVG Pareto plots grouped by exact compatible load/protocol. The plot is descriptive; short sample p99 points remain provisional.

Use `iar inspect --backend real --output-dir .artifacts/vertical-slice-v3` to regenerate a human-readable `inspection/INDEX.md` and machine-readable `index.json` from the real ledger and proposer attempt folders. New evaluations also write per-cell and aggregate phase timings. The Codex proposer reads a small path-only prompt, inspects staged source and non-held-out run files inside its isolated container, and writes notes for later attempts. The current campaign has no opt-in fast triage; an optional one-load validity gate is available for a versioned future campaign. The fresh-server protocol still spends several minutes starting the model for each cell, so ordinary iteration speed has not yet been improved by server reuse.

## Historical v1 search question

The starting conditional domain covers sequence cap, batched-token budget, GPU memory fraction, prefix cache, native MTP depth and, after support checks, chunked-prefill controls. It includes the resolved B0 values **512/8192/0.92/cache on/MTP off**. AIPerf YAML rates and request mixtures are evaluator inputs, not agent parameters. The evaluator-ready performance input is mechanical short chat at **2.56 and 3.2 requests/s**; mixed and session cards are diagnostic inputs awaiting their own realization/baseline gates. The supplied mixed YAML weights are engineered controls, not measured production shares. See [EXPERIMENT_DESIGN.md](EXPERIMENT_DESIGN.md) for suite expansion, confirmation and holdout rules.
