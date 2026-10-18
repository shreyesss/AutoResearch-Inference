#!/usr/bin/env python3
"""Observe the detached v4 pilot and fail a stale status if its process dies."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".artifacts/fast-pilot-v4"
PILOT_STATUS = OUT / "run-status.json"
MONITOR_STATUS = OUT / "pilot-monitor-status.json"

PROCESS_CHECK = r"""
from pathlib import Path
import os
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit() or int(proc.name) == os.getpid():
        continue
    try:
        parts = (proc / 'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        continue
    if any(part.endswith(b'/infra/run_fast_pilot_v4.py') for part in parts) and b'--inside-controller' in parts:
        print(proc.name)
        break
"""

MARK_BLOCKED = r"""
import json
from datetime import datetime, timezone
from pathlib import Path
p = Path('/home/ubuntu/shreyas/skunk-work/.artifacts/fast-pilot-v4/run-status.json')
state = json.loads(p.read_text())
if state.get('status') == 'running':
    state.update(status='blocked', stage='blocked',
                 error='Controller pilot process exited before completion',
                 updated_at_utc=datetime.now(timezone.utc).isoformat())
    tmp = p.with_suffix('.json.monitor-tmp')
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')
    tmp.replace(p)
"""


def record(stage: str, **details: object) -> None:
    payload = {"stage": stage, "updated_at_utc": datetime.now(UTC).isoformat(), **details}
    tmp = MONITOR_STATUS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(MONITOR_STATUS)
    print(json.dumps(payload), flush=True)


def controller_pid() -> str | None:
    result = subprocess.run(
        ["docker", "exec", "deploy-controller-1", "python", "-c", PROCESS_CHECK],
        capture_output=True, text=True, check=False, timeout=15)
    if result.returncode != 0:
        raise RuntimeError(f"controller probe failed: {result.stderr[-500:]}")
    return result.stdout.strip() or None


def main() -> int:
    absent = 0
    while True:
        state = json.loads(PILOT_STATUS.read_text())
        if state.get("status") in {"complete", "blocked"}:
            record(state["status"], pilot_status=state)
            return 0 if state["status"] == "complete" else 1
        try:
            pid = controller_pid()
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            record("probe_error", error=str(exc))
            time.sleep(30)
            continue
        if pid:
            absent = 0
            record("pilot_alive", controller_pid=pid, pilot_stage=state.get("stage"),
                   completed_candidate_screens=state.get("completed_candidate_screens", 0))
        else:
            absent += 1
            record("pilot_process_absent", consecutive_checks=absent)
            if absent >= 2:
                result = subprocess.run(
                    ["docker", "exec", "deploy-controller-1", "python", "-c", MARK_BLOCKED],
                    capture_output=True, text=True, check=False, timeout=15)
                if result.returncode != 0:
                    record("mark_blocked_failed", detail=result.stderr[-500:])
                    return 1
                record("blocked_stale_pilot")
                return 1
        time.sleep(30)


if __name__ == "__main__":
    raise SystemExit(main())
