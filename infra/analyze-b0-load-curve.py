#!/usr/bin/env python3
"""Summarize a bounded B0 load screen from AIPerf request and raw exports."""

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(".artifacts/b0-load-curve")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, q):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return values[low] * (high - position) + values[high] * (position - low) if low != high else values[low]


def metric(record, name):
    value = record["metrics"].get(name)
    return value.get("value") if isinstance(value, dict) else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cells", nargs="+", help="Cell names such as r02 r04")
    args = parser.parse_args()
    summaries = []
    for cell in args.cells:
        directory = ROOT / cell
        plan = json.loads((ROOT / f"{cell}-plan.json").read_text())
        metric_path = directory / "profile_export.jsonl"
        raw_path = directory / "profile_export_raw.jsonl"
        export_path = directory / "profile_export_aiperf.json"
        records = [json.loads(line) for line in metric_path.read_text().splitlines() if line]
        raws = [json.loads(line) for line in raw_path.read_text().splitlines() if line]
        export = json.loads(export_path.read_text())
        raw_by_id = {r["metadata"]["x_request_id"]: r for r in raws}
        if len(records) != len(raws) or len(raw_by_id) != len(raws):
            raise RuntimeError(f"{cell}: raw/metric count mismatch")
        ok = [r for r in records if raw_by_id[r["metadata"]["x_request_id"]]["status"] == 200]
        starts = sorted(r["metadata"]["request_start_ns"] for r in records)
        ends = sorted(r["metadata"]["request_end_ns"] for r in records)
        credits = sorted(r["metadata"]["credit_issued_ns"] for r in records)
        lags = [(r["metadata"]["request_start_ns"] - r["metadata"]["credit_issued_ns"]) / 1e6 for r in records]
        ttft = [metric(r, "time_to_first_token") for r in ok]
        tpot = [metric(r, "inter_token_latency") for r in ok]
        outputs = [metric(r, "usage_completion_tokens") for r in ok]
        prompts = [metric(r, "usage_prompt_tokens") for r in ok]
        latency = [metric(r, "request_latency") for r in ok]
        if not all(v is not None for v in ttft + tpot + outputs + prompts + latency):
            raise RuntimeError(f"{cell}: missing server usage or latency")
        if any(tokens < 2 for tokens in outputs):
            raise RuntimeError(f"{cell}: fewer than two completion tokens")
        tpot_formula_errors = [abs(observed - (duration - first) / (tokens - 1))
                               for observed, duration, first, tokens in zip(tpot, latency, ttft, outputs, strict=True)]
        if max(tpot_formula_errors, default=0) > 1e-6:
            raise RuntimeError(f"{cell}: request-level TPOT counting needs inspection")
        if cell != "warmup" and len(records) != plan["request_count"]:
            raise RuntimeError(f"{cell}: request count differs from plan")
        first, last = min(credits), max(ends)
        horizon = max(max(credits), max(starts)) - first
        bins = []
        for index in range(math.floor(horizon / 1e10) + 1):
            left = first + index * 10_000_000_000
            right = left + 10_000_000_000
            sent = sum(left <= s < right for s in starts)
            completed = sum(left <= e < right for e in ends)
            outstanding_end = sum(s < right for s in starts) - sum(e < right for e in ends)
            bins.append({"index": index, "starts": sent, "completions": completed, "outstanding_at_end": outstanding_end})
        payload_hashes = {
            hashlib.sha256(json.dumps(r["payload"], sort_keys=True).encode()).hexdigest()
            for r in raws
        }
        summary = {
            "cell": cell, "plan": plan,
            "record_count": len(records), "http_200": len(ok),
            "other_statuses": sorted(set(r["status"] for r in raws if r["status"] != 200)),
            "unique_request_bodies": len(payload_hashes),
            "prompt_tokens_min_max": [min(prompts), max(prompts)] if prompts else None,
            "completion_tokens_min_max": [min(outputs), max(outputs)] if outputs else None,
            "dispatch_lag_ms_p50_p99": [percentile(lags, .5), percentile(lags, .99)],
            "actual_start_rps_first_to_last": (len(starts)-1) / ((starts[-1]-starts[0])/1e9) if len(starts)>1 else None,
            "ttft_ms_p50_p99": [percentile(ttft, .5), percentile(ttft, .99)],
            "tpot_ms_p50_p99": [percentile(tpot, .5), percentile(tpot, .99)],
            "tpot_formula_max_abs_error_ms": max(tpot_formula_errors, default=0),
            "request_latency_ms_p50_p99": [percentile(latency, .5), percentile(latency, .99)],
            "output_tokens": sum(outputs),
            "finite_run_output_tokens_per_s": sum(outputs) / ((last-first)/1e9),
            "send_bin_10s": bins,
            "export_is_complete": export.get("is_complete"),
            "export_replay_lag_p99_ms": (export.get("replay_sched_lag_p99") or {}).get("avg"),
            "raw_sha256": sha256(raw_path), "records_sha256": sha256(metric_path),
        }
        if cell == "mixed-probe":
            cohorts = defaultdict(list)
            for record in ok:
                prompt = metric(record, "usage_prompt_tokens")
                label = min((512, 2048, 8192), key=lambda target: abs(prompt - target))
                if abs(prompt - label) > 1:
                    raise RuntimeError(f"{cell}: realized prompt {prompt} misses all intended arms")
                raw = raw_by_id[record["metadata"]["x_request_id"]]
                expected_output = 256 if label == 512 else 512
                if raw["payload"]["max_completion_tokens"] != expected_output or metric(record, "usage_completion_tokens") != expected_output:
                    raise RuntimeError(f"{cell}: output cap not realized for {label}-token arm")
                cohorts[label].append(record)
            summary["cohorts"] = {
                str(label): {
                    "requests": len(items),
                    "prompt_tokens_min_max": [min(metric(r, "usage_prompt_tokens") for r in items), max(metric(r, "usage_prompt_tokens") for r in items)],
                    "ttft_ms_p50": percentile([metric(r, "time_to_first_token") for r in items], .5),
                }
                for label, items in sorted(cohorts.items())
            }
        summaries.append(summary)
    output = {"version": "b0-load-curve-screen-v1", "results": summaries}
    (ROOT / "summary.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    for item in summaries:
        print(json.dumps({k: item[k] for k in ("cell", "record_count", "http_200", "dispatch_lag_ms_p50_p99", "ttft_ms_p50_p99", "tpot_ms_p50_p99", "finite_run_output_tokens_per_s", "send_bin_10s")}))


if __name__ == "__main__":
    main()
