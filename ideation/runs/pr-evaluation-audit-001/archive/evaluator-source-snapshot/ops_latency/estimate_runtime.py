#!/usr/bin/env python3
"""Estimate active campaign GPU wall time from campaign.yaml."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    args = parser.parse_args()
    campaign = yaml.safe_load(args.campaign.read_text(encoding="utf-8"))
    protocol = campaign["active_protocol"]
    configs = [
        item
        for item in campaign["experiments"]
        if item.get("kind") == "configuration"
    ]
    workloads = len(protocol["workloads"])
    cache_tiers = len(protocol["cache_tiers"])
    cells = sum(
        workloads * (cache_tiers + (1 if item["include_uncached"] else 0))
        for item in configs
    )
    warmup_cells = len(configs) * workloads * cache_tiers
    calibrators = sum(item.get("calibrate") is True for item in configs)
    calibration_runs = (
        calibrators
        * workloads
        * int(protocol["calibration"]["rates_per_workload"])
    )
    maximum_adjustments = int(
        protocol["knee"]["maximum_adjustments"]
    )
    seconds = {
        "cache_warmup": warmup_cells * int(protocol["warmup"]["duration_s"]),
        "latency_floor": cells * int(protocol["floor"]["duration_s"]),
        "knee_discovery": cells * int(protocol["knee"]["duration_s"]),
        "calibration": calibration_runs
        * int(protocol["calibration"]["duration_s"]),
        "worst_case_adjustments": (
            cells
            * int(protocol["knee"]["duration_s"])
            * maximum_adjustments
        ),
    }
    base = sum(
        value
        for key, value in seconds.items()
        if key != "worst_case_adjustments"
    )
    result = {
        "configurations": len(configs),
        "matrix_cells": cells,
        "calibration_runs": calibration_runs,
        "seconds": seconds,
        "base_load_hours": base / 3600,
        "all_cells_adjusted_load_hours": (
            base + seconds["worst_case_adjustments"]
        )
        / 3600,
        "extra_hours_per_selected_confirmation": (
            int(protocol["confirmation_repetitions"])
            * int(protocol["knee"]["duration_s"])
            + int(protocol["warmup"]["duration_s"])
        )
        / 3600,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
