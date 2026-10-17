#!/usr/bin/env python3
"""Activate the approved v3 SLA study from matched B0 evidence, then profile B0.

No GPU work occurs in `check` or `activate`. `profile` starts one fresh B0
server only after the input/readiness audit and an idle-GPU check. It records
all observations and never claims independently confirmed capacity.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from inference_autoresearch.evaluation.sla_study import audit_sla_study
from inference_autoresearch.runtime.config import PinnedEnvironment, resolve_config


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT / ".artifacts/v3-independent-capture"
TEMPLATE = ROOT / "configs/sla-study-v3.template.json"
RECEIPT = INPUT_ROOT / "matched-evaluator-b0-receipt.json"
ACTIVE = INPUT_ROOT / "sla-study-activated.json"
PROFILE_RECEIPT = INPUT_ROOT / "b0-sla-profile-receipt.json"
DEVELOPMENT_SESSION = "iar-v3-dev-overnight"
B0_SESSION = "iar-v3-b0-waiter"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_object(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text())
    if not isinstance(result, dict):
        raise ValueError(f"expected JSON object: {path}")
    return result


def write_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def under(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("receipt paths must be project-relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("receipt path escapes project root")
    return path


def build_activated_study(root: Path, template: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    if (template.get("schema_version") != "sla-study-scaffold-v1"
            or template.get("claim") != "not_runnable_until_qualified"
            or receipt.get("schema_version") != "matched-evaluator-b0-receipt-v1"
            or receipt.get("status") != "matched_evaluator_b0_valid"
            or receipt.get("campaign_id") != "qwen38-27b-sla-b0-v3"
            or receipt.get("sla_capacity_confirmed") is not False
            or receipt.get("policy_sha256") != template.get("policy", {}).get("sha256")):
        raise ValueError("B0 receipt or approved policy identity differs from v3 study")
    development = template["adaptive_development"]
    scenario_id = development["scenario_id"]
    manifest_path = under(root, development["manifest_path"])
    manifest = read_object(manifest_path)
    if (manifest.get("scenario_id") != scenario_id
            or manifest.get("readiness") != "validated"
            or manifest.get("suite_role") != "development"
            or manifest.get("n_planned") != 240
            or manifest.get("request_class_path") != development["request_class_path"]):
        raise ValueError("development manifest is not the qualified 240-request window")
    class_path = under(root, development["request_class_path"])
    if digest(class_path) != manifest.get("request_class_sha256"):
        raise ValueError("development class sidecar hash changed")
    cells = receipt.get("cells")
    if not isinstance(cells, dict) or len(cells) != 2 or scenario_id not in cells:
        raise ValueError("B0 receipt must contain both independent development windows")
    cell_paths = []
    for name, entry in sorted(cells.items()):
        path = under(root, entry["path"])
        cell = read_object(path)
        counts = cell.get("counts", {})
        raw = under(root, entry["raw_requests_path"])
        if (digest(path) != entry.get("sha256")
                or digest(raw) != entry.get("raw_requests_sha256")
                or cell.get("scenario_id") != name
                or cell.get("cell_id") != entry.get("cell_id")
                or cell.get("config_id") != receipt.get("baseline_config_id")
                or cell.get("status") != "valid" or cell.get("behavior") != "normal"
                or counts.get("planned") != 240 or counts.get("dispatched") != 240
                or counts.get("completed") != 240
                or any(counts.get(key) != 0 for key in
                       ("failed", "timed_out", "canceled", "censored", "not_dispatched"))
                or cell.get("artifacts", {}).get("raw_requests") != str(raw)):
            raise ValueError(f"matched B0 cell changed or became ineligible: {name}")
        if name == scenario_id:
            cell_paths.append(entry["path"])
    if len(cell_paths) != 1:
        raise ValueError("development anchor B0 cell is absent")
    study = json.loads(json.dumps(template))
    development = study["adaptive_development"]
    development["manifest_sha256"] = digest(manifest_path)
    development["request_class_sha256"] = digest(class_path)
    development["baseline_cell_paths"] = cell_paths
    development["matched_baseline_replication_cell_paths"] = [
        entry["path"] for name, entry in sorted(cells.items()) if name != scenario_id]
    development["baseline_cell_sha256_by_path"] = {
        entry["path"]: entry["sha256"] for entry in cells.values()}
    development["baseline_raw_sha256_by_path"] = {
        entry["path"]: entry["raw_requests_sha256"] for entry in cells.values()}
    development["minimum_baseline_cells"] = 1
    study["baseline_adaptive_run_paths"] = []
    return study


def verify_receipt_provenance(receipt: dict[str, Any]) -> None:
    campaign_path = ROOT / "configs/campaign-sla-b0-v3.json"
    protocol_path = ROOT / "configs/evaluation-protocol-sla-b0-v3.json"
    audit_path = INPUT_ROOT / "development-input-audit.json"
    campaign = read_object(campaign_path)
    stock_id = resolve_config({}, PinnedEnvironment(
        ROOT / campaign["model"]["local_path"])).config_id
    expected_windows = {"qwen-ops-mixed-development-1042-v1",
                        "qwen-ops-mixed-development-1043-v1"}
    if (receipt.get("campaign_sha256") != digest(campaign_path)
            or receipt.get("protocol_sha256") != digest(protocol_path)
            or receipt.get("input_audit_sha256") != digest(audit_path)
            or receipt.get("baseline_config_id") != stock_id
            or set(receipt.get("cells", {})) != expected_windows):
        raise ValueError("B0 receipt provenance differs from pinned campaign, input audit or stock baseline")


def activate() -> dict[str, Any]:
    template = read_object(TEMPLATE)
    receipt = read_object(RECEIPT)
    verify_receipt_provenance(receipt)
    study = build_activated_study(ROOT, template, receipt)
    if ACTIVE.exists():
        existing = read_object(ACTIVE)
        existing.pop("baseline_adaptive_run_paths", None)
        comparison = json.loads(json.dumps(study))
        comparison.pop("baseline_adaptive_run_paths", None)
        if existing != comparison:
            raise RuntimeError("active study differs from freshly verified B0 evidence")
    else:
        write_atomic(ACTIVE, study)
    readiness = audit_sla_study(ACTIVE, root=ROOT)
    if readiness["status"] != "inputs_ready_for_new_campaign":
        raise RuntimeError(f"v3 study remains blocked: {readiness['blockers']}")
    write_atomic(INPUT_ROOT / "sla-study-readiness.json", readiness)
    return {"status": "activated", "study_path": str(ACTIVE), "study_sha256": digest(ACTIVE),
            "readiness": readiness, "capacity_confirmed": False}


def idle_gpu() -> None:
    if subprocess.run(["docker", "container", "inspect", "iar-b0"],
                      capture_output=True, check=False).returncode == 0:
        raise RuntimeError("shared B0 container still exists")
    for _ in range(40):
        process = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                                  "--format=csv,noheader,nounits"], capture_output=True,
                                 text=True, check=True)
        if not process.stdout.strip():
            return
        time.sleep(3)
    raise RuntimeError("GPU remains occupied; refusing SLA profiler launch")


def b0_runner_finished() -> None:
    for session in (DEVELOPMENT_SESSION, B0_SESSION):
        if subprocess.run(["tmux", "has-session", "-t", session],
                          capture_output=True, check=False).returncode == 0:
            raise RuntimeError(f"upstream tmux session still active: {session}")
    lock_path = INPUT_ROOT / "matched-evaluator-b0.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("matched evaluator B0 runner is still active") from exc
        fcntl.flock(lock, fcntl.LOCK_UN)


def run_profile() -> dict[str, Any]:
    activated = activate()
    if PROFILE_RECEIPT.exists():
        raise RuntimeError("B0 SLA profile receipt already exists; inspect before retrying")
    b0_runner_finished()
    idle_gpu()
    argv = [str(ROOT / ".venv/bin/iar"), "sla-profile", "--backend", "real",
            "--campaign", "configs/campaign-v2.json", "--study", str(ACTIVE),
            "--initial-rate-rps", "0.2", "--min-rate-rps", "0.1",
            "--max-rate-rps", "1.6", "--max-points", "6"]
    write_atomic(INPUT_ROOT / "b0-sla-profile-argv.json", {"argv": argv})
    with (INPUT_ROOT / "b0-sla-profile-console.log").open("w") as log:
        process = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                                 timeout=28800, check=False)
        log.write(process.stdout + process.stderr)
    try:
        result = json.loads(process.stdout)
    except ValueError:
        result = {}
    if process.returncode:
        write_atomic(INPUT_ROOT / "b0-sla-profile-invalid.json", {
            "status": "invalid", "exit_code": process.returncode,
            "result": result, "capacity_confirmed": False,
            "note": "Raw profiler artifacts remain in the run directory; no agent evidence was activated."})
        raise RuntimeError(f"iar sla-profile exited {process.returncode}; inspect console log")
    source = Path(result["artifacts"]["all_points"]).resolve()
    if (not source.is_relative_to(ROOT / ".artifacts/autoresearch-codebase")
            or source.name != "sla-profile-points.json" or not source.is_file()):
        raise ValueError("SLA profiler returned an unexpected result path")
    profile = read_object(source)
    approved = read_object(ROOT / "configs/sla-policy-v3.json")
    b0 = read_object(RECEIPT)
    qualified = [point["qualified"] for point in profile.get("points", [])
                 if isinstance(point, dict) and isinstance(point.get("qualified"), dict)]
    assessed = [point for point in qualified if point.get("status") == "valid"
                and isinstance(point.get("assessment"), dict)
                and point["assessment"].get("policy_id") == approved["policy_id"]
                and set(point["assessment"].get("classes", {})) == set(approved["classes"])]
    if (profile.get("schema_version") != "sla-profile-points-v1"
            or profile.get("claim") != "observed_development_points_no_confirmed_capacity"
            or profile.get("capacity_confirmed") is not False
            or profile.get("policy_sha256") != activated["readiness"]["policy_sha256"]
            or profile.get("policy_id") != approved["policy_id"]
            or profile.get("config_id") != b0["baseline_config_id"]
            or profile.get("development_scenario_id")
               != read_object(ACTIVE)["adaptive_development"]["scenario_id"]
            or result.get("status") != "observed"
            or result.get("valid_qualified_point_count", 0) < 1
            or not assessed):
        write_atomic(INPUT_ROOT / "b0-sla-profile-invalid.json", {
            "status": "invalid", "profile_path": str(source), "profile_sha256": digest(source),
            "point_count": len(profile.get("points", [])),
            "valid_class_assessed_point_count": len(assessed),
            "capacity_confirmed": False,
            "note": "All raw points remain in the profiler run directory; no agent evidence was activated."})
        raise ValueError("SLA profiler has no valid class-assessed B0 point under the approved policy")
    entry = {"source_path": str(source.relative_to(ROOT)), "source_sha256": digest(source)}
    study = read_object(ACTIVE)
    study["baseline_adaptive_run_paths"] = [entry]
    write_atomic(ACTIVE, study)
    receipt = {"status": "observed_b0_profile", "study_path": str(ACTIVE),
               "study_sha256": digest(ACTIVE), "source": entry,
               "profile_run_id": result["run_id"], "point_count": len(profile["points"]),
               "capacity_confirmed": False,
               "next_gate": "inspect per-class points, then qualify a separate serving-search campaign"}
    write_atomic(PROFILE_RECEIPT, receipt)
    return receipt


def wait_for_b0(*, timeout_s: int) -> None:
    deadline = time.monotonic() + timeout_s
    seen_b0_session = False
    ended_without_receipt_at: float | None = None
    while time.monotonic() < deadline:
        checkpoint_path = INPUT_ROOT / "development-overnight-checkpoint.json"
        if checkpoint_path.is_file():
            checkpoint = read_object(checkpoint_path)
            if checkpoint.get("status") == "blocked":
                raise RuntimeError(f"development input qualification blocked: {checkpoint.get('error')}")
        active = subprocess.run(["tmux", "has-session", "-t", B0_SESSION],
                                capture_output=True, check=False).returncode == 0
        seen_b0_session = seen_b0_session or active
        if RECEIPT.is_file() and not active:
            b0_runner_finished()
            return
        if seen_b0_session and not active and not RECEIPT.is_file():
            ended_without_receipt_at = ended_without_receipt_at or time.monotonic()
            if time.monotonic() - ended_without_receipt_at > 60:
                raise RuntimeError("matched B0 waiter exited without a validated receipt")
        time.sleep(15)
    raise TimeoutError("matched B0 receipt/session did not finish within the bounded wait")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "activate", "profile", "wait-profile"))
    parser.add_argument("--wait-timeout-s", type=int, default=28800)
    args = parser.parse_args()
    if args.action == "check":
        if not RECEIPT.is_file():
            print(json.dumps({"status": "blocked", "reason": "matched B0 receipt missing"}, indent=2))
            return 2
        receipt = read_object(RECEIPT)
        verify_receipt_provenance(receipt)
        build_activated_study(ROOT, read_object(TEMPLATE), receipt)
        result = {"status": "ready_to_activate", "receipt_sha256": digest(RECEIPT),
                  "capacity_confirmed": False}
    else:
        INPUT_ROOT.mkdir(parents=True, exist_ok=True)
        with (INPUT_ROOT / "sla-activation.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.action == "wait-profile":
                if args.wait_timeout_s < 1 or args.wait_timeout_s > 43200:
                    raise ValueError("wait timeout must be 1..43200 seconds")
                wait_for_b0(timeout_s=args.wait_timeout_s)
            result = activate() if args.action == "activate" else run_profile()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SLA study activation blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
