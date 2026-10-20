#!/usr/bin/env python3
"""Run several existing loadgen.py processes and merge artifacts afterward."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .analyze_latency import metric_summary
except ImportError:  # Direct script execution.
    from analyze_latency import metric_summary


ROOT = Path(__file__).resolve().parents[1]
LOADGEN = ROOT / "testing/common/loadgen.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--base-urls", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--mode", choices=["open", "closed"], required=True)
    parser.add_argument("--request-rate", type=float)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--duration", type=float, default=300)
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if args.shards <= 0:
        parser.error("--shards must be positive")
    if args.concurrency <= 0 or args.concurrency % args.shards:
        parser.error("--concurrency must be positive and divisible by --shards")
    if args.mode == "open" and (
        args.request_rate is None or args.request_rate <= 0
    ):
        parser.error("open mode requires a positive --request-rate")

    lines = [
        line
        for line in args.dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(lines) < args.shards:
        parser.error("dataset must contain at least one row per shard")
    urls = [url.strip() for url in args.base_urls.split(",") if url.strip()]
    if not urls:
        parser.error("--base-urls must contain at least one URL")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    processes: list[tuple[subprocess.Popen[str], Any]] = []
    shard_dirs: list[Path] = []
    for index in range(args.shards):
        shard = args.output_dir / "shards" / str(index)
        shard.mkdir(parents=True, exist_ok=True)
        dataset = shard / "dataset.jsonl"
        dataset.write_text(
            "\n".join(lines[index :: args.shards]) + "\n",
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(LOADGEN),
            "--dataset",
            str(dataset),
            "--base-url",
            urls[index % len(urls)],
            "--model",
            args.model,
            "--mode",
            args.mode,
            "--concurrency",
            str(args.concurrency // args.shards),
            "--duration",
            str(args.duration),
            "--timeout",
            str(args.timeout),
            "--seed",
            str(args.seed + index),
            "--output-dir",
            str(shard),
        ]
        if args.mode == "open":
            command.extend(
                ["--request-rate", f"{args.request_rate / args.shards:.9g}"]
            )
        log = (shard / "loadgen.log").open("w", encoding="utf-8")
        processes.append(
            (
                subprocess.Popen(
                    command,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                ),
                log,
            )
        )
        shard_dirs.append(shard)

    codes: list[int] = []
    for process, log in processes:
        codes.append(process.wait())
        log.close()

    summaries: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    request_files = 0
    for shard in shard_dirs:
        summary_path = shard / "summary.json"
        requests_path = shard / "requests.jsonl"
        if summary_path.is_file():
            summaries.append(json.loads(summary_path.read_text(encoding="utf-8")))
        if requests_path.is_file():
            request_files += 1
            with requests_path.open(encoding="utf-8") as handle:
                records.extend(json.loads(line) for line in handle if line.strip())
    if len(summaries) != args.shards or request_files != args.shards:
        print(
            f"complete artifacts from summaries={len(summaries)}/"
            f"{args.shards}, requests={request_files}/{args.shards}",
            file=sys.stderr,
        )
        return 1

    records.sort(
        key=lambda record: (
            str(record.get("scheduled_at") or ""),
            int(record.get("request_id") or 0),
        )
    )
    with (args.output_dir / "requests.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for index, record in enumerate(records):
            record["request_id"] = index
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")

    successful = [record for record in records if record.get("success") is True]

    def values(key: str) -> list[float]:
        return [
            float(record[key])
            for record in successful
            if isinstance(record.get(key), (int, float))
            and not isinstance(record.get(key), bool)
        ]

    scheduled = sum(int(summary.get("scheduled", 0)) for summary in summaries)
    completed = sum(int(summary.get("completed", 0)) for summary in summaries)
    if len(records) != scheduled or len(successful) != completed:
        print(
            "merged record counts disagree with shard summaries: "
            f"records={len(records)}/{scheduled}, "
            f"successful={len(successful)}/{completed}",
            file=sys.stderr,
        )
        return 1
    failed = scheduled - completed
    run_duration = max(
        float(summary.get("run_duration_s", 0.0)) for summary in summaries
    )
    summary = {
        "schema_version": 1,
        "mode": args.mode,
        "sharded": True,
        "shards": args.shards,
        "shards_reporting": len(summaries),
        "shard_exit_codes": codes,
        "base_urls": urls,
        "configured_concurrency": args.concurrency,
        "configured_request_rate": (
            args.request_rate if args.mode == "open" else None
        ),
        "run_duration_s": run_duration,
        "scheduled": scheduled,
        "completed": completed,
        "failed": failed,
        "completion_ratio": completed / scheduled if scheduled else 0.0,
        "error_rate": failed / scheduled if scheduled else 0.0,
        "request_rps": sum(
            float(summary.get("request_rps", 0.0)) for summary in summaries
        ),
        "offered_request_rps": sum(
            float(summary.get("offered_request_rps", 0.0))
            for summary in summaries
        ),
        "queue_slope_ms_per_s": max(
            float(summary.get("queue_slope_ms_per_s", 0.0))
            for summary in summaries
        ),
        "concurrency_bound": any(
            summary.get("concurrency_bound") is True for summary in summaries
        ),
        "ttft_ms": metric_summary(values("ttft_ms")),
        "tpot_ms": metric_summary(values("tpot_ms")),
        "e2e_ms": metric_summary(values("e2e_ms")),
        "stream_gap_ms": metric_summary(
            [
                float(gap)
                for record in successful
                for gap in (record.get("itl_ms") or [])
                if isinstance(gap, (int, float))
                and not isinstance(gap, bool)
                and math.isfinite(float(gap))
                and float(gap) >= 0
            ]
        ),
        "input_tokens": sum(
            int(summary.get("input_tokens", 0)) for summary in summaries
        ),
        "output_tokens": sum(
            int(summary.get("output_tokens", 0)) for summary in summaries
        ),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(code in {0, 1} for code in codes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
