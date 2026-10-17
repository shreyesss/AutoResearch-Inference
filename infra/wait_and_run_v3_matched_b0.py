#!/usr/bin/env python3
"""Wait for the development input job, then run matched evaluator B0 once.

This is a separate unattended continuation for an already launched input
qualifier. It never starts GPU work while that qualifier still owns B0.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / ".artifacts/v3-independent-capture"
CHECKPOINT = ARTIFACTS / "development-overnight-checkpoint.json"
STATUS = ARTIFACTS / "matched-evaluator-b0-waiter-status.json"
SOURCE_TMUX = "iar-v3-dev-overnight"


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def save(data: dict) -> None:
    data["updated_at_utc"] = now()
    temporary = STATUS.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(STATUS)


def source_alive() -> bool:
    return subprocess.run(["tmux", "has-session", "-t", SOURCE_TMUX],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def gate(checkpoint: dict | None, *, tmux_alive: bool) -> tuple[str, str]:
    if checkpoint is None:
        return "waiting", "development checkpoint absent"
    status = checkpoint.get("status")
    if status == "blocked":
        return "blocked", f"development input gate failed: {checkpoint.get('error', 'inspect checkpoint')}"
    if status != "development_inputs_qualified":
        return "waiting", f"development input status is {status!r}"
    if checkpoint.get("b0_stop_exit_code") not in (None, 0):
        return "blocked", "development B0 shutdown failed"
    if checkpoint.get("b0_stop_exit_code") != 0 or tmux_alive:
        return "waiting", "development job has not completed B0 shutdown"
    return "ready", "qualified development inputs and completed B0 shutdown"


def child(action: str, log: Path, *, timeout_s: int) -> int:
    argv = [str(ROOT / ".venv/bin/python"), "infra/run_v3_matched_b0.py", action]
    with log.open("w") as stream:
        result = subprocess.run(argv, cwd=ROOT, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=timeout_s, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-timeout-s", type=int, default=36000)
    args = parser.parse_args()
    if args.wait_timeout_s <= 0:
        parser.error("--wait-timeout-s must be positive")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    with (ARTIFACTS / "matched-evaluator-b0-waiter.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if STATUS.exists():
            raise RuntimeError(f"Existing waiter status requires inspection: {STATUS}")
        state = {"schema_version": "matched-evaluator-b0-waiter-v1",
                 "status": "waiting", "started_at_utc": now(),
                 "gpu_work_started": False, "sla_capacity_confirmed": False,
                 "source_tmux": SOURCE_TMUX}
        save(state)
        try:
            deadline = time.monotonic() + args.wait_timeout_s
            last_reason = ""
            while time.monotonic() < deadline:
                checkpoint = json.loads(CHECKPOINT.read_text()) if CHECKPOINT.is_file() else None
                decision, reason = gate(checkpoint, tmux_alive=source_alive())
                if decision == "blocked":
                    raise RuntimeError(reason)
                if decision == "ready":
                    state["input_checkpoint_status"] = checkpoint["status"]
                    break
                if reason != last_reason:
                    state["waiting_for"] = reason
                    save(state)
                    print(f"{now()} waiting: {reason}", flush=True)
                    last_reason = reason
                time.sleep(15)
            else:
                raise TimeoutError("development inputs did not qualify within waiter deadline")
            # The B0 runner performs an independent read-only preflight and
            # GPU-idle check before it invokes iar. No failure is bypassed here.
            preflight_log = ARTIFACTS / "matched-evaluator-b0-waiter-preflight.log"
            if child("check", preflight_log, timeout_s=120) != 0:
                raise RuntimeError(f"matched evaluator B0 preflight blocked; inspect {preflight_log}")
            state["status"] = "running_matched_evaluator_b0"
            state["gpu_work_started"] = True
            save(state)
            run_log = ARTIFACTS / "matched-evaluator-b0-waiter-run.log"
            if child("run", run_log, timeout_s=21600) != 0:
                raise RuntimeError(f"matched evaluator B0 failed; inspect {run_log}")
            receipt = ARTIFACTS / "matched-evaluator-b0-receipt.json"
            result = json.loads(receipt.read_text())
            if result.get("status") != "matched_evaluator_b0_valid":
                raise RuntimeError("matched evaluator B0 receipt is absent or invalid")
            state["status"] = "matched_evaluator_b0_valid"
            state["receipt_path"] = str(receipt)
            state["cell_paths"] = {name: row["path"] for name, row in result["cells"].items()}
            save(state)
            return 0
        except Exception as exc:
            state["status"] = "blocked"
            state["error"] = f"{type(exc).__name__}: {exc}"
            save(state)
            raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Matched evaluator B0 waiter stopped: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
