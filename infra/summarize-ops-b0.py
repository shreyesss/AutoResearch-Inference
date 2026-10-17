#!/usr/bin/env python3
"""Build an inspectable index of every real ops_aiperf B0 cell, including failures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(value: object, places: int = 2) -> str:
    return f"{value:.{places}f}" if isinstance(value, (float, int)) else "—"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(".artifacts/ops-b0"))
    args = parser.parse_args()
    root = args.root.resolve()
    items = []
    for plan_path in sorted(root.glob("*/plan.json")):
        cell = plan_path.parent
        plan = json.loads(plan_path.read_text())
        status_path = cell / "status.json"
        status = json.loads(status_path.read_text()) if status_path.exists() else None
        summaries = list((cell / "aiperf").rglob("summary.json"))
        summary = json.loads(summaries[0].read_text()) if len(summaries) == 1 else None
        items.append({"cell": cell.name, "workload": plan.get("workload"),
                      "source_sha256": plan.get("source_sha256"),
                      "input_sha256": plan.get("input_sha256"),
                      "configured_rps": plan.get("offered_rps"),
                      "input_scope": plan.get("input_scope", "synthetic_source_adapter"),
                      "plan_path": str(plan_path), "status_path": str(status_path) if status else None,
                      "summary_path": str(summaries[0]) if summary else None,
                      "exit_code": status.get("aiperf_exit_code") if status else None,
                      "elapsed_s": status.get("elapsed_s") if status else None,
                      "summary": summary})
    (root / "index.json").write_text(json.dumps({"version": "ops-b0-index-v1", "cells": items},
                                           indent=2, sort_keys=True) + "\n")
    lines = ["# Ops AIPerf B0 cells", "",
             "Raw commands, logs, GPU timelines, request exports and summaries are in each cell directory.",
             "A probe validates transport. A curve cell is a bounded B0 load measurement; its p99 is a sample quantile.",
             "", "| Cell | Workload | Configured RPS | Realized RPS | HTTP 200 / records | TTFT p50/p90/p99 ms | TPOT p50/p90/p99 ms | Output tok/s | Status |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for item in items:
        summary = item["summary"] or {}
        ttft = summary.get("ttft_ms_p50_p90_p99") or [None, None, None]
        tpot = summary.get("tpot_ms_p50_p90_p99") or [None, None, None]
        state = summary.get("status") or ("running" if item["exit_code"] is None else "failed")
        lines.append("| " + " | ".join((item["cell"], item["workload"] or "—",
                    fmt(item["configured_rps"]),
                    ("—" if item["input_scope"] == "first_n_transport_probe" else
                     fmt(summary.get("actual_start_rps_first_to_last"))),
                    f"{summary.get('http_200', '—')} / {summary.get('request_count', '—')}",
                    "/".join(fmt(value) for value in ttft),
                    "/".join(fmt(value) for value in tpot),
                    fmt(summary.get("output_tokens_per_s_including_drain")), state)) + " |")
    (root / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(root / "INDEX.md")


if __name__ == "__main__":
    main()
