#!/usr/bin/env python3
"""GPU-free preflight or one-shot Docker launch for the exploratory v4 pilot.

Run `check` before launch. `run` executes the trusted controller inside the
already configured container; never invoke a second copy while one is active.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from inference_autoresearch.search.fast_pilot import CAMPAIGN_ID, preflight, run
from run_v3_candidate_search import controller_runtime_pin


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".artifacts/fast-pilot-v4"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "run"))
    parser.add_argument("--inside-controller", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.action == "check":
        ready = preflight(ROOT, OUT)
        print(json.dumps({"status": ready["status"], "campaign_id": CAMPAIGN_ID,
                          "b0_sha256": ready["b0_sha256"],
                          "screen_manifest_sha256": ready["screen_manifest_sha256"],
                          "rate_rps": 0.4, "proposal_attempt_budget": 8,
                          "capacity_confirmed": False}, indent=2))
        return 0
    # In the controller container the repository and artifact directory are
    # mounted separately; Docker server control is available only there.
    if not args.inside_controller:
        if any((OUT / name).exists() for name in
               ("pilot-campaign-lock.json", "run-status.json", "proposals", "ledger.sqlite")):
            raise RuntimeError("pilot has already started; inspect artifacts before another run")
        OUT.mkdir(parents=True, exist_ok=True)
        pin = controller_runtime_pin()
        (OUT / "controller-image-pin.json").write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n")
        command = ["docker", "exec", "-w", str(ROOT), "deploy-controller-1",
                   "python", str(Path(__file__).resolve()), "run", "--inside-controller"]
        return subprocess.run(command, check=False).returncode
    print(json.dumps(run(ROOT, OUT), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"fast pilot blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
