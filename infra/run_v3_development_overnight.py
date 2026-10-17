#!/usr/bin/env python3
"""Qualify two development inputs overnight; stop before evaluator/SLA claims.

The existing 1042 capture is owned by run_v3_first_capture.sh. This process
waits for that tmux job to exit, checks its evidence, then owns the B0 server
while it replays 1042, captures 1043, replays 1043, and promotes both inputs.
It never touches sealed-test data or starts a serving-search campaign.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from inference_autoresearch.evaluation.split_v2 import (
    audit_frozen_splits, load_split_plan, require_window_class_counts,
)
from inference_autoresearch.workloads.registry import verify_scenario


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/v3-independent-capture"
ASSETS = ROOT / "configs/workloads/ops-frozen"
SPLIT_PATH = ROOT / "configs/evaluation-splits-v3.json"
VALIDATION = ROOT / ".artifacts/v2-independent-validation/development_replication/validation-report.json"
FIRST_TMUX = "iar-v3-dev-1042"
CHECKPOINT = ARTIFACTS / "development-overnight-checkpoint.json"
PYTHON = ROOT / ".venv/bin/python"


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write_checkpoint(state: dict) -> None:
    state["updated_at_utc"] = now()
    pending = CHECKPOINT.with_suffix(".json.tmp")
    pending.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    pending.replace(CHECKPOINT)


def event(state: dict, stage: str, detail: dict | None = None) -> None:
    state["stage"] = stage
    state["events"].append({"at_utc": now(), "stage": stage, **(detail or {})})
    write_checkpoint(state)
    print(f"{now()} {stage}", flush=True)


def tmux_alive() -> bool:
    return subprocess.run(["tmux", "has-session", "-t", FIRST_TMUX],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def container_exists() -> bool:
    return subprocess.run(["docker", "container", "inspect", "iar-b0"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def wait_first(state: dict, scenario_id: str, *, timeout_s: int) -> None:
    exit_path = ARTIFACTS / f"{scenario_id}.capture-exit-code.txt"
    deadline = time.monotonic() + timeout_s
    event(state, "waiting_for_existing_1042_capture", {"tmux_session": FIRST_TMUX})
    disappeared_at: float | None = None
    while time.monotonic() < deadline:
        alive = tmux_alive()
        if exit_path.is_file() and not alive:
            code = int(exit_path.read_text().strip())
            if code != 0:
                raise RuntimeError(f"1042 capture exited {code}; inspect its console and status")
            return
        if not alive and not exit_path.is_file():
            disappeared_at = disappeared_at or time.monotonic()
            if time.monotonic() - disappeared_at > 30:
                raise RuntimeError("1042 tmux ended without a capture exit record")
        time.sleep(15)
    raise TimeoutError("1042 capture did not finish within the overnight wait limit")


def inspect_capture(scenario_id: str, seed: int, split: dict) -> dict:
    """Check source accounting and frozen metadata before any replay or next capture."""
    cell = ARTIFACTS / scenario_id
    plan = read_object(cell / "plan.json")
    status = read_object(cell / "status.json")
    summary = read_object(cell / "aiperf/mixed/summary.json")
    freeze = read_object(ARTIFACTS / f"{scenario_id}.freeze.json")
    manifest_path = ASSETS / f"{scenario_id}.json"
    manifest = read_object(manifest_path)
    expected = split["generation"]
    if (plan.get("cell") != scenario_id or plan.get("workload") != "mixed"
            or plan.get("random_seed") != seed
            or plan.get("source_sha256") != split["source_sha256"]
            or plan.get("request_count") != expected["request_count_per_window"]
            or plan.get("effective_dataset_entries") != expected["dataset_entries"]
            or plan.get("offered_rps") != expected["request_rate_rps"]):
        raise ValueError(f"{scenario_id}: capture plan differs from predeclared split")
    if (status.get("aiperf_exit_code") != 0 or summary.get("status") != "complete"
            or summary.get("request_count") != expected["request_count_per_window"]
            or summary.get("http_200") != expected["request_count_per_window"]
            or summary.get("statuses") != [200]):
        raise ValueError(f"{scenario_id}: source capture incomplete or has failures")
    if (freeze.get("scenario_id") != scenario_id
            or freeze.get("rows") != expected["request_count_per_window"]
            or manifest.get("readiness") != "prepared"
            or manifest.get("suite_role") != "development"
            or manifest.get("payload_sha256") != freeze.get("asset_sha256")
            or manifest.get("seeds", {}).get("arrivals") != seed
            or manifest.get("seeds", {}).get("content") != seed):
        raise ValueError(f"{scenario_id}: frozen capture identity or hash mismatch")
    checked = verify_scenario(manifest, root=ROOT, require_validated=False)
    classes = checked["request_classes"]
    if classes is None:
        raise ValueError(f"{scenario_id}: no explicit class sidecar")
    counts = require_window_class_counts(
        classes, expected_count=expected["request_count_per_window"],
        minimum=split["qualification"]["minimum_class_requests_per_window"])
    return {"scenario_id": scenario_id, "seed": seed, "class_counts": counts,
            "source_requests": summary["request_count"], "source_http_200": summary["http_200"],
            "source_raw_sha256": summary["raw_sha256"],
            "manifest_sha256": digest(manifest_path),
            "class_sidecar_sha256": manifest["request_class_sha256"],
            "input_replay_status": "prepared_only", "evaluator_b0_cell": None,
            "sla_capacity_confirmed": False}


def ensure_idle() -> None:
    for _ in range(60):
        if not container_exists():
            break
        time.sleep(3)
    else:
        raise RuntimeError("iar-b0 still exists after the first capture; refusing overlapping startup")
    for _ in range(40):
        apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                               "--format=csv,noheader,nounits"], check=True,
                              capture_output=True, text=True).stdout.strip()
        if not apps:
            return
        time.sleep(3)
    raise RuntimeError(f"GPU compute process still active; refusing startup: {apps}")


def run_logged(argv: list[str], log: Path, *, timeout_s: int) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as stream:
        completed = subprocess.run(argv, cwd=ROOT, stdout=stream,
                                   stderr=subprocess.STDOUT, timeout=timeout_s, check=False)
    if completed.returncode:
        raise RuntimeError(f"Command exited {completed.returncode}; inspect {log}")


def wait_health(*, timeout_s: int = 1200) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3) as response:
                if response.status == 200:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(5)
    raise TimeoutError("B0 did not become healthy after startup")


def replay(state: dict, scenario_id: str, key: str) -> None:
    event(state, f"replaying_{key}", {"scenario_id": scenario_id})
    argv = [str(PYTHON), "infra/validate-ops4-frozen.py", "replay",
            "--split-plan", "configs/evaluation-splits-v3.json",
            "--split-stage", "development_replication", "--scenario", scenario_id]
    run_logged(argv, ARTIFACTS / f"{scenario_id}.replay-console.log", timeout_s=10800)
    report = read_object(VALIDATION)
    entry = report.get("scenarios", {}).get(scenario_id)
    if (report.get("schema_version") != "v2-independent-validation-v1"
            or not isinstance(entry, dict) or entry.get("status") != "validated"
            or entry.get("planned") != 240 or entry.get("http_200") != 240
            or not all(entry.get(name) is True for name in
                       ("payload_match", "output_caps_realized", "schedule_match"))):
        raise ValueError(f"{scenario_id}: replay report does not validate all requests")
    state["windows"][scenario_id]["input_replay_status"] = "validated_on_B0"
    state["windows"][scenario_id]["replay_report_sha256"] = digest(VALIDATION)
    write_checkpoint(state)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-timeout-s", type=int, default=10800)
    args = parser.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with (ARTIFACTS / "development-overnight.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if CHECKPOINT.exists():
            raise RuntimeError(f"Existing checkpoint requires inspection before rerun: {CHECKPOINT}")
        split = load_split_plan(SPLIT_PATH, root=ROOT)
        windows = split["stages"]["development_replication"]["windows"]
        if len(windows) != 2 or windows[0]["seed"] != 1042 or windows[1]["seed"] != 1043:
            raise ValueError("This launcher is pinned to the 1042/1043 development plan")
        first, second = windows
        state = {"schema_version": "v3-development-overnight-checkpoint-v1",
                 "status": "running", "stage": "init", "started_at_utc": now(),
                 "split_plan_sha256": digest(SPLIT_PATH), "windows": {}, "events": [],
                 "sealed_test_touched": False, "evaluator_b0_complete": False,
                 "sla_capacity_confirmed": False,
                 "next_gate": "matched evaluator B0 cells and class-aware adaptive profiler"}
        write_checkpoint(state)
        owns_b0 = False
        try:
            wait_first(state, first["scenario_id"], timeout_s=args.wait_timeout_s)
            state["windows"][first["scenario_id"]] = inspect_capture(first["scenario_id"], first["seed"], split)
            event(state, "first_capture_passed", {"class_counts": state["windows"][first["scenario_id"]]["class_counts"]})
            ensure_idle()
            event(state, "starting_B0_for_development_replay")
            run_logged(["bash", "infra/first-baseline.sh", "up"],
                       ARTIFACTS / "development-b0-start.log", timeout_s=120)
            owns_b0 = True
            wait_health()
            replay(state, first["scenario_id"], "1042")
            event(state, "first_replay_passed")
            event(state, "capturing_second_development_window", {"scenario_id": second["scenario_id"]})
            run_logged([str(PYTHON), "infra/run-ops-b0.py", "--workload", "mixed",
                        "--rate", str(split["generation"]["request_rate_rps"]),
                        "--count", str(split["generation"]["request_count_per_window"]),
                        "--duration", str(split["generation"]["benchmark_duration_s"]),
                        "--timeout", str(split["generation"]["benchmark_duration_s"] + 600),
                        "--dataset-entries", str(split["generation"]["dataset_entries"]),
                        "--random-seed", str(second["seed"]), "--root", str(ARTIFACTS),
                        "--cell", second["scenario_id"]],
                       ARTIFACTS / f"{second['scenario_id']}.capture-console.log", timeout_s=6000)
            run_logged([str(PYTHON), "infra/freeze-ops-synthetic-cell.py", "--cell",
                        str(ARTIFACTS / second["scenario_id"]), "--scenario-id", second["scenario_id"],
                        "--split", "development"],
                       ARTIFACTS / f"{second['scenario_id']}.freeze.json", timeout_s=120)
            state["windows"][second["scenario_id"]] = inspect_capture(second["scenario_id"], second["seed"], split)
            event(state, "second_capture_passed", {"class_counts": state["windows"][second["scenario_id"]]["class_counts"]})
            replay(state, second["scenario_id"], "1043")
            event(state, "both_replays_passed")
            run_logged([str(PYTHON), "infra/validate-ops4-frozen.py", "promote",
                        "--split-plan", "configs/evaluation-splits-v3.json",
                        "--split-stage", "development_replication"],
                       ARTIFACTS / "development-promote.log", timeout_s=120)
            audit = audit_frozen_splits(split, root=ROOT, stage_name="development_replication")
            if audit.get("status") != "input_audit_passed" or len(audit.get("windows", [])) != 2:
                raise ValueError("Development input split audit did not pass")
            (ARTIFACTS / "development-input-audit.json").write_text(
                json.dumps(audit, indent=2, sort_keys=True) + "\n")
            for window in windows:
                name = window["scenario_id"]
                state["windows"][name]["manifest_sha256"] = digest(ASSETS / f"{name}.json")
                state["windows"][name]["input_replay_status"] = "promoted_and_split_audited"
            state["status"] = "development_inputs_qualified"
            state["next_gate"] = "matched evaluator B0 cells; then class-aware adaptive SLA profiling"
            event(state, "development_inputs_qualified", {"input_audit_path": str(ARTIFACTS / "development-input-audit.json")})
            return 0
        except Exception as exc:
            state["status"] = "blocked"
            state["error"] = f"{type(exc).__name__}: {exc}"
            event(state, "blocked", {"reason": state["error"]})
            raise
        finally:
            if owns_b0:
                stopped = subprocess.run(["bash", "infra/first-baseline.sh", "down"], cwd=ROOT,
                                         capture_output=True, text=True, timeout=180, check=False)
                (ARTIFACTS / "development-b0-stop.log").write_text(stopped.stdout + stopped.stderr)
                state["b0_stop_exit_code"] = stopped.returncode
                write_checkpoint(state)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Overnight development qualification stopped: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
