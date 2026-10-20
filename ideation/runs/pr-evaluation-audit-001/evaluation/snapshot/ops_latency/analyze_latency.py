#!/usr/bin/env python3
"""Post-process completed load-generator artifacts for latency experiments.

This module intentionally does no work in the request-generation hot path. It
reads requests.jsonl and summary.json only after the load generator exits.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = 1
LATENCY_METRICS = ("ttft_ms", "tpot_ms", "e2e_ms", "stream_gap_ms")
PERCENTILES = (("p50", 0.50), ("p95", 0.95), ("p99", 0.99))
THRESHOLD_TO_METRIC = {
    "ttft_p95_ms": ("ttft_ms", "p95"),
    "ttft_p99_ms": ("ttft_ms", "p99"),
    "tpot_p95_ms": ("tpot_ms", "p95"),
    "tpot_p99_ms": ("tpot_ms", "p99"),
    "e2e_p95_ms": ("e2e_ms", "p95"),
    "e2e_p99_ms": ("e2e_ms", "p99"),
    "stream_gap_p95_ms": ("stream_gap_ms", "p95"),
    "stream_gap_p99_ms": ("stream_gap_ms", "p99"),
}


class AnalysisError(RuntimeError):
    """Raised when latency artifacts or campaign configuration are invalid."""


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def percentile(values: Sequence[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def metric_summary(values: Sequence[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "mean": sum(values) / len(values) if values else None,
        **{name: percentile(values, quantile) for name, quantile in PERCENTILES},
    }


def read_json(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisError(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise AnalysisError(f"{path} must contain a JSON object")
    return loaded


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    loaded = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise AnalysisError(
                        f"{path}:{line_number}: invalid JSON: {exc}"
                    ) from exc
                if not isinstance(loaded, dict):
                    raise AnalysisError(
                        f"{path}:{line_number}: record must be an object"
                    )
                records.append(loaded)
    except OSError as exc:
        raise AnalysisError(f"cannot read {path}: {exc}") from exc
    if not records:
        raise AnalysisError(f"{path} contains no request records")
    return records


def workload_value(record: Mapping[str, Any], key: str, fallback: str) -> str:
    workload = record.get("workload")
    if isinstance(workload, Mapping):
        value = workload.get(key)
        if isinstance(value, str) and value:
            return value
    return fallback


def successful(record: Mapping[str, Any]) -> bool:
    return record.get("success") is True


def scalar_values(
    records: Iterable[Mapping[str, Any]], key: str
) -> list[float]:
    values: list[float] = []
    for record in records:
        if not successful(record):
            continue
        value = finite_number(record.get(key))
        if value is not None:
            values.append(value)
    return values


def stream_gap_values(
    records: Iterable[Mapping[str, Any]],
) -> list[float]:
    values: list[float] = []
    for record in records:
        if not successful(record):
            continue
        raw = record.get("itl_ms")
        if not isinstance(raw, list):
            continue
        for item in raw:
            value = finite_number(item)
            if value is not None and value >= 0:
                values.append(value)
    return values


def summarize_group(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    completed_records = [record for record in records if successful(record)]
    input_tokens = [
        value
        for record in completed_records
        if (value := finite_number(record.get("input_tokens"))) is not None
    ]
    output_tokens = [
        value
        for record in completed_records
        if (value := finite_number(record.get("output_tokens"))) is not None
    ]
    scheduled = len(records)
    completed = len(completed_records)
    return {
        "scheduled": scheduled,
        "completed": completed,
        "failed": scheduled - completed,
        "completion_ratio": completed / scheduled if scheduled else 0.0,
        "error_rate": (scheduled - completed) / scheduled if scheduled else 0.0,
        "mean_input_tokens": (
            sum(input_tokens) / len(input_tokens) if input_tokens else None
        ),
        "mean_output_tokens": (
            sum(output_tokens) / len(output_tokens) if output_tokens else None
        ),
        "ttft_ms": metric_summary(scalar_values(records, "ttft_ms")),
        "tpot_ms": metric_summary(scalar_values(records, "tpot_ms")),
        "e2e_ms": metric_summary(scalar_values(records, "e2e_ms")),
        "stream_gap_ms": metric_summary(stream_gap_values(records)),
    }


def merged_thresholds(
    tier: Mapping[str, Any], category: str | None
) -> dict[str, Any]:
    default = tier.get("default") or {}
    if not isinstance(default, Mapping):
        raise AnalysisError("tier.default must be an object")
    merged = dict(default)
    request_limits = default.get("request_limits") or {}
    if not isinstance(request_limits, Mapping):
        raise AnalysisError("tier.default.request_limits must be an object")
    merged_request_limits = dict(request_limits)
    overrides = tier.get("class_overrides") or {}
    if not isinstance(overrides, Mapping):
        raise AnalysisError("tier.class_overrides must be an object")
    if category is not None:
        override = overrides.get(category) or {}
        if not isinstance(override, Mapping):
            raise AnalysisError(
                f"class override for {category!r} must be an object"
            )
        merged.update(override)
        override_limits = override.get("request_limits") or {}
        if not isinstance(override_limits, Mapping):
            raise AnalysisError(
                f"class override request_limits for {category!r} "
                "must be an object"
            )
        merged_request_limits.update(override_limits)
    if merged_request_limits:
        merged["request_limits"] = merged_request_limits
    return merged


def threshold_reasons(
    group: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    *,
    label: str,
    enforce_minimum_samples: bool = True,
) -> list[str]:
    reasons: list[str] = []
    minimum_samples = int(thresholds.get("minimum_samples", 1))
    if (
        enforce_minimum_samples
        and int(group.get("scheduled", 0)) < minimum_samples
    ):
        reasons.append(
            f"{label}: samples {group.get('scheduled', 0)} < {minimum_samples}"
        )
    minimum_completion = finite_number(
        thresholds.get("minimum_completion_ratio")
    )
    if (
        minimum_completion is not None
        and float(group.get("completion_ratio", 0.0)) < minimum_completion
    ):
        reasons.append(
            f"{label}: completion {group.get('completion_ratio')!r} "
            f"< {minimum_completion}"
        )
    maximum_error = finite_number(thresholds.get("maximum_error_rate"))
    if (
        maximum_error is not None
        and float(group.get("error_rate", 1.0)) > maximum_error
    ):
        reasons.append(
            f"{label}: error rate {group.get('error_rate')!r} "
            f"> {maximum_error}"
        )
    mean_output = finite_number(group.get("mean_output_tokens")) or 0.0
    for threshold_name, (metric_name, percentile_name) in THRESHOLD_TO_METRIC.items():
        limit = finite_number(thresholds.get(threshold_name))
        if limit is None:
            continue
        metric = group.get(metric_name)
        value = (
            finite_number(metric.get(percentile_name))
            if isinstance(metric, Mapping)
            else None
        )
        if value is None:
            if metric_name == "tpot_ms" and mean_output <= 1:
                continue
            reasons.append(f"{label}: {threshold_name} has no samples")
        elif value > limit:
            reasons.append(
                f"{label}: {threshold_name} {value:.3f} ms > {limit:.3f} ms"
            )
    return reasons


def request_passes(
    record: Mapping[str, Any], thresholds: Mapping[str, Any]
) -> bool:
    if not successful(record):
        return False
    limits = thresholds.get("request_limits") or {}
    if not isinstance(limits, Mapping):
        raise AnalysisError("request_limits must be an object")
    metric_keys = {
        "ttft_ms": "ttft_ms",
        "tpot_ms": "tpot_ms",
        "e2e_ms": "e2e_ms",
        "maximum_stream_gap_ms": "stream_gap_ms",
    }
    for limit_name, record_name in metric_keys.items():
        limit = finite_number(limits.get(limit_name))
        if limit is None:
            continue
        if record_name == "stream_gap_ms":
            gaps = [
                value
                for item in (record.get("itl_ms") or [])
                if (value := finite_number(item)) is not None
            ]
            value = max(gaps) if gaps else None
        else:
            value = finite_number(record.get(record_name))
        if value is None:
            if record_name == "tpot_ms":
                output_tokens = finite_number(record.get("output_tokens")) or 0
                if output_tokens <= 1:
                    continue
            return False
        if value > limit:
            return False
    return True


def classify_tier(
    *,
    name: str,
    tier: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    overall: Mapping[str, Any],
    by_category: Mapping[str, Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    overall_thresholds = merged_thresholds(tier, None)
    if tier.get("gate_overall_latency") is False:
        for threshold_name in THRESHOLD_TO_METRIC:
            overall_thresholds.pop(threshold_name, None)
    reasons = threshold_reasons(
        overall, overall_thresholds, label="overall"
    )
    category_results: dict[str, Any] = {}
    # A category receives only its arrival share in a mixed workload, so its
    # standalone minimum can be unreachable at every sustainable rate. An
    # advisory minimum preserves the overall sample gate and every category
    # latency/error gate while explicitly labeling sparse categories.
    advisory_samples = (
        len(by_category) > 1
        and tier.get("mixed_category_minimum_samples") == "advisory"
    )
    for category, group in sorted(by_category.items()):
        thresholds = merged_thresholds(tier, category)
        category_reasons = threshold_reasons(
            group,
            thresholds,
            label=f"category {category}",
            enforce_minimum_samples=not advisory_samples,
        )
        category_results[category] = {
            "pass": not category_reasons,
            "reasons": category_reasons,
        }
        minimum_samples = int(thresholds.get("minimum_samples", 1))
        if advisory_samples and int(group.get("scheduled", 0)) < minimum_samples:
            category_results[category]["insufficient_evidence"] = (
                f"samples {group.get('scheduled', 0)} < {minimum_samples}"
            )
        reasons.extend(category_reasons)

    required = tier.get("required_categories") or []
    if not isinstance(required, list):
        raise AnalysisError(f"tier {name}.required_categories must be a list")
    for category in required:
        if category not in by_category:
            reasons.append(f"required category {category!r} has no samples")

    queue_limit = finite_number(
        (tier.get("default") or {}).get("maximum_queue_slope_ms_per_s")
    )
    queue_slope = finite_number(summary.get("queue_slope_ms_per_s"))
    if queue_limit is not None and (
        queue_slope is None or queue_slope > queue_limit
    ):
        reasons.append(
            f"overall: queue slope {queue_slope!r} > {queue_limit} ms/s"
        )
    if summary.get("concurrency_bound") is True:
        reasons.append("overall: open-loop safety concurrency bound was reached")

    qualified = 0
    for record in records:
        category = workload_value(record, "category", "unknown")
        thresholds = merged_thresholds(tier, category)
        if request_passes(record, thresholds):
            qualified += 1
    run_duration = finite_number(summary.get("run_duration_s"))
    goodput = (
        qualified / run_duration
        if run_duration is not None and run_duration > 0
        else None
    )
    return {
        "pass": not reasons,
        "reasons": reasons,
        "qualified_requests": qualified,
        "slo_goodput_rps": goodput,
        "category_results": category_results,
    }


def analyze(
    *,
    records: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
    slo_config: Mapping[str, Any] | None = None,
    source_requests: str | None = None,
    source_summary: str | None = None,
) -> dict[str, Any]:
    categories: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    variants: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        categories[workload_value(record, "category", "unknown")].append(record)
        variants[workload_value(record, "variant", "unknown")].append(record)

    overall = summarize_group(records)
    by_category = {
        name: summarize_group(items) for name, items in sorted(categories.items())
    }
    by_variant = {
        name: summarize_group(items) for name, items in sorted(variants.items())
    }
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "evidence_class": "post_run_latency_analysis",
        "source_requests": source_requests,
        "source_summary": source_summary,
        "mode": summary.get("mode"),
        "configured_request_rate": summary.get("configured_request_rate"),
        "configured_concurrency": summary.get("configured_concurrency"),
        "request_rps": summary.get("request_rps"),
        "offered_request_rps": summary.get("offered_request_rps"),
        "queue_slope_ms_per_s": summary.get("queue_slope_ms_per_s"),
        "concurrency_bound": summary.get("concurrency_bound"),
        "stream_gap_semantics": (
            "SSE chunk gap; not a per-token ITL when one chunk carries multiple tokens"
        ),
        "overall": overall,
        "by_category": by_category,
        "by_variant": by_variant,
        "slo_tiers": {},
    }
    if slo_config is not None:
        tiers = slo_config.get("slo_tiers") or {}
        if not isinstance(tiers, Mapping):
            raise AnalysisError("slo_config.slo_tiers must be an object")
        result["slo_tiers"] = {
            str(name): classify_tier(
                name=str(name),
                tier=tier,
                records=records,
                overall=overall,
                by_category=by_category,
                summary=summary,
            )
            for name, tier in tiers.items()
            if isinstance(tier, Mapping)
        }
    return result


def load_slo_config(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AnalysisError(f"cannot read SLO config {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise AnalysisError(f"{path} must contain a YAML object")
    return loaded


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Post-process a completed latency load-generator run."
    )
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--slo-config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    result = analyze(
        records=read_records(args.requests),
        summary=read_json(args.summary),
        slo_config=load_slo_config(args.slo_config),
        source_requests=str(args.requests.resolve()),
        source_summary=str(args.summary.resolve()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as exc:
        raise SystemExit(f"error: {exc}") from exc
