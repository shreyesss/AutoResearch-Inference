#!/usr/bin/env python3
"""Summarize real AIPerf cells from the ops workload calibration queue."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] if low == high else ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def value(record: dict, name: str) -> float | None:
    item = record.get("metrics", {}).get(name)
    return item.get("value") if isinstance(item, dict) else None


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(cell: Path) -> dict:
    plan_path = cell / "plan.json"
    raw_path = cell / "profile_export_raw.jsonl"
    records_path = cell / "profile_export.jsonl"
    export_path = cell / "profile_export_aiperf.json"
    plan = json.loads(plan_path.read_text())
    raw = read_jsonl(raw_path)
    records = read_jsonl(records_path)
    export = json.loads(export_path.read_text())
    raw_by_id = {row["metadata"]["x_request_id"]: row for row in raw}
    if len(raw_by_id) != len(raw) or len(records) != len(raw):
        raise ValueError(f"{cell}: raw/record count or ID mismatch")
    starts = sorted(row["metadata"]["request_start_ns"] for row in records)
    ends = sorted(row["metadata"]["request_end_ns"] for row in records)
    credits = sorted(row["metadata"]["credit_issued_ns"] for row in records)
    if not starts:
        raise ValueError(f"{cell}: no measured requests")
    ok = [row for row in records if raw_by_id[row["metadata"]["x_request_id"]]["status"] == 200]
    metric_names = ("time_to_first_token", "inter_token_latency", "request_latency",
                    "usage_prompt_tokens", "usage_completion_tokens")
    metrics = {name: [value(row, name) for row in ok] for name in metric_names}
    if any(any(item is None for item in series) for series in metrics.values()):
        raise ValueError(f"{cell}: missing metric or server token usage")
    lags = [(row["metadata"]["request_start_ns"] - row["metadata"]["credit_issued_ns"]) / 1e6
            for row in records]
    origin = min(credits)
    horizon = max(max(starts), max(credits)) - origin
    bins = []
    for index in range(math.floor(horizon / 10_000_000_000) + 1):
        edge = origin + (index + 1) * 10_000_000_000
        bins.append({"index": index, "starts": sum(t < edge for t in starts)
                     - sum(t < edge - 10_000_000_000 for t in starts),
                     "completions": sum(t < edge for t in ends)
                     - sum(t < edge - 10_000_000_000 for t in ends),
                     "outstanding": sum(t < edge for t in starts) - sum(t < edge for t in ends)})
    completion = metrics["usage_completion_tokens"]
    bodies = {hashlib.sha256(json.dumps(row.get("payload"), sort_keys=True).encode()).hexdigest()
              for row in raw}
    result = {
        "plan": plan, "status": "complete" if export.get("is_complete") is True else "incomplete",
        "request_count": len(records), "http_200": len(ok),
        "unique_request_bodies": len(bodies),
        "statuses": sorted({row["status"] for row in raw}),
        "prompt_tokens_min_max": [min(metrics["usage_prompt_tokens"]), max(metrics["usage_prompt_tokens"])] if ok else None,
        "completion_tokens_min_max": [min(completion), max(completion)] if ok else None,
        "ttft_ms_p50_p90_p99": [quantile(metrics["time_to_first_token"], q) for q in (.5, .9, .99)],
        "tpot_ms_p50_p90_p99": [quantile(metrics["inter_token_latency"], q) for q in (.5, .9, .99)],
        "latency_ms_p50_p90_p99": [quantile(metrics["request_latency"], q) for q in (.5, .9, .99)],
        "dispatch_lag_ms_p50_p99": [quantile(lags, q) for q in (.5, .99)],
        "actual_start_rps_first_to_last": ((len(starts) - 1) / ((starts[-1] - starts[0]) / 1e9)
                                          if len(starts) > 1 and starts[-1] > starts[0] else None),
        "replay_schedule_lag_p99_ms": (export.get("replay_sched_lag_p99") or {}).get("avg"),
        "output_tokens_per_s_including_drain": sum(completion) / ((max(ends) - origin) / 1e9),
        "send_bins_10s": bins,
        "raw_sha256": digest(raw_path), "records_sha256": digest(records_path),
    }
    if isinstance(plan.get("request_count"), int) and len(records) != plan["request_count"]:
        result["status"] = "count_mismatch"
    if len(ok) != len(records) and result["status"] == "complete":
        result["status"] = "http_error"
    # Preserve the keys consumed by existing reports while exposing p90 too.
    for name in ("ttft", "tpot", "latency"):
        band = result[f"{name}_ms_p50_p90_p99"]
        result[f"{name}_ms_p50_p99"] = [band[0], band[2]]
    (cell / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cells", nargs="+", type=Path)
    args = parser.parse_args()
    for cell in args.cells:
        result = analyze(cell)
        print(json.dumps({key: result[key] for key in ("status", "request_count", "http_200",
                         "ttft_ms_p50_p90_p99", "tpot_ms_p50_p90_p99", "output_tokens_per_s_including_drain")}))


if __name__ == "__main__":
    main()
