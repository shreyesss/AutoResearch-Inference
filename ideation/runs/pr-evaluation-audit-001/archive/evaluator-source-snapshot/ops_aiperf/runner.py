#!/usr/bin/env python3
"""Run isolated AIPerf workload suites against an already-running endpoint."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ops_aiperf.analyze import AnalysisError, analyze, find_export, write_score

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAMPAIGN = ROOT / "ops_aiperf/campaign.yaml"
WORKLOAD_ROOT = ROOT / "testing/workloads/aiperf"
WORKLOAD_FILES = {
    "chat": "synthetic-chat.yaml",
    "agent": "synthetic-agent.yaml",
    "code": "synthetic-code.yaml",
    "document": "synthetic-document.yaml",
    "mixed": "synthetic-mixed.yaml",
    "mixed-bursty": "synthetic-mixed-bursty.yaml",
    "mooncake-median": "production-mooncake-median.yaml",
    "mooncake-burst": "production-mooncake-burst.yaml",
    "mooncake-cache-heavy": "production-mooncake-cache-heavy.yaml",
    "exgentic": "production-exgentic.yaml",
    "agentx": "production-agentx.yaml",
}


class RunnerError(RuntimeError):
    """Raised when a workload cannot be planned or executed safely."""


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RunnerError(f"{path} must contain a mapping")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str, field: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise RunnerError(f"{field} contains unsafe characters: {value!r}")
    return value


def scaled_trace_path(source: Path, speedup: float) -> Path:
    label = f"{speedup:g}x".replace(".", "p")
    return source.parent.parent / "scaled" / label / source.name


def materialize_scaled_trace(
    source: Path,
    destination: Path,
    speedup: float,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = destination.with_suffix(".manifest.json")
    lock_path = destination.with_suffix(".lock")
    source_hash = sha256_file(source)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if destination.is_file() and manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                manifest.get("source_sha256") == source_hash
                and finite_number(manifest.get("speedup")) == speedup
                and manifest.get("output_sha256") == sha256_file(destination)
            ):
                return

        temporary = destination.with_name(
            f".{destination.name}.{os.getpid()}.tmp"
        )
        try:
            with source.open(encoding="utf-8") as source_handle, temporary.open(
                "w", encoding="utf-8"
            ) as output_handle:
                for line_number, line in enumerate(source_handle, start=1):
                    row = json.loads(line)
                    timestamp = finite_number(row.get("timestamp"))
                    if timestamp is None or timestamp < 0:
                        raise RunnerError(
                            f"{source}:{line_number}: invalid timestamp"
                        )
                    scaled = timestamp / speedup
                    row["timestamp"] = (
                        int(scaled) if scaled.is_integer() else scaled
                    )
                    output_handle.write(
                        json.dumps(row, separators=(",", ":")) + "\n"
                    )
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)

        manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source": str(source),
                    "source_sha256": source_hash,
                    "speedup": speedup,
                    "output": str(destination),
                    "output_sha256": sha256_file(destination),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if number == number and abs(number) != float("inf") else None


def sequence_distribution(config: dict[str, Any]) -> str:
    entries = []
    for item in config.get("pairs") or []:
        input_value = str(int(item["input"]))
        output_value = str(int(item["output"]))
        if item.get("input_stddev") is not None:
            input_value += f"|{int(item['input_stddev'])}"
        if item.get("output_stddev") is not None:
            output_value += f"|{int(item['output_stddev'])}"
        entries.append(
            f"{input_value},{output_value}:{float(item['weight']):g}"
        )
    if not entries:
        raise RunnerError("sequence_distribution workload has no pairs")
    return ";".join(entries)


def repetitions(campaign: dict[str, Any], phase: str) -> int:
    values = campaign["common"]["workload_repetitions"]
    return int(values[phase])


def goodput_spec(campaign: dict[str, Any], category: str) -> str:
    default = dict(campaign["slo"]["default"])
    default.update(campaign["slo"].get(category) or {})
    return " ".join(
        [
            f"time_to_first_token:{float(default['ttft_ms']):g}",
            "inter_token_latency:"
            f"{float(default['inter_token_latency_ms']):g}",
            f"request_latency:{float(default['request_latency_ms']):g}",
        ]
    )


def add_common_args(
    command: list[str],
    *,
    campaign: dict[str, Any],
    workload: dict[str, Any],
    args: argparse.Namespace,
    artifact_dir: Path,
) -> None:
    common = campaign["common"]
    command.extend(
        [
            "--model",
            args.model,
            "--tokenizer",
            args.tokenizer,
            "--tokenizer-revision",
            args.tokenizer_revision,
            "--url",
            args.base_url,
            "--endpoint-type",
            str(common["endpoint_type"]),
            "--streaming",
            "--use-server-token-count",
            "--per-chunk-usage",
            "--export-level",
            str(common["export_level"]),
            "--ui",
            str(common["ui"]),
            "--random-seed",
            str(workload.get("timing", {}).get("random_seed", args.random_seed)),
            "--num-profile-runs",
            str(repetitions(campaign, args.phase)),
            "--confidence-level",
            "0.95",
            "--goodput",
            goodput_spec(campaign, str(workload.get("category") or "default")),
            "--artifact-dir",
            str(artifact_dir),
        ]
    )
    if args.server_metrics_url:
        command.extend(["--server-metrics", args.server_metrics_url])
    if args.gpu_telemetry_url:
        command.extend(["--gpu-telemetry", args.gpu_telemetry_url])


def add_request_extras(command: list[str], workload: dict[str, Any]) -> None:
    request = workload.get("request") or {}
    extras = []
    if request.get("ignore_eos") is True:
        extras.append("ignore_eos:true")
    if request.get("thinking") is not None:
        extras.append(f"thinking:{str(bool(request['thinking'])).lower()}")
    if request.get("reasoning_effort"):
        extras.append(f"reasoning_effort:{request['reasoning_effort']}")
    if extras:
        command.extend(["--extra-inputs", *extras])


def build_command(
    *,
    campaign: dict[str, Any],
    workload: dict[str, Any],
    args: argparse.Namespace,
    artifact_dir: Path,
    data_root: Path,
) -> tuple[list[str], dict[str, str]]:
    command = [args.aiperf_bin, "profile"]
    environment: dict[str, str] = {}
    add_common_args(
        command,
        campaign=campaign,
        workload=workload,
        args=args,
        artifact_dir=artifact_dir,
    )
    add_request_extras(command, workload)
    dataset = workload["dataset"]
    timing = workload.get("timing") or {}
    kind = dataset["kind"]
    if args.trace_speedup is not None and kind != "mooncake_trace":
        raise RunnerError("--trace-speedup only applies to Mooncake traces")

    if workload["suite"] == "synthetic":
        if kind == "synthetic_text":
            command.extend(
                [
                    "--synthetic-input-tokens-mean",
                    str(dataset["input_tokens_mean"]),
                    "--synthetic-input-tokens-stddev",
                    str(dataset["input_tokens_stddev"]),
                    "--output-tokens-mean",
                    str(dataset["output_tokens_mean"]),
                    "--output-tokens-stddev",
                    str(dataset["output_tokens_stddev"]),
                    "--num-dataset-entries",
                    str(dataset["entries"]),
                ]
            )
        elif kind == "sequence_distribution":
            command.extend(
                [
                    "--sequence-distribution",
                    sequence_distribution(dataset),
                    "--num-dataset-entries",
                    str(dataset["entries"]),
                ]
            )
            if dataset.get("maximum_input_tokens"):
                command.extend(
                    ["--synthesis-max-isl", str(dataset["maximum_input_tokens"])]
                )
        else:
            raise RunnerError(f"unsupported synthetic dataset kind {kind!r}")

        command.extend(
            [
                "--benchmark-duration",
                str(args.duration),
                "--benchmark-grace-period",
                str(campaign["common"]["benchmark_grace_period_s"]),
            ]
        )
        if args.request_rate is not None:
            command.extend(["--request-rate", str(args.request_rate)])
            pattern = args.arrival_pattern or timing.get(
                "arrival_pattern", "poisson"
            )
            command.extend(["--arrival-pattern", str(pattern)])
            if pattern == "gamma":
                smoothness = (
                    args.arrival_smoothness
                    if args.arrival_smoothness is not None
                    else timing.get("arrival_smoothness", 1.0)
                )
                command.extend(["--arrival-smoothness", str(smoothness)])
        elif args.concurrency is not None:
            if timing.get("mode") == "request_rate":
                raise RunnerError(
                    f"{workload['name']} requires --request-rate"
                )
            command.extend(["--concurrency", str(args.concurrency)])
        else:
            raise RunnerError(
                "synthetic workloads require --concurrency or --request-rate"
            )
        command.extend(
            [
                "--warmup-duration",
                str(args.warmup_duration),
                "--warmup-grace-period",
                str(max(args.warmup_duration, 300)),
            ]
        )
    elif kind == "mooncake_trace":
        source_trace = data_root / str(dataset["path"])
        if not args.dry_run and not source_trace.is_file():
            raise RunnerError(
                f"missing {source_trace}; "
                "run ops_aiperf/prepare_mooncake.py --download"
            )
        trace = source_trace
        if args.trace_speedup is not None and args.trace_speedup != 1.0:
            trace = scaled_trace_path(source_trace, args.trace_speedup)
            if not args.dry_run:
                materialize_scaled_trace(
                    source_trace, trace, args.trace_speedup
                )
        workers_max = (
            args.workers_max
            if args.workers_max is not None
            else (campaign["production"].get("mooncake") or {}).get(
                "workers_max", 256
            )
        )
        command.extend(
            [
                "--input-file",
                str(trace),
                "--custom-dataset-type",
                "mooncake_trace",
                "--fixed-schedule",
                "--workers-max",
                str(workers_max),
                "--warmup-duration",
                str(args.warmup_duration),
                "--warmup-grace-period",
                str(max(args.warmup_duration, 300)),
            ]
        )
    elif kind == "public" and workload["name"] == "exgentic":
        command.extend(
            ["--public-dataset", str(dataset["public_dataset"])]
        )
        for key, value in sorted((dataset.get("filters") or {}).items()):
            command.extend(["--dataset-filter", f"{key}={value}"])
        command.extend(
            [
                "--num-conversations",
                str(dataset["conversations"]),
                "--fixed-schedule",
            ]
        )
    elif kind == "public" and workload["name"] == "agentx":
        command.extend(
            [
                "--scenario",
                str(timing["scenario"]),
                "--public-dataset",
                str(dataset["public_dataset"]),
                "--concurrency",
                str(timing["concurrency"]),
                "--benchmark-duration",
                str(timing["benchmark_duration_s"]),
                "--benchmark-grace-period",
                str(campaign["common"]["benchmark_grace_period_s"]),
                "--max-context-length",
                str(timing["max_context_length"]),
            ]
        )
        if timing.get("repeat_warmup"):
            command.append("--no-profile-run-disable-warmup-after-first")
        environment["AIPERF_HTTP_X_SESSION_ID_FROM_CORRELATION_ID"] = "1"
    else:
        raise RunnerError(
            f"unsupported production workload {workload['name']!r}"
        )
    return command, environment


def status(path: Path, state: str, message: str, **extra: Any) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": state,
                "message": message,
                "updated_at": datetime.now(UTC).isoformat(),
                **extra,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def git_state() -> tuple[str, bool]:
    revision = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    return revision or "unknown", dirty


def write_manifest(
    *,
    run_root: Path,
    campaign_path: Path,
    workload_path: Path,
    args: argparse.Namespace,
    command: list[str],
    environment: dict[str, str],
) -> None:
    revision, dirty = git_state()
    code_paths = [
        ROOT / "ops_aiperf/runner.py",
        ROOT / "ops_aiperf/analyze.py",
        ROOT / "ops_aiperf/prepare_mooncake.py",
    ]
    profile_hash = None
    if args.profile_path:
        profile = args.profile_path.expanduser().resolve()
        if profile.is_file():
            profile_hash = sha256_file(profile)
    manifest = {
        "schema_version": 1,
        "evidence_class": "aiperf_workload_suite",
        "candidate": args.candidate,
        "profile_label": args.profile_label,
        "profile_path": str(args.profile_path) if args.profile_path else None,
        "profile_sha256": profile_hash,
        "suite": args.suite,
        "workload": args.current_workload,
        "phase": args.phase,
        "base_url": args.base_url,
        "model": args.model,
        "tokenizer": args.tokenizer,
        "tokenizer_revision": args.tokenizer_revision,
        "selected_image": os.environ.get("VLLM_IMAGE"),
        "git_revision": revision,
        "git_dirty": dirty,
        "campaign_sha256": sha256_file(campaign_path),
        "workload_sha256": sha256_file(workload_path),
        "code_sha256": {
            str(path.relative_to(ROOT)): sha256_file(path)
            for path in code_paths
        },
        "aiperf_version": "0.13.0",
        "command": command,
        "environment": environment,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (run_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_root / "command.sh").write_text(
        " ".join(shlex.quote(value) for value in command) + "\n",
        encoding="utf-8",
    )


def latest_run(base: Path) -> Path | None:
    candidates = sorted((path for path in base.glob("*") if path.is_dir()), reverse=True)
    return candidates[0] if candidates else None


def deliver(run_root: Path, args: argparse.Namespace) -> bool:
    if args.no_sync:
        status(
            run_root / "delivery_status.json",
            "skipped",
            "S3 synchronization disabled",
        )
        return True
    bucket = os.environ.get("S3_BUCKET")
    if not bucket:
        status(
            run_root / "delivery_status.json",
            "failed",
            "S3_BUCKET is not set",
        )
        return False
    completed = subprocess.run(
        [
            "bash",
            str(ROOT / "ops/sync_to_s3.sh"),
            "--bucket",
            bucket,
            "--prefix",
            os.environ.get("S3_PREFIX", "deepseek-v4.1-flash"),
            "--execute",
            "--no-campaign",
        ],
        check=False,
        env=os.environ
        | {"DATA_ROOT": os.environ.get("MODEL_STORAGE_ROOT", "/models/deepseek-v4.1-flash")},
    )
    state = "complete" if completed.returncode == 0 else "failed"
    status(
        run_root / "delivery_status.json",
        state,
        "S3 synchronization finished",
        return_code=completed.returncode,
    )
    return completed.returncode == 0


def run_workload(
    *,
    campaign_path: Path,
    campaign: dict[str, Any],
    workload_name: str,
    args: argparse.Namespace,
    results_root: Path,
    data_root: Path,
) -> int:
    workload_path = WORKLOAD_ROOT / WORKLOAD_FILES[workload_name]
    workload = load_yaml(workload_path)
    if workload["suite"] != args.suite:
        raise RunnerError(
            f"{workload_name} belongs to suite {workload['suite']}, not {args.suite}"
        )
    args.current_workload = workload_name
    candidate = safe_name(args.candidate, "candidate")
    base = results_root / args.suite / workload_name / candidate
    run_root = latest_run(base) if args.resume else None
    if run_root is None:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        run_root = base / stamp
    artifact_dir = run_root / "artifacts"
    command, command_env = build_command(
        campaign=campaign,
        workload=workload,
        args=args,
        artifact_dir=artifact_dir,
        data_root=data_root,
    )
    plan = {
        "suite": args.suite,
        "workload": workload_name,
        "candidate": candidate,
        "command": command,
        "environment": command_env,
        "result_root": str(run_root),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return 0

    if not Path(args.aiperf_bin).is_file():
        raise RunnerError(
            f"missing pinned AIPerf binary {args.aiperf_bin}; "
            "run install/aiperf.sh"
        )
    run_root.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    command_path = run_root / "command.json"
    resolved = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.resume and command_path.is_file():
        if command_path.read_text(encoding="utf-8") != resolved:
            raise RunnerError(f"resume command mismatch under {run_root}")
    command_path.write_text(resolved, encoding="utf-8")
    write_manifest(
        run_root=run_root,
        campaign_path=campaign_path,
        workload_path=workload_path,
        args=args,
        command=command,
        environment=command_env,
    )
    score_path = run_root / "score.json"
    if args.resume and score_path.is_file():
        score = json.loads(score_path.read_text(encoding="utf-8"))
        return 0 if score.get("eligible") is True else 1

    status(run_root / "status.json", "running", "AIPerf workload started")
    environment = os.environ.copy()
    environment.update(command_env)
    with (run_root / "console.log").open("w", encoding="utf-8") as log:
        completed = subprocess.run(
            command,
            check=False,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            env=environment,
        )
    if completed.returncode != 0:
        status(
            run_root / "status.json",
            "failed",
            "AIPerf exited non-zero",
            return_code=completed.returncode,
        )
        deliver(run_root, args)
        return completed.returncode or 1

    try:
        export_path = find_export(artifact_dir)
        if not list(artifact_dir.rglob("profile_export.jsonl")):
            raise AnalysisError("AIPerf request record export is missing")
        score = analyze(
            export_path=export_path,
            campaign=campaign,
            workload=workload,
            candidate=candidate,
            phase=args.phase,
            node_cost_per_hour=args.node_cost_per_hour,
            artifact_root=artifact_dir,
        )
        write_score(score, score_path)
    except (AnalysisError, OSError, ValueError, KeyError) as exc:
        status(
            run_root / "status.json",
            "failed",
            f"analysis failed: {exc}",
        )
        deliver(run_root, args)
        return 1

    state = "complete" if score["eligible"] else "ineligible"
    status(
        run_root / "status.json",
        state,
        "AIPerf workload complete",
        eligible=score["eligible"],
    )
    delivered = deliver(run_root, args)
    return 0 if score["eligible"] and delivered else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, default=DEFAULT_CAMPAIGN)
    parser.add_argument("--suite", choices=("synthetic", "production"), required=True)
    parser.add_argument("--workload", default="all")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--profile-label", default="")
    parser.add_argument("--profile-path", type=Path)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--model", default=os.environ.get("SERVED_MODEL", "deepseek-v4.1-flash")
    )
    parser.add_argument(
        "--tokenizer",
        default=os.environ.get(
            "MODEL_LOCAL_DIR",
            os.environ.get("MODEL", "deepseek-ai/DeepSeek-V4.1-Flash"),
        ),
    )
    parser.add_argument(
        "--tokenizer-revision",
        default=os.environ.get(
            "MODEL_REVISION", "2cba9e42aa026125f3ed06c6d98c1db82f7ca027"
        ),
    )
    parser.add_argument(
        "--phase",
        choices=("discovery", "confirmation", "final"),
        default="discovery",
    )
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument("--concurrency", type=int)
    timing.add_argument("--request-rate", type=float)
    parser.add_argument(
        "--arrival-pattern", choices=("constant", "poisson", "gamma")
    )
    parser.add_argument("--arrival-smoothness", type=float)
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--warmup-duration", type=int, default=120)
    parser.add_argument("--workers-max", type=int)
    parser.add_argument(
        "--trace-speedup",
        type=float,
        help="Timestamp-only Mooncake compression (2 means twice the load)",
    )
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--server-metrics-url")
    parser.add_argument("--gpu-telemetry-url")
    parser.add_argument("--node-cost-per-hour", type=float, default=36.0)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument(
        "--aiperf-bin",
        default=str(ROOT / ".venv-aiperf/bin/aiperf"),
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-sync", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    campaign_path = args.campaign.expanduser().resolve()
    campaign = load_yaml(campaign_path)
    results_root = (
        args.results_root
        or Path(
            os.environ.get(
                "RESULTS_ROOT", "/models/deepseek-v4.1-flash/results"
            )
        )
        / campaign["results_subdirectory"]
    ).expanduser().resolve()
    data_root = (
        args.data_root
        or Path(
            os.environ.get(
                "AIPERF_DATA_ROOT",
                os.environ.get(
                    "MODEL_STORAGE_ROOT", "/models/deepseek-v4.1-flash"
                )
                + "/datasets/aiperf",
            )
        )
    ).expanduser().resolve()
    order = list(campaign[args.suite]["order"])
    workload_names = order if args.workload == "all" else [args.workload]
    unknown = [name for name in workload_names if name not in order]
    if unknown:
        raise RunnerError(
            f"unknown {args.suite} workloads: {', '.join(unknown)}"
        )
    if args.duration <= 0 or args.warmup_duration < 0:
        raise RunnerError("durations must be positive")
    if args.concurrency is not None and args.concurrency <= 0:
        raise RunnerError("--concurrency must be positive")
    if args.request_rate is not None and args.request_rate <= 0:
        raise RunnerError("--request-rate must be positive")
    if args.workers_max is not None and args.workers_max <= 0:
        raise RunnerError("--workers-max must be positive")
    if args.trace_speedup is not None and args.trace_speedup <= 0:
        raise RunnerError("--trace-speedup must be positive")

    if args.dry_run:
        return max(
            run_workload(
                campaign_path=campaign_path,
                campaign=campaign,
                workload_name=name,
                args=args,
                results_root=results_root,
                data_root=data_root,
            )
            for name in workload_names
        )

    results_root.mkdir(parents=True, exist_ok=True)
    lock_path = results_root / ".campaign.lock"
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RunnerError("another AIPerf campaign process is running") from exc
        return max(
            run_workload(
                campaign_path=campaign_path,
                campaign=campaign,
                workload_name=name,
                args=args,
                results_root=results_root,
                data_root=data_root,
            )
            for name in workload_names
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RunnerError, OSError, ValueError, KeyError) as exc:
        raise SystemExit(f"error: {exc}") from exc
