#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def telemetry_summary(run_root: Path) -> dict[str, float]:
    path = run_root / "telemetry" / "telemetry.parquet"
    if not path.is_file():
        return {}
    frame = pd.read_parquet(path)
    values: dict[str, float] = {}
    sm = [column for column in frame if column.endswith(".sm_util_percent")]
    hbm = [column for column in frame if column.endswith(".hbm_used_bytes")]
    power = [column for column in frame if column.endswith(".power_w")]
    if sm:
        values["gpu_sm_util_mean_percent"] = float(frame[sm].mean(axis=1).mean())
        values["gpu_sm_util_peak_percent"] = float(frame[sm].max(axis=1).max())
    if hbm:
        values["node_hbm_peak_bytes"] = float(frame[hbm].sum(axis=1).max())
    if power:
        values["node_power_mean_w"] = float(frame[power].sum(axis=1).mean())
    return values


def infer_dimensions(path: Path, root: Path) -> dict[str, str]:
    relative = path.relative_to(root)
    parts = relative.parts
    values = {
        "hardware": "",
        "engine": "",
        "profile": "",
        "workload_suite": "",
        "run_id": "",
        "case": "",
    }
    if len(parts) >= 7:
        (
            values["hardware"],
            values["engine"],
            values["profile"],
            values["workload_suite"],
            values["run_id"],
            values["case"],
        ) = parts[:6]
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.results_root.resolve()

    rows: list[dict[str, Any]] = []
    throughput_rows: list[dict[str, Any]] = []
    telemetry_cache: dict[Path, dict[str, float]] = {}
    for path in sorted(root.rglob("capacity_summary.json")):
        payload = json.loads(path.read_text())
        dimensions = infer_dimensions(path, root)
        run_root = path
        while run_root != root and not (run_root / "manifest.json").is_file():
            run_root = run_root.parent
        if not (run_root / "clean_complete.json").is_file():
            continue
        if run_root not in telemetry_cache:
            telemetry_cache[run_root] = telemetry_summary(run_root)
        rows.append(
            dimensions
            | {
                "highest_passing_rps": payload.get("highest_passing_rps"),
                "operational_rps": payload.get("operational_rps"),
                "max_slo_concurrency": payload.get("max_slo_concurrency"),
                "estimated_users": payload.get("estimated_users"),
                "mean_e2e_ms": payload.get("mean_e2e_ms"),
                "peak_closed_loop_rps": payload.get("peak_closed_loop_rps"),
                "summary_path": str(path),
            }
            | telemetry_cache[run_root]
        )

    for path in sorted(root.rglob("throughput_summary.json")):
        payload = json.loads(path.read_text())
        dimensions = infer_dimensions(path, root)
        run_root = path
        while run_root != root and not (run_root / "manifest.json").is_file():
            run_root = run_root.parent
        if not (run_root / "clean_complete.json").is_file():
            continue
        if run_root not in telemetry_cache:
            telemetry_cache[run_root] = telemetry_summary(run_root)
        throughput_rows.append(
            dimensions
            | {
                "peak_output_tps": payload.get("peak_output_tps"),
                "peak_concurrency": payload.get("peak_concurrency"),
                "stop_reason": payload.get("stop_reason"),
                "evidence_class": payload.get("evidence_class"),
                "summary_path": str(path),
            }
            | telemetry_cache[run_root]
        )

    if not rows and not throughput_rows:
        raise SystemExit(f"no benchmark summaries under {root}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if rows:
        frame = pd.DataFrame(rows)
        frame.to_csv(args.output_dir / "capacity-comparison.csv", index=False)
        (args.output_dir / "capacity-comparison.json").write_text(
            json.dumps(rows, indent=2) + "\n"
        )
        ordered = frame.sort_values(
            ["hardware", "workload_suite", "case", "operational_rps"],
            ascending=[True, True, True, False],
        )
        markdown = [
            "# Capacity comparison",
            "",
            "Capacity values are valid only for their recorded SLO and workload manifest.",
            "",
            ordered.to_markdown(index=False),
            "",
        ]
        (args.output_dir / "capacity-comparison.md").write_text(
            "\n".join(markdown)
        )
    if throughput_rows:
        throughput_frame = pd.DataFrame(throughput_rows)
        throughput_frame.to_csv(
            args.output_dir / "offline-throughput-comparison.csv", index=False
        )
        (args.output_dir / "offline-throughput-comparison.json").write_text(
            json.dumps(throughput_rows, indent=2) + "\n"
        )
        throughput_ordered = throughput_frame.sort_values(
            ["hardware", "workload_suite", "case", "peak_output_tps"],
            ascending=[True, True, True, False],
        )
        throughput_markdown = [
            "# Offline throughput comparison",
            "",
            "These are non-SLO closed-loop output-throughput peaks and must "
            "not be labeled sustainable capacity.",
            "",
            throughput_ordered.to_markdown(index=False),
            "",
        ]
        (args.output_dir / "offline-throughput-comparison.md").write_text(
            "\n".join(throughput_markdown)
        )
    print(f"Comparison report: {args.output_dir}")


if __name__ == "__main__":
    main()
