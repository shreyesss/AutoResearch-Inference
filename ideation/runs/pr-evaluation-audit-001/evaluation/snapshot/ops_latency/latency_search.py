#!/usr/bin/env python3
"""Run latency-only rate/concurrency screens and post-process each completed run.

The existing load generator remains a separate subprocess. Analysis starts
only after that process exits and its artifacts are closed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from .analyze_latency import (
        AnalysisError,
        analyze,
        load_slo_config,
        read_json,
        read_records,
    )
except ImportError:  # Direct script execution.
    from analyze_latency import (
        AnalysisError,
        analyze,
        load_slo_config,
        read_json,
        read_records,
    )


ROOT = Path(__file__).resolve().parents[1]
LOADGEN = ROOT / "testing/common/loadgen.py"


class SearchError(RuntimeError):
    """Raised when a latency-only search cannot continue safely."""


def parse_numbers(value: str, *, integer: bool = False) -> list[float | int]:
    values: list[float | int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            parsed: float | int = int(item) if integer else float(item)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid numeric value {item!r}") from exc
        numeric = float(parsed)
        if not math.isfinite(numeric) or numeric <= 0:
            raise argparse.ArgumentTypeError("values must be positive and finite")
        values.append(parsed)
    if not values:
        raise argparse.ArgumentTypeError("at least one value is required")
    if [float(item) for item in values] != sorted(
        {float(item) for item in values}
    ):
        raise argparse.ArgumentTypeError("values must be unique and increasing")
    return values


def safe_output_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if "latency-campaign" not in resolved.parts:
        raise SearchError(
            "results path must contain a 'latency-campaign' directory segment"
        )
    return resolved


def rate_label(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".").replace(".", "_")


def run_id(
    *,
    mode: str,
    value: float | int,
    repetition: int,
) -> str:
    if mode == "open":
        return f"open-r{rate_label(float(value))}-rep{repetition}"
    return f"closed-c{int(value)}-rep{repetition}"


def scrape_metrics(urls: Sequence[str], output: Path) -> None:
    lines: list[str] = []
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                payload = response.read().decode("utf-8", errors="replace")
        except (OSError, urllib.error.URLError) as exc:
            payload = f"# scrape_error {type(exc).__name__}: {exc}\n"
        lines.append(f"# source {url}\n{payload.rstrip()}\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def make_command(
    *,
    args: argparse.Namespace,
    dataset: Path,
    output_dir: Path,
    value: float | int,
    seed: int,
) -> list[str]:
    concurrency = (
        args.open_concurrency if args.mode == "open" else int(value)
    )
    # One Python client process saturated near 40 req/s in the B200 campaign.
    # Closed-loop points can opt into independent load-generator processes
    # without changing the default path or any open-loop behavior.
    shards = int(os.environ.get("LATENCY_LOADGEN_SHARDS", "1") or 1)
    if args.mode == "closed" and shards > 1:
        if concurrency % shards:
            raise SearchError(
                f"closed-loop concurrency {concurrency} must be divisible "
                f"by LATENCY_LOADGEN_SHARDS={shards}"
            )
        return [
            sys.executable,
            str(LOADGEN.with_name("loadgen_shards.py")),
            "--dataset",
            str(dataset),
            "--base-urls",
            args.base_url,
            "--model",
            args.model,
            "--concurrency",
            str(concurrency),
            "--shards",
            str(shards),
            "--duration",
            str(args.duration),
            "--timeout",
            str(args.timeout),
            "--max-requests",
            str(args.max_requests),
            "--seed",
            str(seed),
            "--output-dir",
            str(output_dir),
        ]
    command = [
        sys.executable,
        str(LOADGEN),
        "--dataset",
        str(dataset),
        "--base-url",
        args.base_url,
        "--model",
        args.model,
        "--mode",
        args.mode,
        "--concurrency",
        str(concurrency),
        "--duration",
        str(args.duration),
        "--max-requests",
        str(args.max_requests),
        "--output-dir",
        str(output_dir),
        "--timeout",
        str(args.timeout),
        "--seed",
        str(seed),
    ]
    if args.mode == "open":
        command.extend(["--request-rate", f"{float(value):.9g}"])
    return command


def dataset_for_run(args: argparse.Namespace, identifier: str) -> Path:
    if args.dataset_dir is not None:
        dataset = args.dataset_dir.expanduser().resolve() / f"{identifier}.jsonl"
    else:
        dataset = args.dataset.expanduser().resolve()
    if not args.plan and not dataset.is_file():
        raise SearchError(f"{identifier}: missing dataset {dataset}")
    return dataset


def validate_unique_request_dataset(
    summary: Mapping[str, Any],
    *,
    identifier: str,
    required: bool,
) -> None:
    scheduled = summary.get("scheduled")
    dataset_requests = summary.get("dataset_requests")
    if (
        required
        and isinstance(scheduled, int)
        and isinstance(dataset_requests, int)
        and scheduled > dataset_requests
    ):
        raise SearchError(
            f"{identifier}: scheduled {scheduled} requests from a "
            f"{dataset_requests}-request dataset; repeated prompts would "
            "invalidate cache measurements"
        )


def tier_passes(analysis: Mapping[str, Any], tier: str) -> bool:
    tiers = analysis.get("slo_tiers")
    if not isinstance(tiers, Mapping):
        return False
    value = tiers.get(tier)
    return isinstance(value, Mapping) and value.get("pass") is True


def measured_rps(summary: Mapping[str, Any]) -> float | None:
    value = summary.get("request_rps")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        result = float(value)
        return result if math.isfinite(result) else None
    return None


def execute(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    results = safe_output_root(args.results)
    runs_dir = results / "runs"
    slo_config = load_slo_config(args.slo_config)
    tiers = list((slo_config or {}).get("slo_tiers", {}))
    values: Sequence[float | int] = (
        args.rates if args.mode == "open" else args.concurrencies
    )
    if not values:
        raise SearchError(f"{args.mode} mode has no configured load points")

    planned: list[dict[str, Any]] = []
    run_references: list[dict[str, Any]] = []
    observations: dict[float, list[dict[str, Any]]] = {}
    counter = 0
    repetition_stop = args.repetition_start + args.repetitions
    for value in values:
        for repetition in range(args.repetition_start, repetition_stop):
            counter += 1
            identifier = run_id(
                mode=args.mode, value=value, repetition=repetition
            )
            output_dir = runs_dir / identifier
            dataset = dataset_for_run(args, identifier)
            command = make_command(
                args=args,
                dataset=dataset,
                output_dir=output_dir,
                value=value,
                seed=args.seed + counter,
            )
            planned.append(
                {
                    "id": identifier,
                    "command": command,
                    "analysis": str(output_dir / "latency_analysis.json"),
                }
            )
            if args.plan:
                continue

            output_dir.mkdir(parents=True, exist_ok=True)
            summary_path = output_dir / "summary.json"
            requests_path = output_dir / "requests.jsonl"
            analysis_path = output_dir / "latency_analysis.json"
            if (
                args.resume
                and summary_path.is_file()
                and requests_path.is_file()
                and analysis_path.is_file()
            ):
                summary = read_json(summary_path)
                analysis_result = read_json(analysis_path)
                return_code: int | None = None
                reused = True
            else:
                scrape_metrics(
                    args.metrics_url, output_dir / "metrics-before.txt"
                )
                completed = subprocess.run(
                    command,
                    check=False,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=max(
                        120.0,
                        args.duration + 2.0 * args.timeout + 90.0,
                    ),
                )
                (output_dir / "loadgen.log").write_text(
                    completed.stdout, encoding="utf-8"
                )
                scrape_metrics(
                    args.metrics_url, output_dir / "metrics-after.txt"
                )
                return_code = completed.returncode
                reused = False
                if return_code not in {0, 1}:
                    raise SearchError(
                        f"{identifier}: load generator exited {return_code}"
                    )
                if not summary_path.is_file() or not requests_path.is_file():
                    raise SearchError(
                        f"{identifier}: load generator did not write complete artifacts"
                    )
                summary = read_json(summary_path)
                analysis_result = analyze(
                    records=read_records(requests_path),
                    summary=summary,
                    slo_config=slo_config,
                    source_requests=str(requests_path),
                    source_summary=str(summary_path),
                )
                analysis_path.write_text(
                    json.dumps(analysis_result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

            validate_unique_request_dataset(
                summary,
                identifier=identifier,
                required=args.require_unique_requests,
            )

            reference = {
                "id": identifier,
                "mode": args.mode,
                "configured_rate": (
                    float(value) if args.mode == "open" else None
                ),
                "configured_concurrency": (
                    args.open_concurrency
                    if args.mode == "open"
                    else int(value)
                ),
                "repetition": repetition,
                "pass_phase": args.phase,
                "return_code": return_code,
                "reused": reused,
                "summary": str(summary_path.relative_to(results)),
                "requests": str(requests_path.relative_to(results)),
                "analysis": str(analysis_path.relative_to(results)),
                "dataset": str(dataset),
                "request_rps": measured_rps(summary),
                "tier_pass": {
                    tier: tier_passes(analysis_result, tier) for tier in tiers
                },
            }
            run_references.append(reference)
            observations.setdefault(float(value), []).append(reference)

    if args.plan:
        result = {
            "schema_version": 1,
            "plan": True,
            "mode": args.mode,
            "results": str(results),
            "runs": planned,
        }
        print(json.dumps(result, indent=2))
        return result, 0

    highest: dict[str, dict[str, float] | None] = {}
    for tier in tiers:
        passing = []
        for value, references in observations.items():
            if len(references) != args.repetitions:
                continue
            if all(
                reference["tier_pass"].get(tier) is True
                for reference in references
            ):
                rps_values = [
                    reference["request_rps"]
                    for reference in references
                    if isinstance(reference.get("request_rps"), (int, float))
                ]
                passing.append(
                    {
                        "load_point": value,
                        "mean_completed_rps": (
                            sum(rps_values) / len(rps_values)
                            if rps_values
                            else 0.0
                        ),
                    }
                )
        highest[tier] = (
            max(passing, key=lambda item: item["load_point"])
            if passing
            else None
        )

    result = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "evidence_class": "latency_campaign_rate_screen",
        "mode": args.mode,
        "dataset": (
            str(args.dataset.expanduser().resolve())
            if args.dataset is not None
            else None
        ),
        "dataset_dir": (
            str(args.dataset_dir.expanduser().resolve())
            if args.dataset_dir is not None
            else None
        ),
        "base_url": args.base_url,
        "model": args.model,
        "duration_s": args.duration,
        "repetitions": args.repetitions,
        "repetition_start": args.repetition_start,
        "pass_phase": args.phase,
        "slo_config": str(args.slo_config.expanduser().resolve()),
        "highest_passing": highest,
        "run_references": run_references,
    }
    results.mkdir(parents=True, exist_ok=True)
    (results / "latency_search_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return result, 0


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run fixed latency load points and classify completed artifacts "
            "against every configured SLO tier."
        )
    )
    datasets = parser.add_mutually_exclusive_group(required=True)
    datasets.add_argument("--dataset", type=Path)
    datasets.add_argument(
        "--dataset-dir",
        type=Path,
        help="directory containing one <run-id>.jsonl dataset per planned run",
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--slo-config", type=Path, required=True)
    parser.add_argument("--mode", choices=["open", "closed"], default="open")
    parser.add_argument(
        "--rates",
        type=lambda value: parse_numbers(value, integer=False),
        default=parse_numbers("0.5,1,2,4,8", integer=False),
    )
    parser.add_argument(
        "--concurrencies",
        type=lambda value: parse_numbers(value, integer=True),
        default=parse_numbers("1,2,4,8,16,32,64", integer=True),
    )
    parser.add_argument("--open-concurrency", type=int, default=4096)
    parser.add_argument("--duration", type=float, default=300.0)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--repetition-start", type=int, default=1)
    parser.add_argument(
        "--phase",
        choices=["calibration", "warmup", "floor", "discovery", "confirm"],
        default="discovery",
    )
    parser.add_argument("--metrics-url", action="append", default=[])
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument(
        "--require-unique-requests",
        action="store_true",
        help="fail if a run schedules more requests than its dataset contains",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args(argv)

    if args.duration <= 0 or not math.isfinite(args.duration):
        parser.error("--duration must be positive and finite")
    if args.timeout <= 0 or not math.isfinite(args.timeout):
        parser.error("--timeout must be positive and finite")
    if args.repetitions <= 0:
        parser.error("--repetitions must be positive")
    if args.repetition_start <= 0:
        parser.error("--repetition-start must be positive")
    if args.open_concurrency <= 0:
        parser.error("--open-concurrency must be positive")
    if args.max_requests < 0:
        parser.error("--max-requests must be non-negative")
    if (
        not args.plan
        and args.dataset is not None
        and not args.dataset.expanduser().is_file()
    ):
        parser.error("--dataset must name an existing JSONL file")
    if (
        not args.plan
        and args.dataset_dir is not None
        and not args.dataset_dir.expanduser().is_dir()
    ):
        parser.error("--dataset-dir must name an existing directory")
    if not args.slo_config.expanduser().is_file():
        parser.error("--slo-config must name an existing YAML file")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    _, exit_code = execute(args)
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AnalysisError, SearchError, OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"error: {exc}") from exc
