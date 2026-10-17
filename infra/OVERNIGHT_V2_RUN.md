# Overnight v2 experiment

## Scope

The campaign is `qwen38-27b-eval-v2`, defined by
`configs/campaign-v2.json` and `configs/evaluation-protocol-v2.json`.
One pinned GPU runs one Dockerized vLLM server at a time. Optuna proposes
admitted serving settings; each proposal gets the same validated 36-request
mixed OPS workload and fixed arrival schedule. The campaign allows at most
18 distinct proposals or 8 hours. It optimizes measured throughput versus
TTFT/TPOT p90 ratios to the matched B0. These are exploratory objectives,
not application SLOs or confirmed capacity.

## Gates before launch

1. `iar doctor` and `iar prepare` pass for the real campaign.
2. The real `triage` B0 is valid with complete request accounting and frozen
   workload provenance.
3. `iar qualify` writes `qualification-report.json` with
   `search_allowed: true`.
4. One Optuna proposal is evaluated and its trial, ledger cell, raw AIPerf
   exports, and result paths are inspected.

Start the persistent session after those gates:

```bash
tmux new-session -d -s iar-v2-overnight 'bash /home/ubuntu/shreyas/skunk-work/infra/run_overnight_v2.sh'
```

Inspect without interrupting it:

```bash
tmux ls
tail -f .artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/overnight-console.log
.venv/bin/iar inspect --campaign configs/campaign-v2.json --backend real
```

`overnight-started-utc.txt`, `overnight-pid.txt`,
`overnight-finished-utc.txt`, and `overnight-exit-code.txt` record process
state. The SQLite ledger, Optuna study, per-cell Docker/vLLM/AIPerf logs,
raw requests, and report files sit under
`.artifacts/autoresearch-codebase/qwen38-27b-eval-v2/real/`.

## Evidence limits and follow-up

The 36-request gate is a fast regression filter. A single run per setting
does not establish a reliable production Pareto frontier. AIPerf adaptive
rate exploration is implemented separately with fixed samples per rate,
repeats, input and dispatch verification, and all-point exports. It needs
an independently qualified development/held-out manifest and application
TTFT/TPOT SLOs before making an SLA-capacity claim. Cache and MTP controls
stay fixed until exact-match and quality/acceptance diagnostics are ready.
