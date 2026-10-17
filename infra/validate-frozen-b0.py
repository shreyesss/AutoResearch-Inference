#!/usr/bin/env python3
"""Compare frozen native single-turn assets with actual Qwen request exports."""

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(".artifacts/b0-frozen-replay")
MANIFEST = Path("infra/b0-frozen-inputs-manifest.json")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main():
    manifest = json.loads(MANIFEST.read_text())
    output = {"version": "b0-frozen-replay-validation-v1", "manifest_sha256": sha256(MANIFEST), "cells": {}}
    for cell, item in manifest["assets"].items():
        asset = Path(item["path"])
        if sha256(asset) != item["sha256"]:
            raise RuntimeError(f"{cell}: asset hash mismatch")
        planned = rows(asset)
        raw_path = ROOT / cell / "profile_export_raw.jsonl"
        metric_path = ROOT / cell / "profile_export.jsonl"
        aggregate = json.loads((ROOT / cell / "profile_export_aiperf.json").read_text())
        if aggregate.get("is_complete") is not True:
            raise RuntimeError(f"{cell}: incomplete AIPerf artifact")
        raw = rows(raw_path)
        records = {r["metadata"]["x_request_id"]: r for r in rows(metric_path)}
        actual = {r["metadata"]["conversation_id"]: r for r in raw}
        if len(planned) != item["rows"] or len(raw) != len(records) or len(actual) != len(planned):
            raise RuntimeError(f"{cell}: request count mismatch")
        first_start = min(r["metadata"]["request_start_ns"] for r in raw)
        timing_errors = []
        prompts = []
        ttft = []
        tpot = []
        starts = []
        ends = []
        for planned_row in planned:
            request = actual[planned_row["session_id"]]
            payload = request["payload"]
            metadata = request["metadata"]
            metrics = records[metadata["x_request_id"]]["metrics"]
            if (request["status"] != 200 or payload["messages"] != [{"role": "user", "content": planned_row["text"]}]
                or payload["max_completion_tokens"] != 256 or payload.get("chat_template_kwargs") != {"enable_thinking": False}
                or payload.get("temperature") != 0 or payload.get("ignore_eos") is not True
                or payload.get("min_tokens") != 256 or metrics["usage_completion_tokens"]["value"] != 256):
                raise RuntimeError(f"{cell}: actual request differs from frozen row {planned_row['session_id']}")
            prompts.append(metrics["usage_prompt_tokens"]["value"])
            ttft.append(metrics["time_to_first_token"]["value"])
            tpot.append(metrics["inter_token_latency"]["value"])
            starts.append(metadata["request_start_ns"])
            ends.append(metadata["request_end_ns"])
            actual_offset = (metadata["request_start_ns"] - first_start) / 1e6
            timing_errors.append(actual_offset - planned_row["timestamp"])
        worst = max(abs(x) for x in timing_errors)
        if worst > 20:
            raise RuntimeError(f"{cell}: fixed schedule error {worst:.3f} ms > 20 ms")
        bins = []
        for index in range(6):
            left = first_start + index * 10_000_000_000
            right = left + 10_000_000_000
            bins.append({
                "starts": sum(left <= value < right for value in starts),
                "completions": sum(left <= value < right for value in ends),
                "outstanding_at_end": sum(value < right for value in starts) - sum(value < right for value in ends),
            })
        output["cells"][cell] = {
            "requests": len(raw), "http_200": len(raw),
            "prompt_tokens_min_max": [min(prompts), max(prompts)],
            "max_absolute_start_offset_error_ms": round(worst, 3),
            "ttft_ms_p50": statistics.median(ttft),
            "tpot_ms_p50": statistics.median(tpot),
            "finite_run_output_tokens_per_s": 256 * len(raw) / ((max(ends) - first_start) / 1e9),
            "send_bin_10s": bins,
            "raw_sha256": sha256(raw_path), "records_sha256": sha256(metric_path),
        }
    Path("infra/b0-frozen-replay-validation.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output["cells"], sort_keys=True))


if __name__ == "__main__":
    main()
