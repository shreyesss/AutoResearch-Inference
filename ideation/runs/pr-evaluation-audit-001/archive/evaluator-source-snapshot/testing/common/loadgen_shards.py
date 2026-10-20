#!/usr/bin/env python3
"""Run loadgen.py as several client processes and merge their results.

One Python loadgen process saturates a CPU core above roughly 40 req/s of
streamed responses, which inflates client-side latency and can cap closed-loop
throughput. This splits the dataset round-robin into --shards disjoint files
(so shards never send the same prompt), gives each shard concurrency / shards,
spreads shards over --base-urls, and writes a merged summary.json with the
same core keys as loadgen.py (rates are summed, percentiles are recomputed
over all requests).
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
QUEUE_FLAT_LIMIT_MS_PER_S = 1.0


class ShardedLoadgenError(RuntimeError):
    """Raised when shard execution cannot produce complete merged artifacts."""


def percentile(values: Sequence[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def metric(values: Sequence[float]) -> dict[str, float | None]:
    return {
        "p50": percentile(values, 0.50),
        "p90": percentile(values, 0.90),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "mean": sum(values) / len(values) if values else None,
    }


def linear_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denominator = sum((value - x_mean) ** 2 for value in xs)
    if denominator <= 0:
        return 0.0
    return sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(xs, ys, strict=True)
    ) / denominator


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-urls", required=True, help="comma-separated")
    parser.add_argument("--model", required=True)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--duration", type=float, default=300)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--max-requests", type=int, default=0)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.concurrency <= 0:
        parser.error("--concurrency must be positive")
    if args.shards <= 0:
        parser.error("--shards must be positive")
    if args.concurrency % args.shards:
        parser.error("--concurrency must be divisible by --shards")
    if not math.isfinite(args.duration) or args.duration < 0:
        parser.error("--duration must be non-negative and finite")
    if args.max_requests < 0:
        parser.error("--max-requests must be non-negative")
    if 0 < args.max_requests < args.shards:
        parser.error("positive --max-requests must be at least --shards")
    if args.duration == 0 and args.max_requests == 0:
        parser.error("at least one of --duration or --max-requests must set a limit")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be positive and finite")
    urls = [url.strip() for url in args.base_urls.split(",") if url.strip()]
    if not urls:
        parser.error("--base-urls must contain at least one URL")
    args.base_urls = urls
    return args


def shard_request_limit(total: int, shards: int, index: int) -> int:
    if total <= 0:
        return 0
    quotient, remainder = divmod(total, shards)
    return quotient + int(index < remainder)


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ShardedLoadgenError(f"{path} contains a non-object record")
            records.append(value)
    return records


def merged_summary(
    *,
    summaries: Sequence[Mapping[str, Any]],
    records: Sequence[Mapping[str, Any]],
    codes: Sequence[int],
    urls: Sequence[str],
    model: str,
    concurrency: int,
    shards: int,
    duration: float,
    dataset_requests: int,
) -> dict[str, Any]:
    successful = [record for record in records if record.get("success") is True]

    def values(key: str) -> list[float]:
        return [
            float(value)
            for record in successful
            if isinstance((value := record.get(key)), (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        ]

    scheduled = sum(int(summary.get("scheduled") or 0) for summary in summaries)
    completed = sum(int(summary.get("completed") or 0) for summary in summaries)
    failed = sum(int(summary.get("failed") or 0) for summary in summaries)
    queue_slopes = [
        float(value)
        for summary in summaries
        if isinstance(
            (value := summary.get("queue_slope_ms_per_s")),
            (int, float),
        )
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ]
    queue_slope = max(queue_slopes, default=0.0)
    return {
        "schema_version": 1,
        "mode": "closed",
        "sharded": True,
        "shards": shards,
        "shards_reporting": len(summaries),
        "shard_exit_codes": list(codes),
        "base_urls": list(urls),
        "configured_concurrency": concurrency,
        "run_duration_s": max(
            float(summary.get("run_duration_s") or 0.0)
            for summary in summaries
        ),
        "scheduled": scheduled,
        "completed": completed,
        "failed": failed,
        "completion_ratio": completed / scheduled if scheduled else 0.0,
        "error_rate": failed / scheduled if scheduled else 0.0,
        "request_rps": sum(
            float(summary.get("request_rps") or 0.0)
            for summary in summaries
        ),
        "input_tokens": sum(
            int(summary.get("input_tokens") or 0) for summary in summaries
        ),
        "output_tokens": sum(
            int(summary.get("output_tokens") or 0) for summary in summaries
        ),
        "input_tps": sum(
            float(summary.get("input_tps") or 0.0) for summary in summaries
        ),
        "output_tps": sum(
            float(summary.get("output_tps") or 0.0) for summary in summaries
        ),
        "ttft_ms": metric(values("ttft_ms")),
        "tpot_ms": metric(values("tpot_ms")),
        "e2e_ms": metric(values("e2e_ms")),
        "per_shard_request_rps": [
            float(summary.get("request_rps") or 0.0) for summary in summaries
        ],
        "dataset_requests": dataset_requests,
        "offered_request_rps": sum(
            float(summary.get("offered_request_rps") or 0.0)
            for summary in summaries
        ),
        "configured_request_rate": None,
        "requested_duration_s": duration,
        "queue_slope_ms_per_s": queue_slope,
        "queue_flat": queue_slope <= QUEUE_FLAT_LIMIT_MS_PER_S,
        "concurrency_bound": any(
            summary.get("concurrency_bound") is True for summary in summaries
        ),
        "model": model,
    }


def write_merged_results(
    output_dir: Path,
    records: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    with (output_dir / "requests.jsonl").open("w", encoding="utf-8") as handle:
        for record in records:
            json.dump(record, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    urls: list[str] = args.base_urls
    dataset = args.dataset.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    try:
        lines = [line for line in dataset.read_text(encoding="utf-8").splitlines() if line]
    except OSError as exc:
        raise ShardedLoadgenError(f"cannot read dataset {dataset}: {exc}") from exc
    if len(lines) < args.shards:
        raise ShardedLoadgenError(
            f"dataset has {len(lines)} requests for {args.shards} shards"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    processes: list[subprocess.Popen[str]] = []
    logs: list[Any] = []
    shard_dirs: list[Path] = []
    for index in range(args.shards):
        shard = output_dir / "shards" / str(index)
        shard.mkdir(parents=True, exist_ok=True)
        shard_dataset = shard / "dataset.jsonl"
        shard_dataset.write_text(
            "\n".join(lines[index :: args.shards]) + "\n",
            encoding="utf-8",
        )
        log = (shard / "loadgen.log").open("w", encoding="utf-8")
        command = [
            sys.executable,
            str(HERE / "loadgen.py"),
            "--dataset",
            str(shard_dataset),
            "--base-url",
            urls[index % len(urls)],
            "--model",
            args.model,
            "--mode",
            "closed",
            "--concurrency",
            str(args.concurrency // args.shards),
            "--duration",
            str(args.duration),
            "--max-requests",
            str(shard_request_limit(args.max_requests, args.shards, index)),
            "--timeout",
            str(args.timeout),
            "--seed",
            str(args.seed + index),
            "--output-dir",
            str(shard),
        ]
        processes.append(
            subprocess.Popen(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        )
        logs.append(log)
        shard_dirs.append(shard)
    try:
        codes = [process.wait() for process in processes]
    finally:
        for log in logs:
            log.close()

    summaries: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    missing: list[str] = []
    for shard in shard_dirs:
        summary_path = shard / "summary.json"
        requests_path = shard / "requests.jsonl"
        if not summary_path.is_file() or not requests_path.is_file():
            missing.append(str(shard))
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not isinstance(summary, dict):
            raise ShardedLoadgenError(f"{summary_path} must contain an object")
        summaries.append(summary)
        records.extend(read_records(requests_path))
    if missing:
        raise ShardedLoadgenError(
            "shards did not produce complete artifacts: " + ", ".join(missing)
        )
    unexpected_codes = [code for code in codes if code not in {0, 1}]
    if unexpected_codes:
        raise ShardedLoadgenError(
            f"shard load generators exited unexpectedly: {codes}"
        )
    scheduled = sum(int(summary.get("scheduled") or 0) for summary in summaries)
    if len(records) != scheduled:
        raise ShardedLoadgenError(
            f"merged {len(records)} request records for {scheduled} scheduled requests"
        )

    summary = merged_summary(
        summaries=summaries,
        records=records,
        codes=codes,
        urls=urls,
        model=args.model,
        concurrency=args.concurrency,
        shards=args.shards,
        duration=args.duration,
        dataset_requests=len(lines),
    )
    write_merged_results(output_dir, records, summary)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in ("request_rps", "error_rate", "shards_reporting")
            }
        )
    )
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ShardedLoadgenError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
