#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def normalize(column: str) -> str:
    return (
        column.strip()
        .lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("%", "percent")
    )


def find_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        for column in columns:
            if candidate in column:
                return column
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top", type=int, default=50)
    args = parser.parse_args()

    frame = pd.read_csv(args.csv, comment="#")
    frame.columns = [normalize(str(column)) for column in frame.columns]
    columns = list(frame.columns)
    name_col = find_column(columns, ("kernel_name", "name"))
    total_col = find_column(columns, ("total_time", "total"))
    instances_col = find_column(columns, ("instances", "count"))
    average_col = find_column(columns, ("average", "avg"))
    if not name_col or not total_col:
        raise SystemExit(f"cannot identify kernel columns: {columns}")

    frame[total_col] = pd.to_numeric(frame[total_col], errors="coerce")
    frame = frame.dropna(subset=[total_col]).sort_values(total_col, ascending=False)
    top = frame.head(args.top).copy()
    total_gpu_time = float(frame[total_col].sum())
    rows: list[dict[str, Any]] = []
    for _, row in top.iterrows():
        total = float(row[total_col])
        rows.append(
            {
                "kernel": str(row[name_col]),
                "total_time": total,
                "critical_share": total / total_gpu_time if total_gpu_time else 0,
                "instances": None
                if not instances_col
                else float(row[instances_col]),
                "average_time": None if not average_col else float(row[average_col]),
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    top.to_csv(args.output_dir / "kernel-top.csv", index=False)
    (args.output_dir / "kernel-summary.json").write_text(
        json.dumps(
            {
                "source": str(args.csv),
                "total_gpu_time": total_gpu_time,
                "top_kernels": rows,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Kernel summary: {args.output_dir}")


if __name__ == "__main__":
    main()
