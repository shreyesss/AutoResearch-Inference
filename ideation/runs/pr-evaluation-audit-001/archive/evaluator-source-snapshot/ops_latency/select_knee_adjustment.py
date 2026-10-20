#!/usr/bin/env python3
"""Choose the next configured knee-rate correction from a completed analysis."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import yaml

from analyze_latency import merged_thresholds


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def comfortably_under(
    analysis: dict[str, Any],
    tier: dict[str, Any],
    comfortable_fraction: float,
) -> bool:
    categories = analysis.get("by_category") or {}
    if not isinstance(categories, dict) or not categories:
        return False
    for category, group in categories.items():
        if not isinstance(group, dict):
            return False
        thresholds = merged_thresholds(tier, str(category))
        for metric_name, threshold_name in (
            ("ttft_ms", "ttft_p95_ms"),
            ("tpot_ms", "tpot_p95_ms"),
        ):
            limit = finite(thresholds.get(threshold_name))
            metric = group.get(metric_name) or {}
            value = finite(metric.get("p95")) if isinstance(metric, dict) else None
            mean_output = finite(group.get("mean_output_tokens")) or 0.0
            if value is None and metric_name == "tpot_ms" and mean_output <= 1:
                continue
            if (
                value is None
                or limit is None
                or value > comfortable_fraction * limit
            ):
                return False
    queue_slope = finite(analysis.get("queue_slope_ms_per_s"))
    return queue_slope is not None and queue_slope <= 0.25


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    analysis = json.loads(args.analysis.read_text(encoding="utf-8"))
    campaign = yaml.safe_load(args.campaign.read_text(encoding="utf-8"))
    balanced = campaign["slo_tiers"]["balanced"]
    protocol = campaign["active_protocol"]["knee"]
    decrease_factor = float(protocol["decrease_factor"])
    increase_factor = float(protocol["increase_factor"])
    comfortable_fraction = float(
        protocol["comfortable_fraction_of_p95_limit"]
    )
    tier_result = (analysis.get("slo_tiers") or {}).get("balanced") or {}
    if tier_result.get("pass") is not True:
        action = "decrease"
        new_rate = args.rate * decrease_factor
        reason = "balanced-tier validity/SLO gate failed"
    elif comfortably_under(analysis, balanced, comfortable_fraction):
        action = "increase"
        new_rate = args.rate * increase_factor
        reason = (
            "p95 latency below the configured fraction of class limits "
            "with a flat queue"
        )
    else:
        action = "keep"
        new_rate = None
        reason = "balanced tier passed without enough headroom to increase"
    result = {
        "schema_version": 1,
        "action": action,
        "original_rate": args.rate,
        "adjusted_rate": new_rate,
        "reason": reason,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
