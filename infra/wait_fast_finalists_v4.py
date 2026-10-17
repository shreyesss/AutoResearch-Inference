#!/usr/bin/env python3
"""Start the matched finalist follow-up only after the fast pilot succeeds."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / ".artifacts/fast-pilot-v4"
STATUS = PILOT / "finalist-waiter-status.json"
PILOT_STATUS = PILOT / "run-status.json"
FOLLOWUP = PILOT / "finalist-240"


def record(stage: str, **details: object) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    payload = {"stage": stage, "updated_at_utc": datetime.now(UTC).isoformat(), **details}
    temporary = STATUS.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(STATUS)


def main() -> int:
    if FOLLOWUP.exists():
        record("blocked", reason="finalist output already exists")
        return 1
    record("waiting_for_pilot")
    for _ in range(960):  # Eight hours maximum, at 30-second intervals.
        if PILOT_STATUS.is_file():
            pilot = json.loads(PILOT_STATUS.read_text())
            if pilot.get("status") == "blocked":
                record("blocked", reason="pilot blocked", pilot_error=pilot.get("error"))
                return 1
            if pilot.get("status") == "complete":
                break
        time.sleep(30)
    else:
        record("blocked", reason="pilot completion timeout")
        return 1
    check = subprocess.run(
        [str(ROOT / ".venv/bin/python"), str(ROOT / "infra/run_fast_finalists_v4.py"), "check"],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True, check=False)
    if check.returncode != 0:
        record("blocked", reason="finalist preflight failed", detail=check.stderr[-2000:])
        return 1
    record("running", preflight=json.loads(check.stdout))
    result = subprocess.run(
        ["docker", "exec", "-w", str(ROOT), "deploy-controller-1", "python",
         str(ROOT / "infra/run_fast_finalists_v4.py"), "run"],
        cwd=ROOT, check=False)
    record("complete" if result.returncode == 0 else "blocked",
           exit_code=result.returncode, output_dir=str(FOLLOWUP))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
