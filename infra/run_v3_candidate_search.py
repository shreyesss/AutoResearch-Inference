#!/usr/bin/env python3
"""Wait for qualified B0 profiling, then launch one bounded v3 Codex search.

This script is intentionally separate from the running B0 profiler watcher.
`check` is read-only. `wait-run` is the sole action allowed to start GPU work.
Every gate and transition is written to a durable status file.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inference_autoresearch.storage import Ledger


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = ROOT / ".artifacts/v3-independent-capture"
PROFILE_RECEIPT = INPUT_ROOT / "b0-sla-profile-receipt.json"
PROFILE_INVALID = INPUT_ROOT / "b0-sla-profile-invalid.json"
STUDY = INPUT_ROOT / "sla-study-activated.json"
B0_RECEIPT = INPUT_ROOT / "matched-evaluator-b0-receipt.json"
CAMPAIGN_ID = "qwen38-27b-sla-serving-v3c"
CAMPAIGN = ROOT / "configs/campaign-sla-serving-v3c.json"
OUT = ROOT / ".artifacts/autoresearch-codebase" / CAMPAIGN_ID / "real"
STATUS = INPUT_ROOT / "candidate-search-v3c-status.json"
CONTROLLER_CONTAINER = "deploy-controller-1"
CONTROLLER_IMAGE = "iar-controller:0.1"
PROFILER_SESSION = "iar-v3-sla-profiler"
UPSTREAM_SESSIONS = ("iar-v3-dev-overnight", "iar-v3-b0-waiter", PROFILER_SESSION)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    pending.replace(path)


def under(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("profile source must be project-relative")
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()) or any(
            marker in part.lower() for part in result.relative_to(root.resolve()).parts
            for marker in ("sealed", "heldout", "test")):
        raise ValueError("profile source is outside development evidence")
    return result


def validate_profile_evidence(root: Path, receipt: dict[str, Any],
                              study: dict[str, Any], b0_receipt: dict[str, Any]) -> dict[str, Any]:
    if (receipt.get("status") != "observed_b0_profile"
            or receipt.get("capacity_confirmed") is not False
            or b0_receipt.get("status") != "matched_evaluator_b0_valid"
            or b0_receipt.get("sla_capacity_confirmed") is not False
            or study.get("policy", {}).get("approval_status") != "approved"):
        raise ValueError("B0 profiler or approved study is not eligible")
    study_path = Path(receipt.get("study_path", "")).resolve()
    if (study_path != (root / ".artifacts/v3-independent-capture/sla-study-activated.json").resolve()
            or not study_path.is_file() or sha(study_path) != receipt.get("study_sha256")):
        raise ValueError("activated study changed after B0 profiler receipt")
    entry = receipt.get("source") or {}
    source = under(root, entry.get("source_path"))
    if (not source.is_file() or sha(source) != entry.get("source_sha256")
            or entry not in study.get("baseline_adaptive_run_paths", [])
            or source.name != "sla-profile-points.json"):
        raise ValueError("B0 profiler source is missing or differs from the activated study")
    profile = read(source)
    policy_path = under(root, study["policy"]["path"])
    policy = read(policy_path)
    if sha(policy_path) != study["policy"]["sha256"]:
        raise ValueError("approved research policy changed")
    qualified = [point["qualified"] for point in profile.get("points", [])
                 if isinstance(point, dict) and isinstance(point.get("qualified"), dict)]
    valid = [point for point in qualified if point.get("status") == "valid"
             and isinstance(point.get("assessment"), dict)
             and point["assessment"].get("policy_id") == policy["policy_id"]
             and set(point["assessment"].get("classes", {})) == set(policy["classes"])]
    if (profile.get("schema_version") != "sla-profile-points-v1"
            or profile.get("claim") != "observed_development_points_no_confirmed_capacity"
            or profile.get("capacity_confirmed") is not False
            or profile.get("config_id") != b0_receipt.get("baseline_config_id")
            or profile.get("development_scenario_id")
               != study["adaptive_development"]["scenario_id"]
            or profile.get("policy_id") != policy["policy_id"]
            or profile.get("policy_sha256") != study["policy"]["sha256"]
            or not valid):
        raise ValueError("B0 profiler has no valid four-class point under the approved policy")
    for key in ("baseline_cell_paths", "matched_baseline_replication_cell_paths"):
        paths = study["adaptive_development"].get(key)
        if not isinstance(paths, list) or len(paths) != 1:
            raise ValueError("both matched development B0 cells are required")
        for relative in paths:
            cell = under(root, relative)
            if (not cell.is_file() or sha(cell) != study["adaptive_development"]
                    .get("baseline_cell_sha256_by_path", {}).get(relative)):
                raise ValueError("matched B0 CellResult missing or changed")
    if (study["adaptive_development"]["baseline_cell_paths"][0]
            == study["adaptive_development"]["matched_baseline_replication_cell_paths"][0]):
        raise ValueError("matched B0 development windows must be independent")
    return {"study_sha256": receipt["study_sha256"],
            "policy_sha256": study["policy"]["sha256"],
            "b0_profile_sha256": entry["source_sha256"],
            "valid_class_assessed_point_count": len(valid),
            "matched_b0_cell_count": 2, "capacity_confirmed": False}


def session_active(name: str) -> bool:
    return subprocess.run(["tmux", "has-session", "-t", name],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def check_upstream() -> dict[str, Any]:
    if PROFILE_INVALID.is_file():
        raise RuntimeError("B0 SLA profiler marked its run invalid")
    checkpoint = INPUT_ROOT / "development-overnight-checkpoint.json"
    if checkpoint.is_file() and read(checkpoint).get("status") == "blocked":
        raise RuntimeError("development input qualification blocked")
    if not PROFILE_RECEIPT.is_file() or not STUDY.is_file() or not B0_RECEIPT.is_file():
        raise RuntimeError("approved B0 profile, activated study or matched B0 receipt is pending")
    if any(session_active(name) for name in UPSTREAM_SESSIONS):
        raise RuntimeError("upstream GPU/profiler tmux session is still active")
    return validate_profile_evidence(ROOT, read(PROFILE_RECEIPT), read(STUDY), read(B0_RECEIPT))


def no_prior_proposals() -> None:
    ledger_path = OUT / "ledger.sqlite3"
    if ledger_path.is_file():
        ledger = Ledger(ledger_path)
        if ledger.events(CAMPAIGN_ID, "proposal"):
            raise RuntimeError("v3 candidate proposals already exist; never rerun automatically")
    if (OUT / "sla-search-summary.json").exists():
        raise RuntimeError("v3 candidate search already completed")


def controller_runtime_pin() -> dict[str, str]:
    """Refuse stale/replaced controller images before either CLI invocation.

    The controller's package is copied into the image at build time while the
    repository is bind-mounted read-only. Check the copied source, not merely
    the visible mount, so a host edit cannot masquerade as a rebuilt image.
    """
    inspect = json.loads(subprocess.run(
        ["docker", "inspect", CONTROLLER_CONTAINER], capture_output=True,
        text=True, check=True, timeout=15).stdout)[0]
    image = json.loads(subprocess.run(
        ["docker", "image", "inspect", CONTROLLER_IMAGE], capture_output=True,
        text=True, check=True, timeout=15).stdout)[0]
    mounts = {item["Destination"]: item for item in inspect.get("Mounts", [])}
    if (not inspect["State"]["Running"] or inspect["Image"] != image["Id"]
            or inspect["Config"]["Image"] != CONTROLLER_IMAGE
            or mounts.get(str(ROOT), {}).get("RW") is not False
            or mounts.get(str(ROOT / ".artifacts"), {}).get("RW") is not True
            or mounts.get("/var/run/docker.sock", {}).get("RW") is not True):
        raise RuntimeError("controller container, current image or required mounts differ")
    relative_paths = ["pyproject.toml"] + [
        str(path.relative_to(ROOT)) for path in sorted((ROOT / "src").rglob("*.py"))]
    host_hashes = {relative: sha(ROOT / relative) for relative in relative_paths}
    code = ("import hashlib,json,pathlib; r=pathlib.Path('/opt/iar-source'); "
            "ps=[pathlib.Path('pyproject.toml')]+[p.relative_to(r) for p in sorted((r/'src').rglob('*.py'))]; "
            "print(json.dumps({str(p):hashlib.sha256((r/p).read_bytes()).hexdigest() for p in ps}))")
    copied_hashes = json.loads(subprocess.run(
        ["docker", "exec", CONTROLLER_CONTAINER, "python3", "-c", code],
        capture_output=True, text=True, check=True, timeout=30).stdout)
    wrapper_hash = subprocess.run(
        ["docker", "exec", CONTROLLER_CONTAINER, "sha256sum", "/usr/local/bin/codex"],
        capture_output=True, text=True, check=True, timeout=15).stdout.split()[0]
    if copied_hashes != host_hashes or wrapper_hash != sha(ROOT / "deploy/codex-isolated"):
        raise RuntimeError("controller image code or isolated Codex wrapper is stale")
    campaign = read(CAMPAIGN)
    if campaign.get("campaign_id") != CAMPAIGN_ID:
        raise RuntimeError("versioned v3c campaign identity differs")
    return {"container_id": inspect["Id"], "image_id": image["Id"],
            "source_tree_sha256": hashlib.sha256(json.dumps(
                copied_hashes, sort_keys=True).encode()).hexdigest(),
            "isolated_wrapper_sha256": wrapper_hash,
            "campaign_sha256": sha(CAMPAIGN)}


def idle_gpu() -> None:
    if subprocess.run(["docker", "container", "inspect", "iar-b0"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        raise RuntimeError("shared B0 server still exists")
    for _ in range(40):
        result = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                                 "--format=csv,noheader,nounits"], capture_output=True,
                                text=True, check=True)
        if not result.stdout.strip():
            return
        time.sleep(3)
    raise RuntimeError("GPU remains occupied; refusing candidate search startup")


def stamp(state: dict[str, Any], stage: str, **details: Any) -> None:
    state.update({"stage": stage, "updated_at_utc": datetime.now(UTC).isoformat(), **details})
    state.setdefault("events", []).append({"stage": stage, "at_utc": state["updated_at_utc"],
                                            **details})
    write(STATUS, state)


def signal_container_process(pid_path: Path | None, signal_name: str) -> None:
    if pid_path is None or not pid_path.is_file():
        return
    try:
        pid = int(pid_path.read_text().strip())
    except (OSError, ValueError):
        return
    if pid <= 1:
        return
    try:
        subprocess.run(["docker", "exec", CONTROLLER_CONTAINER, "kill", "-s",
                        signal_name, str(pid)], capture_output=True, check=False, timeout=15)
    except (OSError, subprocess.SubprocessError):
        # The host docker client is signaled by the caller even if Docker is
        # unavailable during shutdown; the status remains a timed-out failure.
        pass


def run_command(argv: list[str], log_path: Path, *, timeout_s: int,
                inner_pid_path: Path | None = None) -> tuple[int, str, bool]:
    if inner_pid_path is not None:
        inner_pid_path.unlink(missing_ok=True)
    # Both live logs remain readable during a long GPU search. Keep stdout
    # separate so the CLI's final JSON can be parsed without stderr warnings.
    with log_path.open("w") as log, log_path.with_suffix(".stderr.log").open("w") as errors:
        process = subprocess.Popen(argv, cwd=ROOT, stdout=log,
                                   stderr=errors, text=True,
                                   start_new_session=True)
        timed_out = False
        try:
            process.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            signal_container_process(inner_pid_path, "INT")
            try:
                os.killpg(process.pid, signal.SIGINT)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                signal_container_process(inner_pid_path, "KILL")
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
    return process.returncode, log_path.read_text(), timed_out


def wait_for_profile(timeout_s: int, state: dict[str, Any]) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_s
    seen_profiler = False
    ended_at: float | None = None
    stamp(state, "waiting_for_b0_profiler", timeout_s=timeout_s)
    while time.monotonic() < deadline:
        if PROFILE_INVALID.is_file():
            raise RuntimeError("B0 SLA profiler marked its run invalid")
        checkpoint = INPUT_ROOT / "development-overnight-checkpoint.json"
        if checkpoint.is_file() and read(checkpoint).get("status") == "blocked":
            raise RuntimeError("development input qualification blocked")
        active = session_active(PROFILER_SESSION)
        seen_profiler = seen_profiler or active
        if PROFILE_RECEIPT.is_file() and not active:
            return check_upstream()
        if (seen_profiler or (INPUT_ROOT / "b0-sla-profile-argv.json").is_file()) \
                and not active and not PROFILE_RECEIPT.is_file():
            ended_at = ended_at or time.monotonic()
            if time.monotonic() - ended_at > 60:
                raise RuntimeError("B0 profiler tmux exited without a validated receipt")
        time.sleep(15)
    raise TimeoutError("B0 profiler did not finish within the bounded wait")


def run_waiter(timeout_s: int) -> dict[str, Any]:
    INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    with (INPUT_ROOT / "candidate-search-v3c-watcher.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if STATUS.exists():
            raise RuntimeError("existing candidate search status requires inspection; refusing rerun")
        state: dict[str, Any] = {"schema_version": "v3-candidate-search-watcher-v1",
                                 "status": "running", "capacity_confirmed": False,
                                 "sealed_test_touched": False, "events": []}
        try:
            evidence = wait_for_profile(timeout_s, state)
            stamp(state, "b0_profile_gate_passed", evidence=evidence)
            no_prior_proposals()
            controller_pin = controller_runtime_pin()
            stamp(state, "controller_image_verified", controller=controller_pin)
            preflight_pid = INPUT_ROOT / "candidate-search-v3c-preflight.pid"
            search_pid = INPUT_ROOT / "candidate-search-v3c-run.pid"
            check_argv = ["docker", "exec", "-w", str(ROOT), CONTROLLER_CONTAINER,
                          "bash", "-c", 'printf "%s\\n" "$$" > "$1"; shift; exec "$@"',
                          "iar-v3c-watch", str(preflight_pid),
                          "iar", "sla-search", "--backend", "real",
                          "--campaign", str(CAMPAIGN), "--check"]
            stamp(state, "gpu_free_search_preflight", argv=check_argv)
            check_code, check_stdout, check_timeout = run_command(
                check_argv, INPUT_ROOT / "candidate-search-v3c-preflight.log",
                timeout_s=600, inner_pid_path=preflight_pid)
            if check_code or check_timeout:
                raise RuntimeError("GPU-free SLA search preflight failed; inspect candidate-search-v3c-preflight.log")
            preflight = json.loads(check_stdout)
            if (preflight.get("status") != "ready"
                    or preflight.get("study_sha256") != evidence["study_sha256"]
                    or preflight.get("policy_sha256") != evidence["policy_sha256"]
                    or preflight.get("capacity_confirmed") is not False):
                raise RuntimeError("search preflight disagrees with B0 profile receipt")
            stamp(state, "preflight_passed", preflight=preflight)
            no_prior_proposals()
            idle_gpu()
            if controller_runtime_pin() != controller_pin:
                raise RuntimeError("controller image, copied code, wrapper or campaign changed after preflight")
            search_argv = check_argv[:-1].copy()
            search_argv[search_argv.index(str(preflight_pid))] = str(search_pid)
            stamp(state, "candidate_search_running", argv=search_argv)
            code, stdout, timed_out = run_command(
                search_argv, INPUT_ROOT / "candidate-search-v3c-console.log",
                timeout_s=72000, inner_pid_path=search_pid)
            stamp(state, "candidate_search_finished", exit_code=code, timed_out=timed_out)
            if code or timed_out:
                raise RuntimeError("candidate search failed or timed out; inspect v3c console and ledger")
            result = json.loads(stdout)
            if (result.get("capacity_confirmed") is not False
                    or result.get("campaign_id") != CAMPAIGN_ID
                    or result.get("status") != "sequential_development_search_complete"):
                raise RuntimeError("candidate search result identity or claim is invalid")
            state["status"] = "development_search_observed"
            stamp(state, "complete", result=result)
            return state
        except Exception as exc:
            state["status"] = "blocked"
            stamp(state, "blocked", error=f"{type(exc).__name__}: {exc}")
            raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "wait-run"))
    parser.add_argument("--wait-timeout-s", type=int, default=43200)
    args = parser.parse_args()
    if args.action == "check":
        evidence = check_upstream()
        no_prior_proposals()
        print(json.dumps({"status": "ready_for_gpu_free_preflight", "evidence": evidence}, indent=2))
        return 0
    if not 1 <= args.wait_timeout_s <= 43200:
        raise ValueError("wait timeout must be 1..43200 seconds")
    result = run_waiter(args.wait_timeout_s)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"v3 candidate search watcher blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
