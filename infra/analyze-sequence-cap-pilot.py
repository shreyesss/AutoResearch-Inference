#!/usr/bin/env python3
"""Validate matched frozen inputs and summarize the bounded sequence-cap pilot."""

import hashlib
import csv
import json
import math
from pathlib import Path

ROOT = Path(".artifacts/sequence-cap-pilot")
MANIFEST = Path("infra/b0-frozen-inputs-manifest.json")
PHASES = ("b0a", "cap32a", "b0b", "cap32b")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, quantile):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * quantile
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return values[lower]
    return values[lower] * (upper - position) + values[upper] * (position - lower)


def metric(row, name):
    item = row["metrics"].get(name)
    return item.get("value") if isinstance(item, dict) else None


def cell_result(directory, asset, expected_count):
    raw_path = directory / "profile_export_raw.jsonl"
    records_path = directory / "profile_export.jsonl"
    raw = read_jsonl(raw_path)
    records = read_jsonl(records_path)
    export = json.loads((directory / "profile_export_aiperf.json").read_text())
    planned = read_jsonl(asset)
    result = {
        "expected_requests": expected_count,
        "records": len(records),
        "raw_requests": len(raw),
        "complete_artifact": export.get("is_complete"),
        "raw_sha256": sha256(raw_path),
        "records_sha256": sha256(records_path),
        "status_counts": {},
    }
    with (directory / "server_metrics_export.csv").open(newline="") as stream:
        server_rows = list(csv.DictReader(
            line for line in stream if not line.startswith("#") and line.strip()))
    server_metrics = {row["Metric"]: row for row in server_rows}
    result["server_gauges"] = {
        name: {field: float(server_metrics[name][field]) for field in ("avg", "max", "p95")}
        for name in ("vllm:num_requests_running", "vllm:num_requests_waiting", "vllm:kv_cache_usage_perc")
        if name in server_metrics
    }
    result["waiting_by_reason_max"] = {
        row["reason"]: float(row["max"])
        for row in server_rows
        if row["Metric"] == "vllm:num_requests_waiting_by_reason" and row["reason"]
    }
    for request in raw:
        key = str(request.get("status"))
        result["status_counts"][key] = result["status_counts"].get(key, 0) + 1
    actual = {r["metadata"]["conversation_id"]: r for r in raw}
    metrics_by_id = {r["metadata"]["x_request_id"]: r for r in records}
    issues = []
    if len(planned) != expected_count or len(raw) != expected_count or len(records) != expected_count:
        issues.append("request count mismatch")
    if len(actual) != len(raw) or len(metrics_by_id) != len(records):
        issues.append("duplicate request ID")
    if export.get("is_complete") is not True:
        issues.append("incomplete AIPerf artifact")
    if result["status_counts"] != {"200": expected_count}:
        issues.append("non-200 or missing responses")
    starts = []
    ends = []
    ttft = []
    tpot = []
    prompt_counts = []
    output_counts = []
    timing_errors = []
    first_start = min((r["metadata"]["request_start_ns"] for r in raw), default=None)
    for row in planned:
        request = actual.get(row["session_id"])
        if request is None:
            issues.append("missing planned request")
            continue
        payload = request["payload"]
        metadata = request["metadata"]
        if (payload.get("messages") != [{"role": "user", "content": row["text"]}]
            or payload.get("max_completion_tokens") != 256
            or payload.get("chat_template_kwargs") != {"enable_thinking": False}
            or payload.get("temperature") != 0 or payload.get("ignore_eos") is not True
            or payload.get("min_tokens") != 256):
            issues.append("request payload differs from frozen asset")
        starts.append(metadata["request_start_ns"])
        ends.append(metadata["request_end_ns"])
        timing_errors.append((metadata["request_start_ns"] - first_start) / 1e6 - row["timestamp"])
        record = metrics_by_id.get(metadata["x_request_id"])
        if request.get("status") == 200 and record is not None:
            values = [metric(record, name) for name in (
                "time_to_first_token", "inter_token_latency", "usage_prompt_tokens",
                "usage_completion_tokens", "request_latency")]
            if any(value is None for value in values):
                issues.append("missing latency or server token metric")
            else:
                first, per_token, prompt, output, latency = values
                ttft.append(first)
                tpot.append(per_token)
                prompt_counts.append(prompt)
                output_counts.append(output)
                if not 511 <= prompt <= 514:
                    issues.append("prompt token count differs from qualified range")
                if output != 256:
                    issues.append("completion token count differs from frozen output")
                if abs(per_token - (latency - first) / (output - 1)) > 1e-6:
                    issues.append("AIPerf TPOT counting differs from qualified formula")
    worst = max((abs(value) for value in timing_errors), default=None)
    if worst is None or worst > 20:
        issues.append("fixed schedule start error above 20 ms")
    bins = []
    if first_start is not None:
        for index in range(6):
            right = first_start + (index + 1) * 10_000_000_000
            left = right - 10_000_000_000
            bins.append({
                "starts": sum(left <= value < right for value in starts),
                "completions": sum(left <= value < right for value in ends),
                "outstanding_at_end": sum(value < right for value in starts) - sum(value < right for value in ends),
            })
    result.update({
        "valid_realization": not issues,
        "issues": sorted(set(issues)),
        "max_absolute_start_offset_error_ms": worst,
        "prompt_tokens_min_max": [min(prompt_counts), max(prompt_counts)] if prompt_counts else None,
        "completion_tokens_min_max": [min(output_counts), max(output_counts)] if output_counts else None,
        "ttft_ms_p50_p99": [percentile(ttft, 0.5), percentile(ttft, 0.99)],
        "tpot_ms_p50_p99": [percentile(tpot, 0.5), percentile(tpot, 0.99)],
        "finite_run_output_tokens_per_s": (sum(output_counts) / ((max(ends) - first_start) / 1e9)
                                            if ends and first_start is not None else None),
        "send_bin_10s": bins,
    })
    return result


def main():
    manifest = json.loads(MANIFEST.read_text())
    output = {
        "version": "sequence-cap-sensitivity-pilot-v1",
        "manifest_sha256": sha256(MANIFEST),
        "contrast": {"baseline_max_num_seqs": 512, "candidate_max_num_seqs": 32},
        "phase_order": list(PHASES),
        "cells": {},
    }
    for cell, entry in manifest["assets"].items():
        asset = Path(entry["path"])
        if sha256(asset) != entry["sha256"]:
            raise RuntimeError(f"Frozen asset changed: {cell}")
    for phase in PHASES:
        phase_dir = ROOT / phase
        if not phase_dir.exists():
            continue
        argv_path = phase_dir / "server-argv.json"
        if not argv_path.exists():
            continue
        argv = json.loads(argv_path.read_text())
        expected_cap = "512" if phase.startswith("b0") else "32"
        if argv[argv.index("--max-num-seqs") + 1] != expected_cap:
            raise RuntimeError(f"{phase}: resolved server argv differs from planned cap")
        output["cells"][phase] = {}
        for cell, entry in manifest["assets"].items():
            directory = phase_dir / cell
            if (directory / "profile_export_raw.jsonl").exists():
                output["cells"][phase][cell] = cell_result(
                    directory, Path(entry["path"]), entry["rows"])
    target = Path("infra/sequence-cap-pilot-results.json")
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    for phase, cells in output["cells"].items():
        for name, result in cells.items():
            print(json.dumps({"phase": phase, "cell": name,
                              "valid": result["valid_realization"],
                              "status": result["status_counts"],
                              "ttft": result["ttft_ms_p50_p99"],
                              "tpot": result["tpot_ms_p50_p99"],
                              "outstanding_last3": [item["outstanding_at_end"] for item in result["send_bin_10s"][-3:]],
                              "issues": result["issues"]}))


if __name__ == "__main__":
    main()
