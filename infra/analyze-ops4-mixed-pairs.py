#!/usr/bin/env python3
"""Audit two matched OPS4 mixed B0/candidate windows without pooling p99s.

This is descriptive evidence on the same 36 frozen requests, not a tail-SLA
confidence interval or an independent-content test.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


def load_cell(path: Path) -> tuple[dict, dict[str, dict]]:
    cell = json.loads((path / "cell-result.json").read_text())
    rows = [json.loads(line) for line in (path / "aiperf" / "normalized-requests.jsonl").read_text().splitlines()]
    if cell["status"] != "valid" or cell["behavior"] != "normal" or cell["counts"]["completed"] != 36:
        raise ValueError(f"not an eligible 36-request mixed cell: {path}")
    indexed = {row["request_id"]: row for row in rows}
    if len(rows) != 36 or len(indexed) != 36 or any(row["terminal_state"] != "completed" for row in rows):
        raise ValueError(f"request records are incomplete or duplicated: {path}")
    return cell, indexed


def shape(row: dict) -> str:
    output, prompt = row["completion_tokens"], row["input_tokens"]
    if output == 256 and 400 <= prompt < 1024:
        return "chat"
    if output == 1024 and 1024 <= prompt < 4096:
        return "code"
    if output == 1024 and 4096 <= prompt < 16000:
        return "agent"
    if output == 512 and prompt >= 16000:
        return "document"
    raise ValueError(f"unexpected mixed request shape: input={prompt}, output={output}")


def paired(baseline: dict[str, dict], candidate: dict[str, dict]) -> dict:
    if baseline.keys() != candidate.keys():
        raise ValueError("B0/candidate request identities differ")
    grouped: dict[str, list[tuple[dict, dict]]] = {}
    for request_id in sorted(baseline):
        b, c = baseline[request_id], candidate[request_id]
        stable = ("planned_index", "scheduled_arrival_ms", "input_tokens", "completion_tokens")
        if any(b[key] != c[key] for key in stable):
            raise ValueError(f"frozen input/schedule changed for {request_id}")
        grouped.setdefault(shape(b), []).append((b, c))
    result = {}
    for category, pairs in sorted(grouped.items()):
        metrics = {}
        for name in ("ttft_ms", "tpot_ms"):
            deltas = [c[name] - b[name] for b, c in pairs]
            metrics[name] = {
                "b0_median": round(median(b[name] for b, _ in pairs), 6),
                "candidate_median": round(median(c[name] for _, c in pairs), 6),
                "paired_delta_median_candidate_minus_b0": round(median(deltas), 6),
                "requests_lower_on_candidate": sum(delta < 0 for delta in deltas),
                "requests_higher_on_candidate": sum(delta > 0 for delta in deltas),
            }
        result[category] = {"requests": len(pairs), "metrics": metrics}
    return result


def tail_witnesses(baseline: dict[str, dict], candidate: dict[str, dict]) -> dict:
    result = {}
    for name in ("ttft_ms", "tpot_ms"):
        slowest = sorted(baseline.values(), key=lambda row: row[name], reverse=True)[:3]
        result[name] = [{
            "planned_index": b["planned_index"],
            "shape": shape(b),
            "b0": round(b[name], 6),
            "candidate_same_request": round(candidate[b["request_id"]][name], 6),
            "delta_candidate_minus_b0": round(candidate[b["request_id"]][name] - b[name], 6),
        } for b in slowest]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("b0-screen", "candidate-screen", "b0-confirm", "candidate-confirm"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cells = {name: load_cell(getattr(args, name.replace("-", "_"))) for name in
             ("b0-screen", "candidate-screen", "b0-confirm", "candidate-confirm")}
    b0_id = cells["b0-screen"][0]["config_id"]
    candidate_id = cells["candidate-screen"][0]["config_id"]
    if cells["b0-confirm"][0]["config_id"] != b0_id or cells["candidate-confirm"][0]["config_id"] != candidate_id:
        raise ValueError("configuration identity changed between windows")
    if b0_id == candidate_id:
        raise ValueError("B0 and candidate identities are equal")
    windows = {}
    for label in ("screen", "confirm"):
        b_cell, b_rows = cells["b0-" + label]
        c_cell, c_rows = cells["candidate-" + label]
        windows[label] = {
            "b0_cell_id": b_cell["cell_id"],
            "candidate_cell_id": c_cell["cell_id"],
            "b0_primary": {key: b_cell["metrics"][key] for key in
                           ("output_tokens_per_s", "ttft_p99_ms", "tpot_p99_ms", "dispatch_lag_p99_ms")},
            "candidate_primary": {key: c_cell["metrics"][key] for key in
                                  ("output_tokens_per_s", "ttft_p99_ms", "tpot_p99_ms", "dispatch_lag_p99_ms")},
            "b0_queue_max": b_cell["diagnostics"].get("server_gauges", {}).get("queue_max"),
            "candidate_queue_max": c_cell["diagnostics"].get("server_gauges", {}).get("queue_max"),
            "b0_windows": b_cell["diagnostics"].get("windows"),
            "candidate_windows": c_cell["diagnostics"].get("windows"),
            "paired_request_shapes": paired(b_rows, c_rows),
            "b0_tail_request_witnesses": tail_witnesses(b_rows, c_rows),
        }
    result = {
        "evidence_grade": "descriptive_same_frozen_requests_two_windows",
        "limitation": "Only 36 requests, including five document shapes. Windows reuse identical content and arrivals. Per-class medians/signs are descriptive; no p99 SLA or generalization claim.",
        "b0_config_id": b0_id,
        "candidate_config_id": candidate_id,
        "windows": windows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
