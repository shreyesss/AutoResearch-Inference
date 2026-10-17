#!/usr/bin/env python3
"""Run actual evaluator B0 cells on qualified development windows only.

`--check` is read-only and reports blockers. `--run` requires all input gates,
an idle GPU, and a fresh campaign output, then invokes `iar baseline` once for
the two development windows. No sealed-test or adaptive work is performed.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from inference_autoresearch.evaluation.split_v2 import audit_frozen_splits, load_split_plan
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config
from inference_autoresearch.workloads.registry import verify_scenario


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "configs/campaign-sla-b0-v3.json"
PROTOCOL_PATH = ROOT / "configs/evaluation-protocol-sla-b0-v3.json"
REGISTRY_PATH = ROOT / "configs/workloads/sla-development-b0-v3-registry.json"
SPLIT_PATH = ROOT / "configs/evaluation-splits-v3.json"
INPUT_ROOT = ROOT / ".artifacts/v3-independent-capture"
OUT_ROOT = ROOT / ".artifacts/autoresearch-codebase/qwen38-27b-sla-b0-v3/real"
RECEIPT = INPUT_ROOT / "matched-evaluator-b0-receipt.json"
PYTHON = ROOT / ".venv/bin/python"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def static_config() -> tuple[dict, dict, dict, dict]:
    campaign, protocol, registry = map(read, (CAMPAIGN_PATH, PROTOCOL_PATH, REGISTRY_PATH))
    split = load_split_plan(SPLIT_PATH, root=ROOT)
    ids = [row["scenario_id"] for row in split["stages"]["development_replication"]["windows"]]
    source = read(ROOT / "configs/campaign-v2.json")
    if (campaign.get("campaign_id") != "qwen38-27b-sla-b0-v3"
            or campaign.get("model") != source.get("model")
            or campaign.get("runtime") != source.get("runtime")
            or campaign.get("baseline") != source.get("baseline")
            or campaign.get("workload_registry") != str(REGISTRY_PATH.relative_to(ROOT))
            or campaign.get("screen_scenario_ids") != ids
            or campaign.get("evaluation_protocol_path") != str(PROTOCOL_PATH.relative_to(ROOT))
            or campaign.get("qualification_requirements", {}).get("mode") != "baseline_only_v3"
            or campaign.get("search_budget", {}).get("max_distinct_proposals") != 0):
        raise ValueError("B0 campaign differs from the pinned source or development plan")
    expected_map = {name: f"configs/workloads/ops-frozen/{name}.json" for name in ids}
    if registry.get("version") != "workload-registry-v1" or registry.get("scenarios") != expected_map:
        raise ValueError("B0 registry must contain exactly the two development windows")
    if (protocol.get("protocol_id") != "sla-development-b0-v3"
            or protocol.get("engine_stage") != "screen"
            or protocol.get("measurement_protocol") != "fresh-server-cell-v1"
            or protocol.get("scenario_ids") != ids
            or protocol.get("request_count_per_window") != 240
            or protocol.get("split_plan_sha256") != sha(SPLIT_PATH)
            or protocol.get("research_policy_sha256") != sha(ROOT / protocol["research_policy_path"])
            or protocol.get("capacity_confirmed") is not False):
        raise ValueError("B0 protocol hashes, scenarios or stage differ")
    pinned = PinnedEnvironment(ROOT / campaign["model"]["local_path"])
    baseline_id = resolve_config({}, pinned).config_id
    return campaign, protocol, split, {"ids": ids, "config_id": baseline_id}


def preflight() -> dict:
    campaign, protocol, split, expected = static_config()
    checkpoint = read(INPUT_ROOT / "development-overnight-checkpoint.json")
    audit_path = INPUT_ROOT / "development-input-audit.json"
    saved_audit = read(audit_path)
    if (checkpoint.get("status") != "development_inputs_qualified"
            or checkpoint.get("b0_stop_exit_code") != 0
            or checkpoint.get("split_plan_sha256") != sha(SPLIT_PATH)
            or checkpoint.get("sealed_test_touched") is not False
            or checkpoint.get("sla_capacity_confirmed") is not False):
        raise ValueError("Overnight development input checkpoint has not safely completed")
    audit = audit_frozen_splits(split, root=ROOT, stage_name="development_replication")
    if saved_audit != audit or audit.get("status") != "input_audit_passed":
        raise ValueError("Saved development input audit differs from fresh verification")
    windows = checkpoint.get("windows", {})
    for row in audit["windows"]:
        scenario_id = row["scenario_id"]
        manifest_path = ROOT / "configs/workloads/ops-frozen" / f"{scenario_id}.json"
        manifest = read(manifest_path)
        if (windows.get(scenario_id, {}).get("manifest_sha256") != sha(manifest_path)
                or windows.get(scenario_id, {}).get("input_replay_status") != "promoted_and_split_audited"
                or manifest.get("readiness") != "validated"
                or manifest.get("n_planned") != 240):
            raise ValueError(f"Development window no longer matches its qualified checkpoint: {scenario_id}")
        verify_scenario(manifest, root=ROOT)
    return {"status": "ready_for_matched_evaluator_b0", "campaign_id": campaign["campaign_id"],
            "campaign_sha256": sha(CAMPAIGN_PATH), "protocol_sha256": sha(PROTOCOL_PATH),
            "policy_sha256": protocol["research_policy_sha256"],
            "split_plan_sha256": sha(SPLIT_PATH), "scenario_ids": expected["ids"],
            "baseline_config_id": expected["config_id"],
            "manifest_sha256_by_scenario": {row["scenario_id"]: row["manifest_sha256"] for row in audit["windows"]},
            "input_audit_sha256": sha(audit_path), "sla_capacity_confirmed": False}


def idle_gpu() -> None:
    if subprocess.run(["docker", "container", "inspect", "iar-b0"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        raise RuntimeError("Shared B0 container still exists; refuse overlapping evaluator startup")
    for _ in range(40):
        active = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                                 "--format=csv,noheader,nounits"], check=True,
                                capture_output=True, text=True).stdout.strip()
        if not active:
            return
        time.sleep(3)
    raise RuntimeError(f"GPU compute process still active: {active}")


def validate_result(prepared: dict, cli_result: dict) -> dict:
    if cli_result.get("status") != "valid" or cli_result.get("config_id") != prepared["baseline_config_id"]:
        raise ValueError("Evaluator B0 did not return a valid stock configuration result")
    directory = Path(cli_result.get("artifacts", {}).get("directory", ""))
    if not directory.is_absolute() or not directory.is_relative_to(OUT_ROOT) or not directory.is_dir():
        raise ValueError("Evaluator result directory is absent or outside the B0 campaign")
    cells = {}
    for ordinal, scenario_id in enumerate(prepared["scenario_ids"], 1):
        cell_dir = directory / f"cell-{ordinal:02d}-{scenario_id}"
        cell_path = cell_dir / "cell-result.json"
        cell = read(cell_path)
        counts = cell.get("counts", {})
        metrics = cell.get("metrics", {})
        raw_path = Path(cell.get("artifacts", {}).get("raw_requests", ""))
        if (cell.get("scenario_id") != scenario_id
                or cell.get("config_id") != prepared["baseline_config_id"]
                or cell.get("status") != "valid" or cell.get("behavior") != "normal"
                or counts.get("planned") != 240 or counts.get("dispatched") != 240
                or counts.get("completed") != 240
                or any(counts.get(key) != 0 for key in
                       ("failed", "timed_out", "canceled", "censored", "not_dispatched"))
                or cell.get("diagnostics", {}).get("planned_schedule_sha256")
                   != read(ROOT / "configs/workloads/ops-frozen" / f"{scenario_id}.json")["schedule_sha256"]
                or not raw_path.is_file()
                or not raw_path.is_relative_to(cell_dir)):
            raise ValueError(f"Evaluator B0 CellResult incomplete or mismatched: {scenario_id}")
        for key in ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms"):
            value = metrics.get(key)
            if not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"B0 CellResult missing positive {key}: {scenario_id}")
        cells[scenario_id] = {"cell_id": cell["cell_id"],
                              "path": str(cell_path.relative_to(ROOT)),
                              "sha256": sha(cell_path),
                              "raw_requests_path": str(raw_path.relative_to(ROOT)),
                              "raw_requests_sha256": sha(raw_path),
                              "config_id": cell["config_id"],
                              "planned_schedule_sha256": cell["diagnostics"]["planned_schedule_sha256"],
                              "metrics": {key: metrics[key] for key in
                                          ("output_tokens_per_s", "ttft_p90_ms", "tpot_p90_ms")}}
    return {"schema_version": "matched-evaluator-b0-receipt-v1",
            "status": "matched_evaluator_b0_valid", "created_at_utc": datetime.now(UTC).isoformat(),
            "campaign_id": prepared["campaign_id"],
            "campaign_sha256": prepared["campaign_sha256"],
            "protocol_sha256": prepared["protocol_sha256"],
            "policy_sha256": prepared["policy_sha256"],
            "baseline_config_id": prepared["baseline_config_id"],
            "input_audit_sha256": prepared["input_audit_sha256"],
            "cells": cells, "sla_capacity_confirmed": False,
            "next_gate": "class-aware adaptive rate profile on B0 and independent confirmation"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check-config", "check", "run"))
    args = parser.parse_args()
    if args.action == "check-config":
        campaign, protocol, split, expected = static_config()
        print(json.dumps({"status": "config_valid_inputs_not_checked",
                          "campaign_id": campaign["campaign_id"],
                          "baseline_config_id": expected["config_id"],
                          "scenario_ids": expected["ids"],
                          "capacity_confirmed": False}, indent=2))
        return 0
    try:
        prepared = preflight()
    except (OSError, ValueError, KeyError) as exc:
        if args.action == "check":
            print(json.dumps({"status": "blocked", "reason": f"{type(exc).__name__}: {exc}",
                              "sla_capacity_confirmed": False}, indent=2))
            return 2
        raise
    if args.action == "check":
        print(json.dumps(prepared, indent=2, sort_keys=True))
        return 0
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with (INPUT_ROOT / "matched-evaluator-b0.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if RECEIPT.exists() or OUT_ROOT.exists():
            raise RuntimeError("B0 campaign output already exists; inspect before rerunning")
        idle_gpu()
        atomic(INPUT_ROOT / "matched-evaluator-b0-preflight.json", prepared)
        argv = [str(ROOT / ".venv/bin/iar"), "baseline", "--campaign", str(CAMPAIGN_PATH),
                "--backend", "real", "--stage", "screen", "--output-dir",
                str(ROOT / ".artifacts/autoresearch-codebase")]
        for scenario_id in prepared["scenario_ids"]:
            argv += ["--scenario", scenario_id]
        (INPUT_ROOT / "matched-evaluator-b0-argv.json").write_text(json.dumps(argv, indent=2) + "\n")
        with (INPUT_ROOT / "matched-evaluator-b0-console.log").open("w") as log:
            completed = subprocess.run(argv, cwd=ROOT, capture_output=True,
                                       text=True, timeout=14400, check=False)
            log.write(completed.stdout + completed.stderr)
        if completed.returncode:
            raise RuntimeError(f"iar baseline exited {completed.returncode}; inspect matched-evaluator-b0-console.log")
        result = json.loads(completed.stdout)
        receipt = validate_result(prepared, result)
        atomic(RECEIPT, receipt)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Matched evaluator B0 blocked: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
