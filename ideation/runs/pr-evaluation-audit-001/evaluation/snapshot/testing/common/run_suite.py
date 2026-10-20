#!/usr/bin/env python3
from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=env)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hardware", choices=["h200", "b200"], required=True)
    parser.add_argument("--engine", choices=["vllm", "sglang", "tensorrt"], required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--workload", type=Path, required=True)
    parser.add_argument("--case", action="append")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--requests", type=int, default=128)
    parser.add_argument("--screen-duration", type=float, default=30)
    parser.add_argument("--boundary-duration", type=float, default=30)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--closed-duration", type=float)
    parser.add_argument("--open-duration", type=float)
    parser.add_argument("--request-timeout", type=float, default=600)
    parser.add_argument(
        "--search-mode",
        choices=["slo-capacity", "offline-throughput"],
        default="slo-capacity",
    )
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--aiperf-crosscheck", action="store_true")
    parser.add_argument("--no-telemetry", action="store_true")
    parser.add_argument("--engine-metrics-url", action="append", default=[])
    args = parser.parse_args()

    config = yaml.safe_load(args.workload.read_text())
    if args.aiperf_crosscheck and config.get("name") == "ragged-mix":
        raise SystemExit(
            "AIPerf single-turn conversion cannot preserve ragged prefix "
            "system messages; use the native load generator"
        )
    minimum_requests = int(config.get("minimum_requests", 1))
    effective_requests = max(args.requests, minimum_requests)
    available = [str(item["name"]) for item in config["cases"]]
    cases = args.case or available
    unknown = sorted(set(cases) - set(available))
    if unknown:
        raise SystemExit(f"unknown workload cases: {unknown}")

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    results_root = args.results_root or Path(
        os.environ.get("RESULTS_ROOT", ROOT / "results")
    )
    run_root = (
        results_root
        / args.hardware
        / args.engine
        / args.profile
        / args.workload.stem
        / timestamp
    )
    run_root.mkdir(parents=True, exist_ok=False)

    profile_path = (
        ROOT
        / "serving"
        / args.hardware
        / args.engine
        / "profiles"
        / f"{args.profile}.yaml"
    )
    images_path = profile_path.parents[1] / "images.yaml"
    profile_payload = yaml.safe_load(profile_path.read_text())
    images_payload = yaml.safe_load(images_path.read_text())
    image_override = os.environ.get(f"{args.engine.upper()}_IMAGE")
    selected_image = image_override or images_payload.get("default")
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": timestamp,
        "instrumentation": (
            "offline-throughput-clean"
            if args.search_mode == "offline-throughput"
            else "capacity-clean"
        ),
        "search_mode": args.search_mode,
        "hardware": args.hardware,
        "engine": args.engine,
        "profile": args.profile,
        "stage": os.environ.get("TRTLLM_STAGE"),
        "workload": str(args.workload.resolve()),
        "workload_sha256": sha256(args.workload),
        "profile_sha256": sha256(profile_path),
        "images_sha256": sha256(images_path),
        "selected_image": selected_image,
        "image_source_commit": (images_payload.get("source_commit") or {}).get(
            "default"
        ),
        "deployment": {
            "topology": profile_payload.get("topology"),
            "replicas": profile_payload.get("replicas"),
            "scheduler": profile_payload.get("scheduler"),
            "features": profile_payload.get("features"),
            "experiments": os.environ.get("EXPERIMENTS", "").split(),
        },
        "model": os.environ.get("MODEL"),
        "model_revision": os.environ.get("MODEL_REVISION"),
        "base_url": args.base_url,
        "started_at": datetime.now(UTC).isoformat(),
        "cases": cases,
        "workload_generation": {
            "requested_records": args.requests,
            "effective_records": effective_requests,
            "minimum_records": minimum_requests,
            "mix_weights_percent": config.get("mix_weights_percent"),
            "ignore_eos": (config.get("defaults") or {}).get(
                "ignore_eos", False
            ),
            "min_tokens": (config.get("defaults") or {}).get("min_tokens"),
        },
        "slo": {
            "applied": args.search_mode == "slo-capacity",
            "ttft_p95_ms": float(os.environ.get("SLO_TTFT_P95_MS", "2000")),
            "tpot_p95_ms": float(os.environ.get("SLO_TPOT_P95_MS", "50")),
            "error_rate": float(os.environ.get("SLO_ERROR_RATE", "0.001")),
            "think_time_s": float(os.environ.get("USER_THINK_TIME_S", "10")),
        },
    }
    if selected_image:
        try:
            inspect = subprocess.run(
                ["docker", "image", "inspect", "--format", "{{.Id}}", selected_image],
                capture_output=True,
                text=True,
                check=True,
            )
            manifest["local_image_id"] = inspect.stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            manifest["local_image_id_error"] = str(exc)
    try:
        gpu_query = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,uuid,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        manifest["gpus"] = gpu_query.stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        manifest["gpu_query_error"] = str(exc)
    (run_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    telemetry_process: subprocess.Popen[Any] | None = None

    def stop_telemetry() -> None:
        nonlocal telemetry_process
        if telemetry_process is None or telemetry_process.poll() is not None:
            return
        telemetry_process.terminate()
        try:
            telemetry_process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            telemetry_process.kill()
            telemetry_process.wait()

    atexit.register(stop_telemetry)
    if not args.no_telemetry:
        metrics_urls = args.engine_metrics_url or [
            f"http://127.0.0.1:{replica['port']}/metrics"
            for replica in profile_payload.get("replicas", [])
        ]
        if not metrics_urls:
            metrics_urls = [args.base_url.removesuffix("/v1") + "/metrics"]
        telemetry_command = [
            sys.executable,
            str(ROOT / "testing/telemetry/collector.py"),
            "--output-dir",
            str(run_root / "telemetry"),
        ]
        for metrics_url in metrics_urls:
            telemetry_command.extend(["--engine-metrics-url", metrics_url])
        if os.environ.get("DCGM_METRICS_URL"):
            telemetry_command.extend(
                ["--dcgm-metrics-url", os.environ["DCGM_METRICS_URL"]]
            )
        telemetry_process = subprocess.Popen(telemetry_command)

    if not args.skip_smoke:
        run(
            [
                sys.executable,
                str(ROOT / "testing/common/smoke.py"),
                "--base-url",
                args.base_url,
                "--model",
                os.environ.get("SERVED_MODEL", "deepseek-v4.1-flash"),
                "--output",
                str(run_root / "smoke.json"),
            ]
        )

    env = os.environ.copy()
    completed_cases: list[str] = []
    for case in cases:
        case_root = run_root / case
        case_root.mkdir()
        dataset = case_root / "dataset.jsonl"
        run(
            [
                sys.executable,
                str(ROOT / "testing/common/generate_workload.py"),
                "--config",
                str(args.workload),
                "--case",
                case,
                "--requests",
                str(effective_requests),
                "--output",
                str(dataset),
            ],
            env=env,
        )
        if args.aiperf_crosscheck:
            aiperf_env = env | {
                "DATASET": str(dataset),
                "OUTPUT_DIR": str(case_root / "aiperf"),
                "BASE_URL": args.base_url.removesuffix("/v1"),
                "MODEL_NAME": os.environ.get(
                    "SERVED_MODEL", "deepseek-v4.1-flash"
                ),
                "MODE": "closed",
                "CONCURRENCY": "64",
                "DURATION": str(args.screen_duration),
                "WARMUP_DURATION": "30",
            }
            run(
                ["bash", str(ROOT / "testing/common/run_aiperf.sh")],
                env=aiperf_env,
            )
        result_directory = (
            case_root / "throughput"
            if args.search_mode == "offline-throughput"
            else case_root / "capacity"
        )
        search_command = [
                sys.executable,
                str(ROOT / "testing/common/capacity_search.py"),
                "--search-mode",
                args.search_mode,
                "--dataset",
                str(dataset),
                "--base-url",
                args.base_url,
                "--model",
                os.environ.get("SERVED_MODEL", "deepseek-v4.1-flash"),
                "--results",
                str(result_directory),
                "--screen-duration",
                str(args.screen_duration),
                "--boundary-duration",
                str(args.boundary_duration),
                "--repetitions",
                str(args.repetitions),
                "--slo-ttft-p95-ms",
                os.environ.get("SLO_TTFT_P95_MS", "2000"),
                "--slo-tpot-p95-ms",
                os.environ.get("SLO_TPOT_P95_MS", "50"),
                "--slo-error-rate",
                os.environ.get("SLO_ERROR_RATE", "0.001"),
                "--think-time",
                os.environ.get("USER_THINK_TIME_S", "10"),
                "--timeout",
                str(args.request_timeout),
            ]
        if args.closed_duration is not None:
            search_command.extend(
                ["--closed-duration", str(args.closed_duration)]
            )
        if args.open_duration is not None:
            search_command.extend(["--open-duration", str(args.open_duration)])
        if os.environ.get("CLOSED_CONCURRENCIES"):
            search_command.extend(
                ["--closed-concurrencies", os.environ["CLOSED_CONCURRENCIES"]]
            )
        if os.environ.get("OPEN_CONCURRENCY"):
            search_command.extend(
                ["--open-concurrency", os.environ["OPEN_CONCURRENCY"]]
            )
        if args.search_mode == "offline-throughput":
            search_command.extend(
                [
                    "--maximum-error-rate",
                    os.environ.get("OFFLINE_MAX_ERROR_RATE", "0.005"),
                    "--maximum-osl-shortfall-rate",
                    os.environ.get("OFFLINE_MAX_OSL_SHORTFALL_RATE", "0.01"),
                    "--minimum-server-usage-fraction",
                    os.environ.get("OFFLINE_MIN_SERVER_USAGE_FRACTION", "0.99"),
                ]
            )
        run(search_command, env=env)
        completed_cases.append(case)

    marker = {
        "schema_version": 1,
        "clean_run_complete": True,
        "manifest": str(run_root / "manifest.json"),
        "completed_cases": completed_cases,
        "search_mode": args.search_mode,
        "completed_at": datetime.now(UTC).isoformat(),
    }
    stop_telemetry()
    (run_root / "clean_complete.json").write_text(json.dumps(marker, indent=2) + "\n")
    print(f"Clean suite complete: {run_root}")


if __name__ == "__main__":
    main()
