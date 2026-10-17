#!/usr/bin/env python3
"""Execute one measured ops_aiperf load against the pinned, running Qwen B0."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from ops_b0_observe import GPURecorder


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
AIPERF = ROOT / ".venv/bin/aiperf"


def command(args: argparse.Namespace, artifact_dir: Path) -> dict:
    planner = [str(PYTHON), str(ROOT / "infra/prepare-ops-synthetic-inputs.py"),
               "--workload", args.workload, "--request-rate", str(args.rate),
               "--request-count", str(args.count), "--duration", str(args.duration),
               "--random-seed", str(args.random_seed),
               "--artifact-root", str(artifact_dir.parent)]
    if args.dataset_entries is not None:
        planner += ["--dataset-entries", str(args.dataset_entries)]
    result = subprocess.run(planner, check=True, capture_output=True, text=True, cwd=ROOT)
    return json.loads(result.stdout)[args.workload]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True,
                        choices=("chat", "agent", "code", "document", "mixed", "mixed-bursty"))
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--dataset-entries", type=int,
                        help="Calibration-only generated pool override; recorded in plan")
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--random-seed", type=int, default=42,
                        help="Independent content and arrival seed; default preserves historical B0")
    parser.add_argument("--timeout", type=float, default=900,
                        help="Wall-clock safety limit for one AIPerf process")
    parser.add_argument("--cell", required=True, help="Unique output cell name")
    parser.add_argument("--root", type=Path, default=ROOT / ".artifacts/ops-b0")
    args = parser.parse_args()
    cell = args.root.resolve() / args.cell
    if cell.exists():
        raise SystemExit(f"Refusing to reuse cell: {cell}")
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
        if response.status != 200:
            raise SystemExit("B0 health check failed")
    cell.mkdir(parents=True)
    plan = command(args, cell / "aiperf" / args.workload)
    plan.update({"cell": args.cell, "workload": args.workload, "request_count": args.count,
                 "duration_s": args.duration, "offered_rps": args.rate,
                 "server_protocol": "shared-pinned-b0-v1",
                 "started_at": datetime.now(UTC).isoformat()})
    # The planner's artifact path is under cell/aiperf/<workload>; analysis
    # consumes files there while plan/status live in the cell root too.
    target = cell / "aiperf" / args.workload
    target.mkdir(parents=True)
    (cell / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (target / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (cell / "server-inspect.json").write_text(subprocess.run(
        ["docker", "inspect", "iar-b0"], check=True, capture_output=True, text=True).stdout)
    telemetry = ["nvidia-smi", "--query-gpu=timestamp,uuid,memory.used,utilization.gpu,power.draw",
                 "--format=csv,noheader"]
    (cell / "gpu-before.csv").write_text(subprocess.run(
        telemetry, check=True, capture_output=True, text=True).stdout)
    cache = subprocess.run([str(ROOT / "infra/prepare-aiperf-tokenizer-cache.sh")],
                           check=True, capture_output=True, text=True, cwd=ROOT).stdout.strip()
    env = os.environ | {"HF_HUB_CACHE": cache, "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1"}
    start = time.monotonic()
    with GPURecorder(cell / "gpu-series.csv"), (cell / "console.log").open("w") as stream:
        try:
            completed = subprocess.run([str(AIPERF), *plan["aiperf_args"]], cwd=ROOT,
                                       env=env, stdout=stream, stderr=subprocess.STDOUT,
                                       timeout=args.timeout, check=False)
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            exit_code = -1
    status = {"aiperf_exit_code": exit_code,
              "elapsed_s": time.monotonic() - start,
              "finished_at": datetime.now(UTC).isoformat()}
    (cell / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    (cell / "gpu-after.csv").write_text(subprocess.run(
        telemetry, check=True, capture_output=True, text=True).stdout)
    server_logs = subprocess.run(
        ["docker", "logs", "--since", plan["started_at"], "iar-b0"],
        check=False, capture_output=True, text=True)
    (cell / "server.log").write_text(server_logs.stdout + server_logs.stderr)
    if exit_code:
        print(json.dumps(status), file=sys.stderr)
        return exit_code if exit_code > 0 else 1
    analysis = subprocess.run([str(PYTHON), str(ROOT / "infra/analyze-ops-b0.py"),
                               str(target)], cwd=ROOT, check=False)
    return analysis.returncode


if __name__ == "__main__":
    raise SystemExit(main())
