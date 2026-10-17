#!/usr/bin/env python3
"""Run one source-backed production input on the pinned Qwen B0 endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import yaml

from ops_b0_observe import GPURecorder


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
AIPERF = ROOT / ".venv/bin/aiperf"
SOURCE = ROOT / "configs/workloads/ops-aiperf-source"
ORIGINAL = ROOT / "Deepseek_serve/testing/workloads/aiperf"
MODEL = "Qwen/Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
MOONCAKE = ("mooncake-median", "mooncake-burst", "mooncake-cache-heavy")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(args: argparse.Namespace, target: Path) -> dict:
    path = SOURCE / f"production-{args.workload}.yaml"
    original = ORIGINAL / path.name
    if original.is_file() and sha(path) != sha(original):
        raise ValueError(f"ops_aiperf source changed: {original}")
    workload = yaml.safe_load(path.read_text())
    if workload["name"] != args.workload or workload["suite"] != "production":
        raise ValueError("snapshot identity mismatch")
    extra = {"chat_template_kwargs": {"enable_thinking": False}}
    if args.workload in MOONCAKE:
        extra.update({"temperature": 0, "ignore_eos": True})
    argv = ["profile", "--model", MODEL, "--endpoint-type", "chat",
            "--endpoint", "/v1/chat/completions", "--streaming",
            "--url", "127.0.0.1:8000", "--tokenizer", MODEL,
            "--tokenizer-revision", REVISION, "--apply-chat-template",
            "--use-server-token-count", "--per-chunk-usage",
            "--extra-inputs", json.dumps(extra, separators=(",", ":")),
            "--fixed-schedule", "--fixed-schedule-auto-offset",
            "--random-seed", "42", "--benchmark-grace-period", "300",
            "--export-level", "raw", "--export-http-trace",
            "--output-artifact-dir", str(target)]
    dataset = workload["dataset"]
    asset = None
    full_input_sha256 = None
    if args.workload in MOONCAKE:
        asset = (ROOT / ".artifacts/ops-aiperf-inputs/qwen-filtered" / dataset["path"]).resolve()
        if not asset.is_file():
            raise ValueError(f"missing Qwen-filtered Mooncake asset: {asset}")
        full_input_sha256 = sha(asset)
        if args.count is not None:
            # AIPerf 0.13 ignores --request-count for fixed-schedule Mooncake.
            # Materialize an explicitly labeled prefix input for transport
            # probes; never mistake it for the full production window.
            lines = [line for line in asset.read_bytes().splitlines(keepends=True) if line.strip()]
            if args.count <= 0 or args.count > len(lines):
                raise ValueError("invalid Mooncake prefix count")
            prefix = target.parent / "input-prefix.jsonl"
            prefix.write_bytes(b"".join(lines[:args.count]))
            asset = prefix
        argv += ["--input-file", str(asset), "--custom-dataset-type", "mooncake_trace"]
    elif args.workload == "exgentic":
        argv += ["--public-dataset", dataset["public_dataset"]]
        for key, value in sorted(dataset["filters"].items()):
            argv += ["--dataset-filter", f"{key}={value}"]
        argv += ["--num-conversations", str(args.conversations or dataset["conversations"])]
    else:
        raise ValueError(f"unsupported Qwen production workload: {args.workload}")
        if args.count is not None:
            raise ValueError("Exgentic fixed schedule needs a conversation subset, not request-count")
    if args.duration is not None:
        argv += ["--benchmark-duration", str(args.duration)]
    expected_count = args.count
    if expected_count is None and asset is not None:
        expected_count = sum(bool(line.strip()) for line in asset.open())
    if expected_count is None and args.workload == "exgentic" and args.conversations is None:
        expected_count = 894  # Pinned 48-conversation offline scan; verified again live.
    return {"workload": args.workload, "source_path": str(path.relative_to(ROOT)),
            "source_sha256": sha(path), "input_path": str(asset) if asset else None,
            "input_sha256": sha(asset) if asset else None,
            "full_input_sha256": full_input_sha256,
            "public_dataset_revision": ("4b8ad4ab198438e5a170f9171c19c6a2cf7c1814"
                                        if args.workload == "exgentic" else None),
            "qwen_adapter": extra,
            "request_count": expected_count,
            "request_count_override": args.count, "input_scope": "first_n_transport_probe" if args.count else "full_cohort",
            "duration_override_s": args.duration,
            "conversation_count_override": args.conversations,
            "readiness": "live_measurement_pending", "aiperf_args": argv}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", choices=(*MOONCAKE, "exgentic"), required=True)
    parser.add_argument("--cell", required=True)
    parser.add_argument("--count", type=int, help="Transport probe only; omit for full source cohort")
    parser.add_argument("--duration", type=float, help="Transport probe only; omit for full source cohort")
    parser.add_argument("--conversations", type=int, help="Exgentic transport probe only")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--server-container", default="iar-b0")
    parser.add_argument("--server-protocol", default="shared-pinned-b0-v1")
    parser.add_argument("--root", type=Path, default=ROOT / ".artifacts/ops-b0")
    args = parser.parse_args()
    cell = args.root.resolve() / args.cell
    if cell.exists():
        raise SystemExit(f"Refusing to reuse cell: {cell}")
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
        if response.status != 200:
            raise SystemExit("B0 health check failed")
    cell.mkdir(parents=True)
    target = cell / "aiperf"
    plan = build(args, target)
    target.mkdir()
    plan.update({"cell": args.cell, "server_protocol": args.server_protocol,
                 "server_container": args.server_container,
                 "started_at": datetime.now(UTC).isoformat()})
    (cell / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (target / "plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (cell / "server-inspect.json").write_text(subprocess.run(
        ["docker", "inspect", args.server_container], check=True, capture_output=True, text=True).stdout)
    telemetry = ["nvidia-smi", "--query-gpu=timestamp,uuid,memory.used,utilization.gpu,power.draw",
                 "--format=csv,noheader"]
    (cell / "gpu-before.csv").write_text(subprocess.run(
        telemetry, check=True, capture_output=True, text=True).stdout)
    cache = subprocess.run([str(ROOT / "infra/prepare-aiperf-tokenizer-cache.sh")],
                           check=True, capture_output=True, text=True, cwd=ROOT).stdout.strip()
    env = os.environ | {"HF_HUB_CACHE": cache, "TRANSFORMERS_OFFLINE": "1"}
    # Mooncake is entirely local. Exgentic's public loader needs its pinned
    # Hugging Face corpus in this cache and may download it on first use.
    if args.workload in MOONCAKE:
        env["HF_HUB_OFFLINE"] = "1"
    else:
        env.pop("HF_HUB_OFFLINE", None)
        env.pop("TRANSFORMERS_OFFLINE", None)
    start = time.monotonic()
    with GPURecorder(cell / "gpu-series.csv"), (cell / "console.log").open("w") as stream:
        try:
            result = subprocess.run([str(AIPERF), *plan["aiperf_args"]], cwd=ROOT,
                                    env=env, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=args.timeout, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = -1
    status = {"aiperf_exit_code": code, "elapsed_s": time.monotonic() - start,
              "finished_at": datetime.now(UTC).isoformat()}
    (cell / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    (cell / "gpu-after.csv").write_text(subprocess.run(
        telemetry, check=True, capture_output=True, text=True).stdout)
    server_logs = subprocess.run(
        ["docker", "logs", "--since", plan["started_at"], args.server_container],
        check=False, capture_output=True, text=True)
    (cell / "server.log").write_text(server_logs.stdout + server_logs.stderr)
    if code:
        print(json.dumps(status), file=sys.stderr)
        return code if code > 0 else 1
    result = subprocess.run([str(PYTHON), str(ROOT / "infra/analyze-ops-b0.py"),
                             str(target)], cwd=ROOT, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
