# OPS4 execution and inspection

The four tasks, frozen values, model/GPU pins, and objective vector are in `configs/campaign-ops4.json` and `infra/OPS4_STUDY.md`. The trusted controller alone runs vLLM and AIPerf. Its GPU tasks are sequential; do not run the source-calibration server at the same time as a controller cell.

## 1. Independent input replay on the source B0 server

After all four `configs/workloads/ops-frozen/*.jsonl` assets exist in `prepared` state and the pinned source B0 server is healthy:

```bash
.venv/bin/python infra/validate-ops4-frozen.py replay
.venv/bin/python infra/validate-ops4-frozen.py promote
.venv/bin/iar prepare --campaign configs/campaign-ops4.json --backend real
```

`infra/ops4-frozen-validation.json` records exact request counts, payload/output/schedule checks and raw export hashes. Raw replay cells are under `.artifacts/ops4-frozen-validation/`. If replay fails, inspect its cell folder and rerun after resolving the cause; completed validated cells are retained. `prepare` must report `screen_assets_verified` before the baseline.

## 2. Fresh-server B0, qualification, and first agent iteration

Stop the shared source B0 server. Build the controller image from the current code, then:

```bash
export IAR_REPO_ROOT="$(pwd -P)"
export IAR_CODEX_HOME="/home/ubuntu/.codex"
docker compose -f deploy/compose.yaml --profile build-only build
docker compose -f deploy/compose.yaml up -d --force-recreate controller
docker compose -f deploy/compose.yaml exec controller iar doctor --campaign configs/campaign-ops4.json --backend real
docker compose -f deploy/compose.yaml exec controller iar baseline --campaign configs/campaign-ops4.json --backend real
docker compose -f deploy/compose.yaml exec controller iar qualify --campaign configs/campaign-ops4.json --backend real
docker compose -f deploy/compose.yaml exec controller iar report --campaign configs/campaign-ops4.json --backend real
```

Inspect the four B0 cells and `search_allowed` verdict before search. Update `infra/OPS4_BASELINE.md` with exact metrics, durations and artifact paths. If B0 overloads or lacks full accounting on any task, keep the failure and revise/version the task before search. Once qualification says `search_allowed: true`:

```bash
docker compose -f deploy/compose.yaml exec controller iar search --campaign configs/campaign-ops4.json --backend real --max-proposals 1
docker compose -f deploy/compose.yaml exec controller iar inspect --campaign configs/campaign-ops4.json --backend real
```

Later iterations use `iar search ... --resume` with a higher `--max-proposals` cap within the campaign budget. The durable ledger and `report/suite-front.json`, `suite-front.csv`, `points.csv`, `fronts.json` stay in `.artifacts/autoresearch-codebase/qwen38-27b-ops4-v1/real/`. Each proposal attempt has Codex events, receipts, cited evidence, research notes and its final JSON. Each evaluation has exact config, native AIPerf exports, normalized per-request records, server logs, GPU telemetry and timing. The inspection index links these paths without hiding raw data.
